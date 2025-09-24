# NASA Space Biology Knowledge Engine - OSDR Integration

This document explains how to run the NASA Space Biology Knowledge Engine with real OSDR data integration.

## Architecture Overview

The NASA Space Biology Knowledge Engine consists of three main components:

1. **Frontend** (Next.js/React): User interface for exploring NASA OSDR data
2. **Backend API** (http://localhost:4001): Node.js/Express server with AI-powered analysis
3. **Data Pipeline** (Python/FastAPI): Data processing and analysis engine

## Running the Services

### 1. Start the Data Pipeline (Python/FastAPI)

The data pipeline fetches real data from NASA's OSDR S3 repository.

```bash
# Navigate to the data-pipeline directory
cd data-pipeline

# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Run the data pipeline server
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The data pipeline will be available at: http://localhost:8001

### 2. Start the Backend API (Node.js/Express)

The backend acts as a proxy between the frontend and data pipeline.

```bash
# Navigate to the backend directory
cd backend

# Install Node.js dependencies (if not already installed)
npm install

# Run the backend server
npm start
# OR for development
npm run dev
```

The backend API will be available at: http://localhost:4001

### 3. Start the Frontend (Next.js)

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies (if not already installed)
npm install

# Run the frontend development server
npm run dev
```

The frontend will be available at: http://localhost:3000

## Accessing Real OSDR Files

Once all services are running:

1. Open your browser and navigate to http://localhost:3000
2. Click on "OSDR Files" in the navigation bar or on the dashboard
3. The system will fetch real files from NASA's OSDR S3 repository through the backend proxy

## OSDR Data Processing

The system fetches real data from NASA's Open Science Data Repository:
- Base URL: http://nasa-osdr.s3-website-us-west-2.amazonaws.com
- Parses GLDS (GeneLab Data System) study directories
- Extracts file metadata and classification information
- Provides structured data through API endpoints

## API Endpoints

### Backend API (http://localhost:4001)

The backend API provides several endpoints for accessing and analyzing NASA OSDR data:

- `GET /api/osdr/files` - Get all OSDR files
- `GET /api/osdr/files/:studyId` - Get files for a specific study

### Data Pipeline API (http://localhost:8001)
- `GET /osdr-files` - Get all OSDR files
- `GET /osdr-files/:study_id` - Get files for a specific study
- `GET /health` - Health check
- `GET /docs` - API documentation

## Troubleshooting

### No Files Displayed
1. Ensure the data pipeline is running
2. Check that the data pipeline can access NASA's S3 repository
3. Verify network connectivity to http://nasa-osdr.s3-website-us-west-2.amazonaws.com

### Connection Errors
1. Check that all services are running on their correct ports
2. Verify firewall settings
3. Ensure CORS is properly configured

### Data Pipeline Issues
1. Check logs in the data-pipeline directory
2. Verify Python dependencies are installed
3. Ensure internet access to NASA's S3 repository

## Data Source

All data comes from NASA's Open Science Data Repository (OSDR):
https://osdr.nasa.gov/

The system parses the S3 directory listing to find GLDS studies and extracts file information.