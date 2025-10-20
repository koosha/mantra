"""
FastAPI backend for Mantra chat widget.
Exposes the RAG functionality as a REST API.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mantra import DelawareCaseLawIndexer, QueryClassifier, LegalResponseGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components (loaded once at startup)
indexer = None
classifier = None
generator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    global indexer, classifier, generator

    # Startup
    logger.info("Initializing Mantra components...")

    try:
        # Initialize indexer
        indexer = DelawareCaseLawIndexer(
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            index_path=os.getenv("FAISS_INDEX_PATH", "./faiss_index"),
            data_path=os.getenv("DATA_DIR", "./data/cases") + "/delaware_cases.json"
        )

        # Load index
        indexer.load_index()
        logger.info(f"✅ Loaded FAISS index with {indexer.index.ntotal} vectors")

        # Initialize classifier
        classifier = QueryClassifier(
            model=os.getenv("LLM_MODEL", "gpt-4")
        )
        logger.info("✅ Initialized query classifier")

        # Initialize response generator
        generator = LegalResponseGenerator(
            model=os.getenv("LLM_MODEL", "gpt-4")
        )
        logger.info("✅ Initialized response generator")

        logger.info("🎉 Mantra is ready!")

    except FileNotFoundError:
        logger.error("❌ FAISS index not found. Please build the index first.")
        raise
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise

    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down Mantra...")


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Mantra Chat API",
    description="Delaware Corporate Law AI Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (chat widget HTML/CSS/JS)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class ChatMessage(BaseModel):
    """Chat message from user."""
    message: str


class ChatResponse(BaseModel):
    """Response from the chatbot."""
    message: str
    relevant: bool
    sources: list = []
    confidence: str = "medium"


@app.get("/")
async def root():
    """Serve the chat widget demo page."""
    return FileResponse(str(Path(__file__).parent / "static" / "index.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "index_loaded": indexer is not None and indexer.index is not None,
        "vectors": indexer.index.ntotal if indexer and indexer.index else 0
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Main chat endpoint.

    Processes user message through:
    1. Query classification (is it relevant?)
    2. If relevant: RAG search + response generation
    3. If not: polite rejection
    """
    try:
        user_query = message.message.strip()

        if not user_query:
            raise HTTPException(status_code=400, detail="Empty message")

        logger.info(f"Received query: {user_query[:100]}...")

        # Step 1: Classify query
        classification = classifier.classify_query(user_query)

        if not classification.get("relevant", False):
            # Query is not relevant to Delaware law
            rejection_message = classifier.get_rejection_message(user_query, classification)
            return ChatResponse(
                message=rejection_message,
                relevant=False,
                sources=[],
                confidence="high"
            )

        # Step 2: Search for relevant cases
        search_results = indexer.search(user_query, k=4)

        if not search_results:
            return ChatResponse(
                message="I apologize, but I couldn't find relevant Delaware case law for your question. Could you rephrase or provide more context?",
                relevant=True,
                sources=[],
                confidence="low"
            )

        # Step 3: Generate response
        response_data = generator.generate_response(
            question=user_query,
            retrieved_chunks=search_results,
            include_sources=False  # Don't add sources to text; chat widget displays them separately
        )

        # Step 4: Format sources (deduplicate by case_id)
        sources = []
        seen_case_ids = set()

        for result in search_results:
            case_id = result["metadata"].get("case_id")

            # Skip if we've already added this case
            if case_id in seen_case_ids:
                continue

            seen_case_ids.add(case_id)
            sources.append({
                "case_name": result["metadata"]["case_name"],
                "date": result["metadata"]["date_filed"],
                "court": result["metadata"]["court"],
                "citation": result["metadata"].get("case_name_full", result["metadata"]["case_name"]),
                "url": result["metadata"].get("absolute_url", "#")
            })

            # Limit to top 3 unique sources
            if len(sources) >= 3:
                break

        return ChatResponse(
            message=response_data["answer"],
            relevant=True,
            sources=sources,
            confidence=response_data.get("confidence", "medium")
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/examples")
async def get_examples():
    """Get example queries."""
    return {
        "relevant": [
            "What is fiduciary duty?",
            "Explain the Revlon doctrine",
            "What is the business judgment rule?",
            "What are the requirements for entire fairness review?",
            "Explain the MFW framework",
            "What is Caremark oversight?"
        ],
        "irrelevant": [
            "Who is Koosha?",
            "What's the weather today?",
            "How do I make pasta?"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "chat_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
