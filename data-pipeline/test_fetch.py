import asyncio
from osdr_processor import OSDADataProcessor

async def main():
    print("Testing OSDR data fetching...")
    try:
        async with OSDADataProcessor() as processor:
            studies = await processor.fetch_osdr_catalog()
            print(f"Found {len(studies)} studies")
            if studies:
                print("First study:", studies[0]['accession'] if studies else "None")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())