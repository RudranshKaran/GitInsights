# GitInsight Frontend - Quick Start Script

Write-Host "Starting frontend development server..." -ForegroundColor Green
Set-Location frontend

# Check if node_modules exists
if (-Not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Check for .env.local file (optional for local dev)
if (-Not (Test-Path ".env.local")) {
    Write-Host "INFO: .env.local not found (this is optional for local development)" -ForegroundColor Yellow
    Write-Host "Creating .env.local from template..." -ForegroundColor Yellow
    if (Test-Path ".env.local.example") {
        Copy-Item ".env.local.example" ".env.local"
    }
}

# Start development server
Write-Host "Starting Next.js server on http://localhost:3000..." -ForegroundColor Green
npm run dev
