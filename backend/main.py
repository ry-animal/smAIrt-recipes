from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
from typing import Optional, List
import uvicorn

from services.gemini_service import GeminiService
from agents.recipe_agent import RecipeAgent

app = FastAPI(title="Smart Recipe Assistant API", version="1.0.0")

try:
    gemini_service = GeminiService()
    print("✅ Gemini service initialized successfully")
except Exception as e:
    print(f"⚠️ Gemini service failed to initialize: {e}")
    print("📝 Will use fallback recipes instead")
    gemini_service = None

try:
    recipe_agent = RecipeAgent() if gemini_service else None
    print("✅ Recipe agent initialized successfully" if recipe_agent else "⚠️ Recipe agent disabled (no Gemini)")
except Exception as e:
    print(f"⚠️ Recipe agent failed to initialize: {e}")
    recipe_agent = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextQuery(BaseModel):
    query: str
    context: Optional[str] = None

class ImageUpload(BaseModel):
    image_data: str

class RecipeResponse(BaseModel):
    recipes: List[dict]
    ingredients_identified: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    type: str

class IngredientSearchRequest(BaseModel):
    ingredients: List[str]

class ShoppingListRequest(BaseModel):
    recipe: dict
    available_ingredients: Optional[List[str]] = []

@app.get("/")
async def root():
    return {"message": "Smart Recipe Assistant API"}

@app.post("/api/analyze-ingredients", response_model=RecipeResponse)
async def analyze_ingredients(upload: ImageUpload):
    """Analyze uploaded image to identify ingredients and suggest recipes"""
    try:
        if not gemini_service or not recipe_agent:
            fallback_ingredients = ["onion", "carrot", "potato"]
            print("📝 Using fallback ingredients (image analysis not available)")
            recipes = [
                {
                    "name": "Simple Vegetable Stir-Fry",
                    "ingredients": fallback_ingredients + ["oil", "salt", "pepper", "garlic"],
                    "instructions": "1. Heat oil in pan\n2. Add garlic and cook 1 minute\n3. Add vegetables and stir-fry 8-10 minutes\n4. Season with salt and pepper\n5. Serve hot",
                    "cooking_time": "15 minutes",
                    "servings": 4,
                    "source": "Fallback Recipe"
                }
            ]
            return RecipeResponse(
                recipes=recipes,
                ingredients_identified=fallback_ingredients
            )
        result = recipe_agent.process_image_query(upload.image_data)
        if not result["ingredients"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return RecipeResponse(
            recipes=result["recipes"],
            ingredients_identified=result["ingredients"]
        )
    except Exception as e:
        print(f"❌ Image analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_query(query: TextQuery):
    """Handle text-based queries for recipes, cooking questions, etc."""
    try:
        response = recipe_agent.process_query(query.query, query.context or "")
        return ChatResponse(
            response=response,
            type="clarification"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-recipes", response_model=RecipeResponse)
async def search_recipes_by_ingredients(request: IngredientSearchRequest):
    """Search for recipes based on a list of ingredients"""
    try:
        ingredients_str = ", ".join(request.ingredients)
        recipes = [
            {
                "name": f"Vegetable Stir-Fry with {ingredients_str}",
                "ingredients": request.ingredients + ["2 tbsp soy sauce", "1 tbsp olive oil", "2 cloves garlic", "salt", "pepper"],
                "instructions": f"1. Heat olive oil in a large pan over medium-high heat\n2. Add minced garlic and cook for 1 minute until fragrant\n3. Add {request.ingredients[0]} and cook for 3-4 minutes\n4. Add remaining vegetables: {', '.join(request.ingredients[1:]) if len(request.ingredients) > 1 else ''}\n5. Stir-fry for 5-7 minutes until vegetables are tender-crisp\n6. Add soy sauce and season with salt and pepper to taste\n7. Serve immediately while hot",
                "cooking_time": "15 minutes", 
                "servings": 4,
                "source": "Fallback Recipe"
            },
            {
                "name": f"Roasted {ingredients_str}",
                "ingredients": request.ingredients + ["3 tbsp olive oil", "1 tsp dried herbs", "salt", "pepper"],
                "instructions": f"1. Preheat oven to 425°F (220°C)\n2. Wash and chop all vegetables into uniform pieces\n3. Toss vegetables with olive oil, herbs, salt, and pepper\n4. Spread evenly on a baking sheet\n5. Roast for 25-30 minutes, stirring once halfway through\n6. Cook until vegetables are golden and tender\n7. Serve as a side dish or over rice",
                "cooking_time": "35 minutes",
                "servings": 4, 
                "source": "Fallback Recipe"
            }
        ]
        if gemini_service:
            try:
                ai_recipes = gemini_service.suggest_recipes(request.ingredients)
                if ai_recipes and len(ai_recipes) > 0:
                    recipes = ai_recipes[:3]
                    print(f"✅ Generated {len(recipes)} AI recipes")
                else:
                    print("⚠️ No AI recipes generated, using fallback")
            except Exception as ai_error:
                print(f"⚠️ AI recipe generation failed: {ai_error}")
        else:
            print("📝 Using fallback recipes (Gemini not available)")
        return RecipeResponse(
            recipes=recipes,
            ingredients_identified=request.ingredients
        )
    except Exception as e:
        print(f"❌ Recipe search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shopping-list")
async def generate_shopping_list(request: ShoppingListRequest):
    """Generate shopping list from selected recipe"""
    try:
        shopping_items = gemini_service.generate_shopping_list(
            recipe=request.recipe,
            available_ingredients=request.available_ingredients
        )
        if not shopping_items:
            raise HTTPException(status_code=400, detail="Could not generate shopping list")
        return {
            "shopping_list": shopping_items,
            "recipe_name": request.recipe.get("name", "Unknown Recipe"),
            "total_items": len(shopping_items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)