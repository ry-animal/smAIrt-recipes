import pytest
import httpx

BASE_URL = "http://localhost:3000/api"

@pytest.mark.asyncio
async def test_analyze_ingredients_success():
    # Use a dummy base64 image string (not a real image, just for endpoint test)
    payload = {"image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/analyze_ingredients", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "ingredients_identified" in data
        assert "recipes" in data

@pytest.mark.asyncio
async def test_analyze_ingredients_missing():
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/analyze_ingredients", json={})
        assert resp.status_code == 400
        assert resp.json()["error"] == "Missing image_data"

@pytest.mark.asyncio
async def test_chat_success():
    payload = {"query": "How do I boil an egg?"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert data["type"] == "cooking_advice"

@pytest.mark.asyncio
async def test_chat_missing():
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/chat", json={})
        assert resp.status_code == 400
        assert resp.json()["error"] == "Missing query"

@pytest.mark.asyncio
async def test_search_recipes_success():
    payload = {"ingredients": ["onion", "carrot"]}
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/search_recipes", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "recipes" in data
        assert "ingredients_identified" in data

@pytest.mark.asyncio
async def test_search_recipes_missing():
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/search_recipes", json={})
        assert resp.status_code == 400
        assert resp.json()["error"] == "Missing ingredients"

@pytest.mark.asyncio
async def test_shopping_list_success():
    payload = {
        "recipe": {
            "name": "Test Recipe",
            "ingredients": ["onion", "carrot", "potato"]
        },
        "available_ingredients": ["onion"]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/shopping_list", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "shopping_list" in data
        assert "recipe_name" in data
        assert "total_items" in data

@pytest.mark.asyncio
async def test_shopping_list_missing():
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE_URL}/shopping_list", json={})
        assert resp.status_code == 400
        assert resp.json()["error"] == "Missing recipe" 