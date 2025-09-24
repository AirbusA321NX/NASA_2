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
- **Neo4j** for knowledge graph database
- **Redis** for caching
- **Mistral AI** for document analysis

### Data Pipeline
- **AWS S3** integration for OSDR data
- **Apache Airflow** for data orchestration
- **Pandas/NumPy** for data processing
- **spaCy/NLTK** for NLP processing

## 🔧 Features

### Core Functionality
- **Intelligent Search**: Semantic search across 608+ publications
- **Knowledge Graph**: Interactive exploration of research relationships
- **AI Summarization**: Automated research summaries using Mistral AI
- **Gap Analysis**: Identification of research gaps and opportunities
- **Visual Analytics**: Interactive charts and network visualizations

### Advanced Features
- **Multi-modal Search**: Text, visual, and audio search capabilities
- **Research Timeline**: Historical progression of space biology research
- **Collaboration Tools**: Shared annotations and bookmarks
- **Export Capabilities**: Data export in multiple formats

## 📁 Project Structure

```
nasa-space-biology-engine/
├── frontend/                 # Next.js frontend application
├── backend/                  # Node.js/Express API server
├── data-pipeline/           # Python data processing scripts
├── ml-services/             # AI/ML microservices
├── infrastructure/          # Docker, K8s, deployment configs
├── docs/                    # Documentation
└── tests/                   # Test suites
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Docker & Docker Compose
- Neo4j Database

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
cp .env.example .env
# Configure your environment variables
```

4. **Start the application**
```bash
docker-compose up -d
npm run dev
```

## 🔬 Data Sources

- **NASA OSDR**: Primary bioscience publications and datasets
- **NASA Space Life Sciences Library**: Additional relevant publications
- **NASA Task Book**: Grant and funding information
- **Supplementary Datasets**: Research metadata and experimental data

## 🤖 AI Integration

### Mistral AI Agent
- Document analysis and summarization
- Research gap identification  
- Hypothesis generation assistance
- Semantic similarity analysis

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
- Prisma ORM, PostgreSQL
- Redis, Bull Queue
- JWT authentication

### Data & AI Stack
- Python, Pandas, NumPy
- spaCy, NLTK, Transformers
- Neo4j, Cypher queries
- Mistral AI API integration

### Infrastructure
- Docker, Docker Compose
- AWS S3, EC2, Lambda
- GitHub Actions CI/CD
- Vercel deployment

## 📈 Development Roadmap

### Phase 1: Foundation (Current)
- [x] Project setup and architecture
- [ ] Data pipeline implementation
- [ ] Basic web interface

### Phase 2: Core Features
- [ ] AI integration with Mistral
- [ ] Knowledge graph construction
- [ ] Search and visualization

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
- Mistral AI for providing AI capabilities
- Open source community contributors

---

Built with ❤️ for the 2025 NASA Space Apps Challenge