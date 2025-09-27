# NASA Space Biology Knowledge Engine - Startup Script
# This script starts all services in the correct order

Write-Host "Starting NASA Space Biology Knowledge Engine..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python is available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not available. Please install Python." -ForegroundColor Red
    exit 1
}

# Start Data Pipeline (FastAPI) in background
Write-Host "Starting Data Pipeline..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "localhost", "--port", "8003" -WorkingDirectory "g:\NASA\data-pipeline"

# Wait a moment for data pipeline to start
Start-Sleep -Seconds 5

# Check if Node.js and npm are available
$nodeAvailable = $false
$npmAvailable = $false

try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js is available: $nodeVersion" -ForegroundColor Green
    $nodeAvailable = $true
} catch {
    Write-Host "Node.js is not available. Skipping backend and frontend services." -ForegroundColor Yellow
}

if ($nodeAvailable) {
    try {
        $npmVersion = npm --version 2>&1
        Write-Host "npm is available: $npmVersion" -ForegroundColor Green
        $npmAvailable = $true
    } catch {
        Write-Host "npm is not available. Skipping backend and frontend services." -ForegroundColor Yellow
    }
}

# Start Backend (Express) in background if Node.js and npm are available
if ($npmAvailable) {
    Write-Host "Starting Backend..." -ForegroundColor Yellow
    
    # Try to start the backend service using cmd directly
    try {
        Start-Process -NoNewWindow -FilePath "cmd" -ArgumentList "/c", "cd /d G:\NASA && npm run dev:backend"
        Write-Host "Backend service started successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start backend service: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Wait a moment for backend to start
    Start-Sleep -Seconds 5
}

# Start Frontend (Next.js) in foreground if Node.js and npm are available
if ($npmAvailable) {
    Write-Host "Starting Frontend..." -ForegroundColor Yellow
    
    # Try to start the frontend service
    try {
        npm run dev:frontend
        Write-Host "Frontend service started successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start frontend service: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "Skipping frontend service due to missing Node.js/npm." -ForegroundColor Yellow
}

Write-Host "NASA Space Biology Knowledge Engine startup process completed!" -ForegroundColor Green
Write-Host "Data Pipeline should be running on http://localhost:8003" -ForegroundColor Cyan
if ($npmAvailable) {
    Write-Host "Backend should be running on http://localhost:4004" -ForegroundColor Cyan
    Write-Host "Frontend should be running on http://localhost:3000" -ForegroundColor Cyan
}