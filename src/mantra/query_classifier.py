"""
Query Classification and Validation Component.
Determines if queries are relevant to Delaware case law.
"""

import os
import logging
from typing import Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryClassifier:
    """
    Classifies queries as relevant or irrelevant to Delaware case law.
    """
    
    # Legal terms that indicate relevance
    LEGAL_KEYWORDS = {
        # Corporate law concepts
        "fiduciary", "duty", "care", "loyalty", "good faith",
        "entire fairness", "business judgment", "revlon", "corwin", "caremark",
        "mfw", "unocal", "blasius", "schnell",
        
        # Corporate entities and roles
        "director", "officer", "shareholder", "stockholder", "board",
        "corporation", "company", "merger", "acquisition",
        "controlling shareholder", "special committee",
        
        # Legal procedures
        "appraisal", "section 220", "books and records", "derivative",
        "class action", "injunction", "damages", "remedy",
        
        # Transaction types
        "spac", "de-spac", "tender offer", "proxy", "buyout",
        "going private", "freeze-out", "squeeze-out",
        
        # Legal standards
        "standard of review", "burden of proof", "pleading stage",
        "motion to dismiss", "summary judgment", "trial",
        
        # Delaware courts
        "delaware", "chancery", "supreme court", "court of chancery",
        
        # Case law
        "precedent", "case law", "opinion", "ruling", "holding",
        "decision", "judgment", "appeal"
    }
    
    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the classifier.
        
        Args:
            model: OpenAI model to use for classification
        """
        self.model = model
        self.llm = ChatOpenAI(model=model, temperature=0)
        
        # Classification prompt
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a legal query classifier for a Delaware corporate law chatbot.

Your task is to determine if a user's query is relevant to Delaware corporate law and case law.

RELEVANT queries include:
- Questions about Delaware corporate law concepts (fiduciary duty, business judgment rule, etc.)
- Questions about specific Delaware court cases or precedents
- Questions about corporate governance, mergers, acquisitions, shareholder rights
- Questions about Delaware Court of Chancery or Delaware Supreme Court
- Questions about legal standards, procedures, or remedies in Delaware corporate law

IRRELEVANT queries include:
- Personal questions (e.g., "Who is John?" "Where do you work?")
- General knowledge questions unrelated to law
- Questions about other legal domains (criminal law, family law, etc.)
- Questions about other states' corporate law (unless comparing to Delaware)
- Casual conversation or greetings

Respond with a JSON object containing:
- "relevant": true or false
- "confidence": a number between 0 and 1
- "reason": brief explanation of your classification
- "suggested_topics": list of relevant legal topics if relevant, empty list if not

Example responses:
{{"relevant": true, "confidence": 0.95, "reason": "Query asks about fiduciary duty, a core Delaware corporate law concept", "suggested_topics": ["fiduciary duty", "duty of care"]}}
{{"relevant": false, "confidence": 0.99, "reason": "Query is a personal question unrelated to law", "suggested_topics": []}}
"""),
            ("user", "{query}")
        ])
    
    def classify_query(self, query: str) -> Dict:
        """
        Classify a query as relevant or irrelevant.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with classification results
        """
        # Quick keyword check first
        keyword_score = self._keyword_relevance_score(query)
        
        # If very high keyword score, skip LLM call
        if keyword_score > 0.7:
            return {
                "relevant": True,
                "confidence": min(keyword_score, 0.95),
                "reason": "Query contains multiple legal keywords",
                "suggested_topics": self._extract_topics(query),
                "method": "keyword"
            }
        
        # If very low keyword score, likely irrelevant
        if keyword_score < 0.1:
            return {
                "relevant": False,
                "confidence": 0.9,
                "reason": "Query does not contain legal terminology",
                "suggested_topics": [],
                "method": "keyword"
            }
        
        # Use LLM for ambiguous cases
        try:
            prompt = self.classification_prompt.format_messages(query=query)
            response = self.llm.invoke(prompt)
            
            # Parse response (assuming JSON format)
            import json
            result = json.loads(response.content)
            result["method"] = "llm"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Fallback to keyword-based classification
            return {
                "relevant": keyword_score > 0.3,
                "confidence": keyword_score,
                "reason": "Fallback to keyword-based classification",
                "suggested_topics": self._extract_topics(query) if keyword_score > 0.3 else [],
                "method": "keyword_fallback"
            }
    
    def _keyword_relevance_score(self, query: str) -> float:
        """
        Calculate relevance score based on keyword matching.
        
        Args:
            query: Query string
            
        Returns:
            Relevance score between 0 and 1
        """
        query_lower = query.lower()
        
        # Count matching keywords
        matches = sum(1 for keyword in self.LEGAL_KEYWORDS if keyword in query_lower)
        
        # Normalize by query length (longer queries can have more matches)
        query_words = len(query.split())
        
        if query_words == 0:
            return 0.0
        
        # Score based on density of legal terms
        density = matches / max(query_words, 1)
        
        # Cap at 1.0
        return min(density * 2, 1.0)
    
    def _extract_topics(self, query: str) -> list:
        """
        Extract legal topics from query based on keywords.
        
        Args:
            query: Query string
            
        Returns:
            List of identified topics
        """
        query_lower = query.lower()
        topics = []
        
        # Topic mappings
        topic_keywords = {
            "fiduciary duty": ["fiduciary", "duty of care", "duty of loyalty"],
            "business judgment rule": ["business judgment", "bjr"],
            "entire fairness": ["entire fairness", "fair dealing", "fair price"],
            "revlon": ["revlon", "sale of control"],
            "corwin": ["corwin", "stockholder vote"],
            "caremark": ["caremark", "oversight", "monitoring"],
            "appraisal": ["appraisal", "fair value"],
            "section 220": ["section 220", "books and records", "220"],
            "merger": ["merger", "acquisition", "m&a"],
            "shareholder rights": ["shareholder", "stockholder", "voting"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_rejection_message(self, query: str, classification: Dict) -> str:
        """
        Generate a helpful rejection message for irrelevant queries.
        
        Args:
            query: Original query
            classification: Classification result
            
        Returns:
            Rejection message string
        """
        base_message = (
            "I apologize, but your question does not appear to be related to Delaware corporate law or case law. "
            "I am specifically designed to answer questions about:\n\n"
            "• Delaware corporate law concepts (fiduciary duty, business judgment rule, etc.)\n"
            "• Delaware Court of Chancery and Supreme Court cases\n"
            "• Corporate governance, mergers, and acquisitions\n"
            "• Shareholder rights and remedies\n"
            "• Delaware legal standards and procedures\n\n"
            "Please ask a question related to these topics, and I'll be happy to help!"
        )
        
        return base_message


def test_classifier():
    """Test the query classifier with sample queries."""
    classifier = QueryClassifier()
    
    test_queries = [
        # Relevant queries
        "What is fiduciary duty?",
        "Explain the Revlon doctrine",
        "What is the business judgment rule?",
        "Tell me about Smith v. Van Gorkom",
        "What are the requirements for entire fairness review?",
        "How does Section 220 work for books and records requests?",
        
        # Irrelevant queries
        "Who is Koosha and where does he work?",
        "What's the weather today?",
        "How do I make pasta?",
        "Tell me a joke",
        "What is Python programming?",
    ]
    
    print("=" * 80)
    print("Testing Query Classifier")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = classifier.classify_query(query)
        print(f"  Relevant: {result['relevant']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Reason: {result['reason']}")
        print(f"  Method: {result['method']}")
        if result['suggested_topics']:
            print(f"  Topics: {', '.join(result['suggested_topics'])}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_classifier()
