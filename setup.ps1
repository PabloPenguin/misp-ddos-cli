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
Write-Host "Upgrading pip and build tools..." -ForegroundColor Yellow
python -m pip install --upgrade pip wheel setuptools | Out-Null

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies (using pre-built wheels)..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first install..." -ForegroundColor Gray
pip install --prefer-binary -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "WARNING: Some dependencies failed. Trying minimal install..." -ForegroundColor Yellow
    # Try installing without pandas if it fails
    Get-Content requirements.txt | Where-Object { $_ -notmatch '^pandas' -and $_ -notmatch '^numpy' -and $_ -notmatch '^#' -and $_.Trim() -ne '' } | Set-Content requirements-minimal.txt
    pip install -r requirements-minimal.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Minimal dependencies installed (CSV features will use basic parsing)." -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
        Remove-Item requirements-minimal.txt -ErrorAction SilentlyContinue
        exit 1
    }
    Remove-Item requirements-minimal.txt -ErrorAction SilentlyContinue
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
