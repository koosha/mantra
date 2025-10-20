#!/usr/bin/env python3
"""
Script to extract Delaware case law from CourtListener API.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mantra import DelawareCaseLawExtractor


def main():
    """Extract Delaware case law."""
    # Get API token from environment
    api_token = os.getenv("COURTLISTENER_API_TOKEN")
    
    # Initialize extractor
    extractor = DelawareCaseLawExtractor(
        api_token=api_token,
        output_dir="./data/cases"
    )
    
    # Run extraction
    extractor.run(max_results=None, save_individual=True)


if __name__ == "__main__":
    main()
