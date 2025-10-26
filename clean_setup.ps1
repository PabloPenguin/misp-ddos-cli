# Clean Setup - Removes corrupted venv and runs setup fresh
Write-Host "=== Clean MISP CLI Setup ===" -ForegroundColor Cyan
Write-Host ""

# Close any VS Code terminals if needed
Write-Host "Please close any other PowerShell terminals and press Enter to continue..." -ForegroundColor Yellow
Read-Host

# Try to remove venv with retries
Write-Host "Removing old virtual environment..." -ForegroundColor Yellow
$maxRetries = 3
$retry = 0
while ((Test-Path "venv") -and ($retry -lt $maxRetries)) {
    try {
        Remove-Item -Recurse -Force venv -ErrorAction Stop
        Write-Host "Successfully removed venv" -ForegroundColor Green
        break
    } catch {
        $retry++
        Write-Host "Retry $retry of $maxRetries..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (Test-Path "venv") {
    Write-Host ""
    Write-Host "ERROR: Cannot remove venv folder (files are locked)" -ForegroundColor Red
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Close ALL PowerShell/terminal windows" -ForegroundColor White
    Write-Host "  2. Close VS Code" -ForegroundColor White
    Write-Host "  3. Manually delete the 'venv' folder" -ForegroundColor White
    Write-Host "  4. Re-open and run: .\setup.ps1" -ForegroundColor White
    exit 1
}

# Remove .env to trigger prompts
Write-Host "Removing .env file..." -ForegroundColor Yellow
Remove-Item .env -ErrorAction SilentlyContinue

# Run setup
Write-Host ""
Write-Host "Running setup..." -ForegroundColor Cyan
Write-Host ""
.\setup.ps1
