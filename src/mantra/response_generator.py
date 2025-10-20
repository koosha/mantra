"""
Response Generation Component.
Generates legal responses with proper citations and formatting.
"""

import os
import logging
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalResponseGenerator:
    """
    Generates responses for legal queries with proper citations.
    """
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the response generator.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model
        self.llm = ChatOpenAI(model=model, temperature=0)
        
        # Response generation prompt
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Mantra, an expert legal assistant specializing in Delaware corporate law.

Your role is to provide accurate, well-reasoned answers to questions about Delaware corporate law based on the provided case law excerpts.

GUIDELINES:
1. Base your answer primarily on the provided case excerpts
2. Provide clear, concise explanations of legal concepts
3. Cite specific cases when making legal points in the text
4. Use proper legal terminology
5. If the excerpts don't fully answer the question, acknowledge limitations
6. Structure your response clearly with proper formatting

RESPONSE STRUCTURE:
1. Direct answer to the question
2. Legal explanation with case support
3. Key precedents or standards
4. Practical implications (if relevant)

CITATION FORMAT:
- Reference cases naturally in your text: "In Smith v. Van Gorkom, the court held..."
- Do NOT include a separate citations section at the end (sources are provided separately)

Be professional, accurate, and helpful. If you're uncertain, say so."""),
            ("user", """Question: {question}

Relevant Case Law Excerpts:
{context}

Please provide a comprehensive answer based on these excerpts.""")
        ])
    
    def generate_response(
        self,
        question: str,
        retrieved_chunks: List[Dict],
        include_sources: bool = True
    ) -> Dict:
        """
        Generate a response to a legal question.
        
        Args:
            question: User's question
            retrieved_chunks: List of retrieved document chunks with metadata
            include_sources: Whether to include source citations
            
        Returns:
            Dictionary with response and metadata
        """
        if not retrieved_chunks:
            return {
                "answer": "I couldn't find relevant case law to answer your question. Please try rephrasing or ask about a different topic.",
                "sources": [],
                "confidence": "low"
            }
        
        # Format context from retrieved chunks
        context = self._format_context(retrieved_chunks)
        
        # Generate response
        try:
            prompt = self.response_prompt.format_messages(
                question=question,
                context=context
            )
            
            response = self.llm.invoke(prompt)
            answer = response.content
            
            # Extract and format sources
            sources = self._extract_sources(retrieved_chunks) if include_sources else []
            
            # Add sources section to answer if not already included
            if include_sources and sources:
                answer = self._add_sources_section(answer, sources)
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": self._estimate_confidence(retrieved_chunks),
                "chunks_used": len(retrieved_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "answer": "I encountered an error generating a response. Please try again.",
                "sources": [],
                "confidence": "error"
            }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context for the prompt.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get("metadata", {})
            text = chunk.get("text", "")
            
            case_name = metadata.get("case_name", "Unknown Case")
            date = metadata.get("date_filed", "Unknown Date")
            court = metadata.get("court", "Unknown Court")
            
            context_part = f"""
[Excerpt {i}]
Case: {case_name}
Date: {date}
Court: {court}

{text}
"""
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """
        Extract unique sources from chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of unique source dictionaries
        """
        sources_dict = {}
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            case_id = metadata.get("case_id")
            
            if case_id and case_id not in sources_dict:
                sources_dict[case_id] = {
                    "case_name": metadata.get("case_name", "Unknown"),
                    "case_name_full": metadata.get("case_name_full", ""),
                    "date_filed": metadata.get("date_filed", ""),
                    "court": metadata.get("court", ""),
                    "url": metadata.get("absolute_url", ""),
                    "citation_count": metadata.get("citation_count", 0)
                }
        
        # Sort by citation count (more cited cases first)
        sources = list(sources_dict.values())
        sources.sort(key=lambda x: x["citation_count"], reverse=True)
        
        return sources
    
    def _add_sources_section(self, answer: str, sources: List[Dict]) -> str:
        """
        Add a sources section to the answer if not already present.
        
        Args:
            answer: Generated answer
            sources: List of source dictionaries
            
        Returns:
            Answer with sources section
        """
        # Check if answer already has a sources/citations section
        if "**Sources:**" in answer or "**Citations:**" in answer or "**References:**" in answer:
            return answer
        
        # Add sources section
        sources_section = "\n\n---\n\n**Sources:**\n\n"
        
        for i, source in enumerate(sources, 1):
            case_name = source["case_name"]
            date = source["date_filed"]
            court = source["court"]
            url = source["url"]
            
            # Format court name
            court_display = court.replace("-", " ").title()
            
            sources_section += f"{i}. **{case_name}** ({court_display}, {date})\n"
            if url:
                sources_section += f"   [View Case]({url})\n"
            sources_section += "\n"
        
        return answer + sources_section
    
    def _estimate_confidence(self, chunks: List[Dict]) -> str:
        """
        Estimate confidence level based on retrieved chunks.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Confidence level string
        """
        if not chunks:
            return "low"
        
        # Check similarity scores
        avg_similarity = sum(chunk.get("similarity", 0) for chunk in chunks) / len(chunks)
        
        if avg_similarity > 0.8:
            return "high"
        elif avg_similarity > 0.6:
            return "medium"
        else:
            return "low"
    
    def format_rejection_response(self, query: str, reason: str) -> str:
        """
        Format a response for rejected (irrelevant) queries.
        
        Args:
            query: Original query
            reason: Reason for rejection
            
        Returns:
            Formatted rejection message
        """
        return f"""I apologize, but your question does not appear to be related to Delaware corporate law or case law.

**Your question:** {query}

**Why this was flagged:** {reason}

**I can help you with:**
• Delaware corporate law concepts (fiduciary duty, business judgment rule, entire fairness, etc.)
• Delaware Court of Chancery and Supreme Court cases
• Corporate governance, mergers, and acquisitions
• Shareholder rights and remedies
• Legal standards and procedures in Delaware corporate law

Please ask a question related to these topics, and I'll be happy to provide a detailed answer with case citations!"""


