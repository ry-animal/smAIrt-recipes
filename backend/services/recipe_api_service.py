import requests
from typing import List, Dict, Any, Optional
from config import Config

class RecipeAPIService:
    """Service for integrating with external recipe APIs like Spoonacular"""
    
    def __init__(self):
        self.spoonacular_api_key = Config.SPOONACULAR_API_KEY
        self.spoonacular_base_url = "https://api.spoonacular.com/recipes"
    
    def search_recipes_by_ingredients(self, ingredients: List[str], number: int = 5) -> List[Dict[str, Any]]:
        """
        Search for recipes using Spoonacular API based on ingredients
        """
        if not self.spoonacular_api_key:
            print("Spoonacular API key not configured, using fallback")
            return []
        
        try:
            # Join ingredients with comma
            ingredients_str = ",".join(ingredients)
            
            url = f"{self.spoonacular_base_url}/findByIngredients"
            params = {
                "apiKey": self.spoonacular_api_key,
                "ingredients": ingredients_str,
                "number": number,
                "ranking": 1,  # Maximize used ingredients
                "ignorePantry": True
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            recipes_data = response.json()
            
            # Transform Spoonacular format to our format
            recipes = []
            for recipe_data in recipes_data:
                # Get detailed recipe information
                detailed_recipe = self._get_recipe_details(recipe_data["id"])
                if detailed_recipe:
                    recipes.append(detailed_recipe)
            
            return recipes
            
        except Exception as e:
            print(f"Error fetching recipes from Spoonacular: {str(e)}")
            return []
    
    def search_recipes_by_query(self, query: str, number: int = 5) -> List[Dict[str, Any]]:
        """
        Search for recipes using Spoonacular API based on a text query
        """
        if not self.spoonacular_api_key:
            print("Spoonacular API key not configured, using fallback")
            return []
        
        try:
            url = f"{self.spoonacular_base_url}/complexSearch"
            params = {
                "apiKey": self.spoonacular_api_key,
                "query": query,
                "number": number,
                "addRecipeInformation": True,
                "fillIngredients": True
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            recipes_data = data.get("results", [])
            
            # Transform to our format
            recipes = []
            for recipe_data in recipes_data:
                transformed_recipe = self._transform_spoonacular_recipe(recipe_data)
                if transformed_recipe:
                    recipes.append(transformed_recipe)
            
            return recipes
            
        except Exception as e:
            print(f"Error searching recipes from Spoonacular: {str(e)}")
            return []
    
    def _get_recipe_details(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed recipe information from Spoonacular"""
        try:
            url = f"{self.spoonacular_base_url}/{recipe_id}/information"
            params = {
                "apiKey": self.spoonacular_api_key,
                "includeNutrition": False
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            recipe_data = response.json()
            return self._transform_spoonacular_recipe(recipe_data)
            
        except Exception as e:
            print(f"Error fetching recipe details: {str(e)}")
            return None
    
    def _transform_spoonacular_recipe(self, spoonacular_data: Dict) -> Dict[str, Any]:
        """Transform Spoonacular recipe format to our internal format"""
        try:
            # Extract ingredients
            ingredients = []
            if "extendedIngredients" in spoonacular_data:
                ingredients = [
                    ingredient.get("original", ingredient.get("name", "Unknown ingredient"))
                    for ingredient in spoonacular_data["extendedIngredients"]
                ]
            
            # Extract instructions
            instructions = ""
            if "instructions" in spoonacular_data and spoonacular_data["instructions"]:
                instructions = spoonacular_data["instructions"]
            elif "analyzedInstructions" in spoonacular_data:
                # Parse step-by-step instructions
                instruction_steps = []
                for instruction_group in spoonacular_data["analyzedInstructions"]:
                    if "steps" in instruction_group:
                        for step in instruction_group["steps"]:
                            step_text = step.get("step", "")
                            if step_text:
                                instruction_steps.append(f"{step.get('number', len(instruction_steps) + 1)}. {step_text}")
                instructions = "\n".join(instruction_steps)
            
            # Get cooking time
            cooking_time = "Unknown"
            ready_in_minutes = spoonacular_data.get("readyInMinutes")
            if ready_in_minutes:
                cooking_time = f"{ready_in_minutes} minutes"
            
            # Get servings
            servings = spoonacular_data.get("servings", 4)
            
            return {
                "name": spoonacular_data.get("title", "Unknown Recipe"),
                "ingredients": ingredients,
                "instructions": instructions or "Instructions not available",
                "cooking_time": cooking_time,
                "servings": servings,
                "source": "Spoonacular",
                "id": spoonacular_data.get("id"),
                "image": spoonacular_data.get("image"),
                "source_url": spoonacular_data.get("sourceUrl")
            }
            
        except Exception as e:
            print(f"Error transforming Spoonacular recipe: {str(e)}")
            return None