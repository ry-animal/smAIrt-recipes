# Smart Recipe Assistant

A multimodal AI-powered cooking assistant that helps you discover recipes based on ingredient photos and provides intelligent cooking guidance.

## Features

- **Ingredient Recognition**: Upload photos of your ingredients and get automatic identification
- **Recipe Suggestions**: Receive personalized recipe recommendations based on available ingredients
- **Cooking Chat**: Ask cooking questions and get expert guidance on techniques, substitutions, and tips
- **Shopping Lists**: Generate shopping lists for your chosen recipes
- **Multimodal Interface**: Seamlessly switch between image uploads and text conversations

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

## Docker (Local/Dev Only)

- `Dockerfile.backend` and `docker-compose.yml` are for local/dev/alt deployment only.
- Vercel does **not** use these files for production.
- You can still run the backend locally as a FastAPI server for development/testing.

## Deployment

### Vercel

- Connect your repo to Vercel and deploy.
- Set environment variables in the Vercel dashboard.
- Both frontend and backend will be deployed as serverless/static.

### Local Docker (Dev/Alt)

- Use `docker-compose up --build` to run both backend and frontend locally.
- Not used in production on Vercel.

## License

MIT License - see LICENSE file for details

## Support

For questions or issues:

1. Check the documentation in the `docs/` folder
2. Search existing issues on GitHub
3. Create a new issue with detailed information

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**

   - Ensure your `.env` file is properly configured
   - Check that the API key is valid and has necessary permissions

2. **Image upload fails**

   - Verify the image is in a supported format (JPG, PNG, WebP)
   - Check file size is under 10MB
   - Ensure the backend server is running

3. **Frontend can't connect to backend**

   - Verify backend is running on port 8080
   - Check CORS settings in `real_vision_server.py`
   - Confirm API URLs in frontend components

4. **Dependencies installation fails**
   - Use Python 3.8+ and Node.js 16+
   - Try creating a fresh virtual environment
   - Check for any conflicting global packages
