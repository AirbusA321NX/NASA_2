# NASA Space Biology Knowledge Engine - System Architecture

## Overview

This document outlines the system architecture for a production-grade agentic system that processes NASA OSDR and NSLSL data to create a comprehensive knowledge engine for space biology research.

## System Components

### 1. Data Ingestion Layer

#### OSDR Crawler
- **Purpose**: Enumerate study records, file metadata, and data URLs from NASA's Open Science Data Repository
- **Technology**: Python-based crawler using aiohttp for asynchronous requests
- **Endpoints**: 
  - Study records: `http://nasa-osdr.s3-website-us-west-2.amazonaws.com`
  - File metadata: Direct S3 access when available
  - Data URLs: Extracted from study metadata

#### NSLSL Harvester
- **Purpose**: Harvest publication records and DOIs from NASA Scientific and Technical Information (STI) database
- **Technology**: Python-based harvester using requests library
- **Endpoints**:
  - Search endpoint: `https://ntrs.nasa.gov/api/citations`
  - Metadata endpoint: `https://ntrs.nasa.gov/api/citations/{citation_id}`

### 2. Data Storage Layer

#### PostgreSQL Database
- **Purpose**: Store normalized catalog of publications with metadata
- **Schema**:
  - `paper_id` (Primary Key)
  - `title`
  - `authors` (JSON array)
  - `year`
  - `doi`
  - `osd_id`
  - `nslsl_id`
  - `pdf_url`
  - `licences` (JSON array)

#### MinIO Object Storage
- **Purpose**: Persist raw PDFs with immutable provenance fields
- **Features**:
  - Immutable storage with content-addressable identifiers
  - Provenance tracking (source URL, fetch timestamp, checksum)
  - S3-compatible API for easy integration

### 3. Document Processing Pipeline

#### GROBID Service
- **Purpose**: Extract TEI/XML with section boundaries from PDFs
- **Technology**: Dockerized GROBID service
- **Output**: Structured XML with Title/Abstract/Intro/Methods/Results/Conclusions sections

#### Post-processing Engine
- **Purpose**: Normalize section names and strip references/figures
- **Technology**: Python-based rules engine
- **Functions**:
  - Section name normalization
  - Reference removal
  - Figure/table caption extraction
  - Token offset calculation

#### Chunk Storage
- **Purpose**: Store canonical section chunks with token offsets
- **Database**: PostgreSQL with JSON fields
- **Schema**:
  - `chunk_id` (Primary Key)
  - `paper_id` (Foreign Key)
  - `section`
  - `content`
  - `byte_range` (start, end)
  - `token_range` (start, end)

### 4. Semantic Analysis Layer

#### Sentence Transformer Service
- **Purpose**: Generate dense embeddings for each chunk
- **Model**: `all-mpnet-base-v2`
- **Technology**: Python service with GPU/CPU support
- **Output**: Normalized vectors (768 dimensions)

#### Vector Store
- **Purpose**: Enable subsecond semantic retrieval
- **Options**: FAISS or Milvus Lite
- **Schema**:
  - `vector_id` (Primary Key)
  - `paper_id` (Foreign Key)
  - `section`
  - `source_sentence`
  - `embedding` (768-dim vector)

### 5. Knowledge Extraction Layer

#### NER Engine
- **Purpose**: Extract entities from Results/Conclusions chunks
- **Technology**: SciSpacy with rule-based extensions
- **Entities**:
  - Organism (NCBI taxon)
  - Phenotype
  - Assay
  - Platform
  - Outcome

#### Normalization Service
- **Purpose**: Normalize entities to controlled vocabularies
- **Vocabularies**:
  - NCBI Taxonomy
  - Gene Ontology (GO)
  - EDAM Ontology
  - Ontology for Biomedical Investigations (OBI)

#### Knowledge Graph Store
- **Purpose**: Store triples with provenance
- **Technology**: Neo4j Community Edition
- **Schema**:
  - Nodes: Entities with type and normalized ID
  - Relationships: Predicates with confidence scores
  - Properties: Provenance (sentence IDs, source paper)

### 6. Validation Layer

#### Precision Checker
- **Purpose**: Validate KG with automatic precision checks
- **Method**: Hold-out sample evaluation
- **Metrics**: Precision, recall, F1-score

#### QA Service
- **Purpose**: Compute retrieval nDCG on gold queries
- **Method**: Standard information retrieval evaluation
- **Metrics**: nDCG@5, nDCG@10, MAP

### 7. Summarization Engine

#### Retrieval-Augmented Generator
- **Purpose**: Generate evidence-backed summaries
- **Components**:
  - Chunk retrieval from vector store
  - Evidence ranking by section weight
  - Factual compression generator

#### Output Generator
- **Format**:
  - One-line insight
  - 3-5 evidence-backed bullets (with paper_id + sentence snippet + link)
  - Suggested research gaps

#### Audit Logger
- **Purpose**: Log all LLM prompts, model fingerprints, and evidence snippets
- **Technology**: Structured logging with JSON
- **Fields**:
  - Timestamp
  - Prompt
  - Model fingerprint
  - Evidence snippets
  - Generated output

### 8. Infrastructure Layer

#### Containerization
- **Technology**: Docker Compose
- **Services**:
  - Data ingestion workers
  - PostgreSQL database
  - MinIO object storage
  - GROBID service
  - Vector store
  - Neo4j database
  - Web API
  - Frontend UI

#### Incremental Ingest
- **Purpose**: Detect changes in OSDR/NSLSL APIs
- **Method**: ETag comparison and timestamp checking
- **Technology**: Scheduled workers with state persistence

#### Monitoring
- **Components**:
  - Health checks for all services
  - Performance metrics (latency, throughput)
  - Error tracking and alerting

## Data Flow

1. **Ingestion**: OSDR Crawler and NSLSL Harvester fetch metadata and URLs
2. **Storage**: Metadata stored in PostgreSQL, PDFs stored in MinIO
3. **Processing**: PDFs processed through GROBID, chunks extracted and stored
4. **Analysis**: Chunks embedded and stored in vector store
5. **Extraction**: Entities and relationships extracted, stored in Neo4j
6. **Validation**: KG validated with precision checks
7. **Summarization**: User queries processed through retrieval-augmented generation
8. **Output**: Evidence-backed summaries with research gaps identification

## Deployment Architecture

### Single VM Deployment
- **Resource Requirements**: 16GB RAM, 4 CPU cores, 100GB storage
- **Services**:
  - Docker Compose orchestration
  - All components running as containers
  - Shared network for inter-service communication
  - Persistent volumes for data storage

### Scalability Considerations
- **Horizontal Scaling**: Worker processes for ingestion and processing
- **Vertical Scaling**: Resource allocation for compute-intensive tasks
- **Caching**: Redis for frequently accessed data
- **Load Balancing**: Reverse proxy for API services

## Security Considerations

- **Data Integrity**: Immutable storage with checksums
- **Access Control**: Role-based access to services
- **Encryption**: TLS for data in transit, encryption at rest for sensitive data
- **Audit Trail**: Comprehensive logging of all operations

## Monitoring and Maintenance

- **Health Checks**: Automated service health verification
- **Alerting**: Notification system for service failures
- **Backup**: Regular database and storage backups
- **Updates**: Automated update mechanism for containers