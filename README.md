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

- **Python 3.8+** with FastAPI
- **LangChain & LangGraph** for AI orchestration
- **Google Gemini API** for vision and text processing
- **Pydantic** for data validation

### Frontend

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Axios** for API communication

## Quick Start

### Automated Setup (Recommended)

```bash
# Clone and setup everything
git clone <repository-url>
cd smairt-recipes

# Install all dependencies
npm run setup

# Start both backend and frontend
npm start

# When done, stop all services
npm run kill
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Google Gemini API key

### Backend Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd smairt-recipes
   ```

2. **Create Python virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:

   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here  # Optional
   SPOONACULAR_API_KEY=your_spoonacular_api_key_here  # Optional
   DEBUG=True
   ```

5. **Run the backend server**
   ```bash
   python real_vision_server.py
   ```
   The API will be available at `http://localhost:8080`

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

## Getting API Keys

### Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

### Optional APIs

- **Hugging Face**: For additional model options
- **Spoonacular**: For enhanced recipe database access

## Usage

### Upload Ingredients

1. Click "Upload Ingredients" in the navigation
2. Select or drag an image of your ingredients
3. Click "Analyze Ingredients"
4. View identified ingredients and recipe suggestions

### Ask Cooking Questions

1. Click "Ask Questions" in the navigation
2. Type your cooking question in the chat interface
3. Get instant responses about techniques, substitutions, and tips

### Generate Shopping Lists

1. After selecting a recipe, click "Shopping List"
2. Get a customized list of ingredients to purchase

## Project Structure

```
smairt-recipes/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration management
│   ├── services/
│   │   └── gemini_service.py  # Gemini API integration
│   └── agents/
│       └── recipe_agent.py    # LangGraph agent
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Main React component
│   │   └── components/        # React components
│   │       ├── ImageUpload.tsx
│   │       ├── ChatInterface.tsx
│   │       └── RecipeDisplay.tsx
│   ├── tailwind.config.js     # Tailwind configuration
│   └── package.json
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md
```

## API Endpoints

### POST /api/analyze-ingredients

Analyze ingredient photos and get recipe suggestions

- **Body**: `{"image_data": "base64_encoded_image"}`
- **Response**: `{"recipes": [...], "ingredients_identified": [...]}`

### POST /api/chat

Handle cooking questions and conversations

- **Body**: `{"query": "your question", "context": "optional context"}`
- **Response**: `{"response": "answer", "type": "clarification"}`

### POST /api/shopping-list

Generate shopping lists for recipes

- **Body**: `{"recipe": {...}, "available_ingredients": [...]}`
- **Response**: `{"shopping_list": [...]}`

## Development

### NPM Scripts

```bash
# Start/Stop Services
npm start              # Start both backend (8080) and frontend (3000)
npm run dev            # Same as npm start
npm run kill           # Stop all services
npm run stop           # Same as npm run kill

# Individual Services
npm run start:backend  # Start only backend on port 8080
npm run start:frontend # Start only frontend on port 3000

# Setup
npm run setup          # Install all dependencies
npm run install:all    # Same as npm run setup
```

### Manual Control

```bash
# Start services manually
python real_vision_server.py  # Backend on port 8080
cd frontend && npm start       # Frontend on port 3000

# Stop services manually
./kill-services.sh             # Linux/Mac
kill-services.bat              # Windows
```

### Running Tests

```bash
# Backend tests
python -m pytest

# Frontend tests
cd frontend && npm test
```

### Code Formatting

```bash
# Backend
python -m black .
python -m flake8 .

# Frontend
cd frontend && npm run format
cd frontend && npm run lint
```

## Deployment

### Backend Deployment

The backend is configured for deployment on:

- Google Cloud Run
- AWS Lambda
- Traditional VPS with uvicorn

### Frontend Deployment

The React frontend can be deployed to:

- Vercel
- Netlify
- AWS S3 + CloudFront

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

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
