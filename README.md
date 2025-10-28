# MISP DDoS CLI Tool

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A production-ready command-line tool for creating and managing DDoS events in MISP, strictly following the **Streamlined MISP DDoS Playbook** for shared MISP instances.

## 🎯 Purpose

This tool enables SOC analysts to efficiently create DDoS events in MISP with proper structure and tagging, ensuring consistency across multiple organizations sharing a MISP instance. It supports both **interactive manual entry** and **bulk CSV uploads** while enforcing security best practices and comprehensive validation.

## ✨ Features

### Core Functionality
- ✅ **Interactive Mode** - Guided prompts for manual event creation
- ✅ **Bulk Upload** - Process multiple events from CSV files
- ✅ **Export Events** - Export all MISP events to JSON for SIEM ingestion
- ✅ **Playbook Compliance** - Automatic enforcement of MISP DDoS Playbook standards
- ✅ **Rich UI** - Beautiful terminal interface with progress tracking
- ✅ **Comprehensive Validation** - Input validation at all trust boundaries
- ✅ **Retry Logic** - Exponential backoff for transient failures
- ✅ **Detailed Logging** - Structured logging for debugging and auditing

### Security Features
- 🔒 **Defense-in-Depth** - Multiple layers of validation
- 🔒 **Secure-by-Design** - No hardcoded credentials, secure defaults
- 🔒 **Input Sanitization** - SQL injection and path traversal prevention
- 🔒 **SSL/TLS Support** - Configurable certificate verification
- 🔒 **Secret Management** - Environment variable-based configuration

### MISP DDoS Playbook Compliance
Automatically applies:
- **Global Tags**: `tlp:green`, `information-security-indicators:incident-type="ddos"`, `misp-event-type:incident`
- **MITRE ATT&CK**: `T1498` (Network DoS), `T1498.001` (Direct Flood), `T1498.002` (Amplification)
- **Local Tags**: `workflow:state=new|in-progress|reviewed|closed`
- **Structured Objects**: `ip-port` object with `ip-src` attributes for attackers and optional `ip-dst` for destinations, `annotation` for detailed information
- **Streamlined Data**: Focus on attacker IPs (threat intelligence sharing), with optional destination IPs and annotation objects for context

## 📋 Requirements

- **Python**: 3.8 - 3.13+ (tested with 3.13.7)
- **MISP Instance**: Accessible MISP server with API access
- **Network**: Connectivity to MISP instance (Tailscale, VPN, or direct)
- **Dependencies**: All have pre-built wheels (no compilation required)

## 🚀 Installation

### Quick Start (Recommended)

**Windows PowerShell:**
```powershell
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli
.\setup.ps1
```

The `setup.ps1` script will:
1. ✅ Create a virtual environment
2. ✅ Install all dependencies (compatible with Python 3.8-3.13+)
3. ✅ Prompt you for MISP credentials (URL and API key)
4. ✅ Create `.env` configuration file
5. ✅ Test the connection to your MISP instance

**Note**: The script will NOT overwrite an existing `.env` file. To reconfigure, delete `.env` first or answer "y" when prompted.

**Troubleshooting Setup:**
- If dependencies fail to install, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- If you get "module not found" errors, delete `venv` folder and re-run `.\setup.ps1`
- Make sure to activate the virtual environment: `.\venv\Scripts\Activate.ps1`

**Linux/macOS:**
```bash
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py test-connection  # Will prompt for credentials
```

**See [QUICKSTART.md](QUICKSTART.md) for detailed 5-minute setup guide.**

---

### Manual Installation (Advanced)

<details>
<summary>Click to expand manual installation steps</summary>

#### 1. Clone the Repository

```bash
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli
```

#### 2. Create Virtual Environment

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

**All Platforms (Python 3.8-3.13+):**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Note:** pandas and numpy have been removed from this project. CSV processing uses Python's built-in `csv` module for maximum compatibility.

#### 4. Configure Environment

Create a `.env` file in the project root:

```bash
# Manual creation
notepad .env  # Windows
nano .env     # Linux/macOS
```
</details>

#### Required Configuration (.env)

```ini
# MISP Instance Configuration
MISP_URL=https://your-misp-instance.com
MISP_API_KEY=your_api_key_here

# Security Settings
MISP_VERIFY_SSL=false  # Set to true for production with valid certs
MISP_TIMEOUT=30
MISP_MAX_RETRIES=3

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=misp_cli.log
```

---

## 📦 Dependencies

### Core Dependencies (Always Installed)
All dependencies are pure Python with pre-built wheels for Windows/Linux/macOS:

