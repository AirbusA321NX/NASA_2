-- PostgreSQL Schema for NASA Space Biology Knowledge Engine

-- Create database
CREATE DATABASE nasa_biology;


-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core publications table
CREATE TABLE publications (
    paper_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    authors JSONB, -- Array of author names
    year INTEGER,
    doi TEXT UNIQUE,
    osd_id TEXT, -- OSDR study ID
    nslsl_id TEXT, -- NSLSL citation ID
    pdf_url TEXT,
    licences JSONB, -- Array of license information
    abstract TEXT,
    keywords JSONB, -- Array of keywords
    publication_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_publications_doi ON publications(doi);
CREATE INDEX idx_publications_osd_id ON publications(osd_id);
CREATE INDEX idx_publications_nslsl_id ON publications(nslsl_id);
CREATE INDEX idx_publications_year ON publications(year);
CREATE INDEX idx_publications_title ON publications USING gin(to_tsvector('english', title));
CREATE INDEX idx_publications_abstract ON publications USING gin(to_tsvector('english', abstract));

-- File storage metadata
CREATE TABLE file_metadata (
    file_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES publications(paper_id),
    file_url TEXT NOT NULL,
    file_type TEXT, -- PDF, XML, CSV, etc.
    file_size BIGINT, -- Size in bytes
    checksum TEXT, -- SHA256 checksum
    minio_path TEXT, -- Path in MinIO storage
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for file metadata
CREATE INDEX idx_file_metadata_paper_id ON file_metadata(paper_id);
CREATE INDEX idx_file_metadata_file_url ON file_metadata(file_url);

-- Document sections extracted by GROBID
CREATE TABLE document_sections (
    section_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES publications(paper_id),
    section_type TEXT NOT NULL, -- title, abstract, introduction, methods, results, conclusions
    content TEXT NOT NULL,
    byte_start INTEGER,
    byte_end INTEGER,
    token_start INTEGER,
    token_end INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document sections
CREATE INDEX idx_document_sections_paper_id ON document_sections(paper_id);
CREATE INDEX idx_document_sections_section_type ON document_sections(section_type);

-- Vector embeddings for semantic search
CREATE TABLE embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES publications(paper_id),
    section_id UUID REFERENCES document_sections(section_id),
    vector_data VECTOR(768), -- Using pgvector extension for sentence-transformers embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for vector similarity search
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (vector_data vector_cosine_ops);

-- Knowledge graph entities
CREATE TABLE entities (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type TEXT NOT NULL, -- organism, phenotype, assay, platform, outcome
    entity_name TEXT NOT NULL,
    normalized_id TEXT, -- ID from controlled vocabulary (NCBI taxon, GO, etc.)
    normalized_name TEXT, -- Normalized name from controlled vocabulary
    confidence_score REAL, -- Confidence in entity extraction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for entities
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name ON entities(entity_name);
CREATE INDEX idx_entities_normalized_id ON entities(normalized_id);

-- Knowledge graph relationships (triples)
CREATE TABLE relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID REFERENCES entities(entity_id),
    predicate TEXT NOT NULL,
    object_id UUID REFERENCES entities(entity_id),
    confidence_score REAL, -- Confidence in relationship extraction
    sentence_ids JSONB, -- Array of sentence IDs where this relationship was found
    paper_ids JSONB, -- Array of paper IDs where this relationship was found
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for relationships
CREATE INDEX idx_relationships_subject ON relationships(subject_id);
CREATE INDEX idx_relationships_predicate ON relationships(predicate);
CREATE INDEX idx_relationships_object ON relationships(object_id);

-- Processing logs for audit trail
CREATE TABLE processing_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES publications(paper_id),
    component TEXT NOT NULL, -- Which component generated this log (crawler, grobid, ner, etc.)
    log_level TEXT NOT NULL, -- INFO, WARNING, ERROR
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for processing logs
CREATE INDEX idx_processing_logs_paper_id ON processing_logs(paper_id);
CREATE INDEX idx_processing_logs_component ON processing_logs(component);
CREATE INDEX idx_processing_logs_timestamp ON processing_logs(timestamp);

-- Summarization results
CREATE TABLE summaries (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES publications(paper_id),
    insight TEXT, -- One-line insight
    evidence_bullets JSONB, -- Array of evidence-backed bullets
    research_gaps JSONB, -- Array of suggested research gaps
    model_fingerprint TEXT, -- LLM model identifier
    prompt_template TEXT, -- Template used for generation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for summaries
CREATE INDEX idx_summaries_paper_id ON summaries(paper_id);
CREATE INDEX idx_summaries_created_at ON summaries(created_at);

-- Audit logs for LLM prompts and evidence
CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    summary_id UUID REFERENCES summaries(summary_id),
    prompt TEXT, -- Full prompt sent to LLM
    evidence_snippets JSONB, -- Array of evidence snippets used
    generated_output TEXT, -- Full output from LLM
    model_version TEXT, -- Specific model version
    generation_time_ms INTEGER, -- Time taken to generate response
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit logs
CREATE INDEX idx_audit_logs_summary_id ON audit_logs(summary_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Ingestion tracking for incremental updates
CREATE TABLE ingestion_tracker (
    source TEXT PRIMARY KEY, -- 'osdr' or 'nslsl'
    last_ingested TIMESTAMP,
    last_checksum TEXT, -- For detecting changes
    record_count INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial tracker records
INSERT INTO ingestion_tracker (source, last_ingested, record_count) VALUES 
('osdr', '1970-01-01 00:00:00', 0),
('nslsl', '1970-01-01 00:00:00', 0);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_publications_updated_at 
    BEFORE UPDATE ON publications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_file_metadata_updated_at 
    BEFORE UPDATE ON file_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for publication statistics
CREATE VIEW publication_stats AS
SELECT 
    COUNT(*) as total_publications,
    COUNT(DISTINCT osd_id) as osdr_studies,
    COUNT(DISTINCT nslsl_id) as nslsl_citations,
    COUNT(pdf_url) as papers_with_pdfs,
    MIN(year) as earliest_year,
    MAX(year) as latest_year,
    AVG(year) as average_year
FROM publications;

-- View for knowledge graph statistics
CREATE VIEW kg_stats AS
SELECT 
    COUNT(DISTINCT e.entity_id) as total_entities,
    COUNT(DISTINCT r.relationship_id) as total_relationships,
    COUNT(DISTINCT e.entity_type) as entity_types,
    (SELECT COUNT(*) FROM entities WHERE entity_type = 'organism') as organism_entities,
    (SELECT COUNT(*) FROM entities WHERE entity_type = 'phenotype') as phenotype_entities
FROM entities e
LEFT JOIN relationships r ON e.entity_id = r.subject_id OR e.entity_id = r.object_id;

-- View for processing status
CREATE VIEW processing_status AS
SELECT 
    source,
    last_ingested,
    record_count,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_ingested))/3600 as hours_since_last_ingest
FROM ingestion_tracker;