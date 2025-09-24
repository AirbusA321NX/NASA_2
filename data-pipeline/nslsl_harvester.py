import requests
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSLSLHarvester:
    """
    Harvester for NASA Scientific and Technical Information (STI) Database
    Fetches publication records and DOIs from NSLSL endpoints
    """
    
    def __init__(self, base_url: str = "https://ntrs.nasa.gov/api/citations"):
        self.base_url = base_url
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'NASA-Space-Biology-Knowledge-Engine/1.0'
        })

    def search_publications(self, query: str = "space biology", 
                          limit: int = 100, 
                          offset: int = 0) -> Dict[str, Any]:
        """
        Search for publications in the NSLSL database
        
        Args:
            query: Search query terms
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            Dictionary with search results and metadata
        """
        params = {
            'abstract': query,
            'limit': limit,
            'offset': offset
        }
        
        try:
            logger.info(f"Searching NSLSL for: {query}")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Found {data.get('stats', {}).get('total', 0)} total results")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching NSLSL: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing NSLSL response: {e}")
            raise

    def get_publication_metadata(self, citation_id: str) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific publication
        
        Args:
            citation_id: The NTRS citation ID
            
        Returns:
            Dictionary with publication metadata
        """
        url = f"{self.base_url}/{citation_id}"
        
        try:
            logger.info(f"Fetching metadata for citation: {citation_id}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching metadata for {citation_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing metadata response for {citation_id}: {e}")
            raise

    def extract_relevant_fields(self, publication_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant fields from NSLSL publication data
        
        Args:
            publication_data: Raw publication data from NSLSL
            
        Returns:
            Dictionary with normalized publication fields
        """
        # Extract core metadata
        core = publication_data.get('core', {})
        metadata = publication_data.get('metadata', {})
        
        # Extract title
        title = core.get('title', '')
        
        # Extract authors
        authors = []
        if 'author' in core:
            for author in core['author']:
                if isinstance(author, dict):
                    name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                    if name:
                        authors.append(name)
                elif isinstance(author, str):
                    authors.append(author)
        
        # Extract publication date
        pub_date = ''
        if 'created' in core:
            pub_date = core['created']
        elif 'updated' in core:
            pub_date = core['updated']
        
        # Extract DOI
        doi = ''
        if 'doi' in core:
            doi = core['doi']
        elif 'identifier' in core:
            # Look for DOI in identifiers
            for identifier in core['identifier']:
                if isinstance(identifier, dict) and identifier.get('scheme') == 'doi':
                    doi = identifier.get('value', '')
                    break
        
        # Extract abstract
        abstract = core.get('abstract', '')
        
        # Extract keywords
        keywords = core.get('subject', [])
        
        # Extract NASA specific fields
        nasa_fields = {
            'nslsl_id': core.get('id', ''),
            'document_type': core.get('documentType', ''),
            'publication_type': core.get('publicationType', ''),
            'venue': core.get('venue', ''),
            'publisher': core.get('publisher', ''),
            'distribution': core.get('distribution', ''),
            'funding': core.get('funding', []),
            'related': core.get('related', [])
        }
        
        # Extract file URLs if available
        file_urls = []
        if 'downloads' in core:
            for download in core['downloads']:
                if isinstance(download, dict) and 'links' in download:
                    for link in download['links']:
                        if isinstance(link, dict) and link.get('type') == 'fulltext':
                            file_urls.append(link.get('url', ''))
        
        return {
            'title': title,
            'authors': authors,
            'publication_date': pub_date,
            'doi': doi,
            'abstract': abstract,
            'keywords': keywords,
            'file_urls': file_urls,
            'nasa_metadata': nasa_fields
        }

    def harvest_publications(self, query: str = "space biology", 
                           max_records: int = 1000) -> List[Dict[str, Any]]:
        """
        Harvest publications from NSLSL database
        
        Args:
            query: Search query terms
            max_records: Maximum number of records to harvest
            
        Returns:
            List of normalized publication records
        """
        publications = []
        limit = 100  # Number of records per request
        offset = 0
        
        logger.info(f"Starting harvest of up to {max_records} publications for query: {query}")
        
        while len(publications) < max_records:
            try:
                # Search for publications
                search_results = self.search_publications(
                    query=query, 
                    limit=min(limit, max_records - len(publications)), 
                    offset=offset
                )
                
                # Extract citations
                citations = search_results.get('citations', [])
                
                if not citations:
                    logger.info("No more citations found, ending harvest")
                    break
                
                logger.info(f"Processing {len(citations)} citations")
                
                # Process each citation
                for citation in citations:
                    try:
                        # Get detailed metadata
                        citation_id = citation.get('id')
                        if citation_id:
                            metadata = self.get_publication_metadata(citation_id)
                            
                            # Extract relevant fields
                            normalized_data = self.extract_relevant_fields(metadata)
                            normalized_data['nslsl_id'] = citation_id
                            
                            publications.append(normalized_data)
                            
                            # Respect rate limits
                            time.sleep(0.1)
                    
                    except Exception as e:
                        logger.warning(f"Error processing citation {citation.get('id', 'unknown')}: {e}")
                        continue
                
                # Check if we've reached the end of results
                stats = search_results.get('stats', {})
                total_results = stats.get('total', 0)
                
                if offset + len(citations) >= total_results:
                    logger.info("Reached end of search results")
                    break
                
                # Update offset for next iteration
                offset += len(citations)
                logger.info(f"Harvested {len(publications)} publications so far")
                
                # Respect rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in harvest loop: {e}")
                break
        
        logger.info(f"Completed harvest with {len(publications)} publications")
        return publications

    def save_publications(self, publications: List[Dict[str, Any]], filename: str = "nslsl_publications.json"):
        """
        Save harvested publications to a JSON file
        
        Args:
            publications: List of publication records
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(publications, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved {len(publications)} publications to {filename}")
        except Exception as e:
            logger.error(f"Error saving publications: {e}")

def main():
    """
    Main function to demonstrate NSLSL harvester functionality
    """
    harvester = NSLSLHarvester()
    
    try:
        # Harvest publications related to space biology
        publications = harvester.harvest_publications(
            query="space biology", 
            max_records=50  # Limit for demonstration
        )
        
        # Save to file
        harvester.save_publications(publications, "nslsl_space_biology.json")
        
        # Show summary
        print(f"Harvested {len(publications)} publications")
        if publications:
            print("\nFirst publication example:")
            print(json.dumps(publications[0], indent=2, default=str))
            
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()