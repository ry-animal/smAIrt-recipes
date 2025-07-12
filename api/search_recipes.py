from vercel_python import VercelRequest, VercelResponse
from gemini_utils import suggest_recipes

def handler(request: VercelRequest):
    if request.method != "POST":
        return VercelResponse({"error": "Method not allowed"}, status_code=405)

    data = request.json()
    ingredients = data.get("ingredients")
    if not ingredients:
        return VercelResponse({"error": "Missing ingredients"}, status_code=400)

    recipes = suggest_recipes(ingredients)
    if not recipes:
        recipes = [
            {
                "name": f"Stir-Fry with {', '.join(ingredients)}",
                "ingredients": ingredients + ["oil", "salt", "pepper"],
                "instructions": "1. Heat oil. 2. Add ingredients. 3. Cook.",
                "cooking_time": "15 minutes",
                "servings": 4,
                "source": "Generated Recipe"
            }
        ]

    return VercelResponse({
        "recipes": recipes,
        "ingredients_identified": ingredients
    }) 