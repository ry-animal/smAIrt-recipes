#!/bin/bash

# Smart Recipe Assistant - Full Development Startup Script
# This script starts both backend and frontend servers concurrently

set -e  # Exit on any error

echo "🍳 Starting Smart Recipe Assistant (Backend + Frontend)..."
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    # Kill any remaining processes on our ports
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

# Set up cleanup trap
trap cleanup SIGINT SIGTERM EXIT

# Check if required directories exist
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: backend/ or frontend/ directory not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Backend Setup
echo "🔧 Setting up backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/lib/python*/site-packages/fastapi/__init__.py" ]; then
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check environment file
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env file not found."
    if [ -f ".env.example" ]; then
        echo "   Copying .env.example to backend/.env..."
        cp .env.example backend/.env
        echo "   Please edit backend/.env to add your API keys before running again."
        exit 1
    else
        echo "   Please create backend/.env with your API keys."
        exit 1
    fi
fi

# Frontend Setup
echo "🔧 Setting up frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
fi

cd ..

# Start Backend Server
echo ""
echo "🚀 Starting backend server..."
echo "   📍 Backend: http://localhost:8080"
echo "   📚 API docs: http://localhost:8080/docs"

PYTHONPATH=$(pwd) uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check backend.log for details:"
    tail backend.log
    exit 1
fi

echo "✅ Backend started successfully (PID: $BACKEND_PID)"

# Start Frontend Server
echo ""
echo "🚀 Starting frontend server..."
echo "   📍 Frontend: http://localhost:3000"

cd frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 10

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check frontend.log for details:"
    tail frontend.log
    exit 1
fi

echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
echo ""
echo "🎉 Smart Recipe Assistant is now running!"
echo ""
echo "🌐 Open your browser and go to:"
echo "   Frontend (Main App): http://localhost:3000"
echo "   Backend API:         http://localhost:8080"
echo "   API Documentation:   http://localhost:8080/docs"
echo ""
echo "📊 Monitor logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop both servers"
echo ""

# Keep script running and wait for interrupt
while true; do
    # Check if both processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died unexpectedly"
        echo "Backend log:"
        tail backend.log
        exit 1
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend process died unexpectedly"
        echo "Frontend log:"
        tail frontend.log
        exit 1
    fi
    
    sleep 5
done