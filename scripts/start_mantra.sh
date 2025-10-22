#!/bin/bash

# Mantra Startup Script
# Quick way to start the Mantra application

echo "========================================"
echo "  🏛️  Mantra - Delaware Law Assistant"
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
    echo "   The app may not work correctly."
    echo "   Run: python3 tests/test_indexer.py"
    echo ""
fi

# Start Streamlit
echo "Starting Mantra..."
echo "The app will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run mantra_app.py
