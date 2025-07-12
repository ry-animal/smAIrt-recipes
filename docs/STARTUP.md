# Smart Recipe Assistant - Startup Guide

## Quick Start (Choose One Method)

### 🚀 Method 1: Using npm (Recommended - Cross Platform)
```bash
# One-time setup
npm run setup

# Start both servers
npm start
# or
npm run dev

# Stop all services when done
npm run kill
```

### 🐧 Method 2: Using Shell Script (Mac/Linux)
```bash
# Make executable (one time)
chmod +x start-both.sh

# Start both servers
./start-both.sh

# Stop all services
./kill-services.sh
```

### 🪟 Method 3: Using Batch File (Windows)
```cmd
# Start both servers
start-both.bat

# Stop all services
kill-services.bat
```

### 🔧 Method 4: Manual (If Scripts Don't Work)
```bash
# Terminal 1 - Backend
python real_vision_server.py

# Terminal 2 - Frontend  
cd frontend && npm start

# Stop services
./kill-services.sh  # or kill-services.bat on Windows
```

## What Each Script Does

1. **Checks dependencies** - Installs Python and Node.js packages if missing
2. **Validates environment** - Ensures .env file exists with API keys
3. **Starts backend** - Python FastAPI server on http://localhost:8080
4. **Starts frontend** - React development server on http://localhost:3000
5. **Monitors processes** - Keeps both running and handles cleanup

## Endpoints

- **Frontend App**: http://localhost:3000
- **Backend API**: http://localhost:8080  
- **API Documentation**: http://localhost:8080/docs

## Stopping the Servers

### Quick Stop (Recommended)
```bash
npm run kill        # Cross-platform via npm
./kill-services.sh  # Linux/Mac
kill-services.bat   # Windows
```

### Manual Stop
Press `Ctrl+C` in the terminal running the script. This will gracefully shut down both servers.

## Troubleshooting

### Backend Issues
- Check `backend.log` for Python/FastAPI errors
- Ensure GEMINI_API_KEY is set in `backend/.env`
- Verify Python dependencies: `pip install -r requirements.txt`

### Frontend Issues  
- Check `frontend.log` for React/Node.js errors
- Ensure Node.js dependencies: `cd frontend && npm install`
- Try clearing Node cache: `cd frontend && npm start -- --reset-cache`

### Port Conflicts
- Backend uses port 8080, frontend uses port 3000
- Kill existing processes: `npm run kill` or `lsof -ti:8080 | xargs kill -9`

## Environment Setup

Create `backend/.env` with your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SPOONACULAR_API_KEY=your_spoonacular_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
DEBUG=True
```