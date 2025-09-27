# 🧠 NASA OSDR Natural Language Analysis

Advanced natural language processing capabilities for analyzing NASA Open Science Data Repository (OSDR) experiment metadata, protocols, and literature using state-of-the-art LLMs and traditional NLP techniques.

## 🌟 Overview

This module provides comprehensive natural language analysis for NASA space biology research, including:

- **📋 Experiment Metadata Analysis**: Extract and structure experiment protocols and metadata
- **📚 Literature Summarization**: AI-powered analysis and summarization of scientific papers  
- **🔗 Cross-Reference Detection**: Automatic discovery of related studies using semantic similarity
- **💡 Research Hypothesis Generation**: Generate novel, testable hypotheses based on existing literature
- **🧠 Complex Result Interpretation**: Translate complex results into plain language for different audiences

## 🚀 Key Features

### 1. Experiment Metadata Analysis
- **Protocol Type Identification**: Automatically classify experimental protocols
- **Organism Extraction**: Identify studied organisms and model systems
- **Methodology Detection**: Extract experimental methodologies and techniques
- **Objective Extraction**: Parse research objectives and aims
- **Safety Considerations**: Identify safety protocols and considerations

### 2. Literature Analysis
- **AI-Powered Summarization**: Generate concise summaries using local transformer models
- **Key Findings Extraction**: Identify main research findings and conclusions
- **Methodology Analysis**: Extract experimental approaches and techniques
- **Research Gap Identification**: Discover underexplored research areas
- **Future Directions**: Identify suggested future research directions

### 3. Cross-Reference Detection
- **Semantic Similarity**: Calculate similarity between documents using TF-IDF and cosine similarity
- **Common Theme Extraction**: Identify shared research themes and concepts
- **Relationship Classification**: Categorize relationships between studies
- **AI Explanations**: Generate natural language explanations of document relationships

### 4. Research Hypothesis Generation
- **Context-Aware Generation**: Create hypotheses based on current literature
- **Research Area Specialization**: Generate area-specific hypotheses
- **Novelty Scoring**: Rank hypotheses by novelty and feasibility
- **Space Mission Relevance**: Assess relevance to space exploration goals

### 5. Complex Result Interpretation
- **Multi-Audience Support**: Generate interpretations for different audiences:
  - **Scientific**: Technical interpretation for researchers
  - **General Public**: Accessible explanations for general audience
  - **Mission Planning**: Practical implications for space missions
  - **Clinical**: Medical and health implications
- **Plain Language Translation**: Convert technical jargon to accessible language
- **Context Provision**: Explain significance and broader implications

## 🛠️ Installation

### Prerequisites
```bash
# Python dependencies
pip install spacy nltk scikit-learn pandas numpy aiohttp

# Download required NLP models  
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt stopwords
```

### Environment Setup
```bash
# No external API keys required - all models run locally
# Optional: Set custom Python path
export PYTHON_PATH="/usr/bin/python3"
```

## 📖 Usage

### Command Line Interface

```bash
# Run complete analysis demo
python nlp_demo.py

# Use sample data for testing
python nlp_demo.py --mode demo

# Save results to file
python nlp_demo.py --save-results

# Show usage examples
python nlp_demo.py --mode examples
```

### Python API

```python
import asyncio
from nlp_analyzer import analyze_nasa_documents, NaturalLanguageAnalyzer

# Complete analysis
async def main():
    # Load NASA OSDR documents
    with open('data/processed_publications.json', 'r') as f:
        documents = json.load(f)
    
    # Run comprehensive NLP analysis
    results = await analyze_nasa_documents(documents)
    
    print(f"Analyzed {results['analysis_summary']['total_documents']} documents")
    print(f"Generated {results['analysis_summary']['hypotheses_generated']} hypotheses")
    print(f"Found {results['analysis_summary']['cross_references_found']} cross-references")

# Example usage without API key
asyncio.run(main())
```

### Individual Component Usage

