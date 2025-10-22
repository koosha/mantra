#!/bin/bash

# Mantra Quick Start Script
# This script helps you get Mantra up and running quickly

echo "=========================================="
echo "  Mantra - Delaware Corporate Law Bot"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your OPENAI_API_KEY before continuing!"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Check if OPENAI_API_KEY is set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    echo "❌ OPENAI_API_KEY is not set in .env file"
    echo "Please edit .env and add your OpenAI API key, then run this script again."
    exit 1
fi

echo "✅ OPENAI_API_KEY is configured"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"
echo ""

# Check if data exists
if [ ! -f "./data/cases/delaware_cases.json" ]; then
    echo "📥 No case data found. Would you like to:"
    echo "  1) Extract 10 test cases (quick, ~1 minute)"
    echo "  2) Extract all Delaware cases (slow, ~10-30 minutes)"
    echo "  3) Skip for now"
    read -p "Enter choice (1/2/3): " data_choice
    
    case $data_choice in
        1)
            echo "Extracting 10 test cases..."
            python3 test_extractor.py
            ;;
        2)
            echo "Extracting all cases (this may take a while)..."
            python3 data_extractor.py
            ;;
        3)
            echo "⚠️  Skipping data extraction. You'll need to run this later."
            ;;
        *)
            echo "Invalid choice. Skipping data extraction."
            ;;
    esac
    echo ""
fi

# Check if index exists
if [ ! -f "./faiss_index/index.faiss" ]; then
    if [ ! -f "./data/cases/delaware_cases.json" ]; then
        echo "⚠️  No case data available. Cannot build index."
        echo "Please run data extraction first."
        exit 1
    fi
    
    echo "🔨 No FAISS index found. Would you like to:"
    echo "  1) Build index with 5 test cases (quick, ~1 minute)"
    echo "  2) Build full index (slow, ~5-15 minutes depending on data size)"
    echo "  3) Skip for now"
    read -p "Enter choice (1/2/3): " index_choice
    
    case $index_choice in
        1)
            echo "Building test index..."
            python3 test_indexer.py
            ;;
        2)
            echo "Building full index (this may take a while)..."
            python3 indexer.py
            ;;
        3)
            echo "⚠️  Skipping index build. You'll need to run this later."
            ;;
        *)
            echo "Invalid choice. Skipping index build."
            ;;
    esac
    echo ""
fi

# Final check
if [ -f "./faiss_index/index.faiss" ]; then
    echo "=========================================="
    echo "  ✅ Mantra is ready to run!"
    echo "=========================================="
    echo ""
    echo "To start Mantra, run:"
    echo "  streamlit run mantra_app.py"
    echo ""
    echo "Or run it now?"
    read -p "Start Mantra now? (y/n): " start_choice
    
    if [ "$start_choice" = "y" ] || [ "$start_choice" = "Y" ]; then
        echo ""
        echo "Starting Mantra..."
        streamlit run mantra_app.py
    fi
else
    echo "=========================================="
    echo "  ⚠️  Setup incomplete"
    echo "=========================================="
    echo ""
    echo "You still need to:"
    if [ ! -f "./data/cases/delaware_cases.json" ]; then
        echo "  1. Extract case data: python3 data_extractor.py"
    fi
    if [ ! -f "./faiss_index/index.faiss" ]; then
        echo "  2. Build index: python3 indexer.py"
    fi
    echo ""
    echo "Then run: streamlit run mantra_app.py"
fi
