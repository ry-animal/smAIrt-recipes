from vercel_python import VercelRequest, VercelResponse
from gemini_utils import generate_shopping_list

def handler(request: VercelRequest):
    if request.method != "POST":
        return VercelResponse({"error": "Method not allowed"}, status_code=405)

    data = request.json()
    recipe = data.get("recipe")
    available_ingredients = data.get("available_ingredients", [])
    if not recipe:
        return VercelResponse({"error": "Missing recipe"}, status_code=400)

    shopping_list = generate_shopping_list(recipe, available_ingredients)
    if not shopping_list:
        recipe_ingredients = recipe.get("ingredients", [])
        shopping_list = [i for i in recipe_ingredients if i.lower() not in [a.lower() for a in available_ingredients]]

    return VercelResponse({
        "shopping_list": shopping_list,
        "recipe_name": recipe.get("name", "Unknown Recipe"),
        "total_items": len(shopping_list)
    }) 