```
async def analyze_components():
    async with NaturalLanguageAnalyzer() as analyzer:
        
        # 1. Analyze experiment metadata
        metadata = await analyzer.analyze_experiment_metadata(experiment_doc)
        print(f"Protocol Type: {metadata.protocol_type}")
        print(f"Organisms: {metadata.organisms}")
        print(f"Methodologies: {metadata.methodologies}")
        
        # 2. Literature analysis
        literature = await analyzer.analyze_literature(paper_doc)
        print(f"Summary: {literature.summary}")
        print(f"Key Findings: {literature.key_findings}")
        print(f"Research Gaps: {literature.research_gaps}")
        
        # 3. Cross-reference studies
        cross_refs = await analyzer.cross_reference_studies(documents)
        for ref in cross_refs[:5]:
            print(f"Related: {ref.query_doc} ↔ {ref.related_doc}")
            print(f"Similarity: {ref.similarity_score:.3f}")
            print(f"Explanation: {ref.relevance_explanation}")
        
        # 4. Generate hypotheses
        hypotheses = await analyzer.generate_research_hypotheses(
            documents, research_area="Human Physiology"
        )
        for hyp in hypotheses['hypotheses']:
            if isinstance(hyp, dict):
                print(f"Hypothesis: {hyp['hypothesis']}")
                print(f"Score: {hyp['overall_score']:.2f}")
            else:
                print(f"Hypothesis: {hyp}")
        
        # 5. Interpret complex results
        results_data = {
            "gene_expression_changes": 1247,
            "p_value": 0.001,
            "effect_size": "large"
        }
        interpretations = await analyzer.interpret_complex_results(results_data)
        
        print("Scientific Interpretation:")
        print(interpretations['scientific'])
        
        print("General Public Interpretation:")
        print(interpretations['general'])
```

### REST API Integration

```
// Complete NLP analysis
const response = await fetch('/api/nlp/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    documents: nasaDocuments,
    options: { research_area: 'Human Physiology' }
  })
});

const results = await response.json();
console.log(`Analyzed ${results.data.analysis_summary.total_documents} documents`);

// Cross-reference analysis
const crossRefResponse = await fetch('/api/nlp/cross-reference', {
  method: 'POST', 
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    documents: nasaDocuments,
    similarity_threshold: 0.3
  })
});

const crossRefs = await crossRefResponse.json();
console.log(`Found ${crossRefs.data.length} cross-references`);

// Generate research hypotheses
const hypothesesResponse = await fetch('/api/nlp/hypotheses', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    documents: nasaDocuments,
    research_area: 'Plant Biology'
  })
});

const hypotheses = await hypothesesResponse.json();
console.log(`Generated ${hypotheses.data.hypotheses.length} hypotheses`);
```

## 🔧 Configuration

### Environment Variables

```bash
# No external API keys required - all models run locally
# Optional configurations  
PYTHON_PATH=/usr/bin/python3
NLP_TIMEOUT=300000  # 5 minutes
MAX_DOCUMENTS=50    # Limit for analysis
SIMILARITY_THRESHOLD=0.3
```

### Analysis Options

```python
analysis_options = {
    'research_area': 'Human Physiology',  # Filter by research area
    'similarity_threshold': 0.3,          # Cross-reference threshold
    'max_hypotheses': 5,                  # Limit hypothesis generation
    'audience': ['scientific', 'general'], # Interpretation audiences
    'include_metadata': True,             # Include metadata analysis
    'include_literature': True,           # Include literature analysis
    'include_cross_refs': True,           # Include cross-references
    'include_hypotheses': True            # Include hypothesis generation
}
```

## 📊 Output Formats

### Experiment Metadata
```python
{
    "experiment_id": "GLDS-001",
    "title": "Transcriptomic Analysis of Mouse Liver in Microgravity", 
    "protocol_type": "Cell Culture",
    "organisms": ["Mus musculus"],
    "conditions": {"temperature": "37°C", "duration": "21 days"},
    "objectives": ["Understand metabolic adaptations in space"],
    "methodologies": ["RNA-seq", "PCR"],
    "expected_outcomes": ["Gene expression changes"],
    "safety_considerations": ["Biosafety protocols"]
}
```

### Literature Analysis
```python
{
    "document_id": "GLDS-001",
    "summary": "AI-generated summary of key findings...",
    "key_findings": ["Finding 1", "Finding 2"],
    "methodology": "RNA-seq analysis of mouse liver tissue",
    "significance": "Important for understanding space biology",
    "research_gaps": ["Gap 1", "Gap 2"], 
    "future_directions": ["Direction 1", "Direction 2"],
    "related_studies": ["Study 1", "Study 2"]
}
```

### Cross-References
```python
{
    "query_doc": "GLDS-001",
    "related_doc": "GLDS-002", 
    "similarity_score": 0.75,
    "common_themes": ["microgravity", "gene expression"],
    "relationship_type": "Highly Related",
    "relevance_explanation": "Both studies examine gene expression..."
}
```

### Research Hypotheses
```python
{
    "hypotheses": [
        {
            "hypothesis": "Microgravity exposure induces novel adaptive responses...",
            "novelty_score": 0.8,
            "feasibility_score": 0.7,
            "space_relevance": 0.9,
            "overall_score": 0.8,
            "rank": 1
        }
    ],
    "research_context": "Based on analysis of NASA OSDR data...",
    "confidence_score": 0.7
}
```

## 🎯 Use Cases