def test_response_generator():
    """Test the response generator with sample data."""
    generator = LegalResponseGenerator()
    
    # Mock retrieved chunks
    mock_chunks = [
        {
            "text": "The business judgment rule is a presumption that in making a business decision, the directors of a corporation acted on an informed basis, in good faith and in the honest belief that the action taken was in the best interests of the company.",
            "metadata": {
                "case_id": 12345,
                "case_name": "Aronson v. Lewis",
                "case_name_full": "Aronson v. Lewis, 473 A.2d 805 (Del. 1984)",
                "date_filed": "1984-03-01",
                "court": "delaware-supreme",
                "absolute_url": "https://www.courtlistener.com/opinion/...",
                "citation_count": 2500
            },
            "similarity": 0.85
        },
        {
            "text": "To rebut the business judgment rule, a plaintiff must show that the directors breached their fiduciary duty of care or loyalty, or acted in bad faith.",
            "metadata": {
                "case_id": 12346,
                "case_name": "Smith v. Van Gorkom",
                "case_name_full": "Smith v. Van Gorkom, 488 A.2d 858 (Del. 1985)",
                "date_filed": "1985-01-29",
                "court": "delaware-supreme",
                "absolute_url": "https://www.courtlistener.com/opinion/...",
                "citation_count": 3000
            },
            "similarity": 0.82
        }
    ]
    
    question = "What is the business judgment rule?"
    
    print("=" * 80)
    print("Testing Response Generator")
    print("=" * 80)
    print(f"\nQuestion: {question}\n")
    
    result = generator.generate_response(question, mock_chunks)
    
    print("Answer:")
    print(result["answer"])
    print(f"\nConfidence: {result['confidence']}")
    print(f"Chunks used: {result['chunks_used']}")
    print(f"Sources: {len(result['sources'])}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_response_generator()
