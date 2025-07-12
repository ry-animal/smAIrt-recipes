#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json

app = FastAPI(title="Working Recipe API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngredientSearchRequest(BaseModel):
    ingredients: List[str]

class ImageUpload(BaseModel):
    image_data: str

class RecipeResponse(BaseModel):
    recipes: List[dict]
    ingredients_identified: Optional[List[str]] = None

# Mock Gemini service for ingredient identification
def mock_identify_ingredients(image_data: str) -> List[str]:
    """Mock ingredient identification - returns random common ingredients"""
    import random
    
    common_ingredients = [
        ["tomato", "onion", "garlic"],
        ["carrot", "potato", "celery"], 
        ["broccoli", "bell pepper", "zucchini"],
        ["chicken", "onion", "herbs"],
        ["beef", "mushroom", "onion"],
        ["pasta", "tomato", "basil"],
        ["rice", "vegetables", "soy sauce"],
        ["eggs", "cheese", "herbs"],
        ["apple", "cinnamon", "oats"],
        ["banana", "berries", "yogurt"]
    ]
    
    return random.choice(common_ingredients)

def create_recipes_from_ingredients(ingredients: List[str]) -> List[dict]:
    """Create structured recipes from ingredients"""
    ingredients_str = ", ".join(ingredients)
    
    recipes = [
        {
            "name": f"Stir-Fry with {ingredients_str}",
            "ingredients": ingredients + ["2 tbsp oil", "2 cloves garlic", "1 tbsp soy sauce", "salt", "pepper"],
            "instructions": f"1. Heat oil in a large pan over medium-high heat\n2. Add minced garlic and cook for 1 minute\n3. Add {ingredients[0]} and cook for 3-4 minutes\n4. Add remaining ingredients: {', '.join(ingredients[1:]) if len(ingredients) > 1 else ''}\n5. Stir-fry for 5-7 minutes until tender\n6. Season with soy sauce, salt, and pepper\n7. Serve hot over rice",
            "cooking_time": "15 minutes",
            "servings": 4,
            "source": "Generated Recipe"
        },
        {
            "name": f"Roasted {ingredients_str}",
            "ingredients": ingredients + ["3 tbsp olive oil", "1 tsp herbs", "salt", "pepper"],
            "instructions": f"1. Preheat oven to 425°F (220°C)\n2. Wash and chop vegetables into uniform pieces\n3. Toss with olive oil, herbs, salt, and pepper\n4. Spread on baking sheet in single layer\n5. Roast for 25-30 minutes, stirring once\n6. Cook until golden and tender\n7. Serve as side or main dish",
            "cooking_time": "35 minutes", 
            "servings": 4,
            "source": "Generated Recipe"
        }
    ]
    
    # Add a third recipe if we have enough ingredients
    if len(ingredients) >= 2:
        recipes.append({
            "name": f"Simple Soup with {ingredients_str}",
            "ingredients": ingredients + ["4 cups broth", "1 onion", "2 cloves garlic", "salt", "pepper"],
            "instructions": f"1. Sauté onion and garlic in pot until fragrant\n2. Add chopped {ingredients[0]} and cook 5 minutes\n3. Add remaining vegetables: {', '.join(ingredients[1:]) if len(ingredients) > 1 else ''}\n4. Pour in broth and bring to boil\n5. Simmer 20-25 minutes until tender\n6. Season with salt and pepper\n7. Serve hot with bread",
            "cooking_time": "30 minutes",
            "servings": 4,
            "source": "Generated Recipe"
        })
    
    return recipes

@app.get("/")
def root():
    return {"message": "Working Recipe API", "status": "ready"}

@app.post("/api/analyze-ingredients", response_model=RecipeResponse)
def analyze_ingredients(upload: ImageUpload):
    """Analyze uploaded image to identify ingredients"""
    try:
        print(f"📷 Analyzing image (size: {len(upload.image_data)} chars)")
        
        # Mock ingredient identification
        identified_ingredients = mock_identify_ingredients(upload.image_data)
        print(f"🥕 Identified ingredients: {identified_ingredients}")
        
        # Generate recipes
        recipes = create_recipes_from_ingredients(identified_ingredients)
        print(f"📝 Generated {len(recipes)} recipes")
        
        return RecipeResponse(
            recipes=recipes,
            ingredients_identified=identified_ingredients
        )
        
    except Exception as e:
        print(f"❌ Error analyzing ingredients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-recipes", response_model=RecipeResponse) 
def search_recipes(request: IngredientSearchRequest):
    """Search for recipes based on ingredients"""
    try:
        print(f"🔍 Searching recipes for: {request.ingredients}")
        
        recipes = create_recipes_from_ingredients(request.ingredients)
        print(f"📝 Generated {len(recipes)} recipes")
        
        return RecipeResponse(
            recipes=recipes,
            ingredients_identified=request.ingredients
        )
        
    except Exception as e:
        print(f"❌ Error searching recipes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Working Recipe API on http://localhost:8000")
    print("📱 Frontend should connect to this server")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")