### 1. Research Planning
- **Gap Analysis**: Identify underexplored research areas
- **Hypothesis Generation**: Create testable hypotheses for future studies
- **Literature Review**: Automated analysis of existing research
- **Cross-Study Connections**: Discover relationships between studies

### 2. Mission Planning  
- **Risk Assessment**: Extract safety and health implications
- **Technology Requirements**: Identify needed technologies
- **Resource Planning**: Understand experimental requirements
- **Countermeasure Development**: Inform protective measure design

### 3. Public Communication
- **Science Communication**: Translate complex findings for public
- **Educational Content**: Create accessible explanations
- **Policy Briefings**: Summarize implications for decision makers
- **Media Relations**: Generate clear, accurate science summaries

### 4. Research Collaboration
- **Study Matching**: Connect researchers with similar interests
- **Methodology Sharing**: Identify similar experimental approaches
- **Data Integration**: Find complementary datasets
- **Knowledge Transfer**: Facilitate cross-disciplinary insights

## 🔍 Examples

### Example 1: Bone Loss Research Analysis

```python
# Analyze bone loss studies
bone_studies = [doc for doc in documents if 'bone' in doc['title'].lower()]

async with NaturalLanguageAnalyzer(api_key) as analyzer:
    # Generate hypotheses specific to bone research
    hypotheses = await analyzer.generate_research_hypotheses(
        bone_studies, research_area="Musculoskeletal"
    )
    
    # Example output:
    # "Artificial gravity systems could prevent bone density loss 
    #  more effectively than current exercise countermeasures"
```

### Example 2: Plant Biology Cross-References

```python
# Find related plant biology studies
plant_studies = [doc for doc in documents if 'plant' in doc['research_area'].lower()]

cross_refs = await analyzer.cross_reference_studies(plant_studies)

# Example output:
# Document GLDS-002 relates to GLDS-005 through common themes:
# ["plant growth", "microgravity", "adaptation"]
# Explanation: "Both studies examine plant adaptation to space environments..."
```

### Example 3: Mission Planning Interpretation

```python
# Interpret radiation study results for mission planning
radiation_results = {
    "dna_damage_increase": "300%",
    "repair_efficiency_decrease": "45%", 
    "cancer_risk_elevation": "significant"
}

interpretations = await analyzer.interpret_complex_results(radiation_results)

mission_implications = interpretations['mission_planning']
# "These findings indicate increased cancer risk for Mars missions.
#  Recommend enhanced radiation shielding and crew rotation protocols."
```

## 🚨 Error Handling

The system includes comprehensive error handling:

```python
try:
    results = await analyze_nasa_documents(documents, api_key)
except Exception as e:
    if "API key" in str(e):
        # Fall back to heuristic methods
        results = await analyze_nasa_documents(documents, api_key=None)
    elif "timeout" in str(e):
        # Reduce document set and retry
        results = await analyze_nasa_documents(documents[:10], api_key)
    else:
        logger.error(f"Analysis failed: {e}")
        raise
```

## 🔄 Integration with Existing Pipeline

The NLP analyzer integrates seamlessly with the existing data pipeline:

```python
from data_analyzer import NASADataAnalyzer
from nlp_analyzer import analyze_nasa_documents

# Run statistical analysis
stats_analyzer = NASADataAnalyzer()
stats_results = stats_analyzer.run_complete_analysis()

# Convert to format suitable for NLP analysis
documents = stats_analyzer.df.to_dict('records')

# Run NLP analysis
nlp_results = await analyze_nasa_documents(documents)

# Combine results
combined_insights = {
    'statistical_analysis': stats_results,
    'nlp_analysis': nlp_results,
    'combined_summary': generate_combined_summary(stats_results, nlp_results)
}
```

## 📈 Performance Considerations

- **Document Limits**: Processes up to 50 documents per request for optimal performance
- **Caching**: Results are cached to avoid redundant processing
- **Timeouts**: 5-minute timeout for long-running analyses
- **Memory Management**: Efficient processing of large document collections

## 🛡️ Security & Privacy

- **Data Privacy**: No document content is stored permanently
- **Access Control**: API endpoints include proper authentication
- **Audit Logging**: All analysis requests are logged for security

## 📚 Related Documentation

- [Main README](../README.md) - Project overview
- [Data Pipeline Guide](../data-pipeline/README.md) - Data processing pipeline  
- [API Documentation](../backend/README.md) - Backend API reference
- [Developer Guide](../DEVELOPER_GUIDE.md) - Development setup and guidelines

## 🤝 Contributing

See the main [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) for information on contributing to the NLP analysis capabilities.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

🚀 **Ready to unlock the power of NASA's space biology research with advanced natural language processing!**