- **pymisp** (>=2.4.182) - MISP API client
- **requests** (>=2.31.0) - HTTP library
- **python-dotenv** (>=1.0.0) - Environment variable management
- **click** (>=8.1.7) - CLI framework
- **rich** (>=13.7.0) - Beautiful terminal formatting
- **tabulate** (>=0.9.0) - Table output
- **pydantic** (>=2.5.0) - Data validation
- **validators** (>=0.22.0) - Input validation utilities

**Total installation size:** ~50MB (vs ~250MB with pandas/numpy)

### Development/Testing Dependencies (Included)

The following testing dependencies are included in `requirements.txt`:
- **pytest** (>=7.4.3) - Testing framework
- **pytest-cov** (>=4.1.0) - Coverage reporting
- **pytest-mock** (>=3.12.0) - Mocking utilities
- **responses** (>=0.24.1) - HTTP response mocking

### What's NOT Included (Intentionally)

**pandas and numpy** were removed because:
- ❌ No pre-built wheels for Python 3.13 on Windows
- ❌ Require Visual Studio Build Tools to compile
- ❌ Add ~200MB to installation size
- ✅ Not needed - Python's `csv` module handles all CSV operations
- ✅ Built-in `csv.DictReader` is faster for our use case

**CSV processing** uses stdlib only:
- `csv.DictReader` - Read CSV files
- `pathlib.Path` - File handling
- `re` - Pattern matching for validation
- `datetime` - Date parsing

**Result:** Zero compilation dependencies, works on all Python versions 3.8-3.13+

---

## 📖 Usage
```

⚠️ **Security Note**: Never commit `.env` to version control!

---

## 📖 Usage

### Daily Usage

**Every time you want to use the tool:**

```powershell
# Windows - Activate virtual environment
.\venv\Scripts\Activate.ps1

# Linux/macOS - Activate virtual environment  
source venv/bin/activate

# Now use the tool
python main.py --help
```

💡 **Note**: You only run `setup.ps1` once during installation. For daily use, just activate the virtual environment.

---

### Quick Examples

#### Test Connection

First, verify your MISP connection:

```bash
python main.py test-connection
```

#### Interactive Mode

Create events manually with guided prompts:

```bash
python main.py interactive
```

**Features:**
- Step-by-step prompts with validation
- Real-time input validation
- Helpful hints and examples
- Summary before submission
- Rich terminal UI

**Example Session:**
```
Event name: DDoS Attack from Botnet Infrastructure
Event date [2024-01-15]: 2024-01-15
Annotation text: Large-scale volumetric attack from known botnet infrastructure with sustained traffic
Attacker IP #1: 203.0.113.10
Attacker IP #2: 203.0.113.11
Attacker IP #3: [Enter to finish]
Destination IP #1 (Optional): [press Enter to skip]
TLP level (1-4): 2  # green
```

### Bulk Upload Mode

Process multiple events from a CSV file:

```bash
# Upload events from CSV
python main.py bulk events.csv

# Validate without uploading (dry run)
python main.py bulk events.csv --dry-run

# Skip invalid rows instead of failing
python main.py bulk events.csv --skip-invalid

# Stop on first error
python main.py bulk events.csv --no-continue-on-error
```

### Export Events to JSON

Export all MISP events for SIEM ingestion or sharing:

```bash
# Export to timestamped JSON file
python main.py export

# Export to specific file
python main.py export -o misp_events.json

# Export with pretty formatting (human-readable)
python main.py export -o events.json --pretty

# Export to custom directory
python main.py export -o exports/full_export.json --pretty
```

**Features:**
- Exports ALL events with complete details (attributes, objects, tags, galaxies)
- SIEM-ready JSON format
- Automatic timestamped filenames
- Progress tracking and statistics
- Compact or pretty-printed output

**Use Cases:**
- Import events into SIEM platforms (Splunk, ELK, QRadar, Sentinel)
- Share intelligence with other organizations
- Backup MISP event data
- Offline analysis and reporting

### CSV Template

Get information about the CSV format:

```bash
python main.py template
```

#### CSV File Format

Use the template at `templates/ddos_event_template.csv`:

**Required Columns:**
- `date` - Event date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `event_name` - Event title/name
- `attacker_ips` - Semicolon-separated attacker/source IPs launching the attack
- `annotation_text` - Detailed annotation text about the attack

**Optional Columns:**
- `tlp` - TLP level: `clear`, `green`, `amber`, `red` (default: green)
- `destination_ips` - Semicolon-separated destination IPs being targeted (usually not shared)
- `destination_ports` - Semicolon-separated destination ports (usually not shared)

**Example CSV:**
```csv
date,event_name,tlp,attacker_ips,destination_ips,destination_ports,annotation_text
2024-01-15,DDoS Botnet Campaign,green,203.0.113.10;203.0.113.11,,,Large-scale DDoS attack from botnet infrastructure with sustained volumetric traffic
2024-01-16,DNS Amplification Attack,green,198.51.100.20,,,DNS amplification attack exploiting open resolvers with high amplification factor
```

### Advanced Options

```bash
# Use custom .env file
python main.py --env-file /path/to/.env interactive

