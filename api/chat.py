from vercel_python import VercelRequest, VercelResponse
from gemini_utils import answer_cooking_question

def handler(request: VercelRequest):
    if request.method != "POST":
        return VercelResponse({"error": "Method not allowed"}, status_code=405)

    data = request.json()
    query = data.get("query")
    context = data.get("context")
    if not query:
        return VercelResponse({"error": "Missing query"}, status_code=400)

    response = answer_cooking_question(query, context)
    if not response:
        response = "This is a placeholder response."

    return VercelResponse({
        "response": response,
        "type": "cooking_advice"
    }) 