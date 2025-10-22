import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

def load_documents(file_paths):
    """Load and process documents from file paths."""
    documents = []
    for file_path in file_paths:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path)
        else:
            st.error(f"Unsupported file type: {file_path}")
            continue
        documents.extend(loader.load())
    return documents

def create_vector_store(documents):
    """Create a vector store from documents using FAISS."""
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    
    # Create embeddings and vector store with OpenAI
    embeddings = OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    return vector_store

def get_qa_chain(vector_store):
    """Create a QA chain for question answering with GPT-4."""
    # Use GPT-4 for high-quality legal analysis
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        temperature=0
    )
    
    # Create retriever
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

def main():
    st.title("📚 RAG Chat Interface")
    
    # Sidebar for file upload
    st.sidebar.header("Upload Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF or TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )
    
    # Process uploaded files
    if uploaded_files and st.sidebar.button("Process Documents"):
        with st.spinner("Processing documents..."):
            try:
                # Save uploaded files
                file_paths = []
                for file in uploaded_files:
                    file_path = f"./data/{file.name}"
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    file_paths.append(file_path)
                
                # Load and process documents
                documents = load_documents(file_paths)
                
                # Create vector store
                st.session_state.vector_store = create_vector_store(documents)
                st.sidebar.success(f"Processed {len(documents)} documents!")
                
            except Exception as e:
                st.sidebar.error(f"Error processing documents: {str(e)}")
    
    # Chat interface
    st.subheader("Chat with your documents")
    
    # Display chat messages
    for message in st.session_state.conversation:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your documents"):
        # Add user message to chat
        st.session_state.conversation.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check if documents are processed
        if st.session_state.vector_store is None:
            with st.chat_message("assistant"):
                st.error("Please upload and process documents first!")
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": "Please upload and process documents first!"
                })
        else:
            try:
                # Get QA chain
                qa_chain = get_qa_chain(st.session_state.vector_store)
                
                # Get response
                with st.spinner("Thinking..."):
                    response = qa_chain({"query": prompt})
                    answer = response["result"]
                    
                    # Add sources
                    sources = []
                    for doc in response["source_documents"]:
                        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                            source = doc.metadata['source']
                            if source not in sources:
                                sources.append(source)
                    
                    if sources:
                        answer += "\n\n**Sources:**\n"
                        for source in sources:
                            answer += f"- {source}\n"
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    
                # Add to conversation
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": answer
                })
                
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                with st.chat_message("assistant"):
                    st.error(error_msg)
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": error_msg
                })

if __name__ == "__main__":
    main()
