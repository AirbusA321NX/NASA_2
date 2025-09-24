import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

try:
    import nltk
except ImportError:
    nltk = None
try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScientificInsight:
    """Data class for scientific insights"""
    insight_type: str
    content: str
    confidence: float
    supporting_data: List[str]
    scientific_significance: str
    related_studies: List[str]

@dataclass
class DataSummary:
    """Data class for statistical summaries"""
    metric_name: str
    value: float
    description: str
    interpretation: str
    data_points: int
    confidence_level: Optional[float] = None

class NASADataAnalyzer:
    """
    Comprehensive analyzer for NASA OSDR data
    Performs statistical analysis, ML clustering, and generates summaries for Mistral AI
    """
    
    def __init__(self, data_path: str = "data/processed_publications.json"):
        self.data_path = data_path
        self.df = None
        self.summaries: List[DataSummary] = []
        self.scientific_insights: List[ScientificInsight] = []
        self.analysis_results = {}
        
    def load_data(self) -> pd.DataFrame:
        """Load processed NASA OSDR data into pandas DataFrame"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            self.df = pd.DataFrame(data)
            
            # Data preprocessing
            self.df['publication_date'] = pd.to_datetime(self.df['publication_date'])
            self.df['year'] = self.df['publication_date'].dt.year
            self.df['month'] = self.df['publication_date'].dt.month
            
            # Extract numeric features
            self.df['num_authors'] = self.df['authors'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            self.df['num_organisms'] = self.df['organisms'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            self.df['num_keywords'] = self.df['keywords'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            self.df['abstract_length'] = self.df['abstract'].apply(lambda x: len(str(x)) if x else 0)
            self.df['title_length'] = self.df['title'].apply(lambda x: len(str(x)) if x else 0)
            
            logger.info(f"Loaded {len(self.df)} publications for analysis")
            return self.df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def analyze_temporal_trends(self) -> Dict[str, Any]:
        """Analyze publication trends over time"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            # Publications by year
            yearly_counts = self.df.groupby('year').size()
            
            # Growth rate calculation
            growth_rates = yearly_counts.pct_change().dropna()
            avg_growth_rate = growth_rates.mean()
            
            # Research area trends
            area_trends = self.df.groupby(['year', 'research_area']).size().unstack(fill_value=0)
            
            # Monthly patterns
            monthly_patterns = self.df.groupby('month').size()
            peak_month = monthly_patterns.idxmax()
            
            # Extract scalar values safely - handle all pandas types properly
            try:
                peak_month_val = 1
                if not monthly_patterns.empty:
                    peak_val = monthly_patterns.idxmax()
                    # Convert to Python int safely
                    if isinstance(peak_val, (int, float)):
                        peak_month_val = int(peak_val)
                    elif hasattr(peak_val, 'item'):
                        # Type guard for numpy/pandas scalars
                        peak_month_val = int(peak_val.item())  # type: ignore[union-attr]
                    else:
                        peak_month_val = int(str(peak_val))
            except (TypeError, ValueError, AttributeError):
                peak_month_val = 1
                
            try:
                first_year_val = 2000
                last_year_val = 2023
                most_productive_year_val = 2023
                
                if not yearly_counts.empty:
                    # Get first and last years safely
                    years_list = yearly_counts.index.tolist()
                    first_year_val = int(years_list[0])
                    last_year_val = int(years_list[-1])
                    
                    # Get most productive year safely
                    max_year = yearly_counts.idxmax()
                    if isinstance(max_year, (int, float)):
                        most_productive_year_val = int(max_year)
                    elif hasattr(max_year, 'item'):
                        # Type guard for numpy/pandas scalars
                        most_productive_year_val = int(max_year.item())  # type: ignore[union-attr]
                    else:
                        most_productive_year_val = int(str(max_year))
                        
            except (TypeError, ValueError, IndexError, AttributeError):
                first_year_val = 2000
                last_year_val = 2023
                most_productive_year_val = 2023
            
            # Calculate years span safely
            years_span = last_year_val - first_year_val
            
            # Handle avg_growth_rate safely
            try:
                avg_growth_rate_val = 0.0
                if isinstance(avg_growth_rate, (int, float)):
                    avg_growth_rate_val = float(avg_growth_rate)
                elif hasattr(avg_growth_rate, 'item'):
                    avg_growth_rate_val = float(avg_growth_rate.item())  # type: ignore[union-attr]
                elif pd.notna(avg_growth_rate):  # type: ignore[arg-type]
                    avg_growth_rate_val = float(avg_growth_rate)
            except (TypeError, ValueError, AttributeError):
                avg_growth_rate_val = 0.0
            
            results = {
                'yearly_publications': yearly_counts.to_dict(),
                'average_growth_rate': avg_growth_rate_val,
                'peak_publication_month': peak_month_val,
                'total_years_span': years_span,
                'most_productive_year': most_productive_year_val,
                'research_area_trends': area_trends.to_dict()
            }
            
            # Create summary - handle pandas scalar safely
            self.summaries.append(DataSummary(
                metric_name="Publication Growth Rate",
                value=avg_growth_rate_val,
                description=f"Average annual growth rate of NASA OSDR publications",
                interpretation=f"Publications are {'increasing' if avg_growth_rate_val > 0 else 'decreasing'} by {abs(avg_growth_rate_val)*100:.1f}% per year on average",
                data_points=len(yearly_counts)
            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in temporal analysis: {e}")
            return {}
    
    def analyze_research_areas(self) -> Dict[str, Any]:
        """Analyze research area distribution and characteristics"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            # Research area distribution
            area_counts = self.df['research_area'].value_counts()
            
            # Average metrics by research area
            area_stats = self.df.groupby('research_area').agg({
                'num_authors': 'mean',
                'num_organisms': 'mean',
                'num_keywords': 'mean',
                'abstract_length': 'mean',
                'year': ['min', 'max', 'count']
            }).round(2)
            
            # Diversity metrics
            total_areas = len(area_counts)
            shannon_diversity = -sum((p := area_counts / area_counts.sum()) * np.log(p))
            
            # Most collaborative areas (by author count)
            collaborative_areas = self.df.groupby('research_area')['num_authors'].mean()
            # Sort areas by collaboration level in descending order
            collaborative_areas = collaborative_areas.sort_values(ascending=False)  # type: ignore[call-overload]
            
            results = {
                'area_distribution': area_counts.to_dict(),
                'area_statistics': area_stats.to_dict(),
                'shannon_diversity': float(shannon_diversity),
                'total_research_areas': total_areas,
                'most_collaborative_area': collaborative_areas.index[0],
                'avg_collaboration_score': float(collaborative_areas.iloc[0])
            }
            
            # Create summary
            self.summaries.append(DataSummary(
                metric_name="Research Area Diversity",
                value=shannon_diversity,
                description="Shannon diversity index of research areas in NASA OSDR",
                interpretation=f"Research is {'highly diverse' if shannon_diversity > 2 else 'moderately diverse' if shannon_diversity > 1 else 'concentrated'} across {total_areas} different areas",
                data_points=total_areas
            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in research area analysis: {e}")
            return {}
    
    def analyze_organisms(self) -> Dict[str, Any]:
        """Analyze organism usage patterns in research"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            # Flatten organism lists
            all_organisms = []
            for org_list in self.df['organisms']:
                if isinstance(org_list, list):
                    all_organisms.extend(org_list)
            
            organism_counts = Counter(all_organisms)
            
            # Organism diversity by research area
            area_organism_diversity = {}
            for area in self.df['research_area'].unique():
                area_data = self.df[self.df['research_area'] == area]
                area_organisms = []
                for org_list in area_data['organisms']:
                    if isinstance(org_list, list):
                        area_organisms.extend(org_list)
                
                unique_organisms = len(set(area_organisms))
                area_organism_diversity[area] = unique_organisms
            
            # Model organism usage
            model_organisms = ['Homo sapiens', 'Mus musculus', 'Arabidopsis thaliana', 
                             'Drosophila melanogaster', 'Caenorhabditis elegans', 
                             'Saccharomyces cerevisiae', 'Escherichia coli']
            
            model_organism_usage = {org: organism_counts.get(org, 0) for org in model_organisms}
            
            results = {
                'organism_counts': dict(organism_counts.most_common(20)),
                'total_unique_organisms': len(organism_counts),
                'area_organism_diversity': area_organism_diversity,
                'model_organism_usage': model_organism_usage,
                'most_studied_organism': organism_counts.most_common(1)[0] if organism_counts else ('None', 0)
            }
            
            # Create summary
            most_studied = organism_counts.most_common(1)[0] if organism_counts else ('None', 0)
            self.summaries.append(DataSummary(
                metric_name="Organism Diversity",
                value=len(organism_counts),
                description="Number of unique organisms studied in NASA OSDR",
                interpretation=f"Research spans {len(organism_counts)} different organisms, with {most_studied[0]} being most frequently studied ({most_studied[1]} studies)",
                data_points=len(all_organisms)
            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in organism analysis: {e}")
            return {}
    
    def perform_clustering_analysis(self) -> Dict[str, Any]:
        """Perform ML clustering on research publications"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            # Prepare features for clustering
            features = self.df[['num_authors', 'num_organisms', 'num_keywords', 
                              'abstract_length', 'title_length', 'year']].fillna(0)
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Determine optimal number of clusters using elbow method
            inertias = []
            k_range = range(2, min(11, len(features) // 5))
            
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
                kmeans.fit(features_scaled)
                inertias.append(kmeans.inertia_)
            
            # Choose optimal k (simple elbow detection)
            optimal_k = 3  # Default fallback
            if len(inertias) >= 2:
                # Simple elbow detection
                deltas = [inertias[i] - inertias[i+1] for i in range(len(inertias)-1)]
                optimal_k = k_range[deltas.index(max(deltas))]
            
            # Perform clustering with optimal k
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
            clusters = kmeans.fit_predict(features_scaled)
            
            # Add cluster labels to dataframe
            self.df['cluster'] = clusters
            
            # Analyze clusters
            cluster_characteristics = {}
            for cluster_id in range(optimal_k):
                cluster_data = self.df[self.df['cluster'] == cluster_id]
                
                characteristics = {
                    'size': len(cluster_data),
                    'avg_authors': float(cluster_data['num_authors'].mean()),
                    'avg_organisms': float(cluster_data['num_organisms'].mean()),
                    'avg_keywords': float(cluster_data['num_keywords'].mean()),
                    'dominant_research_areas': pd.Series(cluster_data['research_area']).value_counts().head(3).to_dict(),
                    'year_range': f"{cluster_data['year'].min()}-{cluster_data['year'].max()}"
                }
                cluster_characteristics[f"cluster_{cluster_id}"] = characteristics
            
            # PCA for visualization
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(features_scaled)
            
            results = {
                'optimal_clusters': optimal_k,
                'cluster_characteristics': cluster_characteristics,
                'pca_explained_variance': pca.explained_variance_ratio_.tolist(),
                'pca_coordinates': pca_result.tolist()
            }
            
            # Create summary
            self.summaries.append(DataSummary(
                metric_name="Research Clusters",
                value=optimal_k,
                description="Number of distinct research publication clusters identified",
                interpretation=f"NASA OSDR publications naturally group into {optimal_k} distinct clusters based on their characteristics",
                data_points=len(features)
            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in clustering analysis: {e}")
            return {}
    
    def analyze_collaboration_patterns(self) -> Dict[str, Any]:
        """Analyze author collaboration patterns"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            # Author collaboration statistics
            collaboration_stats = {
                'avg_authors_per_paper': float(self.df['num_authors'].mean()),
                'max_authors': int(self.df['num_authors'].max()),
                'min_authors': int(self.df['num_authors'].min()),
                'single_author_papers': int((self.df['num_authors'] == 1).sum()),
                'highly_collaborative_papers': int((self.df['num_authors'] >= 5).sum())
            }
            
            # Collaboration by research area
            area_collaboration = self.df.groupby('research_area')['num_authors'].agg(['mean', 'std']).round(2)
            
            # Collaboration trends over time
            yearly_collaboration = self.df.groupby('year')['num_authors'].mean()
            
            # Calculate collaboration growth - correlation between year and avg authors
            try:
                # Use scipy.stats.pearsonr for proper correlation calculation
                from scipy.stats import pearsonr
                
                # Break down the method chaining for better type inference
                years_array = yearly_collaboration.index.to_numpy()
                years_float = years_array.astype(float)  # type: ignore[call-overload]
                collab_array = yearly_collaboration.to_numpy() 
                collab_float = collab_array.astype(float)  # type: ignore[call-overload]
                
                # Check if we have enough data points
                if len(years_float) < 2 or len(collab_float) < 2:
                    collaboration_trend = 0.0
                else:
                    correlation_result = pearsonr(years_float, collab_float)  # type: ignore[call-overload]
                    # Extract correlation coefficient with explicit type handling
                    corr_val = correlation_result[0]
                    # Handle NaN values safely
                    if pd.isna(corr_val):  # type: ignore[arg-type]
                        collaboration_trend = 0.0
                    else:
                        # Convert to float with type guard for tuple unpacking
                        if isinstance(corr_val, (int, float)):
                            collaboration_trend = float(corr_val)
                        else:
                            collaboration_trend = 0.0
            except Exception:
                collaboration_trend = 0.0
            
            results = {
                'collaboration_statistics': collaboration_stats,
                'collaboration_by_area': area_collaboration.to_dict(),
                'yearly_collaboration_trend': yearly_collaboration.to_dict(),
                'collaboration_growth_correlation': float(collaboration_trend) if pd.notna(collaboration_trend) else 0.0
            }
            
            # Create summary
            self.summaries.append(DataSummary(
                metric_name="Average Collaboration",
                value=collaboration_stats['avg_authors_per_paper'],
                description="Average number of authors per NASA OSDR publication",
                interpretation=f"NASA research shows {'high' if collaboration_stats['avg_authors_per_paper'] > 4 else 'moderate' if collaboration_stats['avg_authors_per_paper'] > 2 else 'low'} collaboration with {collaboration_stats['avg_authors_per_paper']:.1f} authors per paper on average",
                data_points=len(self.df)
            ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error in collaboration analysis: {e}")
            return {}
    
    def analyze_scientific_content(self) -> Dict[str, Any]:
        """Comprehensive scientific content analysis"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            scientific_results = {}
            
            # 1. Abstract Content Analysis
            abstract_analysis = self._analyze_abstracts()
            scientific_results['abstract_analysis'] = abstract_analysis
            
            # 2. Research Methodology Analysis  
            methodology_analysis = self._analyze_methodologies()
            scientific_results['methodology_analysis'] = methodology_analysis
            
            # 3. Scientific Keywords and Topics
            keyword_analysis = self._analyze_scientific_keywords()
            scientific_results['keyword_analysis'] = keyword_analysis
            
            # 4. Experimental Conditions Analysis
            conditions_analysis = self._analyze_experimental_conditions()
            scientific_results['conditions_analysis'] = conditions_analysis
            
            # 5. Scientific Impact and Citations Analysis
            impact_analysis = self._analyze_scientific_impact()
            scientific_results['impact_analysis'] = impact_analysis
            
            # 6. Cross-Study Scientific Relationships
            relationships = self._analyze_study_relationships()
            scientific_results['study_relationships'] = relationships
            
            # Generate scientific insights
            self._generate_scientific_insights(scientific_results)
            
            return scientific_results
            
        except Exception as e:
            logger.error(f"Error in scientific content analysis: {e}")
            return {}
    
    def _analyze_abstracts(self) -> Dict[str, Any]:
        """Analyze scientific content from abstracts"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            abstracts = self.df['abstract'].dropna().astype(str)
            if abstracts.empty:
                return {}
            
            # Combined text for analysis
            combined_text = ' '.join(abstracts)
            
            # Scientific term extraction
            scientific_terms = self._extract_scientific_terms(combined_text)
            
            # Research themes identification
            themes = self._identify_research_themes(abstracts)  # type: ignore[arg-type]
            
            # Sentiment and complexity analysis
            complexity_scores = []
            for abstract in abstracts:
                try:
                    if TextBlob is not None:
                        blob = TextBlob(abstract)
                        # Scientific complexity based on sentence length and vocabulary
                        # Type guard for TextBlob sentences which may have type issues
                        sentences = blob.sentences  # type: ignore[call-overload]
                        sentence_count = len(sentences) if hasattr(sentences, '__len__') else 1  # type: ignore[call-overload,arg-type]
                        avg_sentence_length = len(abstract.split()) / max(sentence_count, 1)
                    else:
                        # Fallback: simple word count based complexity
                        avg_sentence_length = len(abstract.split()) / max(abstract.count('.') + 1, 1)
                    complexity_scores.append(avg_sentence_length)
                except:
                    complexity_scores.append(0)
            
            avg_complexity = np.mean(complexity_scores) if complexity_scores else 0
            
            # Key research findings extraction
            findings = self._extract_key_findings_from_abstracts(abstracts)  # type: ignore[arg-type]
            
            return {
                'total_abstracts_analyzed': len(abstracts),
                'scientific_terms': scientific_terms,
                'research_themes': themes,
                'average_complexity_score': float(avg_complexity),
                'key_findings': findings,
                'most_common_research_focus': self._get_research_focus(combined_text)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing abstracts: {e}")
            return {}
    
    def _analyze_methodologies(self) -> Dict[str, Any]:
        """Analyze experimental methodologies used"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            if 'abstract' not in self.df.columns:
                return {}
            
            abstracts = self.df['abstract'].dropna().astype(str)
            methodology_keywords = {
                'molecular': ['PCR', 'RNA-seq', 'qPCR', 'Western blot', 'ELISA', 'microarray', 'sequencing'],
                'cellular': ['cell culture', 'flow cytometry', 'microscopy', 'immunofluorescence', 'FACS'],
                'physiological': ['ECG', 'blood pressure', 'heart rate', 'bone density', 'muscle mass'],
                'behavioral': ['cognitive test', 'behavioral analysis', 'psychological assessment'],
                'biochemical': ['metabolomics', 'proteomics', 'enzyme assay', 'spectroscopy'],
                'imaging': ['MRI', 'CT scan', 'ultrasound', 'X-ray', 'PET scan'],
                'space_specific': ['microgravity', 'simulated weightlessness', 'centrifuge', 'parabolic flight']
            }
            
            methodology_counts = {category: 0 for category in methodology_keywords}
            method_details = {category: [] for category in methodology_keywords}
            
            for abstract in abstracts:
                abstract_lower = abstract.lower()
                for category, keywords in methodology_keywords.items():
                    for keyword in keywords:
                        if keyword.lower() in abstract_lower:
                            methodology_counts[category] += 1
                            if keyword not in method_details[category]:
                                method_details[category].append(keyword)
            
            # Calculate methodology diversity
            total_methods = sum(methodology_counts.values())
            methodology_diversity = len([count for count in methodology_counts.values() if count > 0])
            
            return {
                'methodology_distribution': methodology_counts,
                'methodology_details': method_details,
                'total_methodologies_identified': total_methods,
                'methodology_diversity_score': methodology_diversity,
                'most_common_methodology': max(methodology_counts, key=methodology_counts.get) if methodology_counts else 'None',  # type: ignore[arg-type]
                'experimental_sophistication_index': total_methods / max(len(abstracts), 1)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing methodologies: {e}")
            return {}
    
    def _analyze_scientific_keywords(self) -> Dict[str, Any]:
        """Analyze scientific keywords and topics using TF-IDF"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            if 'abstract' not in self.df.columns:
                return {}
            
            abstracts = self.df['abstract'].dropna().astype(str)
            if abstracts.empty:
                return {}
            
            # TF-IDF analysis for scientific terms
            tfidf = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2
            )
            
            tfidf_matrix = tfidf.fit_transform(abstracts)
            feature_names = tfidf.get_feature_names_out()
            
            # Get top scientific terms
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)  # type: ignore[call-overload]
            top_terms_indices = np.argsort(mean_scores)[-20:]
            top_scientific_terms = [(feature_names[i], mean_scores[i]) for i in top_terms_indices]
            top_scientific_terms.reverse()
            
            # Space biology specific terms
            space_bio_terms = [
                'microgravity', 'weightlessness', 'space flight', 'ISS', 'space station',
                'bone loss', 'muscle atrophy', 'radiation exposure', 'cosmic radiation',
                'plant growth', 'cell division', 'gene expression', 'protein synthesis'
            ]
            
            space_term_frequency = {}
            combined_text = ' '.join(abstracts).lower()
            for term in space_bio_terms:
                space_term_frequency[term] = combined_text.count(term.lower())
            
            return {
                'top_scientific_terms': top_scientific_terms,
                'space_biology_terms': space_term_frequency,
                'total_unique_terms': len(feature_names),
                'term_diversity_score': len([term for term, freq in space_term_frequency.items() if freq > 0])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing scientific keywords: {e}")
            return {}
    
    def _analyze_experimental_conditions(self) -> Dict[str, Any]:
        """Analyze experimental conditions and environments"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            if 'abstract' not in self.df.columns:
                return {}
            
            abstracts = self.df['abstract'].dropna().astype(str)
            combined_text = ' '.join(abstracts).lower()
            
            # Environmental conditions
            conditions = {
                'microgravity_studies': combined_text.count('microgravity') + combined_text.count('weightless'),
                'ground_control_studies': combined_text.count('ground control') + combined_text.count('control group'),
                'flight_experiments': combined_text.count('space flight') + combined_text.count('iss experiment'),
                'cell_culture_studies': combined_text.count('cell culture') + combined_text.count('in vitro'),
                'animal_studies': combined_text.count('mouse') + combined_text.count('rat') + combined_text.count('mice'),
                'plant_studies': combined_text.count('plant') + combined_text.count('arabidopsis') + combined_text.count('seedling'),
                'human_studies': combined_text.count('human') + combined_text.count('astronaut') + combined_text.count('crew')
            }
            
            # Duration analysis
            duration_keywords = ['day', 'week', 'month', 'hour', 'days', 'weeks', 'months', 'hours']
            duration_mentions = sum(combined_text.count(keyword) for keyword in duration_keywords)
            
            # Environmental factors
            environmental_factors = {
                'radiation': combined_text.count('radiation') + combined_text.count('cosmic ray'),
                'temperature': combined_text.count('temperature') + combined_text.count('thermal'),
                'atmosphere': combined_text.count('atmosphere') + combined_text.count('pressure'),
                'gravity': combined_text.count('gravity') + combined_text.count('gravitational')
            }
            
            return {
                'experimental_conditions': conditions,
                'environmental_factors': environmental_factors,
                'duration_complexity': duration_mentions,
                'total_condition_mentions': sum(conditions.values()),
                'most_studied_condition': max(conditions, key=conditions.get) if conditions else 'None',  # type: ignore[arg-type]
                'environmental_diversity': len([factor for factor, count in environmental_factors.items() if count > 0])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing experimental conditions: {e}")
            return {}
    
    def _analyze_scientific_impact(self) -> Dict[str, Any]:
        """Analyze scientific impact and significance"""
        if self.df is None or self.df.empty:
            return {}
        
        try:
            if 'abstract' not in self.df.columns:
                return {}
            
            abstracts = self.df['abstract'].dropna().astype(str)
            
            # Impact keywords
            impact_keywords = {
                'high_impact': ['significant', 'novel', 'breakthrough', 'discovery', 'first time', 'unprecedented'],
                'medical_relevance': ['clinical', 'therapeutic', 'treatment', 'health', 'disease', 'medical'],
                'space_mission': ['mission', 'exploration', 'astronaut', 'crew health', 'long duration'],
                'fundamental': ['mechanism', 'pathway', 'molecular', 'cellular', 'biological process']
            }
            
            impact_scores = {category: 0 for category in impact_keywords}
            
            for abstract in abstracts:
                abstract_lower = abstract.lower()
                for category, keywords in impact_keywords.items():
                    for keyword in keywords:
                        if keyword in abstract_lower:
                            impact_scores[category] += 1
            
            # Calculate overall impact score
            total_impact = sum(impact_scores.values())
            impact_diversity = len([score for score in impact_scores.values() if score > 0])
            
            # Novelty indicators
            novelty_terms = ['novel', 'new', 'first', 'unique', 'unprecedented', 'innovative']
            novelty_score = sum(abstracts.str.lower().str.count(term).sum() for term in novelty_terms)
            
            return {
                'impact_distribution': impact_scores,
                'total_impact_score': total_impact,
                'impact_diversity': impact_diversity,
                'novelty_score': novelty_score,
                'average_impact_per_study': total_impact / max(len(abstracts), 1),
                'highest_impact_category': max(impact_scores, key=impact_scores.get) if impact_scores else 'None'  # type: ignore[arg-type]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing scientific impact: {e}")
            return {}
    
    def _analyze_study_relationships(self) -> Dict[str, Any]:
        """Analyze relationships and similarities between studies"""
        if self.df is None or self.df.empty or len(self.df) < 2:
            return {}
        
        try:
            if 'abstract' not in self.df.columns or len(self.df) < 2:
                return {}
            
            abstracts = self.df['abstract'].dropna().astype(str)
            if len(abstracts) < 2:
                return {}
            
            # TF-IDF similarity analysis
            tfidf = TfidfVectorizer(max_features=500, stop_words='english', min_df=2)
            tfidf_matrix = tfidf.fit_transform(abstracts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find highly similar studies (excluding self-similarity)
            similar_pairs = []
            threshold = 0.3
            
            for i in range(len(similarity_matrix)):
                for j in range(i + 1, len(similarity_matrix)):
                    if similarity_matrix[i][j] > threshold:
                        similar_pairs.append({
                            'study_1_index': i,
                            'study_2_index': j,
                            'similarity_score': float(similarity_matrix[i][j]),
                            'study_1_title': self.df.iloc[i].get('title', f'Study {i}')[:100],
                            'study_2_title': self.df.iloc[j].get('title', f'Study {j}')[:100]
                        })
            
            # Sort by similarity score
            similar_pairs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Calculate research clustering
            avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
            
            return {
                'total_study_pairs': len(similar_pairs),
                'highly_similar_studies': similar_pairs[:10],  # Top 10 most similar
                'average_similarity_score': float(avg_similarity),
                'research_clustering_index': float(avg_similarity),
                'similarity_threshold_used': threshold
            }
            
        except Exception as e:
            logger.error(f"Error analyzing study relationships: {e}")
            return {}
    
    def _extract_scientific_terms(self, text: str) -> List[str]:
        """Extract scientific terms from text"""
        scientific_patterns = [
            r'\b[A-Z][a-z]+\s+[a-z]+\b',  # Binomial nomenclature
            r'\b[A-Z]{2,}[0-9]*\b',       # Acronyms and gene names
            r'\b\w*ase\b',               # Enzymes
            r'\b\w*osis\b',              # Biological processes
            r'\b\w*emia\b',              # Medical conditions
        ]
        
        terms = set()
        for pattern in scientific_patterns:
            matches = re.findall(pattern, text)
            terms.update(matches)
        
        return list(terms)[:50]  # Top 50 terms
    
    def _identify_research_themes(self, abstracts: pd.Series) -> List[str]:
        """Identify major research themes"""
        themes = {
            'Bone and Muscle': ['bone', 'muscle', 'osteoblast', 'osteoclast', 'calcium', 'osteoporosis'],
            'Cardiovascular': ['heart', 'cardiovascular', 'blood pressure', 'circulation', 'cardiac'],
            'Radiation Biology': ['radiation', 'cosmic', 'DNA damage', 'repair', 'mutation'],
            'Plant Biology': ['plant', 'seedling', 'root', 'shoot', 'photosynthesis', 'arabidopsis'],
            'Microbiology': ['bacteria', 'microbe', 'pathogen', 'immune', 'infection'],
            'Cell Biology': ['cell', 'cellular', 'mitosis', 'apoptosis', 'membrane'],
            'Neuroscience': ['brain', 'neuron', 'cognitive', 'behavior', 'neurological']
        }
        
        theme_scores = {}
        combined_text = ' '.join(abstracts).lower()
        
        for theme, keywords in themes.items():
            score = sum(combined_text.count(keyword) for keyword in keywords)
            if score > 0:
                theme_scores[theme] = score
        
        return sorted(theme_scores.keys(), key=lambda x: theme_scores[x], reverse=True)
    
    def _extract_key_findings_from_abstracts(self, abstracts: pd.Series) -> List[str]:
        """Extract key research findings"""
        findings = []
        finding_patterns = [
            r'(?:found|discovered|showed|demonstrated|revealed)\s+that\s+([^.]+)',
            r'(?:results show|data indicate|findings suggest)\s+([^.]+)',
            r'(?:significant|notable|important)\s+([^.]+)'
        ]
        
        for abstract in abstracts:
            for pattern in finding_patterns:
                matches = re.findall(pattern, abstract, re.IGNORECASE)
                findings.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        return findings[:20]  # Top 20 findings
    
    def _get_research_focus(self, text: str) -> str:
        """Determine primary research focus"""
        focus_areas = {
            'Human Physiology': ['human', 'astronaut', 'crew', 'physiological'],
            'Plant Sciences': ['plant', 'arabidopsis', 'seedling', 'growth'],
            'Cell Biology': ['cell', 'cellular', 'molecular', 'protein'],
            'Space Medicine': ['medical', 'health', 'clinical', 'therapeutic'],
            'Radiation Research': ['radiation', 'cosmic', 'exposure', 'dosimetry']
        }
        
        scores = {}
        text_lower = text.lower()
        
        for focus, keywords in focus_areas.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            scores[focus] = score
        
        return max(scores, key=lambda x: scores[x]) if scores else 'General Biology'  # type: ignore[arg-type]
    
    def _generate_scientific_insights(self, scientific_results: Dict[str, Any]):
        """Generate scientific insights from analysis results"""
        try:
            # Methodology insights
            if 'methodology_analysis' in scientific_results:
                method_data = scientific_results['methodology_analysis']
                most_common = method_data.get('most_common_methodology', '')
                diversity = method_data.get('methodology_diversity_score', 0)
                
                self.scientific_insights.append(ScientificInsight(
                    insight_type="Methodological",
                    content=f"Research predominantly uses {most_common} methodologies with {diversity} different experimental approaches identified.",
                    confidence=0.85,
                    supporting_data=[f"Methodology diversity: {diversity}", f"Primary approach: {most_common}"],
                    scientific_significance="Indicates the breadth and sophistication of experimental techniques in space biology research.",
                    related_studies=[]
                ))
            
            # Impact insights
            if 'impact_analysis' in scientific_results:
                impact_data = scientific_results['impact_analysis']
                highest_impact = impact_data.get('highest_impact_category', '')
                novelty = impact_data.get('novelty_score', 0)
                
                self.scientific_insights.append(ScientificInsight(
                    insight_type="Scientific Impact",
                    content=f"Research shows strongest impact in {highest_impact} areas with {novelty} novelty indicators across studies.",
                    confidence=0.80,
                    supporting_data=[f"Impact category: {highest_impact}", f"Novelty score: {novelty}"],
                    scientific_significance="Demonstrates the pioneering nature and potential applications of space biology research.",
                    related_studies=[]
                ))
            
            # Relationship insights
            if 'study_relationships' in scientific_results:
                rel_data = scientific_results['study_relationships']
                clustering = rel_data.get('research_clustering_index', 0)
                similar_studies = rel_data.get('total_study_pairs', 0)
                
                self.scientific_insights.append(ScientificInsight(
                    insight_type="Research Connectivity",
                    content=f"Studies show {clustering:.2f} clustering index with {similar_studies} highly related research pairs identified.",
                    confidence=0.75,
                    supporting_data=[f"Clustering index: {clustering:.2f}", f"Related pairs: {similar_studies}"],
                    scientific_significance="Reveals the interconnected nature of space biology research and potential for cross-study insights.",
                    related_studies=[]
                ))
                
        except Exception as e:
            logger.error(f"Error generating scientific insights: {e}")
    
    def generate_text_summaries(self) -> List[str]:
        """Generate text summaries for Mistral AI processing"""
        summaries = []
        
        # Overall dataset summary
        if self.df is not None and not self.df.empty:
            total_pubs = len(self.df)
            year_range = f"{self.df['year'].min()}-{self.df['year'].max()}"
            # Safely convert nunique result to int with null checking
            unique_areas_result = self.df['research_area'].nunique()
            try:
                unique_areas = int(unique_areas_result)
            except (TypeError, ValueError):
                unique_areas = 0
            
            overall_summary = (
                f"NASA OSDR dataset contains {total_pubs} publications spanning {year_range}. "
                f"Research covers {unique_areas} distinct areas. "
                f"Average collaboration involves {self.df['num_authors'].mean():.1f} authors per study. "
                f"Studies investigate {self.df['num_organisms'].sum()} organism instances across research."
            )
            summaries.append(overall_summary)
        
        # Statistical findings summaries
        for summary in self.summaries:
            statistical_summary = (
                f"{summary.metric_name}: {summary.value:.2f}. "
                f"{summary.description}. {summary.interpretation} "
                f"(based on {summary.data_points} data points)."
            )
            summaries.append(statistical_summary)
        
        # Research area insights
        if 'research_areas' in self.analysis_results:
            area_data = self.analysis_results['research_areas']
            top_areas = list(area_data['area_distribution'].keys())[:3]
            
            area_summary = (
                f"Top research areas in NASA OSDR: {', '.join(top_areas)}. "
                f"Research diversity index: {area_data['shannon_diversity']:.2f}. "
                f"Most collaborative area: {area_data['most_collaborative_area']} "
                f"with {area_data['avg_collaboration_score']:.1f} average authors."
            )
            summaries.append(area_summary)
        
        # Temporal trends insights
        if 'temporal_trends' in self.analysis_results:
            temporal_data = self.analysis_results['temporal_trends']
            
            temporal_summary = (
                f"Publication trends: {temporal_data['average_growth_rate']*100:.1f}% annual growth rate. "
                f"Most productive year: {temporal_data['most_productive_year']}. "
                f"Research spans {temporal_data['total_years_span']} years. "
                f"Peak publication month: {temporal_data['peak_publication_month']}."
            )
            summaries.append(temporal_summary)
        
        return summaries
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run all analysis components and generate comprehensive results"""
        logger.info("Starting comprehensive NASA OSDR data analysis...")
        
        # Load data
        if self.load_data().empty:
            logger.error("Failed to load data for analysis")
            return {}
        
        # Run all analyses
        self.analysis_results['temporal_trends'] = self.analyze_temporal_trends()
        self.analysis_results['research_areas'] = self.analyze_research_areas()
        self.analysis_results['organisms'] = self.analyze_organisms()
        self.analysis_results['clustering'] = self.perform_clustering_analysis()
        self.analysis_results['collaboration'] = self.analyze_collaboration_patterns()
        self.analysis_results['scientific_content'] = self.analyze_scientific_content()
        
        # Generate text summaries
        text_summaries = self.generate_text_summaries()
        self.analysis_results['text_summaries'] = text_summaries
        
        # Save results
        output_path = "data/analysis_results.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Analysis complete. Results saved to {output_path}")
        logger.info(f"Generated {len(text_summaries)} text summaries for Mistral AI processing")
        
        return self.analysis_results

async def main():
    """Main function to run data analysis"""
    analyzer = NASADataAnalyzer()
    results = analyzer.run_complete_analysis()
    
    if results:
        print("\n=== NASA OSDR Data Analysis Summary ===")
        print(f"Total publications analyzed: {len(analyzer.df) if analyzer.df is not None else 0}")
        print(f"Analysis components completed: {len(results)}")
        print(f"Text summaries generated: {len(results.get('text_summaries', []))}")
        
        # Display key findings
        if 'text_summaries' in results:
            print("\n=== Key Findings for Mistral AI ===")
            for i, summary in enumerate(results['text_summaries'][:3], 1):
                print(f"{i}. {summary}")

if __name__ == "__main__":
    asyncio.run(main())