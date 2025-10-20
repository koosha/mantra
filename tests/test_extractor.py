"""
Quick test script for the Delaware Case Law Extractor.
This fetches a small sample to verify the API connection and data format.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mantra import DelawareCaseLawExtractor


def test_extractor():
    """Test the extractor with a small sample."""
    print("=" * 80)
    print("Testing Delaware Case Law Extractor")
    print("=" * 80)
    
    # Get API token if available
    api_token = os.getenv("COURTLISTENER_API_TOKEN")
    
    # Initialize extractor with test directory
    extractor = DelawareCaseLawExtractor(
        api_token=api_token,
        output_dir="./data/test_cases"
    )
    
    print("\nFetching 5 cases for testing...")
    print("This should take about 10-15 seconds...\n")
    
    # Run with limited results for testing
    extractor.run(max_results=5, save_individual=True)
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\nCheck the following files:")
    print("  - ./data/test_cases/delaware_cases.json")
    print("  - ./data/test_cases/summary_stats.json")
    print("  - ./data/test_cases/individual/case_*.json")
    print("\nIf files exist and contain data, the extractor is working correctly!")
    print("=" * 80)


if __name__ == "__main__":
    test_extractor()
