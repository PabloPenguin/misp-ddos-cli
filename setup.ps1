# Quick Setup Script for MISP DDoS CLI
# Run this script to set up the environment quickly

Write-Host "=== MISP DDoS CLI Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}

# Check if .env exists
Write-Host ""
if (Test-Path ".env") {
    Write-Host ".env file already exists." -ForegroundColor Green
} else {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "IMPORTANT: Edit .env file with your MISP credentials!" -ForegroundColor Red
    Write-Host "File location: $(Get-Location)\.env" -ForegroundColor Yellow
}

# Test connection
Write-Host ""
Write-Host "Testing MISP connection..." -ForegroundColor Yellow
python main.py test-connection

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Setup Complete! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now use the CLI:" -ForegroundColor Cyan
    Write-Host "  python main.py interactive     # Interactive mode" -ForegroundColor White
    Write-Host "  python main.py bulk events.csv # Bulk upload" -ForegroundColor White
    Write-Host "  python main.py --help          # Show help" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "=== Setup Complete with Warnings ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "MISP connection test failed. Please verify:" -ForegroundColor Yellow
    Write-Host "  1. .env file has correct MISP_URL and MISP_API_KEY" -ForegroundColor White
    Write-Host "  2. MISP instance is accessible" -ForegroundColor White
    Write-Host "  3. Tailscale is connected (if applicable)" -ForegroundColor White
    Write-Host ""
    Write-Host "Edit .env and run: python main.py test-connection" -ForegroundColor Cyan
}

Write-Host ""
