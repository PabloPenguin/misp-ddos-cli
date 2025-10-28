# Troubleshooting Guide

## Common Issues and Solutions

### Issue: "pandas build is failing" or "pyproject.toml errors"

**Cause**: Pandas has been removed from this project. If you see these errors, you're using an old `requirements.txt`.

**Solution**:
```powershell
# Pull latest code
git pull origin main

# Remove old venv
Remove-Item -Recurse -Force venv

# Run setup
.\setup.ps1
```

---

### Issue: "No module named 'click'" after running setup

**Cause**: Dependencies were installed to global Python instead of virtual environment.

**Solution**:
1. Delete the `venv` folder manually
2. Close ALL terminal windows
3. Re-run `.\setup.ps1`
4. Always activate the virtual environment before running commands:
   ```powershell
   .\venv\Scripts\Activate.ps1
   python main.py test-connection
   ```

---

### Issue: "The process cannot access the file 'python.exe'"

**Cause**: Virtual environment is locked by another process.

**Solution**:
```powershell
# Close all terminals and VS Code
# Manually delete the venv folder in File Explorer
# OR use Task Manager to kill python.exe processes
# Then run setup again
.\setup.ps1
```

---

### Issue: Setup prompts don't appear

**Cause**: A `.env` file already exists.

**Solution**:
```powershell
# Check if .env exists
Test-Path .env

# If it exists and you want to reconfigure:
Remove-Item .env
.\setup.ps1

# OR manually edit .env file:
notepad .env
```

---

### Issue: "SSL: CERTIFICATE_VERIFY_FAILED"

**Cause**: Using self-signed certificates.

**Solution**:
Edit `.env` and set:
```
MISP_VERIFY_SSL=false
```

---

### Issue: Connection timeout or "Cannot reach MISP instance"

**Checklist**:
1. ✅ Is Tailscale connected? (if using Tailscale)
2. ✅ Can you ping the MISP server?
   ```powershell
   Test-NetConnection server1.tailaa85d9.ts.net -Port 443
   ```
3. ✅ Is the MISP URL correct in `.env`?
4. ✅ Is the API key valid?

**Test**:
```powershell
python main.py test-connection
```

---

### Issue: "Python not found"

**Cause**: Python not in PATH.

**Solution**:
1. Install Python from [python.org](https://www.python.org/downloads/)
2. Check "Add Python to PATH" during installation
3. Verify: `python --version`

---

### Issue: Dependencies install but to wrong location

**Symptoms**:
- Warnings about scripts not on PATH
- "No module named..." errors when running

**Solution**:
```powershell
# Ensure virtual environment is activated (you should see (venv) in prompt)
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | Select-String "click|pymisp|rich"
```

---

## Python Version Compatibility

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.8 - 3.12 | ✅ Fully Supported | Recommended |
| 3.13+ | ✅ Supported | Latest version (tested with 3.13.7) |
| < 3.8 | ❌ Not Supported | Use Python 3.8+ |

---

## Dependency Management

**Core dependencies** (always required):
- pymisp (MISP API client)
- click (CLI framework)
- rich (terminal UI)
- pydantic (validation)
- requests, python-dotenv

**Removed dependencies**:
- pandas (no longer needed - using Python's built-in csv module)
- numpy (no longer needed)

**Testing dependencies** (included in requirements.txt):
- pytest, pytest-cov, pytest-mock, responses

---

## Getting Help

1. Check this troubleshooting guide
2. Review [QUICKSTART.md](QUICKSTART.md)
3. Check [USAGE.md](USAGE.md) for command examples
4. Enable debug logging:
   ```powershell
   # Edit .env
   LOG_LEVEL=DEBUG
   
   # Run command
   python main.py test-connection
   
   # Check logs
   cat misp_cli.log
   ```

---

## Clean Reinstall

If all else fails, start fresh:

```powershell
# 1. Close all terminals
# 2. Close VS Code
# 3. Delete folders
Remove-Item -Recurse -Force venv
Remove-Item .env

# 4. Pull latest code
git pull origin main

# 5. Run setup
.\setup.ps1
```
