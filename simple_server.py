#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Simple Recipe API")

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

class RecipeResponse(BaseModel):
    recipes: List[dict]
    ingredients_identified: Optional[List[str]] = None

@app.get("/")
def root():
    return {"message": "Simple Recipe API is running"}

@app.post("/api/search-recipes", response_model=RecipeResponse)
def search_recipes(request: IngredientSearchRequest):
    """Simple recipe search endpoint"""
    ingredients = request.ingredients
    ingredients_str = ", ".join(ingredients)
    
    # Create test recipes
    recipes = [
        {
            "name": f"Vegetable Stir-Fry with {ingredients_str}",
            "ingredients": ingredients + ["2 tbsp soy sauce", "1 tbsp olive oil", "2 cloves garlic", "salt", "pepper"],
            "instructions": "1. Heat oil in a large pan\n2. Add garlic and cook for 1 minute\n3. Add vegetables and stir-fry for 5-7 minutes\n4. Season with soy sauce, salt, and pepper\n5. Serve hot",
            "cooking_time": "15 minutes",
            "servings": 4,
            "source": "Simple Recipe"
        },
        {
            "name": f"Roasted {ingredients_str}",
            "ingredients": ingredients + ["olive oil", "herbs", "salt", "pepper"],
            "instructions": "1. Preheat oven to 400°F\n2. Chop vegetables into chunks\n3. Toss with oil and seasonings\n4. Roast for 25-30 minutes\n5. Serve as side dish",
            "cooking_time": "35 minutes",
            "servings": 4,
            "source": "Simple Recipe"
        }
    ]
    
    return RecipeResponse(
        recipes=recipes,
        ingredients_identified=ingredients
    )

@app.post("/api/analyze-ingredients")
def analyze_ingredients(request: dict):
    """Simplified ingredient analysis"""
    return {
        "recipes": [
            {
                "name": "Simple Recipe from Image",
                "ingredients": ["onion", "carrot", "broccoli", "salt", "pepper", "oil"],
                "instructions": "1. Prepare vegetables\n2. Cook in pan\n3. Season and serve",
                "cooking_time": "20 minutes",
                "servings": 4
            }
        ],
        "ingredients_identified": ["onion", "carrot", "broccoli"]
    }

if __name__ == "__main__":
    print("Starting Simple Recipe API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")