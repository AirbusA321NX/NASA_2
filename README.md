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

4. **Start the application**

#### Option 1: Using the PowerShell Script (Windows)
```powershell
# Run the startup script
.\start_services.ps1
```

#### Option 2: Manual Start
Start each service in a separate terminal:

```bash
# Terminal 1: Start Data Pipeline
cd data-pipeline
python -m uvicorn main:app --host localhost --port 8003

# Terminal 2: Start Backend
cd backend
npm run dev

# Terminal 3: Start Frontend
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
- Sentence Transformers
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
- [x] Basic web interface

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