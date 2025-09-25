# NASA Space Biology Knowledge Engine - Startup Instructions

## Prerequisites

1. Node.js (v18 or higher)
2. Python (v3.8 or higher)
3. npm (v9 or higher)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
npm install

# Install data pipeline dependencies
cd ../data-pipeline
pip install -r requirements.txt
```

### 2. Environment Configuration

The services are configured to use the following ports:
- Frontend (Next.js): http://localhost:3000
- Backend (Express): http://localhost:4003
- Data Pipeline (FastAPI): http://localhost:8003

### 3. Start Services

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

### 4. Access the Application

Once all services are running:
1. Open your browser to http://localhost:3000
2. The NASA Space Biology Knowledge Engine should be accessible

## Troubleshooting

### Port Conflicts

If you encounter port conflicts, you can modify the ports in the following files:
- Backend port: `backend/.env` (PORT variable)
- Data Pipeline port: `data-pipeline/.env` (PORT variable)
- Frontend port: By default Next.js uses port 3000, but you can specify a different port with `npm run dev -- -p 3001`

### Dependency Issues

If you encounter dependency issues:
1. Make sure all prerequisites are installed
2. Try reinstalling dependencies:
   ```bash
   # Frontend
   cd frontend && rm -rf node_modules package-lock.json && npm install
   
   # Backend
   cd ../backend && rm -rf node_modules package-lock.json && npm install
   
   # Data Pipeline
   cd ../data-pipeline && pip install -r requirements.txt
   ```

### Service Not Starting

1. Check that all required environment variables are set
2. Verify that no other processes are using the required ports
3. Check the logs in each service's terminal for error messages

## Testing Services

You can test if all services are running correctly by running:

```bash
python test_services.py
```

This will check if all three services are responding correctly.