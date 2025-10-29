"""
FastAPI backend for Mantra chat widget.
Exposes the RAG functionality as a REST API.
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging

# Import from mantra package
from src.mantra import (
    DelawareCaseLawIndexer,
    QueryClassifier,
    LegalResponseGenerator,
    get_settings,
    format_sources,
    get_http_status_code,
    MantraException
)

# Load settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
            embedding_model=settings.embedding_model,
            index_path=str(settings.faiss_index_path),
            data_path=str(settings.data_path)
        )

        # Load index
        indexer.load_index()
        logger.info(f"✅ Loaded FAISS index with {indexer.index.ntotal} vectors")

        # Initialize classifier
        classifier = QueryClassifier(
            model=settings.llm_model
        )
        logger.info("✅ Initialized query classifier")

        # Initialize response generator
        generator = LegalResponseGenerator(
            model=settings.llm_model
        )
        logger.info("✅ Initialized response generator")

        logger.info("🎉 Mantra is ready!")

    except FileNotFoundError as e:
        logger.error(f"❌ FAISS index not found. Please build the index first: {e}")
        raise
    except MantraException as e:
        logger.error(f"❌ Mantra error during startup: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during startup: {e}")
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
        search_results = indexer.search(user_query, k=settings.default_retrieval_k)

        # Check if results are high quality enough to answer
        # Escalate if: no results OR top result has low similarity
        if not search_results:
            return ChatResponse(
                message="This is a relevant legal question, but we currently don't have the answer in a document that we can reference. Please kindly create a ticket so we can help you with this issue.",
                relevant=True,
                sources=[],
                confidence="low"
            )

        # Check similarity of top result
        top_similarity = search_results[0].get("similarity", 0)
        logger.info(f"Top result similarity: {top_similarity:.3f}")

        if top_similarity < settings.similarity_threshold:
            logger.info(f"Low similarity ({top_similarity:.3f} < {settings.similarity_threshold}), escalating to ticket")
            return ChatResponse(
                message="This is a relevant legal question, but we currently don't have the answer in a document that we can reference. Please kindly create a ticket so we can help you with this issue.",
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

        # Step 4: Format sources using utility function
        sources = format_sources(search_results, max_sources=3)

        return ChatResponse(
            message=response_data["answer"],
            relevant=True,
            sources=sources,
            confidence=response_data.get("confidence", "medium")
        )

    except MantraException as e:
        # Handle known Mantra exceptions with proper HTTP status codes
        status_code = get_http_status_code(e)
        logger.error(f"Mantra error ({status_code}): {e}")
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


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
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
