"""
Utility functions for Mantra application.
Provides common functionality used across multiple modules.
"""

from typing import List, Dict, Optional


def extract_case_name_from_url(url: str) -> str:
    """
    Extract case name from CourtListener URL.

    Args:
        url: CourtListener URL (e.g., /opinion/123/qian-v-zheng/)

    Returns:
        Case name in title case (e.g., "Qian V Zheng")
    """
    if not url or "/" not in url:
        return "Unknown Case"

    url_parts = url.rstrip("/").split("/")
    if len(url_parts) == 0:
        return "Unknown Case"

    slug = url_parts[-1]
    # Convert slug to title case: qian-v-zheng -> Qian V Zheng
    case_name = " ".join(word.capitalize() for word in slug.split("-"))
    return case_name


def format_sources(
    search_results: List[Dict],
    max_sources: int = 3
) -> List[Dict]:
    """
    Format and deduplicate sources from search results.

    Extracts unique cases from search results and formats them for display.
    Deduplicates by case_id and extracts case names from URLs when needed.

    Args:
        search_results: List of search result dictionaries from indexer
        max_sources: Maximum number of unique sources to return

    Returns:
        List of formatted source dictionaries with keys:
        - case_name: Name of the case
        - date: Filing date
        - court: Court name
        - citation: Full citation
        - url: URL to case
    """
    sources = []
    seen_case_ids = set()

    for result in search_results:
        metadata = result.get("metadata", {})
        case_id = metadata.get("case_id")

        # Skip if we've already added this case
        if case_id in seen_case_ids:
            continue

        seen_case_ids.add(case_id)

        # Get case name, fallback to extracting from URL if "Unknown Case"
        case_name = metadata.get("case_name", "Unknown Case")
        url = metadata.get("absolute_url", "#")

        if case_name == "Unknown Case" or not case_name:
            case_name = extract_case_name_from_url(url)

        sources.append({
            "case_name": case_name,
            "date": metadata.get("date_filed", ""),
            "court": metadata.get("court", ""),
            "citation": metadata.get("case_name_full", case_name),
            "url": url
        })

        # Stop if we have enough sources
        if len(sources) >= max_sources:
            break

    return sources


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated

    Returns:
        Truncated text with suffix
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_confidence(confidence: str) -> str:
    """
    Format confidence level for display.

    Args:
        confidence: Confidence level ("low", "medium", "high")

    Returns:
        Formatted confidence string with emoji
    """
    confidence_map = {
        "low": "🟡 Low",
        "medium": "🟢 Medium",
        "high": "🟢 High"
    }
    return confidence_map.get(confidence.lower(), confidence)


def format_court_name(court: str) -> str:
    """
    Format court name for display.

    Args:
        court: Raw court name

    Returns:
        Formatted court name
    """
    # Common abbreviations and formatting
    court_map = {
        "delaware-supreme": "Delaware Supreme Court",
        "delaware-chancery": "Delaware Court of Chancery",
        "delaware": "Delaware Courts"
    }

    # Check if we have a known mapping
    court_lower = court.lower().strip()
    if court_lower in court_map:
        return court_map[court_lower]

    # Otherwise, just title case it
    return court.title()


def calculate_word_count(text: str) -> int:
    """
    Calculate word count in text.

    Args:
        text: Text to count words in

    Returns:
        Number of words
    """
    return len(text.split())


def validate_k_parameter(k: int, min_k: int = 1, max_k: int = 20) -> int:
    """
    Validate and clamp k parameter for retrieval.

    Args:
        k: Number of documents to retrieve
        min_k: Minimum allowed value
        max_k: Maximum allowed value

    Returns:
        Validated k value (clamped to range)
    """
    return max(min_k, min(k, max_k))
