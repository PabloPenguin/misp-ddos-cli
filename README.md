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
- **Structured Objects**: `ip-port` for attacker/victim IPs, `annotation` for descriptions
- **Confidence Tagging**: Attacker IPs tagged with `confidence-level:high|medium|low`

## 📋 Requirements

- **Python**: 3.8 or higher
- **MISP Instance**: Accessible MISP server with API access
- **Network**: Connectivity to MISP instance (Tailscale, VPN, or direct)

## 🚀 Installation

### Quick Start (Recommended)

**Windows PowerShell:**
```powershell
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli
.\setup.ps1
```

**Linux/macOS:**
```bash
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MISP credentials
```

The `setup.ps1` script automatically handles:
- Virtual environment creation
- Dependency installation (with Windows compatibility)
- Environment configuration
- Connection testing

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

**Windows (Python 3.8-3.11):**
```powershell
pip install -r requirements.txt
```

**Windows (Python 3.12+):**
```powershell
# Core dependencies (required)
pip install pymisp requests python-dotenv click rich tabulate pydantic validators

# pandas/numpy (optional - not available for Python 3.12+)
# Tool works without these, just uses basic CSV parsing
```

**Linux/macOS:**
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your MISP details
```
</details>

#### Required Configuration (.env)

```bash
# MISP Instance Configuration
MISP_URL=https://server1.tailaa85d9.ts.net
MISP_API_KEY=your_api_key_here

# Security Settings
MISP_VERIFY_SSL=false  # Set to true for production with valid certs
MISP_TIMEOUT=30
MISP_MAX_RETRIES=3

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=misp_cli.log
```

⚠️ **Security Note**: Never commit `.env` to version control!

## 📖 Usage

### Test Connection

First, verify your MISP connection:

```bash
python main.py test-connection
```

### Interactive Mode

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
Event name: DDoS Attack on Web Infrastructure
Event date [2024-01-15]: 2024-01-15
Description: Large-scale volumetric attack targeting web servers
Attack type (1-3): 1  # direct-flood
Victim IP: 10.0.50.100
Victim port: 443
Attacker IP #1: 192.168.1.100
Attacker IP #2: 192.168.1.101
Attacker IP #3: [Enter to finish]
TLP level (1-4): 2  # green
Workflow state (1-4): 1  # new
Confidence level (1-3): 1  # high
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
- `attack_type` - Attack type: `direct-flood`, `amplification`, or `both`
- `attacker_ips` - Semicolon-separated attacker IPs
- `victim_ip` - Victim IP address
- `victim_port` - Victim port number
- `description` - Detailed attack description

**Optional Columns:**
- `tlp` - TLP level: `clear`, `green`, `amber`, `red` (default: green)
- `workflow_state` - State: `new`, `in-progress`, `reviewed`, `closed` (default: new)
- `attacker_ports` - Semicolon-separated attacker ports
- `confidence_level` - Confidence: `high`, `medium`, `low` (default: high)

**Example CSV:**
```csv
date,event_name,tlp,workflow_state,attack_type,attacker_ips,attacker_ports,victim_ip,victim_port,description,confidence_level
2024-01-15,DDoS Campaign Against Finance,green,new,direct-flood,192.168.1.100;192.168.1.101,80;443,10.0.0.50,443,Large-scale DDoS attack,high
2024-01-16,Amplification Attack,green,new,amplification,192.168.2.50,53,10.0.0.51,80,DNS amplification,high
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
```

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
