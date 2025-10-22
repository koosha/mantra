"""
Caselaw Access Project (CAP) Delaware Case Extractor

Extracts Delaware Supreme Court and Court of Chancery cases from Harvard's CAP.
Covers cases from 2005-2020.

AUTHENTICATION REQUIRED:
- Register at https://case.law/ to get an API token
- Set CAP_API_TOKEN environment variable or pass to constructor
- Limit: 500 cases per day for full text access
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CAPDelawareExtractor:
    """
    Extracts Delaware corporate law cases from Caselaw Access Project API.
    API from Harvard Law School - requires free registration for API token.
    """

    def __init__(self, api_token: Optional[str] = None, output_dir: str = "./data/cases"):
        """
        Initialize the extractor.

        Args:
            api_token: CAP API token (or set CAP_API_TOKEN env variable)
            output_dir: Directory to save extracted cases
        """
        self.base_url = "https://api.case.law/v1"
        self.output_dir = output_dir

        # Get API token from parameter or environment
        self.api_token = api_token or os.environ.get('CAP_API_TOKEN')

        if not self.api_token:
            raise ValueError(
                "CAP API token required. Either:\n"
                "1. Set CAP_API_TOKEN environment variable, or\n"
                "2. Pass api_token parameter to constructor\n\n"
                "Get your token at: https://case.law/"
            )

        self.headers = {
            'User-Agent': 'Delaware-Corporate-Law-Research/1.0',
            'Authorization': f'Token {self.api_token}'
        }

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def fetch_cases(self,
                   jurisdiction: str = "del",
                   start_year: int = 2005,
                   end_year: int = 2020,
                   max_cases: Optional[int] = None) -> List[Dict]:
        """
        Fetch all Delaware cases from CAP API.

        Args:
            jurisdiction: Jurisdiction code (del for Delaware)
            start_year: Starting year
            end_year: Ending year
            max_cases: Maximum number of cases to fetch

        Returns:
            List of case dictionaries
        """
        logger.info(f"Fetching Delaware cases from {start_year} to {end_year}")
        logger.info("Using Caselaw Access Project API (Harvard Law School)")

        all_cases = []
        url = f"{self.base_url}/cases/"

        # CAP API parameters
        params = {
            'jurisdiction': jurisdiction,
            'decision_date_min': f'{start_year}-01-01',
            'decision_date_max': f'{end_year}-12-31',
            'page_size': 100,  # Max allowed by CAP
            'ordering': '-decision_date',  # Most recent first
            'full_case': 'true'  # Get full case text
        }

        page = 1
        while url:
            try:
                logger.info(f"Fetching page {page}...")
                response = requests.get(url, params=params, headers=self.headers, timeout=30)

                # Check for authentication errors
                if response.status_code == 401:
                    logger.error("Authentication failed. Check your API token.")
                    logger.error("Get your token at: https://case.law/")
                    break

                response.raise_for_status()

                # Try to parse JSON
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response status: {response.status_code}")
                    logger.error(f"Response content (first 500 chars): {response.text[:500]}")
                    break
                page_cases = data.get('results', [])

                logger.info(f"Fetched {len(page_cases)} cases (Total: {len(all_cases)})")

                # Process each case
                for case in page_cases:
                    processed_case = self.process_case(case)
                    if processed_case:
                        all_cases.append(processed_case)

                # Check limits
                if max_cases and len(all_cases) >= max_cases:
                    all_cases = all_cases[:max_cases]
                    logger.info(f"Reached max_cases limit: {max_cases}")
                    break

                # Get next page
                url = data.get('next')
                params = None  # Next URL has all params
                page += 1

                # Rate limiting - be respectful
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching cases: {e}")
                break

        logger.info(f"Total cases fetched: {len(all_cases)}")
        return all_cases

    def process_case(self, case: Dict) -> Optional[Dict]:
        """
        Process and extract relevant fields from a CAP case.

        Args:
            case: Raw case data from CAP API

        Returns:
            Processed case dictionary
        """
        try:
            # Extract case text
            # CAP provides full text in 'casebody' field
            casebody = case.get('casebody', {})
            case_text = casebody.get('data', {})

            # For full_case=true, CAP returns structured text
            # Extract opinions text
            opinions_text = ""
            if isinstance(case_text, dict):
                opinions = case_text.get('opinions', [])
                for opinion in opinions:
                    if isinstance(opinion, dict):
                        text = opinion.get('text', '')
                        if text:
                            opinions_text += text + "\n\n"

            # If no structured text, try plain text
            if not opinions_text:
                opinions_text = case_text.get('text', '') if isinstance(case_text, dict) else str(case_text)

            # Get court info
            court_info = case.get('court', {})
            court_name = court_info.get('name', 'Unknown Court')

            # Create processed case
            processed = {
                'id': case.get('id'),
                'case_name': case.get('name', 'Unknown Case'),
                'case_name_full': case.get('name_abbreviation', ''),
                'docket_number': case.get('docket_number', ''),
                'date_filed': case.get('decision_date', ''),
                'court': court_name,
                'plain_text': opinions_text,
                'html': '',
                'absolute_url': case.get('url', ''),
                'frontend_url': case.get('frontend_url', ''),
                'citation_count': len(case.get('citations', [])),
                'author_str': '',
                'source': 'cap',
                'metadata': {
                    'jurisdiction': case.get('jurisdiction', {}).get('name', ''),
                    'citations': case.get('citations', []),
                    'volume': case.get('volume', {}).get('volume_number', ''),
                    'reporter': case.get('reporter', {}).get('full_name', ''),
                    'first_page': case.get('first_page', ''),
                    'last_page': case.get('last_page', ''),
                }
            }

            # Calculate text statistics
            processed['text_length'] = len(opinions_text)
            processed['word_count'] = len(opinions_text.split()) if opinions_text else 0

            return processed

        except Exception as e:
            logger.error(f"Error processing case: {e}")
            return None

    def save_to_json(self, cases: List[Dict], filename: str = "delaware_cases.json"):
        """
        Save cases to JSON file.

        Args:
            cases: List of case dictionaries
            filename: Output filename
        """
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cases, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(cases)} cases to {filepath}")

    def generate_summary_stats(self, cases: List[Dict]) -> Dict:
        """
        Generate summary statistics.

        Args:
            cases: List of case dictionaries

        Returns:
            Statistics dictionary
        """
        if not cases:
            return {}

        valid_dates = [c.get('date_filed', '') for c in cases if c.get('date_filed')]

        stats = {
            'total_cases': len(cases),
            'date_range': {
                'earliest': min(valid_dates) if valid_dates else 'N/A',
                'latest': max(valid_dates) if valid_dates else 'N/A'
            },
            'total_words': sum(c.get('word_count', 0) for c in cases),
            'avg_words_per_case': sum(c.get('word_count', 0) for c in cases) / len(cases) if cases else 0,
            'cases_with_citations': sum(1 for c in cases if c.get('citation_count', 0) > 0),
            'total_citations': sum(c.get('citation_count', 0) for c in cases),
            'courts': {}
        }

        # Count by court
        for case in cases:
            court = case.get('court', 'Unknown')
            stats['courts'][court] = stats['courts'].get(court, 0) + 1

        return stats

    def run(self, start_year: int = 2005, end_year: int = 2020, max_cases: Optional[int] = None):
        """
        Run the complete extraction pipeline.

        Args:
            start_year: Year to start from
            end_year: Year to end at (CAP only has data through 2020)
            max_cases: Maximum number of cases (None for all)
        """
        logger.info("=" * 80)
        logger.info("Caselaw Access Project (CAP) Delaware Case Extractor")
        logger.info("=" * 80)
        logger.info("Data source: Harvard Law School")
        logger.info("Coverage: Published cases through 2020")
        logger.info("=" * 80)

        # Fetch cases
        cases = self.fetch_cases(
            jurisdiction='del',
            start_year=start_year,
            end_year=min(end_year, 2020),  # CAP only has through 2020
            max_cases=max_cases
        )

        if not cases:
            logger.warning("No cases fetched. Exiting.")
            return

        # Save to JSON
        self.save_to_json(cases)

        # Generate statistics
        stats = self.generate_summary_stats(cases)
        stats_file = os.path.join(self.output_dir, "summary_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        logger.info("=" * 80)
        logger.info("EXTRACTION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total cases: {stats['total_cases']}")
        logger.info(f"Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        logger.info(f"Total words: {stats['total_words']:,}")
        logger.info(f"Average words per case: {stats['avg_words_per_case']:.0f}")
        logger.info(f"Cases with citations: {stats['cases_with_citations']}")
        logger.info(f"Total citations: {stats['total_citations']}")
        logger.info(f"Cases by court:")
        for court, count in stats['courts'].items():
            logger.info(f"  - {court}: {count}")
        logger.info("=" * 80)


def main():
    """
    Main function to run the extractor.
    """
    extractor = CAPDelawareExtractor(output_dir="./data/cases")

    # Run extraction for 2005-2020
    # CAP only has data through 2020
    extractor.run(start_year=2005, end_year=2020, max_cases=None)


if __name__ == "__main__":
    main()
