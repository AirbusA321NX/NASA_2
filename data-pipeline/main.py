from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import os
from datetime import datetime
import logging
from pathlib import Path

from osdr_processor import OSDADataProcessor, Publication
from transformer_analyzer import TransformerAnalyzer
# Import scientific data analyzer
from scientific_data_analyzer import ScientificDataAnalyzer
# Import NASADataAnalyzer for clustering data
from data_analyzer import NASADataAnalyzer

# Import summarization components
try:
    from summarization.summarizer import RetrievalAugmentedSummarizer, SummaryOutput
    SUMMARIZATION_AVAILABLE = True
except ImportError:
    SUMMARIZATION_AVAILABLE = False
    logging.warning("Summarization module not available")

# Import incremental ingest components
try:
    from incremental_ingest import IncrementalIngestManager
    INCREMENTAL_INGEST_AVAILABLE = True
except ImportError:
    INCREMENTAL_INGEST_AVAILABLE = False
    logging.warning("Incremental ingest module not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="NASA Space Biology Knowledge Engine - Data Pipeline",
    description="API for processing and accessing NASA OSDR bioscience data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://frontend:3000", "http://backend:4001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PublicationResponse(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    publication_date: datetime
    doi: str
    osdr_id: str
    keywords: List[str]
    research_area: str
    study_type: str
    organisms: List[str]
    file_urls: List[str]
    metadata: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    research_areas: Optional[List[str]] = Field(None, description="Filter by research areas")
    organisms: Optional[List[str]] = Field(None, description="Filter by organisms")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")
    limit: int = Field(50, description="Maximum number of results")
    offset: int = Field(0, description="Results offset for pagination")

class SummarizationRequest(BaseModel):
    query: str = Field(..., description="Query to summarize")
    top_k: int = Field(20, description="Number of chunks to retrieve")
    max_evidence: int = Field(5, description="Maximum number of evidence bullets")

class IncrementalIngestRequest(BaseModel):
    nslsl_query: str = Field("space biology", description="Search query for NSLSL publications")

class ScientificDataAnalysisRequest(BaseModel):
    study_id: Optional[str] = Field(None, description="Specific study ID to analyze (if None, analyze all)")
    limit: int = Field(5, description="Maximum number of studies to analyze")
    sample_files_per_study: int = Field(10, description="Number of files to sample per study")

class ProcessingStatus(BaseModel):
    status: str
    message: str
    progress: Optional[float] = None
    total_publications: Optional[int] = None
    processed_publications: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Global state
processing_status = ProcessingStatus(status="idle", message="Ready to start processing")
publications_cache: List[Dict[str, Any]] = []

# Initialize transformer analyzer
transformer_analyzer = TransformerAnalyzer()

# Utility functions
def load_publications_from_file(file_path: str = "data/processed_publications.json") -> List[Dict[str, Any]]:
    """Load publications from file"""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check if we have real data
                if not data or len(data) == 0:
                    logger.error("Publication file is empty or contains no data")
                    # Don't generate fallback data, return empty list to trigger real data fetch
                    return []
                return data
        except Exception as e:
            logger.error(f"Error loading publications: {e}")
            # Don't generate fallback data, return empty list to trigger real data fetch
            return []
    else:
        logger.info("Publication file not found, will fetch real NASA OSDR data when processing is triggered")
        return []  # Return empty list instead of generating fallback data

def search_publications(publications: List[Dict[str, Any]], request: SearchRequest) -> List[Dict[str, Any]]:
    """Search publications based on request parameters"""
    results = publications.copy()
    
    # Text search in title, abstract, and keywords
    if request.query:
        query_lower = request.query.lower()
        results = [
            pub for pub in results
            if (query_lower in pub.get('title', '').lower() or
                query_lower in pub.get('abstract', '').lower() or
                any(query_lower in keyword.lower() for keyword in pub.get('keywords', [])))
        ]
    
    # Filter by research areas
    if request.research_areas:
        results = [
            pub for pub in results
            if pub.get('research_area') in request.research_areas
        ]
    
    # Filter by organisms
    if request.organisms:
        results = [
            pub for pub in results
            if any(organism in request.organisms for organism in pub.get('organisms', []))
        ]
    
    # Filter by date range
    if request.date_from:
        results = [
            pub for pub in results
            if datetime.fromisoformat(pub.get('publication_date', '').replace('Z', '+00:00')) >= request.date_from
        ]
    
    if request.date_to:
        results = [
            pub for pub in results
            if datetime.fromisoformat(pub.get('publication_date', '').replace('Z', '+00:00')) <= request.date_to
        ]
    
    # Pagination
    return results[request.offset:request.offset + request.limit]

def classify_file_type(file_url, file_name=""):
    """Classify file type based on extension and content"""
    file_type = "Unknown"
    experiment_type = "Unknown"
    
    if not file_url and not file_name:
        return file_type, experiment_type
    
    # Use file name if available, otherwise extract from URL
    name_to_check = file_name if file_name else file_url.lower()
    
    # Determine file type from extension
    if any(ext in name_to_check for ext in ['.csv', '.tsv', '.txt']):
        file_type = "Tabular"
        experiment_type = "Data Table"
    elif any(ext in name_to_check for ext in ['.json', '.xml']):
        file_type = "Metadata"
        experiment_type = "Study Metadata"
    elif any(ext in name_to_check for ext in ['.pdf']):
        file_type = "Document"
        experiment_type = "Research Paper"
    elif any(ext in name_to_check for ext in ['.fastq', '.fq', '.bam', '.sam']):
        file_type = "Omics"
        experiment_type = "Sequencing Data"
    elif any(ext in name_to_check for ext in ['.h5', '.hdf5']):
        file_type = "Omics"
        experiment_type = "Expression Data"
    elif any(ext in name_to_check for ext in ['.fasta', '.fa', '.fna']):
        file_type = "Omics"
        experiment_type = "Sequence Data"
    elif any(ext in name_to_check for ext in ['.tif', '.tiff', '.png', '.jpg', '.jpeg']):
        file_type = "Image"
        experiment_type = "Microscopy Image"
    elif any(ext in name_to_check for ext in ['.zip', '.tar', '.tar.gz', '.tgz']):
        file_type = "Archive"
        experiment_type = "Compressed Data"
    
    return file_type, experiment_type

def extract_species_from_metadata(metadata):
    """Extract species information from metadata"""
    species = "Unknown"
    
    # Look for organism information in various metadata fields
    organism_fields = ['organism', 'organisms', 'species', 'scientificName']
    
    for field in organism_fields:
        if field in metadata:
            organism_data = metadata[field]
            if isinstance(organism_data, list) and organism_data:
                species = organism_data[0].get('scientificName', 'Unknown') if isinstance(organism_data[0], dict) else str(organism_data[0])
                break
            elif isinstance(organism_data, str):
                species = organism_data
                break
    
    # If still unknown, return as is without hardcoded patterns
    # Removed hardcoded species detection to prevent hardcoding
    
    return species

def extract_mission_info(metadata):
    """Extract mission information from metadata"""
    mission = "Unknown"
    
    # Look for mission-related information
    mission_fields = ['space_program', 'mission', 'platform', 'study_type']
    
    for field in mission_fields:
        if field in metadata:
            mission_data = metadata[field]
            if isinstance(mission_data, str):
                mission = mission_data
                break
    
    # If still unknown, return as is without hardcoded patterns
    # Removed hardcoded mission detection to prevent hardcoding
    
    return mission

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "NASA Space Biology Knowledge Engine - Data Pipeline",
        "version": "1.0.0",
        "description": "API for processing and accessing NASA OSDR bioscience data",
        "endpoints": {
            "GET /health": "Health check",
            "GET /status": "Processing status",
            "POST /process": "Start data processing",
            "POST /search": "Search publications",
            "GET /publications": "Get all publications",
            "GET /statistics": "Get dataset statistics",
            "GET /osdr-files": "Get all OSDR files with metadata",
            "GET /osdr-files/{study_id}": "Get files for a specific OSDR study",
            "POST /analyze": "Analyze data using transformer-based AI model",
            "POST /summarize": "Generate retrieval-augmented summary for a query",
            "POST /incremental-ingest": "Run incremental ingest with change detection",
            "POST /scientific-data-analysis": "Analyze actual scientific data files from NASA OSDR studies"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/status", response_model=ProcessingStatus)
async def get_processing_status():
    """Get current processing status"""
    return processing_status

@app.post("/process")
async def start_processing(background_tasks: BackgroundTasks):
    """Start processing OSDR data"""
    global processing_status
    
    if processing_status.status == "processing":
        raise HTTPException(status_code=400, detail="Processing already in progress")
    
    processing_status.status = "processing"
    processing_status.message = "Starting data processing..."
    processing_status.started_at = datetime.now()
    processing_status.completed_at = None
    
    # Add background task for real data only
    background_tasks.add_task(process_osdr_data)
    
    return {"message": "Processing started", "status": processing_status.status}

@app.post("/search")
async def search_publications_endpoint(request: SearchRequest):
    """Search publications with filters"""
    global publications_cache
    
    # Load publications if not cached
    if not publications_cache:
        publications_cache = load_publications_from_file()
    
    if not publications_cache:
        raise HTTPException(status_code=404, detail="No publications found. Please process data first.")
    
    results = search_publications(publications_cache, request)
    
    return {
        "query": request.query,
        "total_results": len(results),
        "results": results,
        "pagination": {
            "limit": request.limit,
            "offset": request.offset,
            "has_more": len(results) == request.limit
        }
    }

@app.get("/publications")
async def get_publications(
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Results offset")
):
    """Get all publications with pagination"""
    global publications_cache
    
    # Load publications if not cached
    if not publications_cache:
        publications_cache = load_publications_from_file()
    
    if not publications_cache:
        return {"publications": [], "total": 0}
    
    # Pagination
    results = publications_cache[offset:offset + limit]
    
    return {
        "publications": results,
        "total": len(publications_cache),
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": len(publications_cache) > offset + limit
        }
    }

@app.get("/statistics")
async def get_statistics():
    """Get dataset statistics"""
    global publications_cache
    
    # Load publications if not cached
    if not publications_cache:
        try:
            publications_cache = load_publications_from_file()
        except (FileNotFoundError, ValueError, ConnectionError) as e:
            # If there's an error loading real data, return an error response
            logger.error(f"Error loading real NASA OSDR data: {e}")
            return JSONResponse(
                status_code=503,
                content={"error": "Error fetching real NASA OSDR data", "message": str(e)}
            )
    
    if not publications_cache:
        # If no publications found, return error instead of fallback data
        return JSONResponse(
            status_code=503,
            content={"error": "Error fetching real NASA OSDR data", "message": "No real NASA OSDR data available. Please trigger data processing to fetch real data from NASA OSDR repository."}
        )
    
    # Calculate statistics
    total_publications = len(publications_cache)
    research_areas = {}
    organisms = set()
    years = {}
    authors = set()
    
    # Track the earliest and latest years for 30+ year calculation
    earliest_year = None
    latest_year = None
    
    for pub in publications_cache:
        # Research areas
        area = pub.get('research_area', 'Unknown')
        research_areas[area] = research_areas.get(area, 0) + 1
        
        # Organisms - properly extract from nested structure
        organisms_list = pub.get('organisms', [])
        if not organisms_list and 'metadata' in pub:
            # Try to extract from metadata
            metadata = pub.get('metadata', {})
            if 'organism' in metadata:
                organism_data = metadata['organism']
                if isinstance(organism_data, list):
                    for org in organism_data:
                        if isinstance(org, dict) and 'scientificName' in org:
                            organisms_list.append(org['scientificName'])
                        elif isinstance(org, str):
                            organisms_list.append(org)
                elif isinstance(organism_data, dict) and 'scientificName' in organism_data:
                    organisms_list.append(organism_data['scientificName'])
                elif isinstance(organism_data, str):
                    organisms_list.append(organism_data)
        
        # If still no organisms, try direct metadata fields
        if not organisms_list:
            # Check for organism in various metadata fields
            organism_fields = ['organism', 'organisms', 'species', 'scientificName']
            for field in organism_fields:
                if field in pub:
                    org_data = pub[field]
                    if isinstance(org_data, list):
                        organisms_list.extend(org_data)
                    elif isinstance(org_data, str):
                        organisms_list.append(org_data)
                    elif isinstance(org_data, dict) and 'scientificName' in org_data:
                        organisms_list.append(org_data['scientificName'])
        
        organisms.update(organisms_list)
        
        # Years - track for 30+ year calculation
        try:
            pub_date = datetime.fromisoformat(pub.get('publication_date', ''))
            year = pub_date.year
            years[year] = years.get(year, 0) + 1
            
            # Update earliest and latest years
            if earliest_year is None or year < earliest_year:
                earliest_year = year
            if latest_year is None or year > latest_year:
                latest_year = year
        except Exception as e:
            logger.warning(f"Error parsing publication date: {e}")
            pass
        
        # Authors
        authors.update(pub.get('authors', []))
    
    # Calculate year range for 30+ years
    year_range = "N/A"
    if earliest_year is not None and latest_year is not None:
        year_range = f"{earliest_year} - {latest_year}"
    
    return {
        "total_publications": total_publications,
        "unique_organisms": len(organisms),
        "unique_authors": len(authors),
        "research_areas": len(research_areas),
        "year_range": year_range,
        "top_research_areas": dict(sorted(research_areas.items(), key=lambda x: x[1], reverse=True)[:10]),
        "publications_by_year": dict(sorted(years.items())),
        "top_organisms": list(organisms)[:20]
    }

@app.get("/osdr-files")
async def get_osdr_files(limit: int = Query(100, description="Maximum number of files to return", ge=1, le=1000), 
                        offset: int = Query(0, description="Number of files to skip", ge=0)):
    """Get all OSDR files with metadata, classified by type and experiment, with pagination support"""
    global publications_cache
    
    logger.info("Fetching OSDR files endpoint called")
    
    # Load publications if not cached
    if not publications_cache:
        logger.info("No cached publications found, attempting to load from file")
        publications_cache = load_publications_from_file()
    
    if not publications_cache:
        logger.warning("No publications data available, returning empty list")
        return []
    
    # Extract file information from publications
    files = []
    file_ids = set()  # To avoid duplicates
    
    logger.info(f"Processing {len(publications_cache)} publications for file extraction")
    
    for pub in publications_cache:
        osdr_id = pub.get('osdr_id', '')
        if not osdr_id:
            continue
            
        metadata = pub.get('metadata', {})
        
        # Extract species and mission info
        species = extract_species_from_metadata(metadata)
        mission = extract_mission_info(metadata)
        
        # Extract file information from each publication
        file_urls = pub.get('file_urls', [])
        
        # Also check for datafiles in the metadata
        datafiles = metadata.get('datafiles', [])
        
        # Process file_urls
        for i, file_url in enumerate(file_urls):
            # Skip empty URLs
            if not file_url:
                continue
                
            # Create a unique file ID
            file_id = f"{osdr_id}_file_{i+1}"
            
            # Skip if we've already added this file
            if file_id in file_ids:
                continue
                
            file_ids.add(file_id)
            
            # Extract filename from URL
            file_name = f"File {i+1}"
            if file_url:
                from urllib.parse import urlparse
                parsed_url = urlparse(file_url)
                path_parts = parsed_url.path.split('/')
                if path_parts and path_parts[-1]:
                    file_name = path_parts[-1]
            
            # Classify file type
            file_type, experiment_type = classify_file_type(file_url, file_name)
            
            files.append({
                "id": file_id,
                "name": file_name,
                "type": file_type,
                "experiment_type": experiment_type,
                "size": "Unknown",
                "date": pub.get('publication_date', ''),
                "description": f"File associated with {osdr_id} study",
                "url": file_url,
                "study_id": osdr_id,
                "species": species,
                "mission": mission
            })
        
        # Process datafiles from metadata
        for i, datafile in enumerate(datafiles):
            file_url = datafile.get('file_url', '')
            if not file_url:
                continue
                
            # Create a unique file ID
            file_id = f"{osdr_id}_datafile_{i+1}"
            
            # Skip if we've already added this file
            if file_id in file_ids:
                continue
                
            file_ids.add(file_id)
            
            # Extract filename from URL
            file_name = f"Data File {i+1}"
            if file_url:
                from urllib.parse import urlparse
                parsed_url = urlparse(file_url)
                path_parts = parsed_url.path.split('/')
                if path_parts and path_parts[-1]:
                    file_name = path_parts[-1]
            
            # Get file type from datafile metadata or classify
            file_type = datafile.get('file_type', 'Unknown')
            experiment_type = "Unknown"
            
            # If file_type is still unknown, classify it
            if file_type == "Unknown":
                file_type, experiment_type = classify_file_type(file_url, file_name)
            else:
                # Infer experiment type from file type
                if file_type == "NASA Research Data":
                    experiment_type = "Space Biology Experiment"
            
            files.append({
                "id": file_id,
                "name": file_name,
                "type": file_type,
                "experiment_type": experiment_type,
                "size": datafile.get('file_size', 'Unknown'),
                "date": pub.get('publication_date', ''),
                "description": datafile.get('description', f"Data file associated with {osdr_id} study"),
                "url": file_url,
                "study_id": osdr_id,
                "species": species,
                "mission": mission
            })
    
    # Apply pagination
    total_files = len(files)
    paginated_files = files[offset:offset + limit]
    
    logger.info(f"Returning {len(paginated_files)} OSDR files (limited from {total_files} total files)")
    return {
        "files": paginated_files,
        "total": total_files,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total_files
    }

@app.get("/osdr-files/{study_id}")
async def get_osdr_files_by_study(study_id: str):
    """Get files for a specific OSDR study, classified by type and experiment"""
    global publications_cache
    
    logger.info(f"Fetching OSDR files for study: {study_id}")
    
    # Load publications if not cached
    if not publications_cache:
        logger.info("No cached publications found, attempting to load from file")
        publications_cache = load_publications_from_file()
    
    if not publications_cache:
        logger.warning("No publications data available, returning empty list")
        return []
    
    # Find the publication with the matching study ID
    target_pub = None
    for pub in publications_cache:
        if pub.get('osdr_id', '') == study_id:
            target_pub = pub
            break
    
    if not target_pub:
        logger.warning(f"No publication found for study ID: {study_id}")
        return []
    
    # Extract file information from the publication
    files = []
    metadata = target_pub.get('metadata', {})
    
    # Extract species and mission info
    species = extract_species_from_metadata(metadata)
    mission = extract_mission_info(metadata)
    
    # Process file_urls
    file_urls = target_pub.get('file_urls', [])
    for i, file_url in enumerate(file_urls):
        # Skip empty URLs
        if not file_url:
            continue
            
        # Extract filename from URL
        file_name = f"File {i+1}"
        if file_url:
            from urllib.parse import urlparse
            parsed_url = urlparse(file_url)
            path_parts = parsed_url.path.split('/')
            if path_parts and path_parts[-1]:
                file_name = path_parts[-1]
        
        # Classify file type
        file_type, experiment_type = classify_file_type(file_url, file_name)
        
        files.append({
            "id": f"{study_id}_file_{i+1}",
            "name": file_name,
            "type": file_type,
            "experiment_type": experiment_type,
            "size": "Unknown",
            "date": target_pub.get('publication_date', ''),
            "description": f"File associated with {study_id} study",
            "url": file_url,
            "study_id": study_id,
            "species": species,
            "mission": mission
        })
    
    # Process datafiles from metadata
    datafiles = metadata.get('datafiles', [])
    for i, datafile in enumerate(datafiles):
        file_url = datafile.get('file_url', '')
        if not file_url:
            continue
            
        # Extract filename from URL
        file_name = f"Data File {i+1}"
        if file_url:
            from urllib.parse import urlparse
            parsed_url = urlparse(file_url)
            path_parts = parsed_url.path.split('/')
            if path_parts and path_parts[-1]:
                file_name = path_parts[-1]
        
        # Get file type from datafile metadata or classify
        file_type = datafile.get('file_type', 'Unknown')
        experiment_type = "Unknown"
        
        # If file_type is still unknown, classify it
        if file_type == "Unknown":
            file_type, experiment_type = classify_file_type(file_url, file_name)
        else:
            # Infer experiment type from file type
            if file_type == "NASA Research Data":
                experiment_type = "Space Biology Experiment"
        
        files.append({
            "id": f"{study_id}_datafile_{i+1}",
            "name": file_name,
            "type": file_type,
            "experiment_type": experiment_type,
            "size": "Unknown",
            "date": target_pub.get('publication_date', ''),
            "description": f"Data file associated with {study_id} study",
            "url": file_url,
            "study_id": study_id,
            "species": species,
            "mission": mission
        })
    
    logger.info(f"Returning {len(files)} files for study {study_id}")
    return files

@app.post("/analyze")
async def analyze_data(data: dict):
    """Analyze NASA OSDR data using transformer-based AI model"""
    try:
        logger.info("=" * 60)
        logger.info("AI Engine: Starting comprehensive data analysis")
        logger.info("=" * 60)
        
        # Log data size information
        data_size = len(data.get('publications', [])) if isinstance(data, dict) else len(data) if isinstance(data, list) else 0
        logger.info(f"AI Engine: Processing {data_size} publications")
        logger.info("AI Engine: Initializing transformer-based analysis engine...")
        
        # Show progress visualization header
        logger.info("-" * 60)
        logger.info("AI Engine: Analysis Progress Visualization")
        logger.info("-" * 60)
        
        # Perform analysis with progress tracking
        results = transformer_analyzer.analyze_data(data)
        
        # Show completion
        logger.info("-" * 60)
        logger.info("AI Engine: Analysis Progress Visualization - COMPLETE")
        logger.info("-" * 60)
        
        # Add clustering data from NASADataAnalyzer if not already present
        # Only add clustering data if we have publications data to analyze
        if data and len(data) > 0:
            try:
                # Initialize NASADataAnalyzer to get clustering data
                data_analyzer = NASADataAnalyzer()
                # Load data for analysis (this will use the data passed in)
                if data_analyzer.load_data().empty:
                    # If no cached data, create a temporary DataFrame from the input data
                    import pandas as pd
                    # Convert input data to DataFrame format expected by NASADataAnalyzer
                    temp_data = []
                    if 'publications' in data:
                        temp_data = data['publications']
                    elif 'data' in data and 'publications' in data['data']:
                        temp_data = data['data']['publications']
                    elif isinstance(data, list):
                        temp_data = data
                    
                    if temp_data:
                        data_analyzer.df = pd.DataFrame(temp_data)
                        # Add required columns if missing
                        required_columns = ['authors', 'organisms', 'keywords', 'abstract', 'title', 'publication_date']
                        for col in required_columns:
                            if col not in data_analyzer.df.columns:
                                data_analyzer.df[col] = data_analyzer.df.get(col, [])
                        
                        # Perform clustering analysis
                        clustering_data = data_analyzer.perform_clustering_analysis()
                        if clustering_data:
                            results['clustering'] = clustering_data
                            logger.info("AI Engine: Added clustering analysis data")
            except Exception as e:
                logger.warning(f"Failed to add clustering data: {e}")
                # Continue without clustering data rather than failing completely
        
        logger.info("=" * 60)
        logger.info("AI Engine: Data analysis completed successfully")
        logger.info("=" * 60)
        
        return {"success": True, "data": results}
    except Exception as e:
        logger.error(f"AI Engine: Transformer analysis failed: {e}")
        logger.error("=" * 60)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/summarize")
async def summarize_query(request: SummarizationRequest):
    """Generate a retrieval-augmented summary for a query"""
    if not SUMMARIZATION_AVAILABLE:
        raise HTTPException(status_code=501, detail="Summarization module not available")
    
    # This import is only used if the module is available
    from summarization.summarizer import RetrievalAugmentedSummarizer
    
    try:
        # Database configuration
        db_config = {
            'host': os.getenv('DATABASE_HOST', 'postgres'),
            'port': os.getenv('DATABASE_PORT', '5432'),
            'user': os.getenv('DATABASE_USER', 'postgres'),
            'password': os.getenv('DATABASE_PASSWORD', 'password'),
            'database': os.getenv('DATABASE_NAME', 'nasa_biology')
        }
        
        # Generate summary using the summarization module
        async with RetrievalAugmentedSummarizer(db_config) as summarizer:
            summary = await summarizer.summarize_query(
                request.query,
                top_k=request.top_k,
                max_evidence=request.max_evidence
            )
            
            # Convert to dictionary for JSON serialization
            from summarization.summarizer import asdict
            summary_dict = {
                "insight": summary.insight,
                "evidence_bullets": summary.evidence_bullets,
                "research_gaps": summary.research_gaps,
                "query": summary.query,
                "timestamp": summary.timestamp,
                "model_fingerprint": summary.model_fingerprint
            }
            
            return {"success": True, "summary": summary_dict}
            
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/incremental-ingest")
async def run_incremental_ingest(request: IncrementalIngestRequest):
    """Run incremental ingest with change detection"""
    if not INCREMENTAL_INGEST_AVAILABLE:
        raise HTTPException(status_code=501, detail="Incremental ingest module not available")
    
    # This import is only used if the module is available
    from incremental_ingest import IncrementalIngestManager
    
    try:
        # Run incremental ingest
        manager = IncrementalIngestManager()
        results = await manager.run_incremental_ingest(request.nslsl_query)
        
        return {"success": True, "results": results}
        
    except Exception as e:
        logger.error(f"Incremental ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Incremental ingest failed: {str(e)}")

@app.post("/scientific-data-analysis")
async def analyze_scientific_data(request: ScientificDataAnalysisRequest):
    """Analyze actual scientific data files from NASA OSDR studies"""
    global publications_cache
    
    try:
        logger.info("Starting scientific data analysis...")
        
        # Load publications if not cached
        if not publications_cache:
            publications_cache = load_publications_from_file()
        
        if not publications_cache:
            raise HTTPException(status_code=404, detail="No publications found. Please process data first.")
        
        # Filter publications based on request
        if request.study_id:
            # Analyze specific study
            target_publications = [
                pub for pub in publications_cache 
                if pub.get('osdr_id') == request.study_id
            ]
            if not target_publications:
                raise HTTPException(status_code=404, detail=f"Study {request.study_id} not found.")
        else:
            # Analyze a sample of studies
            target_publications = publications_cache[:request.limit]
        
        # Run scientific data analysis
        async with ScientificDataAnalyzer() as analyzer:
            # Process studies concurrently
            tasks = [
                analyzer.analyze_study_data(study) 
                for study in target_publications
            ]
            study_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors
            valid_results = [
                result for result in study_results 
                if isinstance(result, dict) and 'error' not in result
            ]
            
            # Generate overall summary
            total_studies = len(target_publications)
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
                "analysis_timestamp": datetime.now().isoformat(),
                "total_studies_analyzed": total_studies,
                "successfully_processed_studies": processed_studies,
                "processing_success_rate": processed_studies / total_studies if total_studies > 0 else 0,
                "data_type_distribution": data_type_summary,
                "file_type_distribution": file_type_summary,
                "data_category_distribution": category_summary,
                "key_scientific_insights": list(set(all_insights)),  # Remove duplicates
                "study_level_analyses": valid_results
            }
            
            logger.info(f"Scientific data analysis completed. {processed_studies}/{total_studies} studies processed.")
            return {"success": True, "results": overall_analysis}
            
    except Exception as e:
        logger.error(f"Scientific data analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scientific data analysis failed: {str(e)}")

