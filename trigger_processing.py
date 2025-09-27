import asyncio
import sys
import os

# Add the data-pipeline directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'data-pipeline'))

from osdr_processor import OSDADataProcessor

async def main():
    """Trigger data processing to fetch real NASA OSDR data"""
    print("Starting NASA OSDR data processing...")
    
    try:
        # Initialize processor
        # No external API keys required - using local AI models
        
        async with OSDADataProcessor() as processor:
            print("Fetching real NASA OSDR data from S3 repository...")
            publications = await processor.process_all_studies()
            
            print(f"Successfully processed {len(publications)} NASA OSDR publications")
            print("Data saved to data/processed_publications.json")
            
    except Exception as e:
        print(f"Error processing NASA OSDR data: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)