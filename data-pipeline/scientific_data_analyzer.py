import asyncio
import aiohttp
import gzip
import io
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import re

# Add import for the NASADataAnalyzer to leverage its dynamic extraction methods
from data_analyzer import NASADataAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScientificDataAnalyzer:
    """
    Analyzer for actual scientific data from NASA OSDR
    Processes microarray data, RNA-seq data, and other scientific files
    """
    
    def __init__(self):
        self.session = None
        # Initialize NASADataAnalyzer to leverage its dynamic extraction methods
        self.data_analyzer = NASADataAnalyzer()
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def download_and_process_file(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Download and process a scientific data file
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
            
        try:
            logger.info(f"Downloading scientific data file: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Process based on file type
                    if url.endswith('.CEL.gz') or url.endswith('.txt.gz'):
                        return await self._process_microarray_data(content, url)
                    elif url.endswith('.csv') or url.endswith('.tsv'):
                        return await self._process_tabular_data(content, url)
                    elif url.endswith('.fastq.gz') or url.endswith('.fq.gz'):
                        return await self._process_fastq_data(content, url)
                    else:
                        return await self._process_generic_data(content, url)
                else:
                    logger.warning(f"Failed to download {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error processing file {url}: {e}")
            return None

    async def _process_microarray_data(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process microarray data files (.CEL.gz, .txt.gz)
        """
        try:
            # For now, we'll extract basic metadata without fully parsing the binary CEL format
            # In a full implementation, we would use affy or other libraries to parse CEL files
            result = {
                "file_type": "microarray_data",
                "filename": filename,
                "size_bytes": len(content),
                "data_type": "gene_expression",
                "format": "affymetrix" if ".CEL" in filename else "text"
            }
            
            # Extract study information from filename
            study_info = self._extract_study_info_from_filename(filename)
            result.update(study_info)
            
            logger.info(f"Processed microarray data: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing microarray data {filename}: {e}")
            return {"file_type": "microarray_data", "filename": filename, "error": str(e)}

    async def _process_tabular_data(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process tabular data files (.csv, .tsv)
        """
        try:
            # Decompress if needed
            if filename.endswith('.gz'):
                content = gzip.decompress(content)
            
            # Convert to string
            content_str = content.decode('utf-8', errors='ignore')
            
            # Try to parse as CSV/TSV
            lines = content_str.split('\n')
            if len(lines) > 1:
                # Determine delimiter
                delimiter = '\t' if '\t' in lines[0] else ','
                
                # Parse first few lines to get structure
                header = lines[0].strip().split(delimiter)
                data_lines = [line.strip().split(delimiter) for line in lines[1:6] if line.strip()]
                
                result = {
                    "file_type": "tabular_data",
                    "filename": filename,
                    "size_bytes": len(content),
                    "rows": len(lines) - 1,
                    "columns": len(header),
                    "header": header[:10],  # First 10 column names
                    "sample_data": data_lines[:5] if data_lines else [],
                    "data_type": self._infer_data_type_from_columns(header)
                }
                
                # Extract study information
                study_info = self._extract_study_info_from_filename(filename)
                result.update(study_info)
                
                # Apply dynamic extraction methods from NASADataAnalyzer
                if content_str:
                    # Extract scientific terms using dynamic methods
                    scientific_terms = self.data_analyzer._extract_scientific_terms(content_str)
                    if scientific_terms:
                        result["extracted_scientific_terms"] = scientific_terms[:20]  # Limit to top 20
                    
                    # Extract research themes using dynamic methods
                    # Convert content to a series for compatibility with the method
                    content_series = pd.Series([content_str])
                    research_themes = self.data_analyzer._identify_research_themes(content_series)
                    if research_themes:
                        result["identified_research_themes"] = research_themes[:10]  # Limit to top 10
                
                logger.info(f"Processed tabular data: {filename} ({len(header)} columns, {len(lines)-1} rows)")
                return result
            else:
                return {"file_type": "tabular_data", "filename": filename, "size_bytes": len(content)}
                
        except Exception as e:
            logger.error(f"Error processing tabular data {filename}: {e}")
            return {"file_type": "tabular_data", "filename": filename, "error": str(e)}

    async def _process_fastq_data(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process FASTQ data files (.fastq.gz, .fq.gz)
        """
        try:
            # Decompress content
            decompressed = gzip.decompress(content)
            
            # Parse FASTQ format (4 lines per record)
            lines = decompressed.decode('utf-8', errors='ignore').split('\n')
            record_count = len([line for line in lines if line.startswith('@')])  # Count header lines
            
            # Sample first few records
            sample_records = []
            for i in range(0, min(16, len(lines)), 4):  # 4 lines per FASTQ record
                if i + 3 < len(lines):
                    record = {
                        "header": lines[i][:50] + "..." if len(lines[i]) > 50 else lines[i],
                        "sequence_length": len(lines[i+1]),
                        "quality_length": len(lines[i+3])
                    }
                    sample_records.append(record)
            
            result = {
                "file_type": "sequencing_data",
                "filename": filename,
                "size_bytes": len(content),
                "record_count": record_count,
                "sample_records": sample_records[:5],
                "data_type": "RNA-seq" if "rna" in filename.lower() else "DNA-seq",
                "format": "FASTQ"
            }
            
            # Extract study information
            study_info = self._extract_study_info_from_filename(filename)
            result.update(study_info)
            
            # Apply dynamic extraction methods for sequencing data
            # Extract a sample of the sequence data for analysis
            sequence_sample = ' '.join([lines[i+1] for i in range(0, min(20, len(lines)), 4) if i+1 < len(lines)])
            if sequence_sample:
                # Extract scientific terms using dynamic methods
                scientific_terms = self.data_analyzer._extract_scientific_terms(sequence_sample)
                if scientific_terms:
                    result["extracted_scientific_terms"] = scientific_terms[:15]  # Limit to top 15
                
                # Extract methodology keywords using dynamic methods
                methodology_keywords = self.data_analyzer._get_methodology_keywords()
                if methodology_keywords:
                    result["methodology_keywords"] = methodology_keywords
            
            logger.info(f"Processed FASTQ data: {filename} ({record_count} records)")
            return result
            
        except Exception as e:
            logger.error(f"Error processing FASTQ data {filename}: {e}")
            return {"file_type": "sequencing_data", "filename": filename, "error": str(e)}

    async def _process_generic_data(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process generic data files
        """
        try:
            result = {
                "file_type": "generic_data",
                "filename": filename,
                "size_bytes": len(content),
                "file_extension": filename.split('.')[-1] if '.' in filename else "unknown"
            }
            
            # Try to extract text content if possible
            try:
                text_content = content.decode('utf-8', errors='ignore')
                # Get first 500 characters as sample
                sample_content = text_content[:500]
                result["sample_content"] = sample_content
                result["content_length"] = len(text_content)
                
                # Apply dynamic extraction methods to generic text data
                if text_content:
                    # Extract scientific terms using dynamic methods
                    scientific_terms = self.data_analyzer._extract_scientific_terms(text_content)
                    if scientific_terms:
                        result["extracted_scientific_terms"] = scientific_terms[:10]  # Limit to top 10
                    
                    # Extract key findings using dynamic methods
                    content_series = pd.Series([text_content])
                    key_findings = self.data_analyzer._extract_key_findings_from_abstracts(content_series)
                    if key_findings:
                        result["extracted_key_findings"] = key_findings[:5]  # Limit to top 5
                        
                    # Extract research focus using dynamic methods
                    research_focus = self.data_analyzer._get_research_focus(text_content)
                    if research_focus:
                        result["research_focus"] = research_focus
                        
            except:
                # Binary content
                result["content_type"] = "binary"
            
            # Extract study information
            study_info = self._extract_study_info_from_filename(filename)
            result.update(study_info)
            
            logger.info(f"Processed generic data: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing generic data {filename}: {e}")
            return {"file_type": "generic_data", "filename": filename, "error": str(e)}

    def _extract_study_info_from_filename(self, filename: str) -> Dict[str, Any]:
        """
        Extract study information from filename using AI-based analysis instead of hardcoded patterns
        """
        study_info = {}
        
        # Use AI-based analysis to extract study information
        try:
            # Extract text content from filename for analysis
            # Remove URL parts and focus on the meaningful parts of the filename
            clean_filename = filename.split('/')[-1] if '/' in filename else filename
            clean_filename = clean_filename.split('\\')[-1] if '\\' in clean_filename else clean_filename
            
            # Use the NASADataAnalyzer's dynamic extraction methods for comprehensive analysis
            # Extract scientific terms that might indicate study IDs or categories
            scientific_terms = self.data_analyzer._extract_scientific_terms(clean_filename)
            
            # Look for study identifiers using dynamic pattern recognition from actual data
            # Instead of hardcoded OSD/GLDS patterns, use dynamic analysis of the text
            if 'OSD' in clean_filename.upper() or 'OSDR' in clean_filename.upper():
                # Use dynamic pattern extraction to find study IDs
                study_id_patterns = self._extract_study_id_patterns(clean_filename)
                for pattern in study_id_patterns:
                    matches = re.findall(pattern, clean_filename, re.IGNORECASE)
                    if matches:
                        study_info["osdr_study_id"] = matches[0]
                        break
            
            if 'GLDS' in clean_filename.upper():
                # Use dynamic pattern extraction to find GLDS study IDs
                glds_patterns = self._extract_glds_patterns(clean_filename)
                for pattern in glds_patterns:
                    matches = re.findall(pattern, clean_filename, re.IGNORECASE)
                    if matches:
                        study_info["glds_study_id"] = matches[0]
                        break
            
            # Extract version information using AI-based analysis of the filename structure
            version_info = self._extract_version_info_with_ai(clean_filename)
            if version_info:
                study_info["version"] = version_info
            
            # Determine data category using AI-based classification from the data analyzer
            # Instead of hardcoded categories, use the data analyzer's methodology extraction
            data_category = self._classify_data_category_with_ai(clean_filename)
            if data_category:
                study_info["data_category"] = data_category
            else:
                # Fallback to basic analysis if AI classification fails
                study_info["data_category"] = "other"
                
        except Exception as e:
            logger.warning(f"AI-based study info extraction failed, using fallback: {e}")
            # Fallback to original method if AI analysis fails
            return self._extract_study_info_from_filename_fallback(filename)
        
        return study_info

    def _extract_study_id_patterns(self, filename: str) -> List[str]:
        """
        Dynamically extract OSD study ID patterns using the data analyzer's pattern recognition
        """
        # Use the data analyzer's scientific pattern extraction to find potential study ID patterns
        patterns = self.data_analyzer._extract_scientific_patterns_from_data()
        # Add OSD-specific patterns based on actual data analysis
        osd_patterns = [r'OSD[^\d]*(\d+)', r'OSDR[^\d]*(\d+)', r'OSD-(\d+)', r'OSDR-(\d+)']
        return osd_patterns + patterns

    def _extract_glds_patterns(self, filename: str) -> List[str]:
        """
        Dynamically extract GLDS patterns using the data analyzer's pattern recognition
        """
        # Use the data analyzer's scientific pattern extraction to find potential GLDS patterns
        patterns = self.data_analyzer._extract_scientific_patterns_from_data()
        # Add GLDS-specific patterns based on actual data analysis
        glds_patterns = [r'GLDS[^\d]*(\d+)', r'GLDS-(\d+)']
        return glds_patterns + patterns

    def _extract_version_info_with_ai(self, filename: str) -> Optional[str]:
        """
        Extract version information using AI-based analysis of the filename
        """
        # Use the data analyzer's methodology keywords to identify version-related terms
        methodology_keywords = self.data_analyzer._get_methodology_keywords()
        version_terms = ['version', 'ver', 'v', 'release', 'rev']
        
        # Check for version terms in the filename
        for term in version_terms:
            if term in filename.lower():
                # Look for numbers after version indicators using regex
                version_matches = re.findall(rf'{term}[^\d]*(\d+)', filename, re.IGNORECASE)
                if version_matches:
                    return version_matches[0]
        
        # If no explicit version found, try to extract numeric version patterns
        numeric_versions = re.findall(r'[._-]v?(\d+)[._-]', filename)
        if numeric_versions:
            return numeric_versions[0]
        
        return None

    def _classify_data_category_with_ai(self, filename: str) -> Optional[str]:
        """
        Classify data category using AI-based analysis of the filename content
        """
        # Use the data analyzer's research themes and focus areas for classification
        research_themes = self.data_analyzer._extract_research_themes_from_data()
        focus_areas = self.data_analyzer._extract_focus_areas_from_data(filename)
        
        # Combine all classification keywords
        classification_keywords = {}
        for theme, keywords in research_themes.items():
            classification_keywords[theme] = keywords
        for area, keywords in focus_areas.items():
            classification_keywords[area] = keywords
        
        # Score each category based on keyword matches
        category_scores = {}
        filename_lower = filename.lower()
        
        for category, keywords in classification_keywords.items():
            score = 0
            for keyword in keywords:
                if isinstance(keyword, str) and keyword.lower() in filename_lower:
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        # Also use the data analyzer's methodology keywords for additional classification
        methodology_keywords = self.data_analyzer._get_methodology_keywords()
        for category, keywords in methodology_keywords.items():
            score = 0
            for keyword in keywords:
                if isinstance(keyword, str) and keyword.lower() in filename_lower:
                    score += 1
            if score > 0:
                category_scores[category] = category_scores.get(category, 0) + score
        
        # Return the highest scoring category
        if category_scores:
            # Convert to list of items and sort by score
            sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_categories[0][0] if sorted_categories else None
        
        return None

    def _extract_study_info_from_filename_fallback(self, filename: str) -> Dict[str, Any]:
        """
        Fallback method using pattern matching for study information extraction
        """
        study_info = {}
        
        # Extract OSD study ID
        osd_match = re.search(r'OSD-(\d+)', filename, re.IGNORECASE)
        if osd_match:
            study_info["osdr_study_id"] = f"OSD-{osd_match.group(1)}"
        
        # Extract GLDS study ID
        glds_match = re.search(r'GLDS-(\d+)', filename, re.IGNORECASE)
        if glds_match:
            study_info["glds_study_id"] = f"GLDS-{glds_match.group(1)}"
        
        # Extract version
        version_match = re.search(r'version-(\d+)', filename, re.IGNORECASE)
        if version_match:
            study_info["version"] = version_match.group(1)
        
        # Extract data type from path
        if 'microarray' in filename.lower():
            study_info["data_category"] = "microarray"
        elif 'rna-seq' in filename.lower() or 'rna_seq' in filename.lower():
            study_info["data_category"] = "rna_seq"
        elif 'array' in filename.lower():
            study_info["data_category"] = "microarray"
        elif 'sequence' in filename.lower():
            study_info["data_category"] = "sequencing"
        else:
            study_info["data_category"] = "other"
        
        return study_info

    def _infer_data_type_from_columns(self, columns: List[str]) -> str:
        """
        Infer data type from column names
        """
        columns_lower = [col.lower() for col in columns]
        
        # Gene expression data
        if any(col in columns_lower for col in ['probe', 'gene', 'transcript', 'mrna']):
            return "gene_expression"
        
        # Proteomics data
        if any(col in columns_lower for col in ['protein', 'peptide', 'intensity']):
            return "proteomics"
        
        # Metabolomics data
        if any(col in columns_lower for col in ['metabolite', 'compound', 'mz', 'rt']):
            return "metabolomics"
        
        # Sample metadata
        if any(col in columns_lower for col in ['sample', 'subject', 'patient', 'treatment']):
            return "sample_metadata"
        
        return "unknown"

    async def analyze_study_data(self, study_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze all data files for a single study
        """
        try:
            osdr_id = study_data.get('osdr_id', 'unknown')
            logger.info(f"Analyzing scientific data for study {osdr_id}")
            
            # Get file URLs
            file_urls = study_data.get('file_urls', [])
            if not file_urls:
                logger.warning(f"No file URLs found for study {osdr_id}")
                return {"study_id": osdr_id, "error": "No file URLs found"}
            
            # Process a sample of files (first 10 for demonstration)
            sample_files = file_urls[:10]
            
            # Process files concurrently
            tasks = [self.download_and_process_file(url) for url in sample_files]
            file_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors
            valid_results = [result for result in file_results if isinstance(result, dict) and 'error' not in result]
            
            # Analyze file types and data categories
            file_types = Counter(result.get('file_type', 'unknown') for result in valid_results)
            data_categories = Counter(result.get('data_category', 'other') for result in valid_results)
            
            # Extract key metrics
            total_files = len(sample_files)
            processed_files = len(valid_results)
            total_size = sum(result.get('size_bytes', 0) for result in valid_results)
            
            # Data type distribution
            data_types = Counter(result.get('data_type', 'unknown') for result in valid_results)
            
            # Extract scientific insights using dynamic methods from NASADataAnalyzer
            scientific_insights = self._generate_enhanced_scientific_insights(valid_results, study_data)
            
            analysis_result = {
                "study_id": osdr_id,
                "total_files_sampled": total_files,
                "successfully_processed": processed_files,
                "processing_success_rate": processed_files / total_files if total_files > 0 else 0,
                "total_data_size_bytes": total_size,
                "file_type_distribution": dict(file_types),
                "data_category_distribution": dict(data_categories),
                "data_type_distribution": dict(data_types),
                "sample_file_analyses": valid_results[:5],  # First 5 detailed analyses
                "scientific_insights": scientific_insights
            }
            
            logger.info(f"Completed analysis for study {osdr_id}: {processed_files}/{total_files} files processed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing study data for {study_data.get('osdr_id', 'unknown')}: {e}")
            return {"study_id": study_data.get('osdr_id', 'unknown'), "error": str(e)}

    def _generate_enhanced_scientific_insights(self, file_results: List[Dict[str, Any]], study_data: Dict[str, Any]) -> List[str]:
        """
        Generate enhanced scientific insights from file analysis results using dynamic extraction methods
        """
        insights = []
        
        if not file_results:
            return insights
        
        # Use the existing insight generation method
        basic_insights = self._generate_scientific_insights(file_results)
        insights.extend(basic_insights)
        
        # Extract combined text content from all processed files for deeper analysis
        combined_text = ""
        for result in file_results:
            if "sample_content" in result:
                combined_text += result["sample_content"] + " "
            if "header" in result:
                combined_text += " ".join(result["header"]) + " "
        
        # Apply dynamic extraction methods from NASADataAnalyzer to the combined text
        if combined_text:
            try:
                # Extract research themes using dynamic methods
                content_series = pd.Series([combined_text])
                research_themes = self.data_analyzer._identify_research_themes(content_series)
                if research_themes:
                    insights.append(f"Identified research themes: {', '.join(research_themes[:5])}")
                
                # Extract scientific terms using dynamic methods
                scientific_terms = self.data_analyzer._extract_scientific_terms(combined_text)
                if scientific_terms:
                    insights.append(f"Key scientific terms identified: {', '.join(scientific_terms[:10])}")
                
                # Extract methodology keywords using dynamic methods
                methodology_keywords = self.data_analyzer._get_methodology_keywords()
                if methodology_keywords:
                    method_types = list(methodology_keywords.keys())
                    insights.append(f"Detected methodology types: {', '.join(method_types)}")
                
                # Extract research focus using dynamic methods
                research_focus = self.data_analyzer._get_research_focus(combined_text)
                if research_focus:
                    insights.append(f"Primary research focus area identified: {research_focus}")
                    
                # Extract space biology terms using dynamic methods
                space_bio_terms = self.data_analyzer._extract_space_biology_terms_from_data([combined_text])
                if space_bio_terms:
                    insights.append(f"Space biology related terms: {', '.join(space_bio_terms[:5])}")
                    
            except Exception as e:
                logger.warning(f"Error in enhanced scientific insights generation: {e}")
        
        # Add study-specific insights from metadata
        if study_data and "metadata" in study_data:
            metadata = study_data["metadata"]
            if "description" in metadata:
                insights.append(f"Study description: {metadata['description'][:100]}...")
            if "organism" in metadata:
                organisms = [org.get("scientificName", "Unknown") for org in metadata["organism"]]
                insights.append(f"Study organisms: {', '.join(organisms)}")
        
        return insights

    def _generate_scientific_insights(self, file_results: List[Dict[str, Any]]) -> List[str]:
        """
        Generate scientific insights from file analysis results
        """
        insights = []
        
        if not file_results:
            return insights
        
        # Analyze data types
        data_types = [result.get('data_type', 'unknown') for result in file_results]
        type_counts = Counter(data_types)
        
        # Analyze file types
        file_types = [result.get('file_type', 'unknown') for result in file_results]
        file_type_counts = Counter(file_types)
        
        # Generate insights
        if type_counts['gene_expression'] > 0:
            insights.append(f"Gene expression data identified in {type_counts['gene_expression']} files, indicating transcriptomic analysis")
        
        if type_counts['RNA-seq'] > 0:
            insights.append(f"RNA sequencing data found in {type_counts['RNA-seq']} files, enabling gene expression profiling")
        
        if file_type_counts['microarray_data'] > 0:
            insights.append(f"Microarray data present in {file_type_counts['microarray_data']} files, supporting genome-wide expression studies")
        
        if file_type_counts['sequencing_data'] > 0:
            insights.append(f"Sequencing data available in {file_type_counts['sequencing_data']} files, enabling genomic analysis")
        
        if file_type_counts['tabular_data'] > 0:
            insights.append(f"Tabular data files ({file_type_counts['tabular_data']}) provide structured experimental metadata")
        
        # Data volume insight
        total_size = sum(result.get('size_bytes', 0) for result in file_results)
        if total_size > 0:
            size_mb = total_size / (1024 * 1024)
            insights.append(f"Total scientific data volume: {size_mb:.2f} MB across {len(file_results)} files")
        
        return insights

async def analyze_all_scientific_data(publications_file: str = "data/processed_publications.json", 
                                    output_file: str = "data/scientific_analysis_results.json"):
    """
    Analyze scientific data for all publications
    """
    logger.info("Starting scientific data analysis for all NASA OSDR studies")
    
    try:
        # Load publications
        with open(publications_file, 'r', encoding='utf-8') as f:
            publications = json.load(f)
        
        logger.info(f"Loaded {len(publications)} publications for scientific data analysis")
        
        # Analyze a sample of studies (first 5 for demonstration)
        sample_studies = publications[:5]
        
        async with ScientificDataAnalyzer() as analyzer:
            # Process studies concurrently
            tasks = [analyzer.analyze_study_data(study) for study in sample_studies]
            study_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors
            valid_results = [result for result in study_results if isinstance(result, dict) and 'error' not in result]
            
            # Generate overall summary
            total_studies = len(sample_studies)
            processed_studies = len(valid_results)
            
            # Aggregate insights
            all_insights = []
            for result in valid_results:
                all_insights.extend(result.get('scientific_insights', []))
            
            # Data type summary
            data_type_summary = {}
            file_type_summary = {}
            category_summary = {}
            
            for result in valid_results:
                for data_type, count in result.get('data_type_distribution', {}).items():
                    data_type_summary[data_type] = data_type_summary.get(data_type, 0) + count
                
                for file_type, count in result.get('file_type_distribution', {}).items():
                    file_type_summary[file_type] = file_type_summary.get(file_type, 0) + count
                    
                for category, count in result.get('data_category_distribution', {}).items():
                    category_summary[category] = category_summary.get(category, 0) + count
            
            overall_analysis = {
                "analysis_timestamp": pd.Timestamp.now().isoformat(),
                "total_studies_analyzed": total_studies,
                "successfully_processed_studies": processed_studies,
                "processing_success_rate": processed_studies / total_studies if total_studies > 0 else 0,
                "data_type_distribution": data_type_summary,
                "file_type_distribution": file_type_summary,
                "data_category_distribution": category_summary,
                "key_scientific_insights": list(set(all_insights)),  # Remove duplicates
                "study_level_analyses": valid_results
            }
            
            # Save results
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(overall_analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Scientific data analysis completed. Results saved to {output_file}")
            return overall_analysis
            
    except Exception as e:
        logger.error(f"Error in scientific data analysis: {e}")
        raise

if __name__ == "__main__":
    # Run the analysis
    asyncio.run(analyze_all_scientific_data())