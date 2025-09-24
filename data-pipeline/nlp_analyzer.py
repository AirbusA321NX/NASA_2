import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, cast
from dataclasses import dataclass
import os
from datetime import datetime
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from collections import Counter
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExperimentMetadata:
    """Data class for experiment metadata analysis"""
    experiment_id: str
    title: str
    protocol_type: str
    organisms: List[str]
    conditions: Dict[str, Any]
    objectives: List[str]
    methodologies: List[str]
    expected_outcomes: List[str]
    safety_considerations: List[str]

@dataclass
class LiteratureAnalysis:
    """Data class for literature analysis results"""
    document_id: str
    summary: str
    key_findings: List[str]
    methodology: str
    significance: str
    research_gaps: List[str]
    future_directions: List[str]
    related_studies: List[str]

@dataclass
class CrossReference:
    """Data class for cross-reference results"""
    query_doc: str
    related_doc: str
    similarity_score: float
    common_themes: List[str]
    relationship_type: str
    relevance_explanation: str

class NaturalLanguageAnalyzer:
    """
    Advanced Natural Language Analysis for NASA OSDR data
    Provides intelligent analysis of experiment metadata, protocols, and literature
    """
    
    def __init__(self, mistral_api_key: Optional[str] = None):
        self.mistral_api_key = mistral_api_key or os.getenv('MISTRAL_API_KEY')
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self.session = None
        
        # Initialize NLP models
        self.nlp = None
        self.tfidf_vectorizer = None
        self.document_vectors = None
        self.documents = []
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
        
        # Space biology specific terms
        self.space_biology_terms = {
            'environments': ['microgravity', 'weightless', 'space', 'orbital', 'ISS', 'mars', 'lunar'],
            'organisms': ['human', 'mouse', 'plant', 'cell', 'tissue', 'organism', 'bacterial', 'fungal'],
            'effects': ['adaptation', 'response', 'growth', 'development', 'expression', 'regulation'],
            'systems': ['cardiovascular', 'musculoskeletal', 'nervous', 'immune', 'reproductive'],
            'methodologies': ['RNA-seq', 'proteomics', 'microscopy', 'PCR', 'western blot', 'ELISA']
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        await self._initialize_nlp_models()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _initialize_nlp_models(self):
        """Initialize NLP models and components"""
        try:
            # Load spaCy model for advanced NLP
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found. Please install: python -m spacy download en_core_web_sm")
            self.nlp = None

    async def analyze_experiment_metadata(self, experiment_data: Dict[str, Any]) -> ExperimentMetadata:
        """
        Analyze and structure experiment metadata using NLP and AI
        """
        try:
            # Extract basic information
            exp_id = experiment_data.get('accession', 'Unknown')
            title = experiment_data.get('title', '')
            description = experiment_data.get('description', '')
            
            # Combine text for analysis
            full_text = f"{title}\n\n{description}"
            
            # Extract organisms
            organisms = []
            if 'organism' in experiment_data:
                organisms = [org.get('scientificName', '') for org in experiment_data['organism']]
            
            # Use AI to extract structured information
            protocol_analysis = await self._analyze_protocol_with_ai(full_text)
            
            # Extract methodologies using NLP
            methodologies = self._extract_methodologies(full_text)
            
            # Extract objectives and outcomes
            objectives = self._extract_objectives(full_text)
            expected_outcomes = self._extract_expected_outcomes(full_text)
            
            # Safety considerations
            safety_considerations = self._extract_safety_considerations(full_text)
            
            return ExperimentMetadata(
                experiment_id=exp_id,
                title=title,
                protocol_type=protocol_analysis.get('protocol_type', 'Unknown'),
                organisms=organisms,
                conditions=protocol_analysis.get('conditions', {}),
                objectives=objectives,
                methodologies=methodologies,
                expected_outcomes=expected_outcomes,
                safety_considerations=safety_considerations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing experiment metadata: {e}")
            return ExperimentMetadata(
                experiment_id=experiment_data.get('accession', 'Unknown'),
                title=experiment_data.get('title', ''),
                protocol_type='Unknown',
                organisms=[],
                conditions={},
                objectives=[],
                methodologies=[],
                expected_outcomes=[],
                safety_considerations=[]
            )

    async def analyze_literature(self, document: Dict[str, Any]) -> LiteratureAnalysis:
        """
        Comprehensive literature analysis using AI and NLP
        """
        try:
            doc_id = document.get('osdr_id', document.get('doi', 'Unknown'))
            title = document.get('title', '')
            abstract = document.get('abstract', '')
            full_text = f"{title}\n\n{abstract}"
            
            # AI-powered analysis
            ai_analysis = await self._analyze_literature_with_ai(full_text)
            
            # Extract key findings using NLP
            key_findings = self._extract_key_findings(full_text)
            
            # Identify methodology
            methodology = self._extract_methodology(full_text)
            
            # Research gaps analysis
            research_gaps = await self._identify_research_gaps(full_text)
            
            # Future directions
            future_directions = self._extract_future_directions(full_text)
            
            return LiteratureAnalysis(
                document_id=doc_id,
                summary=ai_analysis.get('summary', ''),
                key_findings=key_findings,
                methodology=methodology,
                significance=ai_analysis.get('significance', ''),
                research_gaps=research_gaps,
                future_directions=future_directions,
                related_studies=[]  # Will be populated by cross-reference analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing literature: {e}")
            return LiteratureAnalysis(
                document_id=document.get('osdr_id', 'Unknown'),
                summary='Analysis failed',
                key_findings=[],
                methodology='Unknown',
                significance='',
                research_gaps=[],
                future_directions=[],
                related_studies=[]
            )

    async def cross_reference_studies(self, documents: List[Dict[str, Any]], 
                                    similarity_threshold: float = 0.3) -> List[CrossReference]:
        """
        Automatically search and cross-reference studies using semantic similarity
        """
        try:
            # Prepare documents for vectorization
            doc_texts = []
            doc_ids = []
            
            for doc in documents:
                text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
                doc_texts.append(text)
                doc_ids.append(doc.get('osdr_id', doc.get('doi', 'Unknown')))
            
            # Create TF-IDF vectors
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            cross_references = []
            
            # Find similar documents
            for i in range(len(documents)):
                for j in range(i + 1, len(documents)):
                    similarity_score = similarity_matrix[i][j]
                    
                    if similarity_score >= similarity_threshold:
                        # Extract common themes
                        common_themes = self._extract_common_themes(
                            doc_texts[i], doc_texts[j]
                        )
                        
                        # Determine relationship type
                        relationship_type = self._determine_relationship_type(
                            documents[i], documents[j], similarity_score
                        )
                        
                        # Generate AI explanation
                        relevance_explanation = await self._explain_relationship(
                            documents[i], documents[j], common_themes
                        )
                        
                        cross_ref = CrossReference(
                            query_doc=doc_ids[i],
                            related_doc=doc_ids[j],
                            similarity_score=similarity_score,
                            common_themes=common_themes,
                            relationship_type=relationship_type,
                            relevance_explanation=relevance_explanation
                        )
                        
                        cross_references.append(cross_ref)
            
            # Sort by similarity score
            cross_references.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return cross_references
            
        except Exception as e:
            logger.error(f"Error in cross-reference analysis: {e}")
            return []

    async def generate_research_hypotheses(self, context_documents: List[Dict[str, Any]], 
                                         research_area: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate novel research hypotheses based on literature analysis
        """
        try:
            # Prepare context from documents
            context_text = self._prepare_research_context(context_documents, research_area)
            
            # Extract current findings
            current_findings = self._extract_current_findings(context_documents)
            
            # Generate hypotheses using AI
            hypotheses_result = await self._generate_hypotheses_with_ai(
                context_text, current_findings, research_area
            )
            
            # Rank hypotheses by novelty and feasibility
            ranked_hypotheses = self._rank_hypotheses(hypotheses_result.get('hypotheses', []))
            
            return {
                'hypotheses': ranked_hypotheses,
                'research_context': context_text,
                'current_findings': current_findings,
                'research_area': research_area,
                'confidence_score': hypotheses_result.get('confidence', 0.6),
                'generation_method': 'AI-assisted with literature analysis'
            }
            
        except Exception as e:
            logger.error(f"Error generating research hypotheses: {e}")
            return {
                'hypotheses': [],
                'research_context': '',
                'current_findings': [],
                'research_area': research_area,
                'confidence_score': 0.0,
                'generation_method': 'Error in generation'
            }

    async def interpret_complex_results(self, results_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Interpret complex research results in plain language
        """
        try:
            # Prepare results summary
            results_text = self._format_results_for_analysis(results_data)
            
            # Generate interpretations for different audiences
            interpretations = {}
            
            # Scientific interpretation
            interpretations['scientific'] = await self._interpret_results_scientific(results_text)
            
            # General audience interpretation
            interpretations['general'] = await self._interpret_results_general(results_text)
            
            # Mission planning interpretation
            interpretations['mission_planning'] = await self._interpret_results_mission(results_text)
            
            # Clinical interpretation (if applicable)
            if self._is_medical_research(results_data):
                interpretations['clinical'] = await self._interpret_results_clinical(results_text)
            
            return interpretations
            
        except Exception as e:
            logger.error(f"Error interpreting complex results: {e}")
            return {
                'scientific': 'Interpretation failed',
                'general': 'Analysis unavailable',
                'mission_planning': 'Unable to assess mission impact'
            }

    # AI-powered analysis methods
    async def _analyze_protocol_with_ai(self, protocol_text: str) -> Dict[str, Any]:
        """Use AI to analyze experimental protocols"""
        if not self.mistral_api_key:
            return {'protocol_type': 'Unknown', 'conditions': {}}
        
        prompt = f"""
        Analyze this experimental protocol and extract structured information:
        
        Protocol: {protocol_text}
        
        Extract:
        1. Protocol type (e.g., cell culture, animal study, plant growth, etc.)
        2. Experimental conditions (temperature, pressure, duration, etc.)
        3. Key variables being tested
        
        Format as JSON:
        """
        
        try:
            response = await self._make_mistral_request(prompt)
            # Parse JSON response or provide defaults
            return self._parse_protocol_response(response)
        except Exception as e:
            logger.error(f"Error in AI protocol analysis: {e}")
            return {'protocol_type': 'Unknown', 'conditions': {}}

    async def _analyze_literature_with_ai(self, literature_text: str) -> Dict[str, Any]:
        """Use AI to analyze literature content"""
        if not self.mistral_api_key:
            return {'summary': 'AI analysis unavailable', 'significance': ''}
        
        prompt = f"""
        As a NASA space biology expert, analyze this research paper:
        
        Text: {literature_text}
        
        Provide:
        1. Concise summary of main findings
        2. Scientific significance for space biology
        3. Implications for space missions
        4. Novel contributions to the field
        
        Keep responses focused and scientific.
        """
        
        try:
            response = await self._make_mistral_request(prompt)
            return self._parse_literature_response(response)
        except Exception as e:
            logger.error(f"Error in AI literature analysis: {e}")
            return {'summary': 'Analysis failed', 'significance': 'Unknown'}

    async def _identify_research_gaps(self, text: str) -> List[str]:
        """Identify research gaps using AI"""
        if not self.mistral_api_key:
            return self._identify_research_gaps_heuristic(text)
        
        prompt = f"""
        Identify potential research gaps and unexplored areas in this space biology research:
        
        Research: {text}
        
        List 3-5 specific research gaps or questions that remain unanswered.
        Focus on areas that could benefit future space missions.
        """
        
        try:
            response = await self._make_mistral_request(prompt)
            return self._parse_research_gaps(response)
        except Exception as e:
            logger.error(f"Error identifying research gaps: {e}")
            return self._identify_research_gaps_heuristic(text)

    async def _generate_hypotheses_with_ai(self, context: str, findings: List[str], 
                                         research_area: Optional[str] = None) -> Dict[str, Any]:
        """Generate research hypotheses using AI"""
        if not self.mistral_api_key:
            return self._generate_hypotheses_heuristic(research_area)
        
        area_context = f" in {research_area}" if research_area else ""
        
        prompt = f"""
        Based on current research findings{area_context}, generate 3-5 novel, testable hypotheses:
        
        Research Context: {context}
        
        Current Findings:
        {chr(10).join(findings)}
        
        Generate hypotheses that:
        1. Build on existing knowledge
        2. Are testable in space environments
        3. Address important gaps
        4. Could impact future missions
        
        Format each hypothesis clearly and explain the rationale.
        """
        
        try:
            response = await self._make_mistral_request(prompt)
            return {
                'hypotheses': self._parse_hypotheses(response),
                'confidence': 0.7
            }
        except Exception as e:
            logger.error(f"Error generating hypotheses: {e}")
            return self._generate_hypotheses_heuristic(research_area)

    async def _make_mistral_request(self, prompt: str) -> str:
        """Make request to Mistral AI API"""
        if not self.mistral_api_key or not self.session:
            raise ValueError("Mistral API not available")
        
        headers = {
            "Authorization": f"Bearer {self.mistral_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with self.session.post(
            f"{self.mistral_base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Mistral API error: {response.status}")

    # NLP-based extraction methods
    def _extract_methodologies(self, text: str) -> List[str]:
        """Extract research methodologies using NLP"""
        methodologies = []
        
        # Common space biology methodologies
        method_patterns = [
            r'RNA[-\s]?seq(?:uencing)?',
            r'PCR|qPCR|RT-PCR', 
            r'western\s+blot',
            r'ELISA',
            r'microscopy|imaging',
            r'proteomics?',
            r'genomics?',
            r'transcriptomics?',
            r'metabolomics?',
            r'flow\s+cytometry',
            r'spectroscopy',
            r'chromatography'
        ]
        
        text_lower = text.lower()
        for pattern in method_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            methodologies.extend(matches)
        
        # Use spaCy for additional entity recognition if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT'] and any(term in ent.text.lower() 
                    for term in ['sequencing', 'analysis', 'assay', 'test']):
                    methodologies.append(ent.text)
        
        return list(set(methodologies))

    def _extract_objectives(self, text: str) -> List[str]:
        """Extract research objectives from text"""
        objectives = []
        
        # Look for objective indicators
        objective_patterns = [
            r'(?:objective|aim|goal|purpose)(?:s)?\s*(?:is|are|was|were)?\s*to\s+([^.]+)',
            r'(?:we|this study)\s+(?:aim|seek|intend)(?:s)?\s+to\s+([^.]+)',
            r'(?:in order to|to)\s+([^,.]+)(?:,|\.|$)'
        ]
        
        for pattern in objective_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            objectives.extend([match.strip() for match in matches])
        
        return objectives[:5]  # Limit to top 5

    def _extract_expected_outcomes(self, text: str) -> List[str]:
        """Extract expected outcomes from text"""
        outcomes = []
        
        outcome_patterns = [
            r'(?:expect|anticipate|predict)(?:s|ed)?\s+(?:that\s+)?([^.]+)',
            r'(?:hypothesis|hypothesize)(?:s|d)?\s+(?:that\s+)?([^.]+)',
            r'(?:should|will|would)\s+(?:result in|lead to|cause)\s+([^.]+)'
        ]
        
        for pattern in outcome_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            outcomes.extend([match.strip() for match in matches])
        
        return outcomes[:5]

    def _extract_safety_considerations(self, text: str) -> List[str]:
        """Extract safety considerations from text"""
        safety = []
        
        safety_patterns = [
            r'(?:safety|hazard|risk|precaution)(?:s)?\s*:?\s*([^.]+)',
            r'(?:careful|caution|warning)(?:ly)?\s+([^.]+)',
            r'(?:avoid|prevent|minimize)\s+([^.]+)'
        ]
        
        for pattern in safety_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            safety.extend([match.strip() for match in matches])
        
        return safety[:3]

    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key findings using NLP"""
        findings = []
        
        # Sentence-based analysis
        sentences = sent_tokenize(text)
        
        finding_indicators = [
            'found', 'discovered', 'observed', 'demonstrated', 'showed', 'revealed',
            'indicated', 'suggested', 'confirmed', 'identified', 'detected'
        ]
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in finding_indicators):
                # Clean and add sentence
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:  # Filter very short sentences
                    findings.append(clean_sentence)
        
        return findings[:5]  # Top 5 findings

    def _extract_methodology(self, text: str) -> str:
        """Extract overall methodology description"""
        method_sentences = []
        sentences = sent_tokenize(text)
        
        method_keywords = [
            'method', 'approach', 'technique', 'procedure', 'protocol',
            'analysis', 'measured', 'assessed', 'evaluated', 'performed'
        ]
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in method_keywords):
                method_sentences.append(sentence.strip())
        
        return ' '.join(method_sentences[:3]) if method_sentences else 'Not specified'

    def _extract_future_directions(self, text: str) -> List[str]:
        """Extract future research directions"""
        directions = []
        
        future_patterns = [
            r'(?:future|further|additional)\s+(?:research|studies|work|investigation)(?:s)?\s+([^.]+)',
            r'(?:next|subsequent)\s+(?:steps?|phase|stage)\s+([^.]+)',
            r'(?:remains?|requires?|needs?)\s+(?:to be\s+)?(?:investigated|studied|explored)\s*([^.]*)'
        ]
        
        for pattern in future_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            directions.extend([match.strip() for match in matches if match.strip()])
        
        return directions[:5]

    # Helper methods for cross-referencing and analysis
    def _extract_common_themes(self, text1: str, text2: str) -> List[str]:
        """Extract common themes between two documents"""
        if not self.tfidf_vectorizer:
            return []
        
        try:
            # Get feature names (words)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Transform texts
            vec1 = self.tfidf_vectorizer.transform([text1])
            vec2 = self.tfidf_vectorizer.transform([text2])
            
            # Find common high-scoring terms - convert sparse matrix to dense
            scores1 = vec1.toarray()[0]  # pyright: ignore[reportAttributeAccessIssue]
            scores2 = vec2.toarray()[0]  # pyright: ignore[reportAttributeAccessIssue]
            
            common_themes = []
            for i, (score1, score2) in enumerate(zip(scores1, scores2)):
                if score1 > 0.1 and score2 > 0.1:  # Both documents have this term
                    common_themes.append((feature_names[i], score1 * score2))
            
            # Sort by combined score and return top themes
            common_themes.sort(key=lambda x: x[1], reverse=True)
            return [theme[0] for theme in common_themes[:10]]
            
        except Exception as e:
            logger.error(f"Error extracting common themes: {e}")
            return []

    def _determine_relationship_type(self, doc1: Dict, doc2: Dict, similarity: float) -> str:
        """Determine the type of relationship between documents"""
        if similarity > 0.8:
            return "Highly Related"
        elif similarity > 0.6:
            return "Related"
        elif similarity > 0.4:
            return "Somewhat Related"
        else:
            return "Weakly Related"

    # Parsing and response processing methods
    def _parse_protocol_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for protocol analysis"""
        try:
            # Try to parse as JSON first
            if '{' in response and '}' in response:
                json_part = response[response.find('{'):response.rfind('}')+1]
                return json.loads(json_part)
        except:
            pass
        
        # Fallback parsing
        protocol_type = 'Unknown'
        conditions = {}
        
        if 'cell culture' in response.lower():
            protocol_type = 'Cell Culture'
        elif 'animal study' in response.lower():
            protocol_type = 'Animal Study'
        elif 'plant' in response.lower():
            protocol_type = 'Plant Study'
        
        return {'protocol_type': protocol_type, 'conditions': conditions}

    def _parse_literature_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for literature analysis"""
        lines = response.split('\n')
        summary = ""
        significance = ""
        
        for line in lines:
            if 'summary' in line.lower() and ':' in line:
                summary = line.split(':', 1)[1].strip()
            elif 'significance' in line.lower() and ':' in line:
                significance = line.split(':', 1)[1].strip()
        
        if not summary:
            summary = response[:200] + "..." if len(response) > 200 else response
        
        return {
            'summary': summary,
            'significance': significance
        }

    def _parse_research_gaps(self, response: str) -> List[str]:
        """Parse research gaps from AI response"""
        gaps = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                # Clean the line
                clean_line = re.sub(r'^[-•\d.\s]+', '', line).strip()
                if len(clean_line) > 10:  # Filter very short gaps
                    gaps.append(clean_line)
        
        return gaps[:5]  # Top 5 gaps

    def _parse_hypotheses(self, response: str) -> List[str]:
        """Parse hypotheses from AI response"""
        hypotheses = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                clean_line = re.sub(r'^[-•\d.\s]+', '', line).strip()
                if len(clean_line) > 15:  # Filter very short hypotheses
                    hypotheses.append(clean_line)
        
        return hypotheses[:5]

    # Heuristic fallback methods
    def _identify_research_gaps_heuristic(self, text: str) -> List[str]:
        """Identify research gaps using heuristic methods"""
        gaps = [
            "Long-term effects of microgravity on cellular function",
            "Optimization of life support systems for Mars missions", 
            "Plant growth strategies in low-resource environments",
            "Radiation protection mechanisms for deep space travel",
            "Psychological adaptation to isolated space environments"
        ]
        return gaps[:3]

    def _generate_hypotheses_heuristic(self, research_area: Optional[str] = None) -> Dict[str, Any]:
        """Generate hypotheses using heuristic methods"""
        base_hypotheses = [
            "Microgravity exposure induces novel adaptive responses in cellular metabolism",
            "Artificial gravity systems could prevent bone density loss in long-duration spaceflight",
            "Plant root architecture adapts to optimize nutrient uptake in space environments",
            "Cosmic radiation exposure creates predictable patterns of DNA damage and repair",
            "Closed-loop ecological systems require specific microbial community structures"
        ]
        
        # Filter by research area if specified
        if research_area:
            area_lower = research_area.lower()
            if 'human' in area_lower or 'physiology' in area_lower:
                hypotheses = [h for h in base_hypotheses if any(term in h.lower() 
                    for term in ['cellular', 'bone', 'gravity'])]
            elif 'plant' in area_lower:
                hypotheses = [h for h in base_hypotheses if 'plant' in h.lower() or 'root' in h.lower()]
            else:
                hypotheses = base_hypotheses
        else:
            hypotheses = base_hypotheses
            
        return {
            'hypotheses': hypotheses[:3],
            'confidence': 0.4
        }

    # Result interpretation methods
    async def _interpret_results_scientific(self, results_text: str) -> str:
        """Interpret results for scientific audience"""
        if not self.mistral_api_key:
            return "Scientific interpretation requires AI analysis"
        
        prompt = f"""
        Provide a scientific interpretation of these research results:
        
        Results: {results_text}
        
        Include:
        1. Statistical significance and effect sizes
        2. Mechanistic implications
        3. Comparison to existing literature
        4. Limitations and confounding factors
        
        Write for a scientific audience.
        """
        
        try:
            return await self._make_mistral_request(prompt)
        except Exception as e:
            return f"Scientific interpretation failed: {str(e)}"

    async def _interpret_results_general(self, results_text: str) -> str:
        """Interpret results for general audience"""
        if not self.mistral_api_key:
            return "General interpretation requires AI analysis"
        
        prompt = f"""
        Explain these research findings in simple, accessible language:
        
        Results: {results_text}
        
        Include:
        1. What was discovered in plain English
        2. Why this matters for space exploration
        3. How this could benefit life on Earth
        4. What this means for future astronauts
        
        Avoid technical jargon. Write for general public understanding.
        """
        
        try:
            return await self._make_mistral_request(prompt)
        except Exception as e:
            return f"General interpretation failed: {str(e)}"

    async def _interpret_results_mission(self, results_text: str) -> str:
        """Interpret results for mission planning"""
        if not self.mistral_api_key:
            return "Mission planning interpretation requires AI analysis"
        
        prompt = f"""
        Analyze these research findings for space mission planning:
        
        Results: {results_text}
        
        Assess:
        1. Impact on crew health and safety
        2. Mission design considerations
        3. Technology requirements
        4. Risk mitigation strategies
        5. Recommendations for future missions
        
        Focus on practical applications for mission planners.
        """
        
        try:
            return await self._make_mistral_request(prompt)
        except Exception as e:
            return f"Mission planning interpretation failed: {str(e)}"

    async def _interpret_results_clinical(self, results_text: str) -> str:
        """Interpret results for clinical applications"""
        if not self.mistral_api_key:
            return "Clinical interpretation requires AI analysis"
        
        prompt = f"""
        Provide clinical interpretation of these biomedical research findings:
        
        Results: {results_text}
        
        Include:
        1. Clinical relevance and implications
        2. Potential therapeutic applications
        3. Safety considerations
        4. Translational research opportunities
        5. Relevance to terrestrial medicine
        
        Write for healthcare professionals.
        """
        
        try:
            return await self._make_mistral_request(prompt)
        except Exception as e:
            return f"Clinical interpretation failed: {str(e)}"

    async def _explain_relationship(self, doc1: Dict, doc2: Dict, common_themes: List[str]) -> str:
        """Generate AI explanation of document relationship"""
        if not self.mistral_api_key:
            themes_str = ", ".join(common_themes[:5])
            return f"Documents share common themes including: {themes_str}"
        
        prompt = f"""
        Explain why these two research papers are related:
        
        Paper 1: {doc1.get('title', 'Unknown')}
        Abstract 1: {doc1.get('abstract', 'Not available')[:300]}
        
        Paper 2: {doc2.get('title', 'Unknown')}
        Abstract 2: {doc2.get('abstract', 'Not available')[:300]}
        
        Common themes: {', '.join(common_themes[:5])}
        
        Provide a brief explanation of their relationship and relevance to each other.
        """
        
        try:
            return await self._make_mistral_request(prompt)
        except Exception as e:
            themes_str = ", ".join(common_themes[:5])
            return f"Documents share common themes: {themes_str}"

    # Utility methods
    def _prepare_research_context(self, documents: List[Dict[str, Any]], 
                                research_area: Optional[str] = None) -> str:
        """Prepare research context from documents"""
        context_parts = []
        
        for doc in documents[:5]:  # Limit to avoid token limits
            title = doc.get('title', 'Untitled')
            abstract = doc.get('abstract', 'No abstract')[:200] + '...'
            context_parts.append(f"Title: {title}\nAbstract: {abstract}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        if research_area:
            context = f"Research Area: {research_area}\n\n{context}"
        
        return context

    def _extract_current_findings(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Extract current findings from documents"""
        findings = []
        
        for doc in documents:
            abstract = doc.get('abstract', '')
            if abstract:
                # Look for finding indicators
                sentences = sent_tokenize(abstract)
                for sentence in sentences:
                    if any(indicator in sentence.lower() for indicator in 
                          ['found', 'showed', 'demonstrated', 'observed', 'discovered']):
                        findings.append(sentence.strip())
        
        return findings[:10]  # Top 10 findings

    def _rank_hypotheses(self, hypotheses: List[str]) -> List[Dict[str, Any]]:
        """Rank hypotheses by novelty and feasibility"""
        ranked = []
        
        for i, hypothesis in enumerate(hypotheses):
            # Simple scoring based on length and keywords
            novelty_score = min(len(hypothesis) / 100, 1.0)  # Longer = more detailed
            feasibility_score = 0.7  # Default feasibility
            
            # Adjust for space-specific terms
            space_terms = ['microgravity', 'space', 'mars', 'radiation', 'astronaut']
            space_score = sum(1 for term in space_terms if term in hypothesis.lower()) / len(space_terms)
            
            overall_score = (novelty_score + feasibility_score + space_score) / 3
            
            ranked.append({
                'hypothesis': hypothesis,
                'novelty_score': novelty_score,
                'feasibility_score': feasibility_score,
                'space_relevance': space_score,
                'overall_score': overall_score,
                'rank': i + 1
            })
        
        # Sort by overall score
        ranked.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Update ranks
        for i, item in enumerate(ranked):
            item['rank'] = i + 1
        
        return ranked

    def _format_results_for_analysis(self, results_data: Dict[str, Any]) -> str:
        """Format results data for AI analysis"""
        formatted_parts = []
        
        for key, value in results_data.items():
            if isinstance(value, (int, float)):
                formatted_parts.append(f"{key}: {value}")
            elif isinstance(value, str) and len(value) < 200:
                formatted_parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                formatted_parts.append(f"{key}: {json.dumps(value, indent=2)}")
        
        return "\n".join(formatted_parts)

    def _is_medical_research(self, results_data: Dict[str, Any]) -> bool:
        """Check if results are from medical/biological research"""
        medical_indicators = ['health', 'medical', 'clinical', 'patient', 'treatment', 
                            'therapy', 'disease', 'diagnosis', 'physiological']
        
        text = json.dumps(results_data).lower()
        return any(indicator in text for indicator in medical_indicators)


# Main execution function
async def analyze_nasa_documents(documents: List[Dict[str, Any]], 
                               mistral_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to perform comprehensive NLP analysis on NASA documents
    """
    async with NaturalLanguageAnalyzer(mistral_api_key) as analyzer:
        results = {
            'experiment_metadata': [],
            'literature_analyses': [],
            'cross_references': [],
            'research_hypotheses': {},
            'analysis_summary': {}
        }
        
        logger.info(f"Starting NLP analysis of {len(documents)} documents")
        
        # Analyze experiment metadata
        for doc in documents[:10]:  # Limit for demo
            metadata = await analyzer.analyze_experiment_metadata(doc)
            results['experiment_metadata'].append(metadata.__dict__)
        
        # Analyze literature
        for doc in documents[:10]:
            literature = await analyzer.analyze_literature(doc)
            results['literature_analyses'].append(literature.__dict__)
        
        # Cross-reference studies
        cross_refs = await analyzer.cross_reference_studies(documents)
        results['cross_references'] = [ref.__dict__ for ref in cross_refs[:20]]
        
        # Generate research hypotheses
        hypotheses = await analyzer.generate_research_hypotheses(documents)
        results['research_hypotheses'] = hypotheses
        
        # Create analysis summary
        results['analysis_summary'] = {
            'total_documents': len(documents),
            'experiments_analyzed': len(results['experiment_metadata']),
            'literature_analyzed': len(results['literature_analyses']),
            'cross_references_found': len(results['cross_references']),
            'hypotheses_generated': len(hypotheses.get('hypotheses', [])),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("NLP analysis completed successfully")
        return results


if __name__ == "__main__":
    # Example usage
    async def main():
        # Load documents (this would come from your data pipeline)
        try:
            with open("data/processed_publications.json", 'r') as f:
                documents = json.load(f)
        except FileNotFoundError:
            print("No processed publications found. Run data processing first.")
            return
        
        # Run analysis
        results = await analyze_nasa_documents(documents)
        
        # Save results
        with open("data/nlp_analysis_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"NLP analysis complete. Processed {results['analysis_summary']['total_documents']} documents.")
        print(f"Generated {results['analysis_summary']['hypotheses_generated']} research hypotheses.")
        print(f"Found {results['analysis_summary']['cross_references_found']} cross-references.")
    
    asyncio.run(main())