# Quick Setup Script for MISP DDoS CLI
# Run this script to set up the environment quickly

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     MISP DDoS CLI - Automated Setup for Windows         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment
Write-Host ""
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "⚠️  Virtual environment already exists. Skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "✅ Virtual environment created successfully." -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "[4/6] Upgrading pip and build tools..." -ForegroundColor Yellow
python -m pip install --upgrade pip wheel setuptools | Out-Null
Write-Host "✅ Build tools upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "[5/6] Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first install..." -ForegroundColor Gray
Write-Host ""
# First install core dependencies without pandas/numpy
Write-Host "Installing core dependencies..." -ForegroundColor Gray
pip install pymisp requests python-dotenv click rich tabulate pydantic validators --quiet

# Try to install pandas and numpy with binary-only flag
Write-Host "Installing pandas and numpy (binary wheels only)..." -ForegroundColor Gray
$pandasInstalled = $false
pip install --only-binary :all: pandas==2.1.4 numpy==1.26.4 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pandas and numpy installed successfully" -ForegroundColor Green
    $pandasInstalled = $true
} else {
    Write-Host "⚠ pandas/numpy not available as pre-built wheels for your Python version" -ForegroundColor Yellow
    Write-Host "  CSV processing will use basic Python (slower but functional)" -ForegroundColor Yellow
}

# Verify core dependencies are installed
python -c "import click, rich, pymisp" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Core dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install core dependencies" -ForegroundColor Red
    exit 1
}

# Configure MISP connection
Write-Host ""
Write-Host "[6/6] Configuring MISP connection..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
    $response = Read-Host "Do you want to reconfigure? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Keeping existing configuration" -ForegroundColor Gray
    } else {
        Remove-Item ".env"
    }
}

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "           MISP Connection Configuration" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Prompt for MISP URL
    $mispUrl = Read-Host "Enter MISP URL (e.g., https://server1.tailaa85d9.ts.net)"
    while ([string]::IsNullOrWhiteSpace($mispUrl)) {
        Write-Host "❌ MISP URL cannot be empty" -ForegroundColor Red
        $mispUrl = Read-Host "Enter MISP URL"
    }
    
    # Prompt for API Key
    $apiKey = Read-Host "Enter MISP API Key"
    while ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Host "❌ API Key cannot be empty" -ForegroundColor Red
        $apiKey = Read-Host "Enter MISP API Key"
    }
    
    # Prompt for SSL verification
    Write-Host ""
    Write-Host "Enable SSL certificate verification?" -ForegroundColor Yellow
    Write-Host "  [1] No  (for self-signed certificates - recommended for self-hosted)" -ForegroundColor White
    Write-Host "  [2] Yes (for production with valid certificates)" -ForegroundColor White
    $sslChoice = Read-Host "Choice [1]"
    if ([string]::IsNullOrWhiteSpace($sslChoice)) { $sslChoice = "1" }
    $verifySsl = if ($sslChoice -eq "2") { "true" } else { "false" }
    
    # Create .env file
    Write-Host ""
    Write-Host "Creating .env file..." -ForegroundColor Gray
    
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
    Write-Host "✅ .env file created successfully" -ForegroundColor Green
}

# Test connection
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Testing MISP connection..." -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
python main.py test-connection

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║              ✅ Setup Complete! ✅                        ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick Start Commands:" -ForegroundColor Cyan
    Write-Host "  1. Activate environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  2. Interactive mode:     python main.py interactive" -ForegroundColor White
    Write-Host "  3. Bulk upload:          python main.py bulk events.csv" -ForegroundColor White
    Write-Host "  4. Help:                 python main.py --help" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Remember: Activate the virtual environment each time!" -ForegroundColor Yellow
} else {
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║        ⚠️  Setup Complete with Connection Issues         ║" -ForegroundColor Yellow
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "MISP connection test failed. Please verify:" -ForegroundColor Yellow
    Write-Host "  1. MISP_URL is correct in .env file" -ForegroundColor White
    Write-Host "  2. MISP_API_KEY is valid" -ForegroundColor White
    Write-Host "  3. MISP instance is accessible" -ForegroundColor White
    Write-Host "  4. Tailscale is connected (if applicable)" -ForegroundColor White
    Write-Host ""
    Write-Host "To reconfigure, edit .env file:" -ForegroundColor Cyan
    Write-Host "  notepad .env" -ForegroundColor White
    Write-Host ""
    Write-Host "Then test connection again:" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  python main.py test-connection" -ForegroundColor White
}
    Write-Host "Edit .env and run: python main.py test-connection" -ForegroundColor Cyan
}

Write-Host ""
