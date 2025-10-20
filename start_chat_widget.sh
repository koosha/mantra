#!/bin/bash

# Mantra Chat Widget Startup Script
# Starts the FastAPI backend server

echo "========================================"
echo "  🏛️  Mantra - Chat Widget Server"
echo "========================================"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if index exists
if [ ! -f "./faiss_index/index.faiss" ]; then
    echo "⚠️  Warning: FAISS index not found!"
    echo "   The chat won't work correctly."
    echo "   Run: python3 tests/test_indexer.py"
    echo ""
    read -p "Continue anyway? (y/n): " continue_choice
    if [ "$continue_choice" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "Starting FastAPI server..."
echo "The chat widget will be available at:"
echo "  → http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================"
echo ""

# Start the server
python3 chat_api.py
