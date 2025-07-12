# Smart Recipe Assistant

A multimodal AI-powered cooking assistant that helps you discover recipes based on ingredient photos and provides intelligent cooking guidance.

## Features

- **Ingredient Recognition**: Upload photos of your ingredients and get automatic identification (Gemini + HuggingFace fallback)
- **Recipe Suggestions**: Receive personalized recipe recommendations based on available ingredients
- **Cooking Chat**: Ask cooking questions and get expert guidance on techniques, substitutions, and tips
- **Shopping Lists**: Generate shopping lists for your chosen recipes
- **Multimodal Interface**: Seamlessly switch between image uploads and text conversations
- **Semantic Search & Clustering**: Find and group similar ingredients or recipes using AI-powered embeddings

## Advanced/Over-Engineered Features

- **HuggingFace ViT fallback** for ingredient recognition if Gemini is unavailable
- **Ingredient Embeddings**: `/api/ingredient-embed` returns vector embeddings for ingredient strings
- **Ingredient Semantic Search**: `/api/ingredient-semantic-search` finds the most similar ingredients to a query
- **Ingredient Clustering**: `/api/ingredient-cluster` groups ingredients by meaning
- **Recipe Semantic Search**: `/api/recipe-semantic-search` finds the most similar recipes to a query
- **Recipe Clustering**: `/api/recipe-cluster` groups recipes by similarity

## Technology Stack

### Backend

- **Vercel Python Serverless Functions** (api/\*.py)
- **Google Gemini API** for vision and text processing
- **Pydantic** for data validation

### Frontend

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Axios** for API communication

## Quick Start

### Local Development (Docker, for dev/alt only)

```bash
# Clone and setup everything
git clone <repository-url>
cd smairt-recipes

# Install all dependencies
npm run setup

# Start both backend and frontend (local/dev only)
npm start

# When done, stop all services
npm run kill
```

### Vercel Deployment (Recommended)

1. Connect your GitHub repo to Vercel.
2. Vercel will auto-detect the frontend (React) and backend (api/\*.py Python functions).
3. Configure your environment variables (API keys) in the Vercel dashboard.
4. Deploy!

- Backend endpoints are now serverless functions in `/api/` (e.g., `/api/analyze_ingredients`).
- Frontend is built and served as a static site.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher (for local dev)
- Node.js 16 or higher
- Google Gemini API key

### Backend (Vercel Python Functions)

- Each API endpoint is a Python file in `/api/` (e.g., `api/analyze_ingredients.py`).
- No need to run a FastAPI server for production—Vercel handles routing and execution.
- For local/dev, you can still use Docker and the old FastAPI server if needed.

### Frontend Setup

1. **Navigate to frontend directory**

   ```bash
   cd frontend
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```
   The app will be available at `http://localhost:3000`

## API Endpoints

- POST `/api/analyze_ingredients`
- POST `/api/chat`
- POST `/api/search_recipes`
- POST `/api/shopping_list`
- POST `/api/ingredient-embed`
- POST `/api/ingredient-semantic-search`
- POST `/api/ingredient-cluster`
- POST `/api/recipe-semantic-search`
- POST `/api/recipe-cluster`

## Docker (Local/Dev Only)

- `
