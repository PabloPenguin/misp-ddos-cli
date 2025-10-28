# MISP DDoS CLI - Quick Start Guide

Get started in 5 minutes! ⚡

## Prerequisites

- ✅ Python 3.8 - 3.13+ installed (tested with 3.13.7)
- ✅ Access to MISP instance
- ✅ MISP API key
- ✅ Network connectivity to MISP (Tailscale/VPN if applicable)

## Installation (Windows PowerShell)

### Step 1: Clone the Repository

```powershell
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli
```

### Step 2: Run Automated Setup

**One-time setup - run this only once:**

```powershell
.\setup.ps1
```

**The script will:**
1. ✅ Check Python version (3.8+ required)
2. ✅ Create virtual environment (`venv` folder)
3. ✅ Activate the virtual environment
4. ✅ Upgrade pip and build tools
5. ✅ Install all dependencies (pure Python, no compilation)
6. ✅ Prompt you for MISP URL and API key
7. ✅ Create `.env` configuration file
8. ✅ Test connection to MISP instance

**Interactive prompts you'll see:**
```
Enter MISP URL (e.g., https://server1.tailaa85d9.ts.net): [your MISP URL]
Enter MISP API Key: [your API key]
Enable SSL certificate verification?
  [1] No  (for self-signed certificates)
  [2] Yes (for production with valid certificates)
Choice [1]: 1
```

**That's it!** The entire setup is automated.

⚠️ **Important:** You only run `setup.ps1` once during initial installation!

---

### Troubleshooting Setup

**Issue: "venv folder already exists" or "files are locked"**
```powershell
# Close all terminals and VS Code, then manually delete venv:
# 1. Open File Explorer (Windows + E)
# 2. Navigate to the project folder
# 3. Delete the 'venv' folder
# 4. Re-run: .\setup.ps1
```

**Issue: "No module named 'click'" after setup**
```powershell
# Virtual environment wasn't activated. Fix:
.\venv\Scripts\Activate.ps1
pip list  # Verify dependencies are installed
```

**Issue: Connection test fails**
- Check Tailscale is connected (if using Tailscale)
- Verify MISP URL and API key in `.env` file
- Test network: `Test-NetConnection your-misp-url -Port 443`

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting.

---

### Alternative: Manual Setup (Advanced Users)

Only use this if the setup script fails:

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip
pip install --upgrade pip setuptools wheel

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
notepad .env
```

**Add to .env:**
```ini
MISP_URL=https://your-misp-instance.com
MISP_API_KEY=your-api-key-here
MISP_VERIFY_SSL=false
MISP_TIMEOUT=30
MISP_MAX_RETRIES=3
LOG_LEVEL=INFO
LOG_FILE=misp_cli.log
```

---

## Daily Usage

**Every time you open a new PowerShell window:**

```powershell
# 1. Navigate to the project folder
cd C:\path\to\misp-ddos-cli

# 2. Activate the virtual environment (REQUIRED)
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt:
# (venv) PS C:\path\to\misp-ddos-cli>

# 3. Now use the tool
python main.py --help
python main.py test-connection
python main.py interactive
```

💡 **Remember:** Always activate the virtual environment first!

---

## First Steps

### 1. Test Connection

```powershell
# Make sure venv is activated (you'll see (venv) in prompt)
.\venv\Scripts\Activate.ps1

# Test MISP connection
python main.py test-connection
```

**Expected output:**
```
Testing MISP connection...
MISP URL: https://your-misp-instance.com
SSL Verification: False
✅ Connection successful!
MISP instance is accessible and API key is valid
```

Expected output:
```
✅ Connection successful!
MISP instance is accessible and API key is valid
```

### 2. View Help

```powershell
python main.py --help
```

### 3. Create Your First Event (Interactive)

```powershell
python main.py interactive
```

Follow the prompts:
```
Event name: Test DDoS Event
Event date [2024-10-26]: [press Enter]
Annotation text: Testing MISP CLI tool with sample DDoS event data
Destination IP #1: 10.0.0.1
Destination IP #2: [press Enter to finish]
Do you want to specify destination ports? [y/N]: y
Port for 10.0.0.1: 443
TLP level: 2  # green
Submit? [Y/n]: Y
```

### 4. Bulk Upload from CSV

```powershell
# View CSV template
python main.py template

