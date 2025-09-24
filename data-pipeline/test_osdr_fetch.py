#!/usr/bin/env python3
"""
Test script to verify we can fetch data from NASA OSDR repository
"""

import asyncio
import logging
from osdr_processor import OSDADataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_osdr_fetch():
    """Test fetching OSDR catalog"""
    logger.info("Testing OSDR catalog fetch...")
    
    try:
        # Initialize processor
        async with OSDADataProcessor() as processor:
            logger.info(f"Processor initialized with base URL: {processor.base_url}")
            
            # Fetch catalog
            logger.info("Fetching OSDR catalog...")
            studies = await processor.fetch_osdr_catalog()
            
            logger.info(f"Found {len(studies)} studies")
            
            if studies:
                logger.info("First few studies:")
                for i, study in enumerate(studies[:3]):
                    logger.info(f"  {i+1}. {study['accession']}: {study['title']}")
                    if 'datafiles' in study:
                        logger.info(f"      Datafiles: {len(study['datafiles'])}")
                        for j, datafile in enumerate(study['datafiles'][:2]):
                            logger.info(f"        {j+1}. {datafile.get('file_url', 'No URL')}")
            else:
                logger.warning("No studies found")
                
    except Exception as e:
        logger.error(f"Error fetching OSDR catalog: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    asyncio.run(test_osdr_fetch())