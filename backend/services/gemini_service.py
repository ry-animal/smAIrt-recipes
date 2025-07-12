import base64
import json
from typing import List, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

from config import Config

class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def identify_ingredients(self, image_data: str) -> List[str]:
        try:
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            ingredient_schema = {
                "type": "object",
                "properties": {
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["ingredients"]
            }
            prompt = """
            Analyze this image and identify all the food ingredients you can see.
            Focus on identifying:
            - Vegetables (onions, tomatoes, peppers, carrots, broccoli, etc.)
            - Fruits (apples, bananas, citrus, berries, etc.)
            - Proteins (meat, fish, chicken, eggs, tofu, etc.)
            - Grains and starches (rice, pasta, bread, potatoes, etc.)
            - Herbs and spices (basil, parsley, garlic, ginger, etc.)
            - Dairy products (milk, cheese, yogurt, etc.)
            - Other cooking ingredients (oils, sauces, etc.)
            Return each ingredient as a simple, clear name (e.g., "onion", "carrot", "chicken breast").
            Only include ingredients you can clearly identify in the image.
            """
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ingredient_schema
                )
            )
            response = model.generate_content([prompt, image])
            result = json.loads(response.text)
            ingredients = result.get("ingredients", [])
            cleaned_ingredients = []
            for ingredient in ingredients:
                if isinstance(ingredient, str) and ingredient.strip():
                    cleaned_ingredients.append(ingredient.strip().lower())
            return cleaned_ingredients
        except Exception as e:
            print(f"Error identifying ingredients with structured output: {str(e)}")
            return []

    def suggest_recipes(self, ingredients: List[str], dietary_preferences: str = None) -> List[Dict[str, Any]]:
        try:
            ingredients_str = ', '.join(ingredients)
            recipe_schema = {
                "type": "object",
                "properties": {
                    "recipes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "ingredients": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "instructions": {"type": "string"},
                                "cooking_time": {"type": "string"},
                                "servings": {"type": "integer"}
                            },
                            "required": ["name", "ingredients", "instructions", "cooking_time", "servings"]
                        }
                    }
                },
                "required": ["recipes"]
            }
            prompt = f"""
            Based on these ingredients: {ingredients_str}
            Please suggest 2-3 specific recipes that can be made primarily with these ingredients.
            {f"Consider these dietary preferences: {dietary_preferences}" if dietary_preferences else ""}
            For each recipe, provide:
            - A descriptive recipe name
            - Complete ingredients list with quantities (e.g., "1 cup onion", "2 tbsp olive oil")
            - Step-by-step cooking instructions as a single string with numbered steps separated by newlines
            - Estimated cooking time (e.g., "30 minutes")
            - Number of servings as an integer
            Make the recipes practical and achievable with common cooking methods.
            """
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=recipe_schema
                )
            )
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            recipes = result.get("recipes", [])
            formatted_recipes = []
            for recipe in recipes:
                if all(key in recipe for key in ["name", "ingredients", "instructions", "cooking_time", "servings"]):
                    formatted_recipes.append({
                        "name": recipe["name"],
                        "ingredients": recipe["ingredients"],
                        "instructions": recipe["instructions"],
                        "cooking_time": recipe["cooking_time"],
                        "servings": recipe["servings"],
                        "source": "AI Generated"
                    })
            return formatted_recipes if formatted_recipes else self._create_fallback_recipe(ingredients)
        except Exception as e:
            print(f"Error suggesting recipes with structured output: {str(e)}")
            return self._create_fallback_recipe(ingredients)

    def _create_fallback_recipe(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        try:
            ingredients_str = ", ".join(ingredients[:3])
            fallback_recipe = {
                "name": f"Simple Stir-Fry with {ingredients_str}",
                "ingredients": ingredients + ["2 tbsp olive oil", "1 tsp salt", "1/2 tsp black pepper", "2 cloves garlic"],
                "instructions": f"1. Heat olive oil in a large pan over medium-high heat\n2. Add garlic and cook for 1 minute until fragrant\n3. Add {ingredients[0]} and cook for 3-4 minutes\n4. Add remaining vegetables: {', '.join(ingredients[1:])}\n5. Stir-fry for 5-7 minutes until vegetables are tender-crisp\n6. Season with salt and pepper to taste\n7. Serve immediately while hot",
                "cooking_time": "15 minutes",
                "servings": 4,
                "source": "Fallback Recipe"
            }
            return [fallback_recipe]
        except Exception as e:
            print(f"Error creating fallback recipe: {str(e)}")
            return []

    def answer_cooking_question(self, question: str, context: str = None) -> str:
        try:
            prompt = f"""
            You are a knowledgeable cooking assistant. Please answer this cooking question:
            Question: {question}
            {f"Previous conversation context: {context}" if context else ""}
            Provide a helpful, clear, and practical answer. If the question is about:
            - Cooking techniques: Explain step-by-step
            - Ingredient substitutions: Provide alternatives and ratios
            - Recipe modifications: Give specific guidance
            - Food safety: Prioritize safety information
            Keep your response concise but informative.
            """
            response = self.text_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error answering cooking question: {str(e)}")
            return "I'm sorry, I'm having trouble answering that question right now. Please try again."

    def generate_shopping_list(self, recipe: Dict[str, Any], available_ingredients: List[str] = None) -> List[str]:
        try:
            available_str = ', '.join(available_ingredients) if available_ingredients else "none"
            shopping_schema = {
                "type": "object",
                "properties": {
                    "shopping_items": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["shopping_items"]
            }
            prompt = f"""
            Recipe: {recipe['name']}
            Recipe ingredients needed: {', '.join(recipe['ingredients'])}
            Already available ingredients: {available_str}
            Create a shopping list of ingredients that need to be purchased.
            Rules:
            1. Exclude ingredients that are already available
            2. Include quantities where specified in the recipe
            3. Only include items that actually need to be bought
            4. Use clear, specific item names (e.g., "1 lb ground beef", "2 large onions")
            """
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=shopping_schema
                )
            )
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            shopping_items = result.get("shopping_items", [])
            return shopping_items
        except Exception as e:
            print(f"Error generating shopping list: {str(e)}")
            return []