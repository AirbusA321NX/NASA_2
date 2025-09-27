# NASA Space Biology Knowledge Engine - Start All Services Script
# This script starts all required services for the NASA OSDR integration

Write-Host "🚀 Starting NASA Space Biology Knowledge Engine Services..." -ForegroundColor Cyan

# Start Data Pipeline (Python/FastAPI) in background
Write-Host "Starting Data Pipeline (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\data-pipeline'; python -m uvicorn main:app --host localhost --port 8003" -WindowStyle Minimized

# Wait a moment for the data pipeline to start
Start-Sleep -Seconds 5

# Start Backend API (Node.js/Express) in background
Write-Host "Starting Backend API (Node.js)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)\backend'; npm run dev" -WindowStyle Minimized

# Wait a moment for the backend to start
Start-Sleep -Seconds 5

# Start Frontend (Next.js) in foreground
Write-Host "Starting Frontend (Next.js)..." -ForegroundColor Yellow
Set-Location frontend
npm run dev

Write-Host "✅ All services started successfully!" -ForegroundColor Green
Write-Host "Frontend Dashboard: http://localhost:3000" -ForegroundColor Blue
Write-Host "Backend API: http://localhost:3001" -ForegroundColor Blue
Write-Host "Data Pipeline API: http://localhost:8003" -ForegroundColor Blue
Write-Host "" -ForegroundColor Blue
Write-Host "Advanced visualizations are available through the Analytics section of the dashboard." -ForegroundColor Blue