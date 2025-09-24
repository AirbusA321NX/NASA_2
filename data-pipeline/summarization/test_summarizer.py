import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from summarization.summarizer import RetrievalAugmentedSummarizer

async def test_summarizer():
    """Test the retrieval-augmented summarizer"""
    
    # Database configuration (using example values)
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'user': 'postgres',
        'password': 'password',
        'database': 'nasa_space_biology'
    }
    
    # Test with summarizer
    async with RetrievalAugmentedSummarizer(db_config, log_directory="../logs") as summarizer:
        # Test query
        query = "What are the effects of microgravity on plant physiology?"
        
        print(f"Testing summarization for query: {query}")
        print("=" * 50)
        
        try:
            # Generate summary
            summary = await summarizer.summarize_query(query, top_k=5, max_evidence=3)
            
            # Display results
            print(f"Insight: {summary.insight}")
            print("\nEvidence Bullets:")
            for i, bullet in enumerate(summary.evidence_bullets, 1):
                print(f"  {i}. {bullet}")
            print("\nResearch Gaps:")
            for i, gap in enumerate(summary.research_gaps, 1):
                print(f"  {i}. {gap}")
            
            print(f"\nModel Fingerprint: {summary.model_fingerprint}")
            print(f"Timestamp: {summary.timestamp}")
            
            # Save audit
            audit_file = f"test_summary_audit.json"
            summarizer.save_summary_audit(summary, audit_file)
            print(f"\nAudit saved to: {audit_file}")
            
            # Show audit log location
            print(f"Audit log: {summarizer.audit_logger.get_audit_log_path()}")
            
        except Exception as e:
            print(f"Error during summarization: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_summarizer())