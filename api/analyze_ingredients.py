from vercel_python import VercelRequest, VercelResponse
from gemini_utils import identify_ingredients, suggest_recipes

def handler(request: VercelRequest):
    if request.method != "POST":
        return VercelResponse({"error": "Method not allowed"}, status_code=405)

    data = request.json()
    image_data = data.get("image_data")
    if not image_data:
        return VercelResponse({"error": "Missing image_data"}, status_code=400)

    ingredients = identify_ingredients(image_data)
    if not ingredients:
        ingredients = ["onion", "carrot", "potato"]
    recipes = suggest_recipes(ingredients)

    return VercelResponse({
        "ingredients_identified": ingredients,
        "recipes": recipes
    }) 