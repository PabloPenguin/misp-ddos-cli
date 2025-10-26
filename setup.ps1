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
if (-not (Test-Path "venv")) {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "ERROR: Activation script not found" -ForegroundColor Red
    Write-Host "Try deleting the venv folder and running setup again" -ForegroundColor Yellow
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip and build tools..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upgrade pip" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Gray
pip install -r requirements.txt --quiet --disable-pip-version-check
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
Write-Host ""
if (Test-Path ".env") {
    Write-Host ".env file already exists." -ForegroundColor Green
    $response = Read-Host "Do you want to reconfigure MISP connection? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Remove-Item ".env"
    }
}

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "=== MISP Connection Configuration ===" -ForegroundColor Cyan
    Write-Host ""
    
    $mispUrl = Read-Host "Enter MISP URL (e.g., https://server1.tailaa85d9.ts.net)"
    while ([string]::IsNullOrWhiteSpace($mispUrl)) {
        Write-Host "ERROR: MISP URL cannot be empty" -ForegroundColor Red
        $mispUrl = Read-Host "Enter MISP URL"
    }
    
    $apiKey = Read-Host "Enter MISP API Key"
    while ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Host "ERROR: API Key cannot be empty" -ForegroundColor Red
        $apiKey = Read-Host "Enter MISP API Key"
    }
    
    Write-Host ""
    Write-Host "Enable SSL certificate verification?" -ForegroundColor Yellow
    Write-Host "  [1] No  (for self-signed certificates)" -ForegroundColor White
    Write-Host "  [2] Yes (for production with valid certificates)" -ForegroundColor White
    $sslChoice = Read-Host "Choice [1]"
    if ([string]::IsNullOrWhiteSpace($sslChoice)) { $sslChoice = "1" }
    $verifySsl = if ($sslChoice -eq "2") { "true" } else { "false" }
    
    $envContent = @"
# MISP Instance Configuration
MISP_URL=$mispUrl
MISP_API_KEY=$apiKey

# Security Settings
MISP_VERIFY_SSL=$verifySsl
MISP_TIMEOUT=30
MISP_MAX_RETRIES=3

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=misp_cli.log
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host ""
    Write-Host ".env file created successfully!" -ForegroundColor Green
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
