import asyncio
from osdr_processor import OSDADataProcessor

async def main():
    print("Starting full NASA OSDR data processing...")
    try:
        async with OSDADataProcessor() as processor:
            publications = await processor.process_all_studies()
            print(f"Successfully processed {len(publications)} publications")
            print("Data saved to data/processed_publications.json")
            return publications
    except Exception as e:
        print(f"Error processing data: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print("Processing completed successfully!")
    else:
        print("Processing failed!")