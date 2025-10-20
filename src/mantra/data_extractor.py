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


class DelawareCaseLawExtractor:
    """
    Extracts Delaware corporate law cases from CourtListener API.
    Focuses on key corporate governance topics.
    """
    
    def __init__(self, api_token: Optional[str] = None, output_dir: str = "./data/cases"):
        """
        Initialize the extractor.
        
        Args:
            api_token: CourtListener API token (optional but recommended for higher rate limits)
            output_dir: Directory to save extracted cases
        """
        self.base_url = "https://www.courtlistener.com/api/rest/v3/opinions/"
        self.api_token = api_token
        self.output_dir = output_dir
        self.headers = {}
        
        if api_token:
            self.headers["Authorization"] = f"Token {api_token}"
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def build_search_params(self) -> Dict:
        """
        Build search parameters for all Delaware Supreme Court and Court of Chancery cases.
        No keyword filtering - retrieves all cases from these courts.
        """
        params = {
            "jurisdiction": "del",
            "court": "delaware-supreme,delaware-chancery",
            "date_filed__gte": "2005-01-01",
            # No full_text filter - get ALL cases from these courts
            "order_by": "-date_filed",  # Most recent first
        }
        return params
    
    def fetch_opinions(self, max_results: Optional[int] = None) -> List[Dict]:
        """
        Fetch opinions from CourtListener API with pagination.
        
        Args:
            max_results: Maximum number of results to fetch (None for all)
            
        Returns:
            List of opinion dictionaries
        """
        results = []
        params = self.build_search_params()
        url = self.base_url
        page = 1
        
        logger.info("Starting to fetch Delaware corporate law cases...")
        
        while True:
            try:
                logger.info(f"Fetching page {page}...")
                response = requests.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                page_results = data.get("results", [])
                results.extend(page_results)
                
                logger.info(f"Fetched {len(page_results)} opinions (Total: {len(results)})")
                
                # Check if we've reached max_results
                if max_results and len(results) >= max_results:
                    results = results[:max_results]
                    logger.info(f"Reached max_results limit: {max_results}")
                    break
                
                # Check for next page
                next_url = data.get("next")
                if not next_url:
                    logger.info("No more pages to fetch")
                    break
                
                url = next_url
                params = None  # Params are included in next_url
                page += 1
                
                # Rate limiting - be nice to the API
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data: {e}")
                break
        
        logger.info(f"Total opinions fetched: {len(results)}")
        return results
    
    def process_opinion(self, opinion: Dict) -> Dict:
        """
        Process and extract relevant fields from an opinion.
        
        Args:
            opinion: Raw opinion data from API
            
        Returns:
            Processed opinion dictionary
        """
        processed = {
            "id": opinion.get("id"),
            "case_name": opinion.get("case_name", "Unknown Case"),
            "case_name_full": opinion.get("case_name_full", ""),
            "date_filed": opinion.get("date_filed"),
            "court": opinion.get("court", ""),
            "plain_text": opinion.get("plain_text", ""),
            "html": opinion.get("html", ""),
            "absolute_url": opinion.get("absolute_url", ""),
            "citation_count": opinion.get("citation_count", 0),
            "author_str": opinion.get("author_str", ""),
            "type": opinion.get("type", ""),
            "download_url": opinion.get("download_url", ""),
            "local_path": opinion.get("local_path", ""),
            "extracted_by_ocr": opinion.get("extracted_by_ocr", False),
            "metadata": {
                "cluster": opinion.get("cluster", ""),
                "per_curiam": opinion.get("per_curiam", False),
                "joined_by": opinion.get("joined_by", []),
            }
        }
        
        # Calculate text statistics
        text = processed["plain_text"]
        processed["text_length"] = len(text)
        processed["word_count"] = len(text.split()) if text else 0
        
        return processed
    
    def save_to_json(self, opinions: List[Dict], filename: str = "delaware_cases.json"):
        """
        Save processed opinions to JSON file.
        
        Args:
            opinions: List of processed opinions
            filename: Output filename
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(opinions, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(opinions)} opinions to {filepath}")
        
    def save_individual_cases(self, opinions: List[Dict]):
        """
        Save each case as an individual JSON file.
        Useful for incremental processing.
        
        Args:
            opinions: List of processed opinions
        """
        individual_dir = os.path.join(self.output_dir, "individual")
        os.makedirs(individual_dir, exist_ok=True)
        
        for opinion in opinions:
            case_id = opinion.get("id", "unknown")
            filename = f"case_{case_id}.json"
            filepath = os.path.join(individual_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(opinion, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(opinions)} individual case files to {individual_dir}")
    
    def generate_summary_stats(self, opinions: List[Dict]) -> Dict:
        """
        Generate summary statistics about the extracted cases.
        
        Args:
            opinions: List of processed opinions
            
        Returns:
            Dictionary of statistics
        """
        if not opinions:
            return {}
        
        stats = {
            "total_cases": len(opinions),
            "date_range": {
                "earliest": min(op.get("date_filed", "") for op in opinions if op.get("date_filed")),
                "latest": max(op.get("date_filed", "") for op in opinions if op.get("date_filed"))
            },
            "total_words": sum(op.get("word_count", 0) for op in opinions),
            "avg_words_per_case": sum(op.get("word_count", 0) for op in opinions) / len(opinions),
            "cases_with_citations": sum(1 for op in opinions if op.get("citation_count", 0) > 0),
            "total_citations": sum(op.get("citation_count", 0) for op in opinions),
            "courts": {}
        }
        
        # Count cases by court
        for opinion in opinions:
            court = opinion.get("court", "Unknown")
            stats["courts"][court] = stats["courts"].get(court, 0) + 1
        
        return stats
    
    def run(self, max_results: Optional[int] = None, save_individual: bool = True):
        """
        Run the complete extraction pipeline.
        
        Args:
            max_results: Maximum number of results to fetch
            save_individual: Whether to save individual case files
        """
        logger.info("=" * 80)
        logger.info("Delaware Corporate Law Case Extractor")
        logger.info("=" * 80)
        
        # Fetch opinions
        raw_opinions = self.fetch_opinions(max_results=max_results)
        
        if not raw_opinions:
            logger.warning("No opinions fetched. Exiting.")
            return
        
        # Process opinions
        logger.info("Processing opinions...")
        processed_opinions = [self.process_opinion(op) for op in raw_opinions]
        
        # Save to JSON
        self.save_to_json(processed_opinions)
        
        # Save individual files if requested
        if save_individual:
            self.save_individual_cases(processed_opinions)
        
        # Generate and save statistics
        stats = self.generate_summary_stats(processed_opinions)
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
    # Get API token from environment variable (optional)
    api_token = os.getenv("COURTLISTENER_API_TOKEN")
    
    if not api_token:
        logger.warning("No API token found. Rate limits will be lower.")
        logger.warning("Set COURTLISTENER_API_TOKEN environment variable for higher limits.")
    
    # Initialize extractor
    extractor = DelawareCaseLawExtractor(
        api_token=api_token,
        output_dir="./data/cases"
    )
    
    # Run extraction
    # Set max_results to limit the number of cases (e.g., 100 for testing)
    # Set to None to fetch all available cases
    extractor.run(max_results=None, save_individual=True)


if __name__ == "__main__":
    main()
