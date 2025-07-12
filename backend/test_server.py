from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="Test Recipe API", version="1.0.0")

# Configure CORS for React frontend
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
async def root():
    return {"message": "Test Recipe API"}

@app.post("/api/search-recipes", response_model=RecipeResponse)
async def search_recipes_by_ingredients(request: IngredientSearchRequest):
    """Search for recipes based on a list of ingredients"""
    try:
        ingredients_str = ", ".join(request.ingredients)
        
        # Create structured test recipes
        recipes = [
            {
                "name": f"Stir-Fry with {ingredients_str}",
                "ingredients": request.ingredients + ["salt", "pepper", "soy sauce", "garlic"],
                "instructions": "1. Heat oil in a large pan\n2. Add garlic and cook for 1 minute\n3. Add vegetables and stir-fry for 5-7 minutes\n4. Season with salt, pepper, and soy sauce\n5. Serve hot over rice",
                "cooking_time": "15 minutes",
                "servings": 4,
                "source": "Test Recipe"
            },
            {
                "name": f"Roasted {ingredients_str}",
                "ingredients": request.ingredients + ["olive oil", "herbs", "salt", "pepper"],
                "instructions": "1. Preheat oven to 400°F (200°C)\n2. Chop vegetables into even pieces\n3. Toss with olive oil, salt, pepper, and herbs\n4. Spread on baking sheet\n5. Roast for 20-25 minutes until tender",
                "cooking_time": "30 minutes",
                "servings": 4,
                "source": "Test Recipe"
            }
        ]
        
        return RecipeResponse(
            recipes=recipes,
            ingredients_identified=request.ingredients
        )
    except Exception as e:
        print(f"Recipe search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)