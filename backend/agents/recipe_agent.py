from typing import Dict, List, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import ChatPromptTemplate

from backend.config import Config
from backend.services.gemini_service import GeminiService
from backend.services.recipe_api_service import RecipeAPIService
from sklearn.cluster import KMeans
import numpy as np

@tool("ingredient_recognition", return_direct=True)
def ingredient_recognition_tool(image_data: str) -> str:
    """Identifies ingredients from an uploaded image using Gemini."""
    return GeminiService().identify_ingredients(image_data)

@tool("hf_ingredient_recognition", return_direct=True)
def hf_ingredient_recognition_tool(image_data: str) -> str:
    """Identifies food class from an uploaded image using HuggingFace ViT (food101)."""
    # TODO: Use HF fallback directly
    return "[HF fallback not implemented in this wrapper]"

@tool("recipe_search", return_direct=True)
def recipe_search_tool(query: str = "", ingredients: list = None) -> str:
    """Searches for recipes based on ingredients or recipe names."""
    return RecipeAPIService().search_recipes_by_ingredients(ingredients or [])

@tool("cooking_question", return_direct=True)
def cooking_question_tool(question: str, context: str = "") -> str:
    """Answers cooking-related questions, techniques, and clarifications."""
    return GeminiService().answer_cooking_question(question, context)

@tool("ingredient_embedding", return_direct=True)
def ingredient_embedding_tool(ingredients: list) -> list:
    """Returns vector embeddings for a list of ingredient strings."""
    return GeminiService().ingredient_embeddings(ingredients)

@tool("recipe_embedding", return_direct=True)
def recipe_embedding_tool(recipes: list) -> list:
    """Returns vector embeddings for a list of recipe dicts (name + ingredients)."""
    # recipes: list of dicts with 'name' and 'ingredients'
    def recipe_to_text(recipe):
        name = recipe.get("name", "")
        ingredients = recipe.get("ingredients", [])
        if isinstance(ingredients, list):
            ingredients = ", ".join(ingredients)
        return f"{name}: {ingredients}"
    texts = [recipe_to_text(r) for r in recipes]
    return GeminiService().ingredient_embeddings(texts)

@tool("ingredient_semantic_search", return_direct=True)
def ingredient_semantic_search_tool(query: str, candidates: list, top_n: int = 5) -> list:
    """Finds the most semantically similar ingredients to a query from a list of candidates."""
    all_ingredients = [query] + candidates
    embeddings = GeminiService().ingredient_embeddings(all_ingredients)
    query_emb = np.array(embeddings[0])
    candidate_embs = np.array(embeddings[1:])
    sims = candidate_embs @ query_emb / (np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb) + 1e-8)
    top_idx = sims.argsort()[::-1][:top_n]
    return [{"ingredient": candidates[i], "score": float(sims[i])} for i in top_idx]

@tool("recipe_semantic_search", return_direct=True)
def recipe_semantic_search_tool(query: str, candidates: list, top_n: int = 3) -> list:
    """Finds the most semantically similar recipes to a query from a list of candidate recipes."""
    def recipe_to_text(recipe):
        name = recipe.get("name", "")
        ingredients = recipe.get("ingredients", [])
        if isinstance(ingredients, list):
            ingredients = ", ".join(ingredients)
        return f"{name}: {ingredients}"
    candidate_texts = [recipe_to_text(r) for r in candidates]
    all_texts = [query] + candidate_texts
    embeddings = GeminiService().ingredient_embeddings(all_texts)
    query_emb = np.array(embeddings[0])
    candidate_embs = np.array(embeddings[1:])
    sims = candidate_embs @ query_emb / (np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb) + 1e-8)
    top_idx = sims.argsort()[::-1][:top_n]
    return [{"recipe": candidates[i], "score": float(sims[i])} for i in top_idx]

@tool("ingredient_cluster", return_direct=True)
def ingredient_cluster_tool(ingredients: list, k: int = 3) -> dict:
    """Clusters ingredients into k groups using KMeans on their embeddings."""
    embeddings = GeminiService().ingredient_embeddings(ingredients)
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    clusters = [{"ingredient": ing, "cluster": int(label)} for ing, label in zip(ingredients, labels)]
    centroids = kmeans.cluster_centers_.tolist()
    return {"clusters": clusters, "centroids": centroids}

@tool("recipe_cluster", return_direct=True)
def recipe_cluster_tool(candidates: list, k: int = 3) -> dict:
    """Clusters recipes into k groups using KMeans on their embeddings."""
    def recipe_to_text(recipe):
        name = recipe.get("name", "")
        ingredients = recipe.get("ingredients", [])
        if isinstance(ingredients, list):
            ingredients = ", ".join(ingredients)
        return f"{name}: {ingredients}"
    texts = [recipe_to_text(r) for r in candidates]
    embeddings = GeminiService().ingredient_embeddings(texts)
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    clusters = [{"recipe": recipe, "cluster": int(label)} for recipe, label in zip(candidates, labels)]
    centroids = kmeans.cluster_centers_.tolist()
    return {"clusters": clusters, "centroids": centroids}

class RecipeAgent:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        self.gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=Config.GEMINI_API_KEY,
            temperature=0.7
        )
        # Fallback LLM
        self.fallback_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=Config.OPENAI_API_KEY if hasattr(Config, 'OPENAI_API_KEY') else None,
            temperature=0.7
        )
        self.memory = ConversationSummaryBufferMemory(
            llm=self.gemini_llm,
            max_token_limit=2000,
            return_messages=True
        )
        self.tools = [
            ingredient_recognition_tool,
            hf_ingredient_recognition_tool,
            recipe_search_tool,
            cooking_question_tool,
            ingredient_embedding_tool,
            recipe_embedding_tool,
            ingredient_semantic_search_tool,
            recipe_semantic_search_tool,
            ingredient_cluster_tool,
            recipe_cluster_tool,
            # TODO: Add more tools here
        ]
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI recipe assistant. You have access to tools for ingredient recognition, recipe search, semantic search, clustering, and more."),
            ("user", "{input}"),
            ("system", "{agent_scratchpad}")
        ])
        self.agent = create_tool_calling_agent(
            llm=self.gemini_llm,
            tools=self.tools,
            prompt=prompt
        )
        self.executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )
    def chat(self, query: str, context: str = "") -> str:
        # Direct chat, no tool use
        try:
            response = self.gemini_llm.invoke(query)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            # Fallback to OpenAI
            response = self.fallback_llm.invoke(query)
            return response.content if hasattr(response, 'content') else str(response)
    def tool_use(self, query: str, context: str = "", **kwargs) -> str:
        # Tool-use flow
        try:
            result = self.executor.invoke({"input": query, **kwargs})
            return result["output"] if isinstance(result, dict) and "output" in result else str(result)
        except Exception as e:
            return f"[Agent error] {str(e)}"