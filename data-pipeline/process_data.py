import asyncio
import json
from osdr_processor import OSDADataProcessor

async def main():
    """Process OSDR data with improved research area categorization"""
    try:
        async with OSDADataProcessor() as processor:
            print("Starting NASA OSDR data processing...")
            publications = await processor.process_all_studies()
            
            # Save results
            publications_data = []
            research_areas = {}
            
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
                
                # Count research areas
                area = pub.research_area
                research_areas[area] = research_areas.get(area, 0) + 1
            
            # Save to file
            with open('data/processed_publications.json', 'w', encoding='utf-8') as f:
                json.dump(publications_data, f, indent=2, ensure_ascii=False)
            
            print(f"Successfully processed {len(publications)} NASA OSDR publications")
            print(f"Research Areas Distribution: {research_areas}")
            
            # Show sample publications
            print("\nSample Publications:")
            for i, pub in enumerate(publications[:5]):
                print(f"{i+1}. {pub.title} - {pub.research_area}")
                
    except Exception as e:
        print(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())