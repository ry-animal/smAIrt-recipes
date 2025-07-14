import base64
import json
from typing import List, Dict, Any
import google.generativeai as genai
from PIL import Image
import io
import torch
from transformers import ViTImageProcessor, ViTForImageClassification
from sentence_transformers import SentenceTransformer
from threading import Lock
import redis
import hashlib
import logging
import re

from backend.config import Config

class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.hf_processor = None
        self.hf_model = None
        self.hf_class_names = None
        self.st_model = None
        self._embedding_cache = {}
        self._embedding_cache_lock = Lock()
        self._use_redis = True
        try:
            self.redis = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=False
            )
            # Test connection
            self.redis.ping()
        except Exception as e:
            logging.warning(f"Redis unavailable, falling back to in-memory cache: {e}")
            self._use_redis = False
            self.redis = None

    def _hf_load(self):
        if self.hf_processor is None or self.hf_model is None:
            self.hf_processor = ViTImageProcessor.from_pretrained("nateraw/food")
            self.hf_model = ViTForImageClassification.from_pretrained("nateraw/food")
            self.hf_class_names = self.hf_model.config.id2label

    def _hf_predict(self, image: 'PIL.Image.Image') -> str:
        self._hf_load()
        inputs = self.hf_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            logits = self.hf_model(**inputs).logits
        predicted_class_idx = logits.argmax(-1).item()
        return self.hf_class_names[predicted_class_idx]

    def ingredient_embeddings(self, ingredients: list[str]) -> list[list[float]]:
        if self.st_model is None:
            self.st_model = SentenceTransformer('all-MiniLM-L6-v2')
        key_str = json.dumps(ingredients, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()
        redis_key = f"embedding:{key_hash}"
        if self._use_redis and self.redis:
            try:
                cached = self.redis.get(redis_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logging.warning(f"Redis error, using in-memory cache: {e}")
                self._use_redis = False
        if not self._use_redis:
            with self._embedding_cache_lock:
                if redis_key in self._embedding_cache:
                    return self._embedding_cache[redis_key]
        embeddings = self.st_model.encode(ingredients, convert_to_numpy=True).tolist()
        if self._use_redis and self.redis:
            try:
                self.redis.set(redis_key, json.dumps(embeddings))
            except Exception as e:
                logging.warning(f"Redis set error, using in-memory cache: {e}")
                self._use_redis = False
        if not self._use_redis:
            with self._embedding_cache_lock:
                self._embedding_cache[redis_key] = embeddings
        return embeddings

    def identify_ingredients(self, image_data: str) -> List[str]:
        try:
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
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
                )
            )
            response = model.generate_content([prompt, image])
            result = json.loads(response.text)
            ingredients = result.get("ingredients", [])
            cleaned_ingredients = []
            for ingredient in ingredients:
                if isinstance(ingredient, str) and ingredient.strip():
                    cleaned_ingredients.append(ingredient.strip().lower())
            if cleaned_ingredients:
                return cleaned_ingredients
        except Exception as e:
            print(f"Error identifying ingredients with Gemini: {str(e)}")
        # HuggingFace fallback
        try:
            if image is None:
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            food_label = self._hf_predict(image)
            print(f"[HF fallback] Predicted food: {food_label}")
            return [food_label.replace('_', ' ')]
        except Exception as e:
            print(f"Error in HuggingFace fallback: {str(e)}")
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
            You must return exactly 3 specific recipes that can be made primarily with these ingredients.
            Return your answer as a valid JSON object with a single key 'recipes', whose value is an array of 3 recipe objects.
            Each recipe object must have:
            - name (string)
            - ingredients (array of strings, with quantities, e.g., '1 cup onion')
            - instructions (string, numbered steps separated by newlines)
            - cooking_time (string)
            - servings (integer)
            Example:
            {{"recipes": [
              {{"name": "Recipe 1", "ingredients": ["1 cup onion"], "instructions": "1. ...", "cooking_time": "30 minutes", "servings": 4}},
              {{"name": "Recipe 2", "ingredients": ["2 cups flour"], "instructions": "1. ...", "cooking_time": "45 minutes", "servings": 6}},
              {{"name": "Recipe 3", "ingredients": ["1 lb meat"], "instructions": "1. ...", "cooking_time": "60 minutes", "servings": 4}}
            ]}}
            {f"Consider these dietary preferences: {dietary_preferences}" if dietary_preferences else ""}
            Make the recipes practical and achievable with common cooking methods.
            """
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=genai.GenerationConfig(
                )
            )
            response = model.generate_content(prompt)
            # Robust JSON extraction
            raw_text = response.text
            json_str = None
            try:
                # Try direct parse
                result = json.loads(raw_text)
            except Exception:
                # Try to extract JSON substring
                match = re.search(r'\{\s*"recipes"\s*:\s*\[.*?\]\s*\}', raw_text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        result = json.loads(json_str)
                    except Exception as e:
                        print(f"Error parsing extracted JSON: {e}\nExtracted: {json_str}")
                        result = {}
                else:
                    print(f"No JSON object found in Gemini output:\n{raw_text}")
                    result = {}
            recipes = result.get("recipes", []) if isinstance(result, dict) else []
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
            if len(formatted_recipes) < 3:
                print(f"Gemini output did not yield 3 valid recipes. Raw output:\n{raw_text}")
                return self._create_fallback_recipe(ingredients)
            return formatted_recipes
        except Exception as e:
            print(f"Error suggesting recipes with structured output: {str(e)}")
            return self._create_fallback_recipe(ingredients)

    def _create_fallback_recipe(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        try:
            ingredients_str = ", ".join(ingredients[:3])
            
            # Create 3 diverse fallback recipes
            fallback_recipes = [
                {
                    "name": f"Simple Stir-Fry with {ingredients_str}",
                    "ingredients": ingredients + ["2 tbsp olive oil", "1 tsp salt", "1/2 tsp black pepper", "2 cloves garlic"],
                    "instructions": f"1. Heat olive oil in a large pan over medium-high heat\n2. Add garlic and cook for 1 minute until fragrant\n3. Add {ingredients[0]} and cook for 3-4 minutes\n4. Add remaining vegetables: {', '.join(ingredients[1:])}\n5. Stir-fry for 5-7 minutes until vegetables are tender-crisp\n6. Season with salt and pepper to taste\n7. Serve immediately while hot",
                    "cooking_time": "15 minutes",
                    "servings": 4,
                    "source": "Fallback Recipe"
                },
                {
                    "name": f"Roasted {ingredients_str} with Herbs",
                    "ingredients": ingredients + ["3 tbsp olive oil", "1 tsp dried thyme", "1 tsp dried rosemary", "Salt and pepper"],
                    "instructions": f"1. Preheat oven to 425°F (220°C)\n2. Cut vegetables into similar-sized pieces\n3. Toss with olive oil, thyme, rosemary, salt and pepper\n4. Spread on a baking sheet in single layer\n5. Roast for 25-30 minutes until tender and golden\n6. Serve as a side dish or over grains",
                    "cooking_time": "30 minutes",
                    "servings": 4,
                    "source": "Fallback Recipe"
                },
                {
                    "name": f"{ingredients_str} Soup",
                    "ingredients": ingredients + ["4 cups vegetable broth", "1 onion diced", "2 cloves garlic", "1 tbsp olive oil", "Salt and pepper"],
                    "instructions": f"1. Heat olive oil in a large pot over medium heat\n2. Add diced onion and garlic, cook until fragrant\n3. Add chopped vegetables and cook for 5 minutes\n4. Pour in vegetable broth and bring to a boil\n5. Reduce heat and simmer for 20-25 minutes until vegetables are tender\n6. Season with salt and pepper to taste\n7. Serve hot with crusty bread",
                    "cooking_time": "35 minutes",
                    "servings": 4,
                    "source": "Fallback Recipe"
                }
            ]
            
            return fallback_recipes
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
                )
            )
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            shopping_items = result.get("shopping_items", [])
            return shopping_items
        except Exception as e:
            print(f"Error generating shopping list: {str(e)}")
            return []