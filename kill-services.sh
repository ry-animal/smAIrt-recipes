#!/bin/bash

echo "🛑 Stopping Smart Recipe Assistant services..."

# Kill Python processes (backend servers)
echo "📱 Stopping backend servers..."
pkill -f "python.*real_vision_server.py" 2>/dev/null
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*test_server.py" 2>/dev/null
pkill -f "python.*working_server.py" 2>/dev/null
pkill -f "python.*simple_server.py" 2>/dev/null
pkill -f "python.*debug_server.py" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null

# Kill Node.js processes (React frontend)
echo "⚛️  Stopping frontend server..."
pkill -f "node.*react-scripts" 2>/dev/null
pkill -f "npm.*start" 2>/dev/null

# Kill any processes using ports 3000 and 8080
echo "🔌 Freeing up ports 3000 and 8080..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Optional: Kill any other Python processes if needed
# Uncomment the line below if you want to kill ALL Python processes
# pkill -f python 2>/dev/null

echo "✅ All Smart Recipe Assistant services stopped!"
echo ""
echo "To restart services:"
echo "  Backend:  python real_vision_server.py"
echo "  Frontend: npm start (in frontend directory)"