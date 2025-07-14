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
        ingredients_str = ", ".join(ingredients[:3])
        recipes = [
            {
                "name": f"Stir-Fry with {ingredients_str}",
                "ingredients": ingredients + ["2 tbsp oil", "salt", "pepper"],
                "instructions": "1. Heat oil in pan. 2. Add ingredients. 3. Stir-fry 5-7 minutes. 4. Season and serve.",
                "cooking_time": "15 minutes",
                "servings": 4,
                "source": "Generated Recipe"
            },
            {
                "name": f"Roasted {ingredients_str}",
                "ingredients": ingredients + ["3 tbsp olive oil", "herbs", "salt"],
                "instructions": "1. Preheat oven to 425°F. 2. Toss with oil and seasonings. 3. Roast 25-30 minutes.",
                "cooking_time": "30 minutes",
                "servings": 4,
                "source": "Generated Recipe"
            },
            {
                "name": f"{ingredients_str} Soup",
                "ingredients": ingredients + ["4 cups broth", "onion", "garlic"],
                "instructions": "1. Sauté onion and garlic. 2. Add vegetables and broth. 3. Simmer 20-25 minutes.",
                "cooking_time": "35 minutes",
                "servings": 4,
                "source": "Generated Recipe"
            }
        ]

    return VercelResponse({
        "recipes": recipes,
        "ingredients_identified": ingredients
    }) 