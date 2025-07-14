import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print("DEBUG sys.path:", sys.path)
from fastapi import FastAPI, HTTPException, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import numpy as np
from sklearn.cluster import KMeans

from backend.services.gemini_service import GeminiService
from backend.agents.recipe_agent import RecipeAgent

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

class IngredientEmbedRequest(BaseModel):
    ingredients: list[str]

class IngredientEmbedResponse(BaseModel):
    embeddings: list[dict]

class IngredientSemanticSearchRequest(BaseModel):
    query: str
    candidates: list[str]
    top_n: int = 5

class IngredientSemanticSearchResponse(BaseModel):
    matches: list[dict]

class RecipeSemanticSearchRequest(BaseModel):
    query: str
    candidates: list[dict]
    top_n: int = 3

class RecipeSemanticSearchResponse(BaseModel):
    matches: list[dict]

class RecipeClusterRequest(BaseModel):
    candidates: list[dict]
    k: int = 3

class RecipeClusterResponse(BaseModel):
    clusters: list[dict]
    centroids: list[list[float]]

class IngredientClusterRequest(BaseModel):
    ingredients: list[str]
    k: int = 3

class IngredientClusterResponse(BaseModel):
    clusters: list[dict]
    centroids: list[list[float]]

class RecipeEmbedRequest(BaseModel):
    recipes: list[dict]

class RecipeEmbedResponse(BaseModel):
    embeddings: list[dict]

@app.get("/")
async def root():
    return {"message": "Smart Recipe Assistant API"}

@app.post("/api/analyze-ingredients", response_model=RecipeResponse)
async def analyze_ingredients(upload: ImageUpload):
    """Analyze uploaded image to identify ingredients and suggest recipes"""
    try:
        # Use tool_use for ingredient recognition (Gemini + HF fallback)
        gemini_result = recipe_agent.tool_use("ingredient_recognition", image_data=upload.image_data)
        hf_result = recipe_agent.tool_use("hf_ingredient_recognition", image_data=upload.image_data)
        # Parse results (assume both return lists of ingredients or strings)
        gemini_ingredients = gemini_result if isinstance(gemini_result, list) else []
        hf_ingredients = hf_result if isinstance(hf_result, list) else []
        # For recipes, use Gemini ingredients if available, else fallback to HF, else fallback
        ingredients_for_recipes = gemini_ingredients or hf_ingredients or ["onion", "carrot", "potato"]
        recipes = gemini_service.suggest_recipes(ingredients_for_recipes)
        return RecipeResponse(
            recipes=recipes,
            ingredients_identified=gemini_ingredients or hf_ingredients or []
        )
    except Exception as e:
        print(f"❌ Image analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_query(query: TextQuery):
    """Handle text-based queries for recipes, cooking questions, etc."""
    try:
        response = recipe_agent.chat(query.query, query.context or "")
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

@app.post("/api/ingredient-embed", response_model=IngredientEmbedResponse)
async def ingredient_embed(request: IngredientEmbedRequest):
    try:
        embeddings = gemini_service.ingredient_embeddings(request.ingredients)
        return IngredientEmbedResponse(
            embeddings=[{"ingredient": ing, "embedding": emb} for ing, emb in zip(request.ingredients, embeddings)]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingredient-semantic-search", response_model=IngredientSemanticSearchResponse)
async def ingredient_semantic_search(request: IngredientSemanticSearchRequest):
    try:
        all_ingredients = [request.query] + request.candidates
        embeddings = gemini_service.ingredient_embeddings(all_ingredients)
        query_emb = np.array(embeddings[0])
        candidate_embs = np.array(embeddings[1:])
        # Cosine similarity
        sims = candidate_embs @ query_emb / (np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb) + 1e-8)
        top_idx = sims.argsort()[::-1][:request.top_n]
        matches = [
            {"ingredient": request.candidates[i], "score": float(sims[i])}
            for i in top_idx
        ]
        return IngredientSemanticSearchResponse(matches=matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recipe-semantic-search", response_model=RecipeSemanticSearchResponse)
async def recipe_semantic_search(request: RecipeSemanticSearchRequest):
    try:
        def recipe_to_text(recipe):
            name = recipe.get("name", "")
            ingredients = recipe.get("ingredients", [])
            if isinstance(ingredients, list):
                ingredients = ", ".join(ingredients)
            return f"{name}: {ingredients}"
        candidate_texts = [recipe_to_text(r) for r in request.candidates]
        all_texts = [request.query] + candidate_texts
        embeddings = gemini_service.ingredient_embeddings(all_texts)
        query_emb = np.array(embeddings[0])
        candidate_embs = np.array(embeddings[1:])
        sims = candidate_embs @ query_emb / (np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb) + 1e-8)
        top_idx = sims.argsort()[::-1][:request.top_n]
        matches = [
            {"recipe": request.candidates[i], "score": float(sims[i])}
            for i in top_idx
        ]
        return RecipeSemanticSearchResponse(matches=matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recipe-cluster", response_model=RecipeClusterResponse)
async def recipe_cluster(request: RecipeClusterRequest):
    try:
        def recipe_to_text(recipe):
            name = recipe.get("name", "")
            ingredients = recipe.get("ingredients", [])
            if isinstance(ingredients, list):
                ingredients = ", ".join(ingredients)
            return f"{name}: {ingredients}"
        texts = [recipe_to_text(r) for r in request.candidates]
        embeddings = gemini_service.ingredient_embeddings(texts)
        kmeans = KMeans(n_clusters=request.k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        clusters = [
            {"recipe": recipe, "cluster": int(label)}
            for recipe, label in zip(request.candidates, labels)
        ]
        centroids = kmeans.cluster_centers_.tolist()
        return RecipeClusterResponse(clusters=clusters, centroids=centroids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingredient-cluster", response_model=IngredientClusterResponse)
async def ingredient_cluster(request: IngredientClusterRequest):
    try:
        embeddings = gemini_service.ingredient_embeddings(request.ingredients)
        kmeans = KMeans(n_clusters=request.k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(embeddings)
        clusters = [
            {"ingredient": ing, "cluster": int(label)}
            for ing, label in zip(request.ingredients, labels)
        ]
        centroids = kmeans.cluster_centers_.tolist()
        return IngredientClusterResponse(clusters=clusters, centroids=centroids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recipe-embed", response_model=RecipeEmbedResponse)
async def recipe_embed(request: RecipeEmbedRequest):
    try:
        def recipe_to_text(recipe):
            name = recipe.get("name", "")
            ingredients = recipe.get("ingredients", [])
            if isinstance(ingredients, list):
                ingredients = ", ".join(ingredients)
            return f"{name}: {ingredients}"
        texts = [recipe_to_text(r) for r in request.recipes]
        embeddings = gemini_service.ingredient_embeddings(texts)
        return RecipeEmbedResponse(
            embeddings=[{"recipe": recipe, "embedding": emb} for recipe, emb in zip(request.recipes, embeddings)]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)