# Create your CSV file (use templates/ddos_event_template.csv as reference)

# Validate CSV (dry run)
python main.py bulk your_events.csv --dry-run

# Upload events
python main.py bulk your_events.csv
```

### 5. Export Events to JSON

```powershell
# Export all events to JSON (for SIEM ingestion)
python main.py export -o misp_events.json --pretty

# Export with automatic timestamped filename
python main.py export --pretty
```

**Use Cases:**
- Import into SIEM platforms (Splunk, ELK Stack, QRadar, Sentinel)
- Share intelligence with other organizations
- Backup MISP event data
- Offline analysis

## Sample CSV File

Create `test_events.csv`:

```csv
date,event_name,tlp,attacker_ips,destination_ips,destination_ports,annotation_text
2024-10-26,Test Botnet Attack,green,203.0.113.10;203.0.113.11,,,Test DDoS attack from botnet with volumetric traffic
2024-10-26,Test Amplification,green,198.51.100.20,,,DNS amplification test using open resolvers
```

Then upload:
```powershell
python main.py bulk test_events.csv
```

## Common Commands

```powershell
# Show version
python main.py --version

# Show all available commands
python main.py --help

# Enable debug logging
python main.py --debug interactive

# Export all events to JSON
python main.py export -o misp_export.json --pretty

# Bulk upload with skip invalid
python main.py bulk events.csv --skip-invalid

# Dry run (validate only)
python main.py bulk events.csv --dry-run

# View template info
python main.py template
```

## Troubleshooting

### Virtual Environment Not Activated

If you see "ModuleNotFoundError", activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt.

### Connection Failed

1. Check Tailscale is connected:
   ```powershell
   tailscale status
   ```

2. Verify .env configuration:
   ```powershell
   notepad .env
   ```

3. Test network connectivity:
   ```powershell
   ping server1.tailaa85d9.ts.net
   ```

### Import Errors

Reinstall dependencies:
```powershell
pip install -r requirements.txt --force-reinstall
```

### Windows Installation Issues

**Problem: "Could not find vswhere.exe" or pandas build error**

This occurs when trying to build pandas/numpy from source without Visual Studio Build Tools.

**Solution: Install core dependencies only (pandas/numpy optional)**

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install core dependencies (required - always works)
pip install pymisp requests python-dotenv click rich tabulate pydantic validators

# Try pandas/numpy (optional - only if pre-built wheels available)
pip install --only-binary :all: pandas==2.1.4 numpy==1.26.4
```

**If pandas/numpy fail to install, that's OK!** The tool will work with basic CSV parsing.

**Solution 2: Use older Python version**

Pandas 2.1.4 pre-built wheels are available for Python 3.8-3.11. If you're on Python 3.12+, either:
- Use Python 3.11 instead, OR
- Skip pandas/numpy (tool still works without them)

**Problem: "ModuleNotFoundError: No module named 'click'"**

This means dependencies didn't install. Solution:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies manually with pre-built wheels
pip install --prefer-binary -r requirements.txt

# Or install core dependencies individually
pip install click rich pymisp python-dotenv requests
```

**Problem: Setup script execution policy error**

```powershell
# Run this first, then run setup.ps1
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Next Steps

- 📖 Read the full [README.md](README.md) for detailed documentation
- 📚 Review [USAGE.md](USAGE.md) for comprehensive examples
- 📋 Check [Requirements.MD](Requirements.MD) for MISP DDoS Playbook details
- 🧪 Run tests: `pytest tests/ -v`

## Support

- **GitHub Issues**: Report bugs or request features
- **MISP Documentation**: https://www.misp-project.org/documentation/

---

**Ready to streamline your DDoS event management! 🚀**
