# NASA Space Biology Knowledge Engine - Summarization Module

This module implements the retrieval-augmented summarization loop for the NASA Space Biology Knowledge Engine. It provides automated summarization capabilities that retrieve relevant scientific evidence and generate concise, factual summaries with proper provenance tracking.

## Components

### 1. RetrievalAugmentedSummarizer
The main summarization engine that orchestrates the entire pipeline:
- **Retrieval**: Uses vector search to find semantically relevant document chunks
- **Ranking**: Weights evidence by section type (Results > Conclusions > Methods)
- **Compression**: Generates factual summaries with insights, evidence bullets, and research gaps

### 2. AuditLogger
Comprehensive audit logging for all system operations:
- Tracks all LLM prompts and queries
- Records model fingerprints and versions
- Logs evidence snippets used in summarization
- Maintains full provenance for traceability

### 3. Evidence Ranking
Intelligent evidence ranking based on section importance:
- Results sections: Highest weight (1.0)
- Conclusions sections: High weight (0.9)
- Discussion sections: Medium-high weight (0.8)
- Methods sections: Medium weight (0.7)
- Abstract sections: Medium weight (0.6)
- Introduction sections: Lower weight (0.5)

## Key Features

### Retrieval-Augmented Summarization
The system follows a three-stage pipeline:
1. **Retrieve**: Semantic search using sentence transformers and FAISS
2. **Rank**: Evidence weighting based on section importance
3. **Compress**: Factual summary generation with:
   - One-line insight
   - 3-5 evidence-backed bullets
   - Suggested research gaps

### Audit & Provenance
Complete audit trail for all operations:
- All prompts and queries logged with timestamps
- Model versions and fingerprints tracked
- Evidence snippets preserved with source links
- Session-based logging for traceability

### Template-Based Generation
Current implementation uses template-based summarization for reliability:
- Entity extraction using SciSpacy
- Research gap inference using heuristic rules
- Evidence bullet generation with proper attribution

## Usage

```python
from summarization.summarizer import RetrievalAugmentedSummarizer

# Database configuration
db_config = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': 'password',
    'database': 'nasa_space_biology'
}

# Generate summary
async with RetrievalAugmentedSummarizer(db_config) as summarizer:
    summary = await summarizer.summarize_query(
        "How does microgravity affect plant growth?",
        top_k=20,
        max_evidence=5
    )
    
    print(f"Insight: {summary.insight}")
    for bullet in summary.evidence_bullets:
        print(f"- {bullet}")
```

## Output Format

The summarizer produces structured output with:

1. **Insight**: One-line summary of key findings
2. **Evidence Bullets**: 3-5 evidence-backed statements with paper/section attribution
3. **Research Gaps**: Suggested areas for future investigation
4. **Metadata**: Query, timestamp, and model fingerprint

## Audit Logging

All operations are logged for compliance and traceability:
- JSONL format for efficient streaming
- Session-based organization
- Exportable audit reports
- Full prompt and evidence tracking

## Integration Points

The summarization module integrates with:
- **Vector Store**: FAISS-based semantic retrieval
- **Embedding Generator**: Sentence transformer models
- **Chunk Storage**: PostgreSQL document sections
- **NER Extractor**: SciSpacy entity extraction
- **Vocabulary Normalizer**: Controlled vocabulary mapping

## Future Enhancements

Planned improvements:
- Integration with local LLMs for more sophisticated summarization
- Advanced research gap detection using knowledge graph analysis
- Multi-document summarization capabilities
- Interactive summarization with user feedback loops