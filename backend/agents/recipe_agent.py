from typing import Dict, List, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langgraph.graph import StateGraph, START, END, MessagesState
from pydantic import BaseModel, Field

from config import Config
from services.gemini_service import GeminiService
from services.recipe_api_service import RecipeAPIService

class RecipeAgentState(MessagesState):
    query_type: str = "unknown"
    ingredients: List[str] = []
    recipes: List[Dict] = []
    context: str = ""
    image_data: str = ""

class IngredientRecognitionTool(BaseTool):
    name: str = "ingredient_recognition"
    description: str = "Identifies ingredients from an uploaded image"
    gemini_service: GeminiService = Field(exclude=True)
    def __init__(self, gemini_service: GeminiService, **kwargs):
        super().__init__(gemini_service=gemini_service, **kwargs)
    def _run(self, image_data: str) -> str:
        ingredients = self.gemini_service.identify_ingredients(image_data)
        return f"Identified ingredients: {', '.join(ingredients)}"

class RecipeSearchTool(BaseTool):
    name: str = "recipe_search"
    description: str = "Searches for recipes based on ingredients or recipe names"
    gemini_service: GeminiService = Field(exclude=True)
    recipe_api_service: RecipeAPIService = Field(exclude=True)
    def __init__(self, gemini_service: GeminiService, recipe_api_service: RecipeAPIService, **kwargs):
        super().__init__(gemini_service=gemini_service, recipe_api_service=recipe_api_service, **kwargs)
    def _run(self, query: str, ingredients: List[str] = None) -> str:
        external_recipes = []
        ai_recipes = []
        try:
            if ingredients:
                external_recipes = self.recipe_api_service.search_recipes_by_ingredients(ingredients)
                if len(external_recipes) < 3:
                    ai_recipes = self.gemini_service.suggest_recipes(ingredients)
            else:
                external_recipes = self.recipe_api_service.search_recipes_by_query(query)
                if len(external_recipes) < 3:
                    ai_recipes = self.gemini_service.suggest_recipes([query])
        except Exception as e:
            print(f"External API error, using AI fallback: {str(e)}")
            if ingredients:
                ai_recipes = self.gemini_service.suggest_recipes(ingredients)
            else:
                ai_recipes = self.gemini_service.suggest_recipes([query])
        all_recipes = external_recipes + ai_recipes
        recipe_names = [r['name'] for r in all_recipes[:5]]
        return f"Found {len(all_recipes)} recipes: {recipe_names}"

class CookingQuestionTool(BaseTool):
    name: str = "cooking_question"
    description: str = "Answers cooking-related questions, techniques, and clarifications"
    gemini_service: GeminiService = Field(exclude=True)
    def __init__(self, gemini_service: GeminiService, **kwargs):
        super().__init__(gemini_service=gemini_service, **kwargs)
    def _run(self, question: str, context: str = "") -> str:
        return self.gemini_service.answer_cooking_question(question, context)

class HuggingFaceIngredientRecognitionTool(BaseTool):
    name: str = "hf_ingredient_recognition"
    description: str = "Identifies food class from an uploaded image using HuggingFace ViT (food101)"
    gemini_service: GeminiService = Field(exclude=True)
    def __init__(self, gemini_service: GeminiService, **kwargs):
        super().__init__(gemini_service=gemini_service, **kwargs)
    def _run(self, image_data: str) -> str:
        try:
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            import base64, io
            from PIL import Image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            food_label = self.gemini_service._hf_predict(image)
            return f"[HF] Predicted food: {food_label.replace('_', ' ')}"
        except Exception as e:
            return f"[HF] Error: {str(e)}"

