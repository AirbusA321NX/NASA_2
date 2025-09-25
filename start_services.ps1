# NASA Space Biology Knowledge Engine - Startup Script
# This script starts all services in the correct order

Write-Host "Starting NASA Space Biology Knowledge Engine..." -ForegroundColor Green

# Start Data Pipeline (FastAPI) in background
Write-Host "Starting Data Pipeline..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "localhost", "--port", "8003" -WorkingDirectory "g:\NASA\data-pipeline"

# Wait a moment for data pipeline to start
Start-Sleep -Seconds 5

# Start Backend (Express) in background
Write-Host "Starting Backend..." -ForegroundColor Yellow
Set-Location -Path "g:\NASA\backend"
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run", "dev"

# Wait a moment for backend to start
Start-Sleep -Seconds 5

# Start Frontend (Next.js) in foreground
Write-Host "Starting Frontend..." -ForegroundColor Yellow
Set-Location -Path "g:\NASA\frontend"
npm run dev

Write-Host "All services started!" -ForegroundColor Green