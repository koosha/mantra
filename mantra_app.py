"""
Mantra - Delaware Corporate Law Chatbot
Integrated application with all components.
"""

import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mantra import DelawareCaseLawIndexer, QueryClassifier, LegalResponseGenerator

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Mantra - Delaware Corporate Law Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for legal theme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .confidence-high {
        color: #16a34a;
        font-weight: 600;
    }
    .confidence-medium {
        color: #ea580c;
        font-weight: 600;
    }
    .confidence-low {
        color: #dc2626;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "indexer" not in st.session_state:
    st.session_state.indexer = None
if "classifier" not in st.session_state:
    st.session_state.classifier = None
if "generator" not in st.session_state:
    st.session_state.generator = None
if "index_loaded" not in st.session_state:
    st.session_state.index_loaded = False


def initialize_components():
    """Initialize all Mantra components."""
    if st.session_state.indexer is None:
        with st.spinner("Initializing Mantra components..."):
            try:
                # Initialize indexer
                st.session_state.indexer = DelawareCaseLawIndexer(
                    embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                    index_path=os.getenv("FAISS_INDEX_PATH", "./faiss_index"),
                    data_path=os.getenv("DATA_DIR", "./data/cases") + "/delaware_cases.json"
                )
                
                # Load existing index
                try:
                    st.session_state.indexer.load_index()
                    st.session_state.index_loaded = True
                    st.sidebar.success("✅ Index loaded successfully!")
                except FileNotFoundError:
                    st.sidebar.warning("⚠️ No index found. Please build the index first.")
                    st.session_state.index_loaded = False
                
                # Initialize classifier
                st.session_state.classifier = QueryClassifier(
                    model=os.getenv("LLM_MODEL", "gpt-4")
                )
                
                # Initialize response generator
                st.session_state.generator = LegalResponseGenerator(
                    model=os.getenv("LLM_MODEL", "gpt-4")
                )
                
            except Exception as e:
                st.error(f"Error initializing components: {e}")


def process_query(query: str) -> dict:
    """
    Process a user query through the complete pipeline.
    
    Args:
        query: User's question
        
    Returns:
        Response dictionary
    """
    # Step 1: Classify query
    classification = st.session_state.classifier.classify_query(query)
    
    if not classification["relevant"]:
        return {
            "type": "rejection",
            "answer": st.session_state.generator.format_rejection_response(
                query,
                classification["reason"]
            ),
            "classification": classification
        }
    
    # Step 2: Retrieve relevant cases
    try:
        # Get filters from sidebar if any
        filters = {}
        if st.session_state.get("filter_court"):
            filters["court"] = st.session_state.filter_court
        if st.session_state.get("filter_date_from"):
            filters["date_filed"] = {"$gte": st.session_state.filter_date_from}
        
        retrieved_chunks = st.session_state.indexer.search(
            query=query,
            k=4,
            filters=filters if filters else None,
            retrieve_k=20
        )
        
        if not retrieved_chunks:
            return {
                "type": "no_results",
                "answer": "I couldn't find relevant case law to answer your question. Please try rephrasing or ask about a different topic.",
                "classification": classification
            }
        
        # Step 3: Generate response
        response = st.session_state.generator.generate_response(
            question=query,
            retrieved_chunks=retrieved_chunks,
            include_sources=True
        )
        
        response["type"] = "success"
        response["classification"] = classification
        response["retrieved_chunks"] = retrieved_chunks
        
        return response
        
    except Exception as e:
        return {
            "type": "error",
            "answer": f"An error occurred while processing your query: {str(e)}",
            "classification": classification
        }


def display_message(role: str, content: dict):
    """Display a chat message with proper formatting."""
    with st.chat_message(role):
        if role == "user":
            st.markdown(content)
        else:
            # Display answer
            st.markdown(content.get("answer", ""))
            
            # Display confidence if available
            if "confidence" in content and content["type"] == "success":
                confidence = content["confidence"]
                confidence_class = f"confidence-{confidence}"
                st.markdown(
                    f'<p class="{confidence_class}">Confidence: {confidence.upper()}</p>',
                    unsafe_allow_html=True
                )
            
            # Display sources in expandable section
            if content.get("sources"):
                with st.expander("📚 View Source Cases", expanded=False):
                    for i, source in enumerate(content["sources"], 1):
                        st.markdown(f"""
                        <div class="source-box">
                            <strong>{i}. {source['case_name']}</strong><br>
                            Court: {source['court'].replace('-', ' ').title()}<br>
                            Date: {source['date_filed']}<br>
                            Citations: {source['citation_count']}<br>
                            {f'<a href="{source["url"]}" target="_blank">View Full Case →</a>' if source['url'] else ''}
                        </div>
                        """, unsafe_allow_html=True)


def main():
    """Main application."""
    
    # Header
    st.markdown('<h1 class="main-header">⚖️ Mantra</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Your Delaware Corporate Law Assistant</p>',
        unsafe_allow_html=True
    )
    
    # Initialize components
    initialize_components()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Index status
        st.subheader("Index Status")
        if st.session_state.index_loaded:
            st.success("✅ Index loaded")
            if st.session_state.indexer:
                st.info(f"📊 {st.session_state.indexer.index.ntotal:,} chunks indexed")
        else:
            st.error("❌ Index not loaded")
            st.info("Run `python indexer.py` to build the index")
        
        st.divider()
        
        # Search filters
        st.subheader("🔍 Search Filters")
        
        court_options = ["All Courts", "delaware-supreme", "delaware-chancery"]
        selected_court = st.selectbox("Court", court_options)
        st.session_state.filter_court = None if selected_court == "All Courts" else selected_court
        
        date_from = st.date_input(
            "Cases from",
            value=None,
            help="Filter cases filed on or after this date"
        )
        st.session_state.filter_date_from = date_from.isoformat() if date_from else None
        
        if st.button("Clear Filters"):
            st.session_state.filter_court = None
            st.session_state.filter_date_from = None
            st.rerun()
        
        st.divider()
        
        # About
        st.subheader("ℹ️ About Mantra")
        st.markdown("""
        Mantra is an AI-powered assistant specializing in Delaware corporate law.
        
        **Features:**
        - Query classification
        - Semantic search over case law
        - GPT-4 powered responses
        - Source citations
        - Metadata filtering
        
        **Data Source:**
        Delaware Supreme Court and Court of Chancery cases (2005-present)
        """)
        
        st.divider()
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.conversation = []
            st.rerun()
    
    # Main chat interface
    if not st.session_state.index_loaded:
        st.warning("⚠️ Please build the index first by running: `python indexer.py`")
        st.info("💡 You can test with a small sample by running: `python test_indexer.py`")
        return
    
    # Display conversation history
    for message in st.session_state.conversation:
        display_message(message["role"], message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about Delaware corporate law..."):
        # Add user message
        st.session_state.conversation.append({
            "role": "user",
            "content": prompt
        })
        display_message("user", prompt)
        
        # Process query
        with st.spinner("Researching case law..."):
            response = process_query(prompt)
        
        # Add assistant response
        st.session_state.conversation.append({
            "role": "assistant",
            "content": response
        })
        display_message("assistant", response)
    
    # Example queries
    if not st.session_state.conversation:
        st.markdown("### 💡 Example Questions")
        
        example_queries = [
            "What is fiduciary duty?",
            "Explain the business judgment rule",
            "What is the Revlon doctrine?",
            "How does entire fairness review work?",
            "What is the Corwin doctrine?",
            "Explain Section 220 books and records requests"
        ]
        
        cols = st.columns(3)
        for i, query in enumerate(example_queries):
            with cols[i % 3]:
                if st.button(query, key=f"example_{i}"):
                    st.session_state.conversation.append({
                        "role": "user",
                        "content": query
                    })
                    with st.spinner("Researching case law..."):
                        response = process_query(query)
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.rerun()


if __name__ == "__main__":
    main()