class RecipeAgent:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        self.gemini_service = GeminiService()
        self.recipe_api_service = RecipeAPIService()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=Config.GEMINI_API_KEY,
            temperature=0.7
        )
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=2000,
            return_messages=True
        )
        self.tools = [
            IngredientRecognitionTool(self.gemini_service),
            HuggingFaceIngredientRecognitionTool(self.gemini_service),
            RecipeSearchTool(self.gemini_service, self.recipe_api_service),
            CookingQuestionTool(self.gemini_service)
        ]
        self.graph = self._create_graph()
    def _create_graph(self) -> StateGraph:
        def classify_query(state: RecipeAgentState) -> RecipeAgentState:
            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                query = last_message.content
                classification_prompt = f"""
                Analyze this user query and classify it into one of these categories:
                1. "recipe_search" - User wants to find recipes or cooking instructions
                2. "cooking_question" - User has questions about cooking techniques, ingredients, or food safety
                3. "ingredient_recognition" - User wants to identify ingredients from an image or already mentioned an image
                User query: "{query}"
                Additional context:
                - If the query mentions finding, making, or cooking specific dishes, it's recipe_search
                - If the query asks how, what, why, or asks for explanations, it's cooking_question  
                - If there's image data in the state or query mentions images/photos, it's ingredient_recognition
                Respond with only one word: recipe_search, cooking_question, or ingredient_recognition
                """
                try:
                    if state.get("image_data"):
                        state["query_type"] = "ingredient_recognition"
                    else:
                        response = self.llm.invoke([HumanMessage(content=classification_prompt)])
                        intent = response.content.strip().lower()
                        if intent in ["recipe_search", "cooking_question", "ingredient_recognition"]:
                            state["query_type"] = intent
                        else:
                            if any(word in query.lower() for word in ["recipe", "cook", "make", "dish", "meal"]):
                                state["query_type"] = "recipe_search"
                            elif any(word in query.lower() for word in ["how", "what", "why", "technique", "substitute", "mean"]):
                                state["query_type"] = "cooking_question"
                            else:
                                state["query_type"] = "cooking_question"
                except Exception as e:
                    print(f"LLM classification error: {str(e)}")
                    if any(word in query.lower() for word in ["recipe", "cook", "make", "ingredients"]):
                        state["query_type"] = "recipe_search"
                    elif any(word in query.lower() for word in ["how", "what", "why", "technique", "substitute"]):
                        state["query_type"] = "cooking_question"
                    else:
                        state["query_type"] = "cooking_question"
            return state
        def handle_recipe_search(state: RecipeAgentState) -> RecipeAgentState:
            last_message = state["messages"][-1]
            query = last_message.content
            ingredients = state.get("ingredients", [])
            recipe_tool = next(tool for tool in self.tools if tool.name == "recipe_search")
            try:
                if ingredients:
                    tool_result = recipe_tool._run(query, ingredients)
                    external_recipes = self.recipe_api_service.search_recipes_by_ingredients(ingredients)
                    ai_recipes = self.gemini_service.suggest_recipes(ingredients) if len(external_recipes) < 3 else []
                    recipes = external_recipes + ai_recipes
                else:
                    tool_result = recipe_tool._run(query)
                    external_recipes = self.recipe_api_service.search_recipes_by_query(query)
                    ai_recipes = self.gemini_service.suggest_recipes([query]) if len(external_recipes) < 3 else []
                    recipes = external_recipes + ai_recipes
                state["recipes"] = recipes[:5]
                if recipes:
                    response = f"I found {len(recipes)} recipes for you:\n\n"
                    for recipe in recipes[:3]:
                        response += f"**{recipe['name']}**\n"
                        response += f"Ingredients: {', '.join(recipe['ingredients'][:5])}\n\n"
                else:
                    response = "I couldn't find any recipes matching your request. Could you provide more details?"
            except Exception as e:
                print(f"Recipe search tool error: {str(e)}")
                response = "I'm having trouble finding recipes right now. Could you try rephrasing your request?"
            state["messages"].append(AIMessage(content=response))
            return state
        def handle_cooking_question(state: RecipeAgentState) -> RecipeAgentState:
            last_message = state["messages"][-1]
            query = last_message.content
            memory_context = ""
            try:
                memory_variables = self.memory.load_memory_variables({})
                if "history" in memory_variables:
                    memory_context = str(memory_variables["history"])
            except Exception as e:
                print(f"Memory load error: {str(e)}")
            recent_context = "\n".join([msg.content for msg in state["messages"][-3:-1]])
            full_context = f"Previous conversation: {memory_context}\nRecent messages: {recent_context}"
            cooking_tool = next(tool for tool in self.tools if tool.name == "cooking_question")
            try:
                response = cooking_tool._run(query, full_context)
            except Exception as e:
                response = "I'm having trouble answering that question right now. Please try again."
            state["messages"].append(AIMessage(content=response))
            return state
        def handle_ingredient_recognition(state: RecipeAgentState) -> RecipeAgentState:
            last_message = state["messages"][-1]
            image_data = state.get("image_data", "")
            ingredient_tool = next(tool for tool in self.tools if tool.name == "ingredient_recognition")
            hf_tool = next(tool for tool in self.tools if tool.name == "hf_ingredient_recognition")
            try:
                gemini_result = ingredient_tool._run(image_data)
            except Exception as e:
                gemini_result = f"[Gemini] Error: {str(e)}"
            try:
                hf_result = hf_tool._run(image_data)
            except Exception as e:
                hf_result = f"[HF] Error: {str(e)}"
            response = f"Gemini: {gemini_result}\nHuggingFace: {hf_result}"
            state["messages"].append(AIMessage(content=response))
            return state
        def route_query(state: RecipeAgentState) -> str:
            return state["query_type"]
        graph = StateGraph()
        graph.add_node("classify_query", classify_query)
        graph.add_node("handle_recipe_search", handle_recipe_search)
        graph.add_node("handle_cooking_question", handle_cooking_question)
        graph.add_node("handle_ingredient_recognition", handle_ingredient_recognition)
        graph.add_edge("classify_query", "handle_recipe_search", condition=lambda s: s["query_type"] == "recipe_search")
        graph.add_edge("classify_query", "handle_cooking_question", condition=lambda s: s["query_type"] == "cooking_question")
        graph.add_edge("classify_query", "handle_ingredient_recognition", condition=lambda s: s["query_type"] == "ingredient_recognition")
        graph.add_edge("handle_recipe_search", END)
        graph.add_edge("handle_cooking_question", END)
        graph.add_edge("handle_ingredient_recognition", END)
        graph.set_entry("classify_query")
        return graph
    def process_query(self, query: str, context: str = "", ingredients: List[str] = None) -> str:
        try:
            initial_state = RecipeAgentState(
                messages=[HumanMessage(content=query)],
                query_type="unknown",
                ingredients=ingredients or [],
                context=context
            )
            result = self.graph.invoke(initial_state)
            if result["messages"] and len(result["messages"]) > 1:
                assistant_response = result["messages"][-1].content
                try:
                    self.memory.save_context(
                        {"input": query},
                        {"output": assistant_response}
                    )
                except Exception as e:
                    print(f"Memory save error: {str(e)}")
                return assistant_response
            else:
                return "I'm sorry, I couldn't process your request. Could you please try again?"
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return "I'm experiencing some technical difficulties. Please try again later."
    def process_image_query(self, image_data: str, query: str = "") -> Dict[str, Any]:
        try:
            initial_state = RecipeAgentState(
                messages=[HumanMessage(content=query or "Please analyze this image for ingredients")],
                query_type="ingredient_recognition",
                image_data=image_data,
                ingredients=[],
                context=""
            )
            result = self.graph.invoke(initial_state)
            ingredients = result.get("ingredients", [])
            recipes = result.get("recipes", [])
            if ingredients:
                try:
                    ingredients_text = ", ".join(ingredients)
                    self.memory.save_context(
                        {"input": f"Image uploaded with ingredients: {ingredients_text}"},
                        {"output": f"I identified {len(ingredients)} ingredients and found {len(recipes)} recipes."}
                    )
                except Exception as e:
                    print(f"Memory save error for image query: {str(e)}")
            if not ingredients:
                return {
                    "ingredients": [],
                    "recipes": [],
                    "message": "I couldn't identify any ingredients in the image. Please try a clearer photo."
                }
            return {
                "ingredients": ingredients,
                "recipes": recipes,
                "message": f"I identified {len(ingredients)} ingredients and found {len(recipes)} recipes for you!"
            }
        except Exception as e:
            print(f"Error processing image query: {str(e)}")
            return {
                "ingredients": [],
                "recipes": [],
                "message": "I'm having trouble processing your image. Please try again."
            }
    def clear_memory(self):
        try:
            self.memory.clear()
        except Exception as e:
            print(f"Error clearing memory: {str(e)}")
    def get_conversation_history(self) -> str:
        try:
            memory_variables = self.memory.load_memory_variables({})
            return str(memory_variables.get("history", ""))
        except Exception as e:
            print(f"Error loading conversation history: {str(e)}")
            return ""