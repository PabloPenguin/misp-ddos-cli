# MISP DDoS CLI - Quick Start Guide

Get started in 5 minutes! ⚡

## Prerequisites

- ✅ Python 3.8 or higher installed
- ✅ Access to MISP instance (server1.tailaa85d9.ts.net)
- ✅ MISP API key
- ✅ Tailscale connected (if applicable)

## Installation (Windows PowerShell)

### Recommended: Automated Setup Script

**One-time setup - run this only once:**

```powershell
.\setup.ps1
```

**What it does:**
- ✅ Creates virtual environment
- ✅ Installs all required dependencies
- ✅ Handles Windows compatibility issues automatically
- ✅ Skips pandas/numpy if your Python version doesn't support them (tool still works!)
- ✅ Tests MISP connection

**That's it!** The script handles everything, including Python 3.13 compatibility.

⚠️ **You only run setup.ps1 once!** After initial setup, see "Daily Usage" below.

---

### Alternative: Manual Setup (Advanced Users Only)

Only use this if the setup script fails or you want full control:

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip
python -m pip install --upgrade pip wheel

# 4. Install REQUIRED dependencies (these always work)
pip install pymisp requests python-dotenv click rich tabulate pydantic validators

# 5. OPTIONAL: Try pandas/numpy (only works on Python 3.8-3.11)
pip install --only-binary :all: pandas==2.1.4 numpy==1.26.4
# If this fails, ignore it - the tool works without pandas/numpy

# 6. Copy .env file
copy .env.example .env

# 7. Edit .env with your credentials
notepad .env

# 7. Test connection
python main.py test-connection
```

---

## Daily Usage

**Every time you open a new PowerShell window:**

```powershell
# 1. Navigate to the project folder
cd path\to\misp-ddos-cli

# 2. Activate the virtual environment (REQUIRED)
.\venv\Scripts\Activate.ps1

# 3. Now use the tool normally
python main.py interactive
python main.py bulk events.csv
python main.py test-connection
```

**That's it!** Just activate the venv, then use the tool.

---

## First Steps

### 1. Test Connection

```powershell
# Make sure venv is activated first!
.\venv\Scripts\Activate.ps1

# Then test
python main.py test-connection
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
Description: Testing MISP CLI tool
Attack type: 1  # direct-flood
Victim IP: 10.0.0.1
Victim port: 443
Attacker IP #1: 192.168.1.100
Attacker IP #2: [press Enter to finish]
TLP level: 2  # green
Workflow state: 1  # new
Confidence level: 1  # high
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

## Sample CSV File

Create `test_events.csv`:

```csv
date,event_name,tlp,workflow_state,attack_type,attacker_ips,attacker_ports,victim_ip,victim_port,description,confidence_level
2024-10-26,Test Event 1,green,new,direct-flood,192.168.1.100,80,10.0.0.1,443,Test DDoS attack,high
2024-10-26,Test Event 2,green,new,amplification,192.168.1.101,53,10.0.0.2,53,DNS amplification test,high
```

Then upload:
```powershell
python main.py bulk test_events.csv
```

## Common Commands

```powershell
# Show version
python main.py --version

# Enable debug logging
python main.py --debug interactive

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
