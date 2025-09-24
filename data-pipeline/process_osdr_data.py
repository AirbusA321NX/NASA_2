#!/usr/bin/env python3
"""
Script to process OSDR data and save to cache file
"""

import asyncio
import logging
import json
import os
from osdr_processor import OSDADataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_osdr_data():
    """Process OSDR data and save to cache file"""
    logger.info("Starting OSDR data processing...")
    
    try:
        # Initialize processor
        async with OSDADataProcessor() as processor:
            logger.info("Processor initialized")
            
            # Process all studies
            publications = await processor.process_all_studies()
            
            logger.info(f"Successfully processed {len(publications)} publications")
            
            # Save to a more accessible location for testing
            output_path = "data/processed_publications.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Convert to JSON-serializable format
            publications_data = []
            for pub in publications:
                pub_dict = {
                    'title': pub.title,
                    'authors': pub.authors,
                    'abstract': pub.abstract,
                    'publication_date': pub.publication_date.isoformat(),
                    'doi': pub.doi,
                    'osdr_id': pub.osdr_id,
                    'keywords': pub.keywords,
                    'research_area': pub.research_area,
                    'study_type': pub.study_type,
                    'organisms': pub.organisms,
                    'file_urls': pub.file_urls,
                    'metadata': pub.metadata
                }
                publications_data.append(pub_dict)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(publications_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {output_path}")
            
            # Show some statistics
            if publications_data:
                total_pubs = len(publications_data)
                unique_organisms = set()
                research_areas = {}
                
                for pub in publications_data:
                    unique_organisms.update(pub.get('organisms', []))
                    area = pub.get('research_area', 'Unknown')
                    research_areas[area] = research_areas.get(area, 0) + 1
                
                print(f"\n=== Processing Summary ===")
                print(f"Total Publications: {total_pubs}")
                print(f"Unique Organisms: {len(unique_organisms)}")
                print(f"Research Areas: {len(research_areas)}")
                print(f"\nTop Research Areas:")
                for area, count in sorted(research_areas.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {area}: {count}")
                    
    except Exception as e:
        logger.error(f"Error processing OSDR data: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    asyncio.run(process_osdr_data())