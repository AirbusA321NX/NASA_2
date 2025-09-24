import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

# Local imports
from vector_store.vector_storage import VectorStorage
from embedding.embedding_generator import EmbeddingGenerator
from database.chunk_storage import ChunkStorage
from kg_extraction.ner_extractor import NERExtractor
from kg_extraction.vocabulary_normalizer import VocabularyNormalizer
from summarization.audit_logger import AuditLogger  # Added import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EvidenceSnippet:
    """Data class for evidence snippets"""
    paper_id: str
    section_type: str
    content: str
    score: float
    chunk_id: str
    position: int  # Position in ranking

@dataclass
class SummaryOutput:
    """Data class for summary output"""
    insight: str
    evidence_bullets: List[str]
    research_gaps: List[str]
    evidence_snippets: List[EvidenceSnippet]
    query: str
    timestamp: str
    model_fingerprint: str

class RetrievalAugmentedSummarizer:
    """
    Retrieval-augmented summarization loop with local LLM or template generator
    """
    
    def __init__(self, 
                 db_config: Dict[str, str],
                 vector_store_path: str = "vector_index.faiss",
                 log_directory: str = "logs"):  # Added log_directory parameter
        self.db_config = db_config
        self.vector_store_path = vector_store_path
        
        # Initialize components
        self.vector_storage = VectorStorage(index_path=vector_store_path)
        self.embedding_generator = EmbeddingGenerator()
        self.chunk_storage = None  # Will initialize in context manager
        self.ner_extractor = NERExtractor()
        self.vocabulary_normalizer = VocabularyNormalizer()
        self.audit_logger = AuditLogger(log_directory)  # Initialize audit logger
        
        # Section weights for evidence ranking (Results > Conclusions > Methods)
        self.section_weights = {
            'results': 1.0,
            'conclusions': 0.9,
            'methods': 0.7,
            'introduction': 0.5,
            'abstract': 0.6,
            'discussion': 0.8,
            'unknown': 0.5
        }
        
        # Initialize models
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize required models"""
        try:
            self.vector_storage.initialize_index()
            self.embedding_generator.initialize_model()
            
            # Log model initialization
            self.audit_logger.log_model({
                "model_name": "all-mpnet-base-v2",
                "component": "embedding_generator",
                "version": "1.0",
                "fingerprint": self._generate_model_fingerprint()
            })
            
            logger.info("Models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    async def __aenter__(self):
        """Async context manager entry"""
        self.chunk_storage = ChunkStorage(self.db_config)
        await self.chunk_storage.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.chunk_storage:
            await self.chunk_storage.__aexit__(exc_type, exc_val, exc_tb)

    async def retrieve_relevant_chunks(self, 
                                     query: str, 
                                     top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks using vector search
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with scores
        """
        try:
            # Log the prompt
            self.audit_logger.log_prompt(
                prompt=query,
                prompt_type="retrieval",
                metadata={"top_k": top_k}
            )
            
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Search vector store
            results = self.vector_storage.search_vectors(query_embedding, k=top_k)
            
            # Enrich with chunk content
            enriched_results = []
            for result in results:
                chunk_id = result.get('section_id')
                if chunk_id:
                    chunk = await self.chunk_storage.get_chunk_by_id(chunk_id)
                    if chunk:
                        # Combine vector store metadata with chunk content
                        enriched_result = {**result, **chunk}
                        enriched_results.append(enriched_result)
            
            logger.info(f"Retrieved {len(enriched_results)} relevant chunks")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []

    def rank_evidence(self, 
                     chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank evidence by section weight and similarity score
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            List of ranked chunks
        """
        try:
            # Apply section weights to scores
            weighted_chunks = []
            for chunk in chunks:
                section_type = chunk.get('section_type', 'unknown').lower()
                base_score = chunk.get('score', 0.0)
                weight = self.section_weights.get(section_type, 0.5)
                weighted_score = base_score * weight
                
                ranked_chunk = {**chunk, 'weighted_score': weighted_score}
                weighted_chunks.append(ranked_chunk)
            
            # Sort by weighted score
            ranked_chunks = sorted(weighted_chunks, 
                                 key=lambda x: x['weighted_score'], 
                                 reverse=True)
            
            logger.info(f"Ranked {len(ranked_chunks)} chunks by evidence weight")
            return ranked_chunks
            
        except Exception as e:
            logger.error(f"Error ranking evidence: {e}")
            return chunks

    def generate_factual_compression(self, 
                                   query: str,
                                   ranked_chunks: List[Dict[str, Any]],
                                   max_evidence: int = 5) -> SummaryOutput:
        """
        Generate factual compression with insight, bullets, and research gaps
        
        Args:
            query: User query
            ranked_chunks: Ranked evidence chunks
            max_evidence: Maximum number of evidence bullets
            
        Returns:
            SummaryOutput with insight, bullets, and research gaps
        """
        try:
            # Extract top evidence snippets
            top_chunks = ranked_chunks[:max_evidence]
            evidence_snippets = []
            
            for i, chunk in enumerate(top_chunks):
                snippet = EvidenceSnippet(
                    paper_id=chunk.get('paper_id', ''),
                    section_type=chunk.get('section_type', ''),
                    content=chunk.get('content', '')[:300] + '...' if len(chunk.get('content', '')) > 300 else chunk.get('content', ''),
                    score=chunk.get('weighted_score', 0.0),
                    chunk_id=chunk.get('section_id', ''),
                    position=i+1
                )
                evidence_snippets.append(snippet)
            
            # Generate one-line insight (simplified template-based approach)
            insight = self._generate_insight(query, top_chunks)
            
            # Generate evidence-backed bullets
            evidence_bullets = self._generate_evidence_bullets(top_chunks)
            
            # Infer research gaps
            research_gaps = self._infer_research_gaps(query, top_chunks)
            
            # Create model fingerprint
            model_fingerprint = self._generate_model_fingerprint()
            
            summary = SummaryOutput(
                insight=insight,
                evidence_bullets=evidence_bullets,
                research_gaps=research_gaps,
                evidence_snippets=evidence_snippets,
                query=query,
                timestamp=datetime.now().isoformat(),
                model_fingerprint=model_fingerprint
            )
            
            # Log the summary output
            self.audit_logger.log_summary(
                summary_output=asdict(summary),
                metadata={"component": "factual_compression"}
            )
            
            logger.info("Generated factual compression successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating factual compression: {e}")
            # Return fallback summary
            fallback_summary = SummaryOutput(
                insight=f"Findings related to: {query}",
                evidence_bullets=[f"Relevant research on '{query}' was identified in the literature."],
                research_gaps=["Further investigation is needed to understand the full scope of this topic."],
                evidence_snippets=[],
                query=query,
                timestamp=datetime.now().isoformat(),
                model_fingerprint=self._generate_model_fingerprint()
            )
            
            # Log the fallback summary
            self.audit_logger.log_summary(
                summary_output=asdict(fallback_summary),
                metadata={"component": "factual_compression", "fallback": True}
            )
            
            return fallback_summary

    def _generate_insight(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Generate one-line insight from evidence (template-based approach)
        
        Args:
            query: User query
            chunks: Evidence chunks
            
        Returns:
            One-line insight
        """
        # Simple template-based approach for now
        # In a production system, this would use an LLM
        if not chunks:
            return f"Research on '{query}' shows potential areas for investigation."
        
        # Extract key entities from chunks
        all_content = ' '.join([chunk.get('content', '') for chunk in chunks[:3]])
        entities = self.ner_extractor.extract_entities(all_content)
        
        if entities:
            entity_names = list(set([e.entity_name for e in entities[:3]]))
            return f"Research on '{query}' indicates connections between {', '.join(entity_names[:2])}."
        else:
            return f"Research on '{query}' reveals important findings in space biology."
    
    def _generate_evidence_bullets(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Generate evidence-backed bullets
        
        Args:
            chunks: Evidence chunks
            
        Returns:
            List of evidence bullets
        """
        bullets = []
        for i, chunk in enumerate(chunks[:5]):  # Limit to 5 bullets
            paper_id = chunk.get('paper_id', 'N/A')
            section_type = chunk.get('section_type', 'N/A')
            content_preview = chunk.get('content', '')[:100] + '...' if len(chunk.get('content', '')) > 100 else chunk.get('content', '')
            
            bullet = f"[{i+1}] {content_preview} (Source: {paper_id}, Section: {section_type})"
            bullets.append(bullet)
            
        return bullets if bullets else ["Evidence from multiple studies supports these findings."]
    
    def _infer_research_gaps(self, query: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Infer research gaps from evidence
        
        Args:
            query: User query
            chunks: Evidence chunks
            
        Returns:
            List of research gaps
        """
        # Simple heuristic-based approach
        gaps = [
            f"Further research is needed on the long-term effects of '{query}'.",
            "The mechanisms underlying these observations require deeper investigation.",
            "Controlled experiments are needed to validate these preliminary findings."
        ]
        return gaps

    def _generate_model_fingerprint(self) -> str:
        """
        Generate model fingerprint for audit purposes
        
        Returns:
            Model fingerprint string
        """
        # In a real implementation, this would include actual model details
        fingerprint_data = {
            'embedding_model': 'all-mpnet-base-v2',
            'summarization_approach': 'template-based',
            'version': '1.0',
            'timestamp': datetime.now().isoformat()
        }
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    async def summarize_query(self, 
                            query: str,
                            top_k: int = 20,
                            max_evidence: int = 5) -> SummaryOutput:
        """
        Main summarization pipeline: retrieve -> rank -> compress
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            max_evidence: Maximum number of evidence bullets
            
        Returns:
            SummaryOutput with complete summary
        """
        try:
            # Log the incoming query
            self.audit_logger.log_prompt(
                prompt=query,
                prompt_type="summarization_pipeline",
                metadata={"top_k": top_k, "max_evidence": max_evidence}
            )
            
            # Step 1: Retrieve relevant chunks
            logger.info(f"Retrieving chunks for query: {query}")
            chunks = await self.retrieve_relevant_chunks(query, top_k)
            
            # Step 2: Rank evidence
            logger.info("Ranking evidence by section weight")
            ranked_chunks = self.rank_evidence(chunks)
            
            # Log evidence snippets
            evidence_for_audit = []
            for i, chunk in enumerate(ranked_chunks[:max_evidence]):
                evidence_for_audit.append({
                    "position": i+1,
                    "paper_id": chunk.get('paper_id', ''),
                    "section_type": chunk.get('section_type', ''),
                    "content_preview": chunk.get('content', '')[:100] + '...' if len(chunk.get('content', '')) > 100 else chunk.get('content', ''),
                    "score": chunk.get('weighted_score', 0.0),
                    "chunk_id": chunk.get('section_id', '')
                })
            
            self.audit_logger.log_evidence(
                evidence_snippets=evidence_for_audit,
                query=query,
                metadata={"total_retrieved": len(chunks), "total_ranked": len(ranked_chunks)}
            )
            
            # Step 3: Generate factual compression
            logger.info("Generating factual compression")
            summary = self.generate_factual_compression(query, ranked_chunks, max_evidence)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in summarization pipeline: {e}")
            raise

    def save_summary_audit(self, 
                          summary: SummaryOutput, 
                          filepath: str):
        """
        Save summary with audit information for traceability
        
        Args:
            summary: Summary output to save
            filepath: Path to save audit file
        """
        try:
            # Convert to dictionary for JSON serialization
            summary_dict = asdict(summary)
            
            # Add audit information
            audit_data = {
                'summary': summary_dict,
                'audit_info': {
                    'generated_at': datetime.now().isoformat(),
                    'component_versions': {
                        'vector_storage': '1.0',
                        'embedding_generator': '1.0',
                        'chunk_storage': '1.0'
                    },
                    'session_id': self.audit_logger.get_session_id()
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(audit_data, f, indent=2)
                
            logger.info(f"Saved summary audit to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving summary audit: {e}")

def main():
    """
    Main function to demonstrate summarizer functionality
    """
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'user': 'postgres',
        'password': 'password',
        'database': 'nasa_space_biology'
    }
    
    # Example usage
    async def run_example():
        async with RetrievalAugmentedSummarizer(db_config) as summarizer:
            # Example query
            query = "How does microgravity affect plant growth?"
            
            print(f"Processing query: {query}")
            
            # Generate summary
            summary = await summarizer.summarize_query(query, top_k=10, max_evidence=3)
            
            # Display results
            print("\n=== SUMMARY ===")
            print(f"Insight: {summary.insight}")
            print("\nEvidence:")
            for bullet in summary.evidence_bullets:
                print(f"  - {bullet}")
            print("\nResearch Gaps:")
            for gap in summary.research_gaps:
                print(f"  - {gap}")
            
            # Save audit
            audit_file = f"summary_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            summarizer.save_summary_audit(summary, audit_file)
            print(f"\nAudit saved to: {audit_file}")
            
            # Show audit log location
            print(f"Audit log: {summarizer.audit_logger.get_audit_log_path()}")
    
    # Run example
    import asyncio
    asyncio.run(run_example())

if __name__ == "__main__":
    main()