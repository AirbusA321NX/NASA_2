import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib
import asyncio

# Import existing components
from osdr_crawler import OSDRCrawler
from nslsl_harvester import NSLSLHarvester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncrementalIngestManager:
    """
    Manager for incremental ingest with change detection against OSDR/NSLSL APIs
    """
    
    def __init__(self, state_file: str = "ingest_state.json"):
        self.state_file = state_file
        self.state = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        """
        Load ingest state from file
        
        Returns:
            Dictionary with ingest state
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading state file: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """
        Save ingest state to file
        """
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving state file: {e}")
    
    def _generate_content_hash(self, content: Any) -> str:
        """
        Generate a hash for content to detect changes
        
        Args:
            content: Content to hash
            
        Returns:
            Hash string
        """
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def check_osdr_changes(self) -> Dict[str, Any]:
        """
        Check for changes in OSDR studies
        
        Returns:
            Dictionary with change information
        """
        logger.info("Checking for OSDR changes...")
        
        # Get last check timestamp
        last_check = self.state.get('osdr', {}).get('last_check', '1970-01-01T00:00:00')
        
        try:
            async with OSDRCrawler() as crawler:
                # Fetch current studies
                current_studies = await crawler.fetch_study_records()
                
                # Generate hash of current studies
                current_hash = self._generate_content_hash(current_studies)
                
                # Get previous hash
                previous_hash = self.state.get('osdr', {}).get('content_hash', '')
                
                # Check for changes
                has_changes = current_hash != previous_hash
                new_studies = []
                updated_studies = []
                
                if has_changes:
                    logger.info("Detected changes in OSDR studies")
                    
                    # Get previous studies if available
                    previous_studies = self.state.get('osdr', {}).get('studies', [])
                    previous_study_dict = {study.get('osd_id'): study for study in previous_studies}
                    current_study_dict = {study.get('osd_id'): study for study in current_studies}
                    
                    # Identify new studies
                    for study_id, study in current_study_dict.items():
                        if study_id not in previous_study_dict:
                            new_studies.append(study)
                    
                    # Identify updated studies
                    for study_id, study in current_study_dict.items():
                        if study_id in previous_study_dict:
                            prev_study = previous_study_dict[study_id]
                            if self._generate_content_hash(study) != self._generate_content_hash(prev_study):
                                updated_studies.append(study)
                
                # Update state
                self.state['osdr'] = {
                    'last_check': datetime.now().isoformat(),
                    'content_hash': current_hash,
                    'studies': current_studies,
                    'changes_detected': has_changes,
                    'new_studies_count': len(new_studies),
                    'updated_studies_count': len(updated_studies)
                }
                
                self._save_state()
                
                return {
                    'has_changes': has_changes,
                    'new_studies': new_studies,
                    'updated_studies': updated_studies,
                    'total_studies': len(current_studies),
                    'last_check': last_check
                }
                
        except Exception as e:
            logger.error(f"Error checking OSDR changes: {e}")
            return {
                'has_changes': False,
                'error': str(e)
            }
    
    def check_nslsl_changes(self, query: str = "space biology") -> Dict[str, Any]:
        """
        Check for changes in NSLSL publications
        
        Args:
            query: Search query for NSLSL
            
        Returns:
            Dictionary with change information
        """
        logger.info("Checking for NSLSL changes...")
        
        # Get last check timestamp
        last_check = self.state.get('nslsl', {}).get('last_check', '1970-01-01T00:00:00')
        
        try:
            harvester = NSLSLHarvester()
            
            # Fetch current publications
            current_publications = harvester.harvest_publications(query, max_records=100)
            
            # Generate hash of current publications
            current_hash = self._generate_content_hash(current_publications)
            
            # Get previous hash
            previous_hash = self.state.get('nslsl', {}).get('content_hash', '')
            
            # Check for changes
            has_changes = current_hash != previous_hash
            new_publications = []
            updated_publications = []
            
            if has_changes:
                logger.info("Detected changes in NSLSL publications")
                
                # Get previous publications if available
                previous_publications = self.state.get('nslsl', {}).get('publications', [])
                previous_pub_dict = {pub.get('nslsl_id'): pub for pub in previous_publications}
                current_pub_dict = {pub.get('nslsl_id'): pub for pub in current_publications}
                
                # Identify new publications
                for pub_id, pub in current_pub_dict.items():
                    if pub_id not in previous_pub_dict:
                        new_publications.append(pub)
                
                # Identify updated publications
                for pub_id, pub in current_pub_dict.items():
                    if pub_id in previous_pub_dict:
                        prev_pub = previous_pub_dict[pub_id]
                        if self._generate_content_hash(pub) != self._generate_content_hash(prev_pub):
                            updated_publications.append(pub)
            
            # Update state
            self.state['nslsl'] = {
                'last_check': datetime.now().isoformat(),
                'content_hash': current_hash,
                'publications': current_publications,
                'changes_detected': has_changes,
                'new_publications_count': len(new_publications),
                'updated_publications_count': len(updated_publications),
                'query': query
            }
            
            self._save_state()
            
            return {
                'has_changes': has_changes,
                'new_publications': new_publications,
                'updated_publications': updated_publications,
                'total_publications': len(current_publications),
                'last_check': last_check
            }
            
        except Exception as e:
            logger.error(f"Error checking NSLSL changes: {e}")
            return {
                'has_changes': False,
                'error': str(e)
            }
    
    def get_ingest_report(self) -> Dict[str, Any]:
        """
        Get a report of the current ingest state
        
        Returns:
            Dictionary with ingest report
        """
        return {
            'osdr': self.state.get('osdr', {}),
            'nslsl': self.state.get('nslsl', {}),
            'generated_at': datetime.now().isoformat()
        }
    
    async def run_incremental_ingest(self, nslsl_query: str = "space biology") -> Dict[str, Any]:
        """
        Run incremental ingest for both OSDR and NSLSL
        
        Args:
            nslsl_query: Search query for NSLSL
            
        Returns:
            Dictionary with ingest results
        """
        logger.info("Starting incremental ingest...")
        
        # Check OSDR changes
        osdr_results = await self.check_osdr_changes()
        
        # Check NSLSL changes
        nslsl_results = self.check_nslsl_changes(nslsl_query)
        
        # Combine results
        results = {
            'osdr': osdr_results,
            'nslsl': nslsl_results,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Incremental ingest completed")
        return results

def main():
    """
    Main function to demonstrate incremental ingest functionality
    """
    manager = IncrementalIngestManager()
    
    async def run_example():
        try:
            # Run incremental ingest
            results = await manager.run_incremental_ingest("space biology")
            
            # Display results
            print("Incremental Ingest Results:")
            print("==========================")
            
            print("\nOSDR Results:")
            osdr_results = results.get('osdr', {})
            print(f"  Has Changes: {osdr_results.get('has_changes', False)}")
            print(f"  New Studies: {len(osdr_results.get('new_studies', []))}")
            print(f"  Updated Studies: {len(osdr_results.get('updated_studies', []))}")
            print(f"  Total Studies: {osdr_results.get('total_studies', 0)}")
            
            print("\nNSLSL Results:")
            nslsl_results = results.get('nslsl', {})
            print(f"  Has Changes: {nslsl_results.get('has_changes', False)}")
            print(f"  New Publications: {len(nslsl_results.get('new_publications', []))}")
            print(f"  Updated Publications: {len(nslsl_results.get('updated_publications', []))}")
            print(f"  Total Publications: {nslsl_results.get('total_publications', 0)}")
            
            # Save report
            report = manager.get_ingest_report()
            with open('ingest_report.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print("\nReport saved to ingest_report.json")
            
        except Exception as e:
            logger.error(f"Error in main: {e}")
    
    # Run example
    asyncio.run(run_example())

if __name__ == "__main__":
    main()