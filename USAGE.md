# MISP DDoS CLI - Detailed Usage Guide

This guide provides comprehensive examples and workflows for using the MISP DDoS CLI tool.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Interactive Mode Examples](#interactive-mode-examples)
3. [Bulk Upload Examples](#bulk-upload-examples)
4. [Export Events Examples](#export-events-examples)
5. [CSV Template Guide](#csv-template-guide)
6. [Common Workflows](#common-workflows)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

## Quick Start

### First-Time Setup

```powershell
# 1. Clone and navigate to repository
git clone https://github.com/PabloPenguin/misp-ddos-cli.git
cd misp-ddos-cli

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure MISP connection
cp .env.example .env
notepad .env  # Edit with your MISP details

# 5. Test connection
python main.py test-connection
```

### Verify Installation

```bash
# Check version
python main.py --version

# View help
python main.py --help

# Test MISP connectivity
python main.py test-connection
```

## Interactive Mode Examples

### Example 1: Simple DDoS Event

Create a basic DDoS event with minimal information:

```bash
python main.py interactive
```

**Input:**
```
Event name: Web Server DDoS Attack
Event date [2024-10-26]: 2024-10-26
Description: HTTP flood targeting e-commerce platform
Attack type (1-3): 1  # direct-flood
Victim IP: 203.0.113.50
Victim port: 443
Attacker IP #1: 198.51.100.10
Attacker IP #2: [press Enter]
TLP level (1-4): 2  # green
Workflow state (1-4): 1  # new
Confidence level (1-3): 1  # high
Submit this event to MISP? [Y/n]: Y
```

**Output:**
```
✅ Event created successfully!

Event ID:       1234
Event UUID:     5f4dcc3b-5aa7-65d3-b6d5-3bd4e8b9e8a1
Event URL:      https://server1.tailaa85d9.ts.net/events/view/1234
```

### Example 2: Multi-Source DDoS with Ports

Create an event with multiple attackers and port information:

```bash
python main.py interactive
```

**Input:**
```
Event name: Multi-Vector DDoS Campaign
Event date: 2024-10-26 14:30:00
Description: Coordinated attack from botnet targeting DNS and web services
Attack type: 3  # both (direct-flood and amplification)
Victim IP: 203.0.113.100
Victim port: 53
Attacker IP #1: 198.51.100.20
Attacker IP #2: 198.51.100.21
Attacker IP #3: 198.51.100.22
Attacker IP #4: [press Enter]
Specify attacker ports? [y/N]: y
Port for 198.51.100.20: 53
Port for 198.51.100.21: 80
Port for 198.51.100.22: 443
TLP level: 2  # green
Workflow state: 2  # in-progress
Confidence level: 1  # high
```

### Example 3: High-Sensitivity Event

Create an event with restricted sharing:

```bash
python main.py interactive
```

**Input:**
```
Event name: Nation-State APT DDoS
Event date: 2024-10-26
Description: Suspected nation-state actor conducting reconnaissance via DDoS
Attack type: 1  # direct-flood
Victim IP: 203.0.113.200
Victim port: 443
Attacker IP #1: 198.51.100.50
Attacker IP #2: [press Enter]
TLP level: 4  # red (restricted sharing)
Workflow state: 2  # in-progress
Confidence level: 2  # medium
```

## Bulk Upload Examples

### Example 1: Basic Bulk Upload

Upload multiple events from a CSV file:

```bash
# Create CSV file with events
# (Use template: templates/ddos_event_template.csv)

# Upload all events
python main.py bulk events.csv
```

**Sample CSV (events.csv):**
```csv
date,event_name,tlp,workflow_state,attack_type,attacker_ips,attacker_ports,victim_ip,victim_port,description,confidence_level
2024-10-26,Retail DDoS Wave 1,green,new,direct-flood,198.51.100.10;198.51.100.11,80;443,203.0.113.10,443,First wave of retail sector attacks,high
2024-10-26,Retail DDoS Wave 2,green,new,direct-flood,198.51.100.12;198.51.100.13,,203.0.113.11,80,Second wave targeting checkout systems,high
2024-10-27,DNS Amplification,green,new,amplification,198.51.100.20,53,203.0.113.20,53,DNS amplification attack,high
```

**Output:**
```
📊 Upload Results

Metric              Value
──────────────────────────
Total Events            3
Successful              3
Failed                  0
Duration           4.52s
Avg Time/Event     1.51s

✅ Successfully Created Events:
Event Name                          Event ID    UUID
────────────────────────────────────────────────────
Retail DDoS Wave 1                     1235    a1b2c3d4...
Retail DDoS Wave 2                     1236    e5f6g7h8...
DNS Amplification                      1237    i9j0k1l2...

🎉 All 3 events uploaded successfully!
```

### Example 2: Dry Run Validation

Validate CSV without uploading to MISP:

```bash
python main.py bulk events.csv --dry-run
```

**Use Case:** Validate large CSV files before committing to upload.

### Example 3: Skip Invalid Rows

Process valid rows and skip invalid ones:

```bash
python main.py bulk events_with_errors.csv --skip-invalid
```

**Sample Output:**
```
⚠️  Invalid Rows Detected:

Row    Error
────────────────────────────────────────────────────
  3    Row 3: Invalid victim IP address '999.999.999.999'
  5    Row 5: Missing required field 'description'
  7    Row 7: Invalid TLP level 'purple'

📊 Upload Results

Metric              Value
──────────────────────────
Total Events            7
Successful              4
Failed                  0
Duration           5.23s

⚠️  Partial success: 4 uploaded, 3 failed validation
```

### Example 4: Stop on First Error

Fail fast on validation errors:

```bash
python main.py bulk events.csv --no-continue-on-error
```

**Use Case:** Strict validation for production uploads.

## Export Events Examples

### Example 1: Basic Export

Export all MISP events to JSON with automatic timestamped filename:

```bash
python main.py export
```

**Output:**
```
📥 MISP Event Export

Output file: C:\path\to\misp_events_export_2024-10-27_143025.json
Pretty print: No

🔗 Connecting to MISP instance...
✓ Connected successfully

📤 Exporting all events from MISP...
✓ Successfully retrieved 249 events

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric           ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Events           │   249 │
│ Total Attributes │  1461 │
│ Total Objects    │   117 │
└──────────────────┴───────┘

💾 Writing to JSON file...
✓ Export complete!

📄 File saved: C:\path\to\misp_events_export_2024-10-27_143025.json
File size: 25.49 MB
```

### Example 2: Pretty-Printed Export

Export with human-readable JSON formatting:

```bash
python main.py export -o misp_events.json --pretty
```

**Benefits:**
- ✅ Indented JSON (easier to read/debug)
- ✅ Better for version control diffs
- ⚠️ Larger file size (~30-40% increase)

**File Size Comparison:**
- Compact: 25.49 MB
- Pretty: 37.26 MB

### Example 3: Custom Output Directory

Export to organized directory structure:

```bash
# Create exports directory
mkdir exports

# Export to specific location
python main.py export -o exports/misp_full_export_2024-10-27.json --pretty
```

### Example 4: SIEM Integration Export

Export for Splunk, ELK Stack, or other SIEM platforms:

```bash
# Compact JSON for faster ingestion
python main.py export -o siem_import/misp_events.json

# The JSON contains:
# - All event attributes (IPs, ports, indicators)
# - All objects (ip-port, annotation)
# - All tags (TLP, MITRE ATT&CK, workflow states)
# - All galaxies (threat actor, malware, techniques)
# - Complete event metadata
```

**JSON Structure (per event):**
```json
{
  "id": "1234",
  "uuid": "5f4dcc3b-5aa7-65d3-b6d5-3bd4e8b9e8a1",
  "info": "DDoS Attack on Web Infrastructure",
  "date": "2024-10-26",
  "threat_level_id": "2",
  "analysis": "1",
  "Attribute": [
    {
      "type": "ip-src",
      "value": "192.168.1.100",
      "category": "Network activity",
      "to_ids": true
    }
  ],
  "Object": [
    {
      "name": "ip-port",
      "description": "Attacker IP and Port",
      "Attribute": [...]
    }
  ],
  "Tag": [
    {"name": "tlp:green"},
    {"name": "misp-event-type:incident"},
    {"name": "information-security-indicators:incident-type=\"ddos\""}
  ],
  "Galaxy": [...]
}
```

### Example 5: Scheduled Export for Backup

Create a scheduled task for regular exports:

**Windows Task Scheduler:**
```powershell
# Create backup script (backup_misp.ps1)
cd C:\path\to\misp-ddos-cli
.\venv\Scripts\Activate.ps1
$date = Get-Date -Format "yyyy-MM-dd"
python main.py export -o "backups\misp_backup_$date.json"
```

**Linux Cron Job:**
```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/misp-ddos-cli && source venv/bin/activate && python main.py export -o backups/misp_backup_$(date +\%Y-\%m-\%d).json
```

### Example 6: Export for Cross-Organization Sharing

Export events for sharing with partner organizations:

```bash
# Export all events
python main.py export -o shared/all_events.json --pretty

# Review the JSON and filter by TLP if needed
# Only share TLP:green or TLP:clear events with external parties
```

**Security Considerations:**
- ⚠️ Review TLP levels before sharing
- ⚠️ Filter out TLP:red and TLP:amber events for restricted sharing
- ⚠️ Sanitize descriptions for sensitive information
- ✅ This export includes ALL events visible to your API key

## CSV Template Guide

### Template Location

```bash
templates/ddos_event_template.csv
```

### Field Descriptions

#### Required Fields

**date**
- Format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`
- Example: `2024-10-26` or `2024-10-26 14:30:00`
- Description: When the DDoS attack occurred

**event_name**
- Format: String (max 255 characters)
- Example: `DDoS Attack on Financial Services`
- Description: Descriptive name for the event

**attack_type**
- Format: `direct-flood`, `amplification`, or `both`
- Example: `direct-flood`
- Description: Type of DDoS attack
  - `direct-flood`: Direct volumetric attack (T1498.001)
  - `amplification`: Reflection/amplification (T1498.002)
  - `both`: Both attack types

**attacker_ips**
- Format: Semicolon-separated IP addresses
- Example: `192.168.1.100;192.168.1.101;192.168.1.102`
- Description: Source IPs of the attack
- Supports: IPv4 and IPv6
- Limit: Maximum 1000 IPs per event

**victim_ip**
- Format: Single IP address
- Example: `10.0.50.100`
- Description: Target IP of the attack

**victim_port**
- Format: Integer (1-65535)
- Example: `443`
- Description: Target port of the attack

**description**
- Format: String (max 5000 characters)
- Example: `Large-scale volumetric attack targeting web infrastructure`
- Description: Detailed description of the attack

#### Optional Fields

**tlp**
- Format: `clear`, `green`, `amber`, or `red`
- Default: `green`
- Example: `green`
- Description: Traffic Light Protocol sharing level

**workflow_state**
- Format: `new`, `in-progress`, `reviewed`, or `closed`
- Default: `new`
- Example: `new`
- Description: Investigation workflow state

**attacker_ports**
- Format: Semicolon-separated ports
- Example: `80;443;8080`
- Description: Source ports used by attackers (optional)

**confidence_level**
- Format: `high`, `medium`, or `low`
- Default: `high`
- Example: `high`
- Description: Confidence in attribution

### CSV Best Practices

1. **UTF-8 Encoding**: Save CSV files as UTF-8
2. **No Extra Commas**: Ensure descriptions don't contain unescaped commas
3. **Semicolon Separator**: Use semicolons (`;`) for multiple values
4. **No Empty Lines**: Remove blank rows between data
5. **Header Required**: First row must be column headers
6. **File Size**: Keep under 10MB for optimal performance

## Common Workflows

### Workflow 1: Daily SOC Incident Reporting

```bash
# 1. Export incidents from SIEM to CSV
# 2. Validate CSV structure
python main.py bulk daily_incidents.csv --dry-run

# 3. Upload to MISP
python main.py bulk daily_incidents.csv

# 4. Review in MISP web interface
# Navigate to: https://server1.tailaa85d9.ts.net/events
```

### Workflow 2: Rapid Incident Response

```bash
# During active incident - use interactive mode for speed
python main.py interactive

# Quick entry:
# - Event name: Active DDoS - [Target Name]
# - Date: Use default (today)
# - Add known attacker IPs
# - Set workflow_state to "in-progress"
# - Upload immediately
```

### Workflow 3: Weekly Intelligence Sharing

```bash
# 1. Collect DDoS indicators from various sources
# 2. Consolidate into standardized CSV
# 3. Validate before sharing
python main.py bulk weekly_intel.csv --dry-run

# 4. Upload to shared MISP
python main.py bulk weekly_intel.csv

# 5. Verify TLP:green for sharing
```

### Workflow 4: Bulk Import from Threat Feed

```bash
# 1. Convert threat feed to CSV format
# 2. Set appropriate TLP levels
# 3. Upload with skip-invalid for resilience
python main.py bulk threat_feed_ddos.csv --skip-invalid

# 4. Review failed rows
# 5. Fix and re-upload failures
```

### Workflow 5: SIEM Integration Pipeline

```bash
# 1. Export all MISP events to JSON
python main.py export -o siem/misp_events.json

# 2. Import JSON into SIEM platform
# For Splunk:
# - Upload to $SPLUNK_HOME/etc/apps/search/lookups/
# - Create lookup definition
# - Use in searches: | inputlookup misp_events.json

# For ELK Stack:
# - Use Logstash with json codec
# - Index into Elasticsearch
# - Visualize in Kibana

# 3. Schedule regular exports (daily/weekly)
# 4. Automate SIEM ingestion process
```

### Workflow 6: Cross-Organization Intelligence Sharing

```bash
# 1. Export events from your MISP instance
python main.py export -o exports/org_events.json --pretty

# 2. Filter for shareable TLP levels (green/clear)
# Review JSON and remove TLP:red or TLP:amber events if needed

# 3. Share JSON file with partner organizations
# 4. Partners can import into their MISP instances or SIEM platforms
# 5. Establish regular sharing cadence (weekly/monthly)
```

## Error Handling

### Connection Errors

**Error:**
```
❌ MISP Connection Error:
Failed to connect to MISP: Connection refused
```

**Solutions:**
1. Verify MISP instance is running
2. Check Tailscale connection: `tailscale status`
3. Test connectivity: `ping server1.tailaa85d9.ts.net`
4. Verify `MISP_URL` in `.env`

### Authentication Errors

**Error:**
```
❌ MISP Connection Error:
Failed to connect to MISP: Invalid API key
```

**Solutions:**
1. Verify `MISP_API_KEY` in `.env`
2. Check API key in MISP: My Profile → Auth Keys
3. Ensure API key has proper permissions
4. Regenerate API key if needed

### Validation Errors

**Error:**
```
❌ Validation Error:
Invalid attacker IP address: '999.999.999.999'
```

**Solutions:**
1. Verify IP address format (IPv4: `192.168.1.1`, IPv6: `2001:db8::1`)
2. Check for typos or copy-paste errors
3. Validate against IP address standards

### CSV Parsing Errors

**Error:**
```
❌ CSV Validation Error:
CSV missing required columns: {'attacker_ips', 'victim_ip'}
```

**Solutions:**
1. Verify CSV has all required column headers
2. Check spelling of column names (case-sensitive)
3. Use provided template as reference
4. Ensure no extra spaces in headers

## Best Practices

### Security

1. **API Key Protection**
   ```bash
   # Set restrictive permissions on .env
   icacls .env /inheritance:r /grant:r "%USERNAME%:(R,W)"
   ```

2. **SSL Verification**
   ```bash
   # Production: Use valid SSL certificates
   MISP_VERIFY_SSL=true
   
   # Development/Testing only:
   MISP_VERIFY_SSL=false
   ```

3. **Sensitive Data**
   - Use TLP:red for sensitive intelligence
   - Review events before setting TLP:clear or TLP:green
   - Sanitize descriptions to remove PII

### Performance

1. **Bulk Uploads**
   - Process in batches of 100-500 events
   - Use `--skip-invalid` for large datasets
   - Monitor MISP server load

2. **Network Optimization**
   ```bash
   # Increase timeout for slow networks
   MISP_TIMEOUT=60
   
   # Increase retries for unstable connections
   MISP_MAX_RETRIES=5
   ```

### Data Quality

1. **Validation**
   - Always run `--dry-run` first for bulk uploads
   - Review validation errors before fixing
   - Use high confidence only for verified data

2. **Consistency**
   - Use standardized event naming: `[Attack Type] - [Target] - [Date]`
   - Consistent descriptions: Include attack vector, impact, duration
   - Proper workflow states: Update as investigation progresses

### Collaboration

1. **Shared MISP**
   - Default to TLP:green for community sharing
   - Include detailed descriptions for context
   - Tag with appropriate MITRE ATT&CK techniques

2. **Documentation**
   - Log all uploads for audit trail
   - Document special cases in event descriptions
   - Keep CSV source files for reference

---

## Additional Resources

- **MISP DDoS Playbook**: See `Requirements.MD` for full playbook
- **CSV Template**: `templates/ddos_event_template.csv`
- **Example Data**: See `examples/` directory (if available)
- **Troubleshooting**: See README.md Troubleshooting section

## Support

For additional help:
- GitHub Issues: https://github.com/PabloPenguin/misp-ddos-cli/issues
- MISP Documentation: https://www.misp-project.org/documentation/

---

**Happy Hunting! 🎯**