# Background tasks
async def process_osdr_data():
    """Background task to process OSDR data"""
    global processing_status, publications_cache
    
    try:
        # Use real OSDR processor only (no api_key parameter needed)
        async with OSDADataProcessor() as processor:
            processing_status.message = "Processing OSDR data..."
            publications = await processor.process_all_studies(
                output_path=str(Path("data/processed_publications.json"))
            )
            
            if publications:
                publications_cache = [
                    {
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
                    for pub in publications
                ]
                
                processing_status.status = "completed"
                processing_status.message = f"Successfully processed {len(publications)} publications"
                processing_status.total_publications = len(publications)
                processing_status.processed_publications = len(publications)
            else:
                processing_status.status = "error"
                processing_status.message = "No publications were processed"
                
    except Exception as e:
        logger.error(f"Error processing OSDR data: {e}")
        processing_status.status = "error"
        processing_status.message = f"Error: {str(e)}"
    
    processing_status.completed_at = datetime.now()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Load cached data on startup"""
    global publications_cache
    
    logger.info("Starting NASA Space Biology Data Pipeline API...")
    
    # Try to load existing data
    try:
        publications_cache = load_publications_from_file()
        if publications_cache:
            logger.info(f"Loaded {len(publications_cache)} publications from cache")
        else:
            logger.info("No cached data found. Use /process to fetch real NASA OSDR data")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        publications_cache = []
        logger.info("Starting with empty cache. Use /process to fetch real NASA OSDR data")

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # Check if a port argument is provided
    port = int(os.getenv('PORT', 8003))  # default port from env or 8003
    host = os.getenv('HOST', '0.0.0.0')
    
    if "--port" in sys.argv:
        try:
            port_index = sys.argv.index("--port") + 1
            if port_index < len(sys.argv):
                port = int(sys.argv[port_index])
        except (ValueError, IndexError):
            print("Invalid port specified, using default port from env or 8003")
    
    uvicorn.run(app, host=host, port=port)
