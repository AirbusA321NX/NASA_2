# NASA Space Biology Knowledge Engine - Developer Guide

## 🚀 2025 NASA Space Apps Challenge

This comprehensive guide will help you understand, deploy, and extend the NASA Space Biology Knowledge Engine.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [API Documentation](#api-documentation)
5. [Data Pipeline](#data-pipeline)
6. [AI Integration](#ai-integration)
7. [Knowledge Graph](#knowledge-graph)
8. [Frontend Components](#frontend-components)
9. [Deployment Guide](#deployment-guide)
10. [Contributing](#contributing)

## 🎯 System Overview

The NASA Space Biology Knowledge Engine is a comprehensive platform that:

- **Processes 608+ NASA bioscience publications** from the OSDR repository
- **Uses Local AI Models** for intelligent analysis and summarization
- **Builds knowledge graphs** to show research relationships
- **Provides interactive visualizations** for data exploration
- **Offers semantic search** capabilities across all publications
- **Identifies research gaps** and opportunities

### Key Features

- 🧠 **AI-Powered Analysis**: Local transformer models for summarization and insights
- 🕸️ **Knowledge Graph**: Interactive network visualization
- 🔍 **Advanced Search**: Semantic search with multiple filters
- 📊 **Analytics Dashboard**: Research trends and statistics
- 🎨 **Modern UI**: React/Next.js with Tailwind CSS
- 🐳 **Containerized**: Docker-based deployment
- 📡 **Real-time Data**: Live updates from NASA OSDR

## 🚀 Quick Start

### Prerequisites

- Docker Desktop 4.0+
- Node.js 18+ (for development)
- Python 3.9+ (for data pipeline)
- 8GB RAM minimum
- 20GB disk space

### 1. Clone and Setup

```bash
git clone <repository-url>
cd nasa-space-biology-engine

# Copy environment file
cp .env.example .env

# Edit .env with your API keys (optional for demo)
nano .env
```

### 2. Run the Demo

**Windows (PowerShell):**
```powershell
.\start-demo.ps1
```

**Linux/Mac:**
```bash
chmod +x start-demo.sh
./start-demo.sh
```

**Manual Docker Compose:**
```bash
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:4000
- **Data Pipeline**: http://localhost:8001
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, pass: password)

## 🏗️ Architecture Deep Dive

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Data Pipeline  │
│   (Next.js)     │◄──►│   (Node.js)     │◄──►│   (Python)      │
│   Port: 3000    │    │   Port: 4000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Neo4j       │    │   Local AI      │
│   (Metadata)    │    │ (Knowledge Graph)│    │   (Analysis)    │
│   Port: 5432    │    │   Port: 7687    │    │   (Internal)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Details

#### Frontend (Next.js 14)
- **Framework**: Next.js with App Router
- **Styling**: Tailwind CSS with custom NASA theme
- **State Management**: Zustand for global state
- **Visualizations**: D3.js, Recharts, Cytoscape.js
- **Features**: 
  - Consolidated dashboard with advanced visualizations
  - Interactive analytics with multiple chart types
  - Advanced search interface
  - Knowledge graph visualization
  - Responsive design

#### Backend API (Node.js/Express)
- **Framework**: Express.js with TypeScript support
- **Authentication**: JWT-based (ready for implementation)
- **Rate Limiting**: Express-rate-limit
- **Validation**: Joi/Express-validator
- **Features**:
  - RESTful API endpoints
  - Advanced search capabilities
  - Analytics generation
  - Knowledge graph queries
  - Error handling and logging

#### Data Pipeline (Python/FastAPI)
- **Framework**: FastAPI for high-performance APIs
- **Data Processing**: Pandas, NumPy for data manipulation
- **NLP**: spaCy, NLTK for text processing
- **AI Integration**: Local transformer models
- **Features**:
  - NASA OSDR data fetching
  - Heterogeneous file processing
  - AI-powered analysis
  - Data transformation
  - Background task processing

### Database Architecture

#### PostgreSQL (Metadata & Cache)
```sql
-- Publications table
publications (
  id SERIAL PRIMARY KEY,
  osdr_id VARCHAR UNIQUE,
  title TEXT,
  abstract TEXT,
  authors JSONB,
  keywords JSONB,
  research_area VARCHAR,
  organisms JSONB,
  publication_date TIMESTAMP,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics cache
analytics_cache (
  cache_key VARCHAR PRIMARY KEY,
  data JSONB,
  expires_at TIMESTAMP
);
```

#### Neo4j (Knowledge Graph)
```cypher
// Node types
(:Publication {osdr_id, title, research_area})
(:ResearchArea {name})
(:Organism {scientific_name})
(:Author {name})
(:Keyword {term})

// Relationship types
(:Publication)-[:BELONGS_TO]->(:ResearchArea)
(:Publication)-[:STUDIES]->(:Organism)
(:Author)-[:AUTHORED]->(:Publication)
(:Publication)-[:TAGGED_WITH]->(:Keyword)
(:Publication)-[:SIMILAR_TO]->(:Publication)
```

## 📡 API Documentation

### Core Endpoints

#### Publications API

```http
GET /api/publications
GET /api/publications/:id
GET /api/publications/meta/research-areas
```

#### Search API

```http
POST /api/search
GET /api/search/suggestions?q=query
POST /api/search/semantic
GET /api/search/filters
POST /api/search/similar
```

#### Analytics API

```http
GET /api/analytics
GET /api/analytics/trends
GET /api/analytics/research-areas
GET /api/analytics/organisms
GET /api/analytics/gaps
```

#### Knowledge Graph API

```http
GET /api/knowledge-graph
GET /api/knowledge-graph/nodes/:id
POST /api/knowledge-graph/search
GET /api/knowledge-graph/paths
GET /api/knowledge-graph/clusters
```

### Example API Calls

#### 1. Search Publications

```javascript
const response = await fetch('http://localhost:4000/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'microgravity effects on bone density',
    research_areas: ['Human Physiology'],
    organisms: ['Homo sapiens'],
    limit: 20
  })
});

const data = await response.json();
console.log(`Found ${data.data.total_results} publications`);
```

#### 2. Get Knowledge Graph

```javascript
const response = await fetch('http://localhost:4000/api/knowledge-graph?limit=100');
const graphData = await response.json();

// Use with D3.js or other visualization libraries
renderGraph(graphData.data.graph);
```

#### 3. Get Analytics

```javascript
const response = await fetch('http://localhost:4000/api/analytics');
const analytics = await response.json();

console.log(`Total publications: ${analytics.data.overview.total_publications}`);
console.log(`Research areas: ${analytics.data.overview.research_areas}`);
```

## 🔄 Data Pipeline

### Data Sources

1. **NASA OSDR (Primary)**
   - 608+ bioscience publications
   - Heterogeneous file formats (PDF, JSON, XML)
   - Compressed archives (tar.gz, zip)

2. **NASA Space Life Sciences Library**
   - Additional relevant publications
   - Historical research data

3. **NASA Task Book**
   - Grant and funding information
   - Project metadata

### Processing Pipeline

```python
# Example data processing flow
async def process_osdr_data():
    # 1. Fetch catalog from OSDR
    studies = await fetch_osdr_catalog()
    
    # 2. Download and extract files
    for study in studies:
        files = await download_study_files(study)
        extracted = extract_archives(files)
        
        # 3. Extract text from PDFs
        text = extract_text_from_pdf(extracted['paper.pdf'])
        
        # 4. AI analysis with local models
        # Summary and keyword extraction using local transformer models
        
        # 5. Entity extraction
        entities = extract_entities(text)
        
        # 6. Store in database
        publication = Publication(
            title=study['title'],
            abstract=text[:1000],
            ai_summary=summary,
            keywords=keywords,
            entities=entities
        )
        await save_publication(publication)
```

### Custom Data Integration

To add your own data sources:

1. **Create a new processor**:
```python
# data-pipeline/processors/custom_processor.py
class CustomDataProcessor(BaseProcessor):
    async def fetch_data(self):
        # Your data fetching logic
        pass
    
    async def process_document(self, doc):
        # Your processing logic
        pass
```

2. **Register the processor**:
```python
# data-pipeline/main.py
from processors.custom_processor import CustomDataProcessor

app.include_processor(CustomDataProcessor())
```

## 🤖 AI Integration

The NASA Space Biology Knowledge Engine leverages state-of-the-art local AI models for intelligent analysis of space biology research publications.

### Local AI Models

#### Primary Models
- **all-MiniLM-L6-v2**: For semantic search and document similarity
- **distilbert-base-uncased**: For text classification and entity extraction
- **Sentence Transformers**: For generating embeddings

#### Model Capabilities
1. **Semantic Analysis**: Understanding research context and relationships
2. **Text Summarization**: Automated generation of research summaries
3. **Entity Recognition**: Identification of organisms, research areas, and key terms
4. **Research Gap Identification**: Detection of underexplored research areas
5. **Clustering**: Grouping similar research publications
6. **Similarity Matching**: Finding related studies and concepts

### Implementation Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Data Pipeline  │
│                 │    │                 │    │                 │
│ User Interface  │◄──►│  REST API       │◄──►│  Python Service │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Local AI        │    │ Local AI        │
                       │ Analyzer        │    │ Transformer     │
                       │ (Node.js)       │    │ Analyzer        │
                       │                 │    │ (Python)        │
                       └─────────────────┘    └─────────────────┘
```

### 1. Local AI Analyzer (Node.js)

Located in `backend/src/services/localAIAnalyzer.js`, this service provides JavaScript-based AI analysis with Python transformer fallback.

**Key Features:**
- Semantic analysis of research publications
- Research trend identification
- Gap analysis in current research
- Organism and research area clustering
- Future research predictions
- Confidence scoring for all analyses

**Usage Example:**
```javascript
const localAI = new LocalAIAnalyzer();
const analysis = await localAI.analyzeData(nasaData);
```

### 2. Transformer Analyzer (Python)

Located in `data-pipeline/transformer_analyzer.py`, this service provides high-performance transformer-based analysis using pre-trained models.

**Key Features:**
- High-accuracy semantic embeddings using all-MiniLM-L6-v2
- Detailed text classification with distilbert-base-uncased
- Research area clustering using K-means
- Semantic similarity calculations
- Research gap detection using cosine similarity

**API Endpoint:**
```http
POST /analyze
Content-Type: application/json

{
  "publications": [...],
  "research_areas": {...},
  "organisms": [...]
}
```

### 3. Analysis Pipeline

The AI analysis follows this pipeline:

1. **Data Preparation**: NASA OSDR data is prepared for analysis
2. **Semantic Embedding**: Text is converted to vector representations
3. **Clustering**: Similar research areas and publications are grouped
4. **Gap Analysis**: Underrepresented research areas are identified
5. **Trend Analysis**: Research patterns over time are detected
6. **Summary Generation**: Key findings are extracted and formatted
7. **Confidence Scoring**: Each analysis is scored for reliability

### 4. Local AI Analysis

```javascript
// 1. Overview Analysis
const overview = await localAI.generateOverview(nasaData);

// 2. Research Trends Analysis  
const trends = await localAI.analyzeTrends(nasaData);

// 3. Research Gaps Analysis
const gaps = await localAI.identifyGaps(nasaData);

// 4. Organism Analysis
const organisms = await localAI.analyzeOrganisms(nasaData);
```

### Python Transformer Analysis

```python
# 1. Initialize analyzer
analyzer = TransformerAnalyzer()

# 2. Analyze NASA data
results = analyzer.analyze_data(nasa_data)

# 3. Access results
overview = results['overview']
trends = results['researchTrends']
gaps = results['researchGaps']
```

### Model Performance

| Model | Task | Accuracy | Speed |
|-------|------|----------|-------|
| all-MiniLM-L6-v2 | Semantic Search | High | Fast |
| distilbert-base-uncased | Classification | Medium-High | Medium |
| Sentence Transformers | Embeddings | High | Fast |

### Configuration

The local AI models are configured through environment variables:

```
# No external API keys required - all models run locally
TRANSFORMER_MODEL=all-MiniLM-L6-v2
CLASSIFIER_MODEL=distilbert-base-uncased
```

### Production Environment
```
# Production environment variables
NODE_ENV=production
LOG_LEVEL=info
# No external API keys required - all models run locally
TRANSFORMER_MODEL=all-MiniLM-L6-v2
CLASSIFIER_MODEL=distilbert-base-uncased
```

### Testing Environment  
```bash
# Testing environment variables
NODE_ENV=test
LOG_LEVEL=debug
# No external API keys required - all models run locally
TRANSFORMER_MODEL=all-MiniLM-L6-v2
CLASSIFIER_MODEL=distilbert-base-uncased
```

### Benefits of Local AI

1. **Privacy**: All analysis happens locally, no data leaves your system
2. **Reliability**: No external service dependencies or rate limits
3. **Performance**: Optimized for the specific NASA OSDR dataset
4. **Cost**: No API costs for AI services
5. **Customization**: Models can be fine-tuned for space biology research

## 🕸️ Knowledge Graph

### Graph Schema

The knowledge graph uses Neo4j with the following schema:

``cypher
// Create constraints
CREATE CONSTRAINT pub_osdr_id IF NOT EXISTS FOR (p:Publication) REQUIRE p.osdr_id IS UNIQUE;
CREATE CONSTRAINT area_name IF NOT EXISTS FOR (a:ResearchArea) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT org_name IF NOT EXISTS FOR (o:Organism) REQUIRE o.scientific_name IS UNIQUE;

// Example queries
// Find all publications in a research area
MATCH (p:Publication)-[:BELONGS_TO]->(a:ResearchArea {name: 'Human Physiology'})
RETURN p.title, p.osdr_id;

// Find research connections
MATCH (p1:Publication)-[:SIMILAR_TO]-(p2:Publication)
WHERE p1.research_area <> p2.research_area
RETURN p1.research_area, p2.research_area, count(*) as connections
ORDER BY connections DESC;

// Find most studied organisms
MATCH (o:Organism)<-[:STUDIES]-(p:Publication)
RETURN o.scientific_name, count(p) as study_count
ORDER BY study_count DESC LIMIT 10;
```

### Graph Visualization

The frontend uses D3.js for interactive graph visualization:

```javascript
// components/knowledge-graph.tsx
const KnowledgeGraph = ({ data }) => {
  // D3.js force simulation
  const simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.edges))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width/2, height/2));
    
  // Interactive features
  // - Drag nodes
  // - Zoom and pan
  // - Hover tooltips
  // - Click for details
};
```

## 🎨 Frontend Components

### Key Components

1. **Dashboard** (`components/dashboard.tsx`)
   - Main overview page
   - Statistics cards
   - Recent publications
   - Quick actions

2. **Search Interface** (`components/search.tsx`)
   - Advanced search form
   - Filter options
   - Results display
   - Pagination

3. **Knowledge Graph** (`components/knowledge-graph.tsx`)
   - Interactive D3.js visualization
   - Node filtering
   - Path finding
   - Export capabilities

4. **Analytics Dashboard** (`components/analytics.tsx`)
   - Research trends
   - Distribution charts
   - Time series data
   - Interactive filters
   - Advanced visualizations:
     - Heatmaps & Correlation Analysis
     - Volcano Plots for Differential Analysis
     - Time Series Analysis with Trend Detection
     - Principal Component Analysis (PCA)
     - Network Analysis for Collaboration Mapping
     - 3D Research Landscapes
     - Real-time Data Streaming

### Styling System

The application uses a custom NASA-themed design system:

```css
/* Custom NASA colors */
:root {
  --nasa-blue: #0B3D91;
  --nasa-red: #FC3D21;
  --space-dark: #0D1117;
  --cosmic-purple: #6366F1;
  --stellar-blue: #3B82F6;
}

/* Component patterns */
.space-card {
  @apply bg-space-gray/80 backdrop-blur-10 border border-gray-600 rounded-lg;
}

.nasa-glow {
  box-shadow: 0 0 20px rgba(11, 61, 145, 0.3);
}
```

## 🚀 Deployment Guide

### Development Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Scale services
docker-compose up -d --scale backend=3

# Update a service
docker-compose up -d --build backend
```

### Production Deployment

1. **Environment Configuration**:
```bash
# .env.production
NODE_ENV=production
MISTRAL_API_KEY=prod_key
DATABASE_URL=postgresql://user:pass@prod-db:5432/nasa_bio
CORS_ORIGIN=https://your-domain.com
```

2. **Docker Compose Production**:
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 2
```

3. **Kubernetes Deployment**:
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Scale deployment
kubectl scale deployment nasa-backend --replicas=5
```

### Cloud Deployment Options

#### AWS Deployment
- **ECS/Fargate** for container orchestration
- **RDS** for PostgreSQL
- **ElastiCache** for Redis
- **CloudFront** for CDN

#### Google Cloud
- **GKE** for Kubernetes
- **Cloud SQL** for PostgreSQL
- **Memorystore** for Redis
- **Cloud CDN** for static assets

#### Azure
- **AKS** for container orchestration
- **Database for PostgreSQL**
- **Redis Cache**
- **Azure CDN**

## 🧪 Testing

### Backend Testing

```javascript
// tests/api.test.js
describe('Publications API', () => {
  test('should fetch publications', async () => {
    const response = await request(app)
      .get('/api/publications')
      .expect(200);
      
    expect(response.body.success).toBe(true);
    expect(response.body.data.publications).toBeDefined();
  });
  
  test('should search publications', async () => {
    const response = await request(app)
      .post('/api/search')
      .send({ query: 'microgravity', limit: 10 })
      .expect(200);
      
    expect(response.body.data.results).toBeDefined();
  });
});
```

### Frontend Testing

```javascript
// tests/components.test.tsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../components/dashboard';
import Analytics from '../components/analytics';

test('renders dashboard with statistics', () => {
  render(<Dashboard />);
  
  expect(screen.getByText('608+')).toBeInTheDocument();
  expect(screen.getByText('Publications')).toBeInTheDocument();
});

test('renders analytics with visualization selector', () => {
  render(<Analytics />);
  
  expect(screen.getByText('Select Visualization')).toBeInTheDocument();
});
```

### Load Testing

To run load tests against the backend API:

```bash
# Test with Apache Bench (ab)
ab -n 1000 -c 10 http://localhost:4001/api/publications
```

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Clone your fork**:
```bash
git clone https://github.com/your-username/nasa-space-biology-engine.git
cd nasa-space-biology-engine
```

3. **Create a feature branch**:
```bash
git checkout -b feature/amazing-feature
```

4. **Set up development environment**:
```bash
# Install dependencies
npm run setup

# Start development servers
npm run dev
```

### Code Style

- **Backend**: ESLint + Prettier
- **Frontend**: ESLint + Prettier + TypeScript
- **Python**: Black + isort + flake8

### Pull Request Process

1. Update README.md with changes
2. Add tests for new features
3. Ensure all tests pass
4. Update API documentation
5. Create pull request with detailed description

### Feature Ideas

- **Multi-language support** for international collaboration
- **Machine learning models** for research prediction
- **Real-time collaboration** features
- **Mobile app** development
- **Voice search** capabilities
- **3D visualizations** for complex data
- **Integration** with other NASA systems

## 📚 Additional Resources

### NASA Resources
- [NASA OSDR](https://osdr.nasa.gov/)
- [NASA Space Life Sciences](https://www.nasa.gov/biological-physical/)
- [NASA Task Book](https://taskbook.nasaprs.com/)

### Technical Documentation
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Hugging Face Transformers Documentation](https://huggingface.co/docs/transformers/index)

### Community
- [NASA Space Apps Challenge](https://www.spaceappschallenge.org/)
- [Project GitHub Issues](https://github.com/your-repo/issues)
- [Development Discord](https://discord.gg/nasa-space-apps)

---

## 🎉 Conclusion

The NASA Space Biology Knowledge Engine represents a significant step forward in making space biology research accessible and actionable. By combining cutting-edge AI, modern web technologies, and comprehensive data processing, we've created a platform that serves scientists, mission planners, and researchers worldwide.

This project demonstrates the power of open science, collaborative development, and innovative technology in advancing human space exploration. We invite you to explore, contribute, and help us build the future of space biology research.

**Built with ❤️ for the 2025 NASA Space Apps Challenge**

---

*For technical support or questions, please refer to the GitHub issues or contact the development team.*