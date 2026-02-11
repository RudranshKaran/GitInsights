# GitInsight - Quick Start Scripts

# Backend Development
Write-Host "Starting backend development server..." -ForegroundColor Green
Set-Location backend

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check for .env file
if (-Not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and add your API keys" -ForegroundColor Red
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file from template. Please edit it with your keys." -ForegroundColor Yellow
    exit 1
}

# Start server
Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Green
uvicorn app.main:app --reload --port 8000
