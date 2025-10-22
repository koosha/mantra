"""
Justia Delaware Case Law Extractor

Extracts Delaware Supreme Court and Court of Chancery cases from Justia.
More reliable alternative to CourtListener API.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JustiaDelawareExtractor:
    """
    Extracts Delaware corporate law cases from Justia.
    Focuses on Delaware Supreme Court and Court of Chancery.
    """

    def __init__(self, output_dir: str = "./data/cases"):
        """
        Initialize the extractor.

        Args:
            output_dir: Directory to save extracted cases
        """
        self.base_url = "https://law.justia.com"
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def get_years_to_fetch(self, start_year: int = 2005) -> List[int]:
        """
        Get list of years to fetch cases from.

        Args:
            start_year: Starting year (default 2005)

        Returns:
            List of years
        """
        current_year = datetime.now().year
        return list(range(start_year, current_year + 1))

    def fetch_year_index(self, court: str, year: int) -> List[Dict]:
        """
        Fetch all cases from a specific year for a court.

        Args:
            court: Either 'supreme-court' or 'court-of-chancery'
            year: Year to fetch

        Returns:
            List of case dictionaries with basic info
        """
        url = f"{self.base_url}/cases/delaware/{court}/{year}/"
        logger.info(f"Fetching {court} cases from {year}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            cases = []

            # Find all case links
            # Justia lists cases with links like /cases/delaware/supreme-court/2024/123/
            case_links = soup.find_all('a', href=re.compile(rf'/cases/delaware/{court}/{year}/\d+/'))

            for link in case_links:
                case_url = link.get('href')
                if not case_url.startswith('http'):
                    case_url = self.base_url + case_url

                case_name = link.get_text(strip=True)

                cases.append({
                    'url': case_url,
                    'case_name': case_name,
                    'year': year,
                    'court': 'Delaware Supreme Court' if court == 'supreme-court' else 'Delaware Court of Chancery'
                })

            logger.info(f"Found {len(cases)} cases for {court} {year}")
            return cases

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {court} {year}: {e}")
            return []

    def fetch_case_details(self, case_info: Dict) -> Optional[Dict]:
        """
        Fetch full details of a specific case.

        Args:
            case_info: Basic case info with URL

        Returns:
            Complete case dictionary with full text
        """
        url = case_info['url']
        logger.info(f"Fetching case: {case_info['case_name']}")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract case number/docket
            docket = ""
            docket_elem = soup.find('span', class_='docket')
            if docket_elem:
                docket = docket_elem.get_text(strip=True)

            # Extract decision date
            date_filed = ""
            date_elem = soup.find('span', class_='date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                # Try to parse date
                try:
                    date_obj = datetime.strptime(date_text, '%B %d, %Y')
                    date_filed = date_obj.strftime('%Y-%m-%d')
                except:
                    date_filed = date_text

            # Extract full case text
            case_text = ""
            # Justia puts case text in div with class 'entry-content' or similar
            content_div = soup.find('div', class_=['entry-content', 'case-content'])
            if content_div:
                case_text = content_div.get_text(separator='\n', strip=True)

            # If we didn't find content_div, try finding the main content area
            if not case_text:
                main_content = soup.find('article') or soup.find('main')
                if main_content:
                    case_text = main_content.get_text(separator='\n', strip=True)

            # Create complete case dictionary
            case_data = {
                'id': hash(url) % (10 ** 8),  # Generate simple ID from URL
                'case_name': case_info['case_name'],
                'case_name_full': case_info['case_name'],
                'docket_number': docket,
                'date_filed': date_filed,
                'court': case_info['court'],
                'plain_text': case_text,
                'html': str(content_div) if content_div else "",
                'absolute_url': url,
                'citation_count': 0,
                'author_str': "",
                'source': 'justia',
                'metadata': {
                    'year': case_info['year'],
                    'court_slug': 'supreme-court' if 'Supreme' in case_info['court'] else 'court-of-chancery'
                }
            }

            # Calculate text statistics
            case_data['text_length'] = len(case_text)
            case_data['word_count'] = len(case_text.split()) if case_text else 0

            return case_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching case details: {e}")
            return None

    def fetch_all_cases(self,
                       start_year: int = 2005,
                       max_cases: Optional[int] = None,
                       courts: List[str] = None) -> List[Dict]:
        """
        Fetch all cases from specified courts and years.

        Args:
            start_year: Starting year
            max_cases: Maximum number of cases to fetch (None for all)
            courts: List of courts to fetch from (default: both)

        Returns:
            List of case dictionaries
        """
        if courts is None:
            courts = ['supreme-court', 'court-of-chancery']

        years = self.get_years_to_fetch(start_year)
        all_cases = []

        logger.info(f"Fetching cases from {start_year} to {datetime.now().year}")
        logger.info(f"Courts: {', '.join(courts)}")

        # First, get all case URLs
        case_list = []
        for year in years:
            for court in courts:
                year_cases = self.fetch_year_index(court, year)
                case_list.extend(year_cases)

                # Rate limiting
                time.sleep(1)

                if max_cases and len(case_list) >= max_cases:
                    case_list = case_list[:max_cases]
                    break

            if max_cases and len(case_list) >= max_cases:
                break

        logger.info(f"Found {len(case_list)} total cases to fetch")

        # Now fetch full details for each case
        for i, case_info in enumerate(case_list, 1):
            logger.info(f"Progress: {i}/{len(case_list)}")

            case_data = self.fetch_case_details(case_info)
            if case_data:
                all_cases.append(case_data)

            # Rate limiting - be respectful
            time.sleep(2)

            # Check max_cases limit
            if max_cases and len(all_cases) >= max_cases:
                break

        logger.info(f"Successfully fetched {len(all_cases)} cases")
        return all_cases

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

        stats = {
            'total_cases': len(cases),
            'date_range': {
                'earliest': min(c.get('date_filed', '9999') for c in cases if c.get('date_filed')),
                'latest': max(c.get('date_filed', '0000') for c in cases if c.get('date_filed'))
            },
            'total_words': sum(c.get('word_count', 0) for c in cases),
            'avg_words_per_case': sum(c.get('word_count', 0) for c in cases) / len(cases),
            'courts': {}
        }

        # Count by court
        for case in cases:
            court = case.get('court', 'Unknown')
            stats['courts'][court] = stats['courts'].get(court, 0) + 1

        return stats

    def run(self, start_year: int = 2005, max_cases: Optional[int] = None):
        """
        Run the complete extraction pipeline.

        Args:
            start_year: Year to start from
            max_cases: Maximum number of cases (None for all)
        """
        logger.info("=" * 80)
        logger.info("Justia Delaware Case Law Extractor")
        logger.info("=" * 80)

        # Fetch cases
        cases = self.fetch_all_cases(start_year=start_year, max_cases=max_cases)

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
        logger.info(f"Cases by court:")
        for court, count in stats['courts'].items():
            logger.info(f"  - {court}: {count}")
        logger.info("=" * 80)


def main():
    """
    Main function to run the extractor.
    """
    extractor = JustiaDelawareExtractor(output_dir="./data/cases")

    # Run extraction
    # Set max_cases to limit (e.g., 10 for testing, None for all)
    extractor.run(start_year=2005, max_cases=None)


if __name__ == "__main__":
    main()