# Enable debug logging
python main.py --debug bulk events.csv

# Show version
python main.py --version

# Show help
python main.py --help
python main.py bulk --help
python main.py export --help
```

### Available Commands

- `interactive` - Create events manually with guided prompts
- `bulk` - Upload multiple events from CSV file
- `export` - Export all MISP events to JSON format
- `test-connection` - Verify MISP connectivity
- `template` - Display CSV template information

## 🏗️ Project Structure

```
misp-ddos-cli/
├── src/
│   ├── __init__.py
│   ├── misp_client.py       # MISP API client with retry logic
│   ├── csv_processor.py     # CSV validation and processing
│   ├── cli_interactive.py   # Interactive CLI interface
│   ├── cli_bulk.py          # Bulk upload CLI interface
│   └── config.py            # Configuration management
├── tests/
│   ├── __init__.py
│   └── test_misp_cli.py     # Comprehensive test suite
├── templates/
│   └── ddos_event_template.csv  # CSV template for bulk uploads
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── requirements-lock.txt    # Locked dependency versions
├── .env.example            # Example environment configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test class
pytest tests/test_misp_cli.py::TestMISPClient -v
```

**Test Coverage:**
- ✅ Security validation (SQL injection, path traversal)
- ✅ Input validation (IPs, ports, dates, TLP levels)
- ✅ CSV processing (valid/invalid data, edge cases)
- ✅ MISP client operations (connection, event creation)
- ✅ Configuration loading and validation
- ✅ Error handling and retries

## 🔒 Security Considerations

### Known Limitations
1. **API Key Security**: API keys are stored in `.env` - ensure proper file permissions
2. **SSL Verification**: Can be disabled for self-hosted instances - use only on trusted networks
3. **Input Validation**: Event names and descriptions are not sanitized for display (assumed trusted)
4. **Rate Limiting**: No built-in rate limiting - MISP server may enforce limits

### Best Practices
- ✅ Store `.env` outside version control
- ✅ Use SSL verification in production (`MISP_VERIFY_SSL=true`)
- ✅ Rotate API keys regularly
- ✅ Review logs for security events
- ✅ Limit CSV file sizes (default: 10MB max)
- ✅ Validate data sources before bulk upload
- ✅ Use TLP tags appropriately for data sensitivity

## 🐛 Troubleshooting

### Connection Issues

**Problem**: `Connection Error: Failed to connect to MISP`

**Solutions:**
1. Verify `MISP_URL` is correct in `.env`
2. Check `MISP_API_KEY` is valid
3. Ensure MISP instance is running and accessible
4. For Tailscale: Verify Tailscale is connected
5. For self-signed certs: Set `MISP_VERIFY_SSL=false`
6. Check firewall/network settings

### CSV Validation Errors

**Problem**: `CSV Validation Error: Invalid IP address`

**Solutions:**
1. Verify IP addresses are in correct format (IPv4: `192.168.1.1` or IPv6: `2001:db8::1`)
2. Check for extra spaces or special characters
3. Ensure semicolons (`;`) are used to separate multiple IPs
4. Validate date format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'pymisp'`

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Permission Errors

**Problem**: `PermissionError: [Errno 13] Permission denied: '.env'`

**Solution:**
```bash
# Windows - Set file permissions
icacls .env /grant:r "%USERNAME%:(R,W)"

# Linux/macOS
chmod 600 .env
```

## 📝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Security First**: All contributions must follow secure coding practices
2. **Test Coverage**: Add tests for new features
3. **Documentation**: Update README and docstrings
4. **Code Style**: Follow PEP 8, use Black formatter
5. **Commit Messages**: Use clear, descriptive commit messages

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install black pylint mypy

# Format code
black src/ tests/

# Lint code
pylint src/

# Type check
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- MISP Project - https://www.misp-project.org/
- MITRE ATT&CK Framework - https://attack.mitre.org/
- Traffic Light Protocol (TLP) - https://www.first.org/tlp/

## 📞 Support

For issues and questions:
- **GitHub Issues**: https://github.com/PabloPenguin/misp-ddos-cli/issues
- **Documentation**: See [USAGE.md](USAGE.md) for detailed examples
- **MISP Project**: https://www.misp-project.org/documentation/

---

**Built with ❤️ for SOC Analysts**

*Following defense-in-depth principles and secure-by-design practices*
