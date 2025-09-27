# NASA Space Biology Knowledge Engine

## 2025 NASA Space Apps Challenge

A dynamic dashboard that leverages artificial intelligence, knowledge graphs, and advanced data processing to summarize NASA bioscience publications and enable users to explore the impacts and results of space biology experiments.

## 🚀 Project Overview

This application processes 608+ NASA bioscience publications from the Open Science Data Repository (OSDR) to create an intelligent knowledge engine that helps:

- **Scientists** generating new hypotheses
- **Managers** identifying investment opportunities  
- **Mission architects** planning safe and efficient Moon and Mars exploration

## 🏗️ Architecture

### Frontend
- **Next.js 14** with App Router
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **D3.js** for data visualization
- **React Query** for data fetching

### Backend
- **Node.js** with Express
- **Python** for data processing
- **PostgreSQL** for database
- **Redis** for caching
- **Local AI Models** for document analysis (all-MiniLM-L6-v2, distilbert-base-uncased)

### Data Pipeline
- **AWS S3** integration for OSDR data
- **Pandas/NumPy** for data processing
- **spaCy/NLTK** for NLP processing
- **Sentence Transformers** for embeddings

## 🔧 Features

### Core Functionality
- **Intelligent Search**: Semantic search across NASA OSDR publications
- **Knowledge Graph**: Interactive exploration of research relationships
- **AI Summarization**: Automated research summaries using local AI models
- **Gap Analysis**: Identification of research gaps and opportunities
- **Visual Analytics**: Interactive charts and network visualizations

### Advanced Features
- **Multi-modal Search**: Text and visual search capabilities
- **Research Timeline**: Historical progression of space biology research
- **Export Capabilities**: Data export in multiple formats

## 📁 Project Structure

```
nasa-space-biology-engine/
├── frontend/                 # Next.js frontend application
├── backend/                  # Node.js/Express API server
├── data-pipeline/           # Python data processing scripts
├── embedding/               # AI embedding models
├── kg_extraction/           # Knowledge graph extraction
├── processing/              # Data processing utilities
├── summarization/           # Text summarization modules
└── vector_store/            # Vector database storage
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm 9+

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd nasa-space-biology-engine
```

2. **Install dependencies**
```bash
# Frontend
cd frontend && npm install

# Backend
cd ../backend && npm install

# Data pipeline
cd ../data-pipeline && pip install -r requirements.txt
```

3. **Environment Setup**
```bash
# Copy example environment files
cp .env.example .env
cp backend/.env.example backend/.env
# Configure your environment variables
```

4. **Database Setup (Optional but Recommended)**

The application can run with or without a database. For better performance, we recommend setting up the PostgreSQL database:

**Option 1: Using Docker (Recommended)**
```bash
# Start the database
# From the backend directory
docker-compose -f ../docker-compose.yml up -d postgres

# Initialize the database
# From the backend directory
npm run db:init
```

**Option 2: Using Local PostgreSQL**
1. Install PostgreSQL (version 12 or higher)
2. Create a database:
   ```sql
   CREATE DATABASE nasa_space_biology;
   CREATE USER postgres WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE nasa_space_biology TO postgres;
   ```
3. Initialize the database:
   ```bash
   # From the backend directory
   npm run db:init
   ```

**Option 3: No Database (Fallback Mode)**

If you don't have PostgreSQL available, the application will automatically fall back to using the data pipeline API. This mode works but may be slower for some operations.

4. **Start the application**

#### Option 1: Using the PowerShell Script (Windows)
```powershell
# Run the startup script
.\start_services.ps1
```

#### Option 2: Manual Start
Start each service in a separate terminal:

```bash
# Terminal 1: Start Database (Optional but Recommended)
# From the backend directory
start-db.bat

# Terminal 2: Start Data Pipeline
cd data-pipeline
python -m uvicorn main:app --host localhost --port 8003

# Terminal 3: Start Backend
cd backend
npm run dev

# Terminal 4: Start Frontend
cd frontend
npm run dev
```

5. **Access the Application**
Open your browser to http://localhost:3000

## 🔬 Data Sources

- **NASA OSDR**: Primary bioscience publications and datasets
- **NASA Space Life Sciences Library**: Additional relevant publications
- **NASA Task Book**: Grant and funding information

## 🤖 AI Integration

### Local AI Models
- **all-MiniLM-L6-v2**: For semantic search and document similarity
- **distilbert-base-uncased**: For text classification and entity extraction
- **Sentence Transformers**: For generating embeddings

### Knowledge Extraction Pipeline
1. **Document Processing**: PDF parsing and text extraction
2. **Entity Recognition**: Scientific entities, organisms, experiments
3. **Relationship Extraction**: Research connections and dependencies
4. **Graph Construction**: Knowledge graph building and validation

## 📊 Dashboard Features

### Research Explorer
- Interactive search with filters
- Publication timeline and trends
- Research topic clustering
- Author and institution networks

### Knowledge Graph Visualization
- Network exploration interface
- Node filtering and highlighting
- Path finding between concepts
- Export and sharing capabilities

### Analytics Dashboard
- Research impact metrics
- Collaboration patterns
- Geographic research distribution
- Funding and resource allocation

### Advanced Visualizations
- Heatmaps & Correlation Analysis
- Volcano Plots for Differential Analysis
- Time Series Analysis with Trend Detection
- Principal Component Analysis (PCA)
- Network Analysis for Collaboration Mapping
- 3D Research Landscapes
- Real-time Data Streaming

## 🧪 Technologies Used

### Frontend Stack
- Next.js 14, React 18, TypeScript
- Tailwind CSS, Headless UI
- D3.js, Recharts, Cytoscape.js
- React Hook Form, Zod validation

### Backend Stack
- Node.js, Express.js, TypeScript
- PostgreSQL
- Redis
- JWT authentication

### Data & AI Stack
- Python, Pandas, NumPy
- spaCy, NLTK, Transformers
- Sentence Transformers (all-MiniLM-L6-v2, distilbert-base-uncased)
- FAISS for similarity search

### Infrastructure
- Docker, Docker Compose
- AWS S3
- GitHub Actions CI/CD
- Vercel deployment

## 📈 Development Roadmap

### Phase 1: Foundation (Current)
- [x] Project setup and architecture
- [x] Data pipeline implementation
- [x] Advanced visualization dashboard

### Phase 2: Core Features
- [x] Local AI integration
- [x] Knowledge graph construction
- [x] Search and visualization

### Phase 3: Advanced Features
- [ ] Multi-modal search
- [ ] Collaboration tools
- [ ] Mobile optimization

### Phase 4: Deployment
- [ ] Production deployment
- [ ] Performance optimization
- [ ] Documentation completion

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- NASA Open Science Data Repository team
- 2025 NASA Space Apps Challenge organizers
- Open source community contributors

---

Built with ❤️ for the 2025 NASA Space Apps Challenge