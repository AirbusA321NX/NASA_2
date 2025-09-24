import asyncio
import sys
import os
import json

# Change to the data-pipeline directory
os.chdir(os.path.join(os.path.dirname(__file__), 'data-pipeline'))

# Now import the processor
from osdr_processor import OSDADataProcessor

async def fetch_and_process_data():
    print("Starting to fetch NASA OSDR data...")
    try:
        # Initialize processor
        async with OSDADataProcessor() as processor:
            print("Fetching catalog from NASA OSDR...")
            publications = await processor.process_all_studies()
            print(f"Successfully processed {len(publications)} publications")
            return publications
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    publications = asyncio.run(fetch_and_process_data())
    if publications:
        print("Data fetching completed successfully!")
        # Save a small sample to verify
        sample_data = publications[:3]  # First 3 publications
        with open('sample_real_data.json', 'w') as f:
            json.dump(sample_data, f, indent=2, default=str)
        print("Sample data saved to sample_data.json")
    else:
        print("Failed to fetch real data")

if __name__ == "__main__":
    main()