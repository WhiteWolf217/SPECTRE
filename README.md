# SPECTRE

A comprehensive red team automation platform designed to streamline reconnaissance, vulnerability assessment, and exploitation workflows.

## Features

### Reconnaissance Tools
- **Nmap** — Network scanning and port discovery
- **Subfinder** — Subdomain enumeration
- **Amass** — Advanced subdomain discovery
- **WhatWeb** — Web technology fingerprinting
- **TheHarvester** — OSINT data harvesting
- **Whois** — Domain registration information

### Web Penetration Testing
- **Nuclei** — Template-based vulnerability scanning
- **Ffuf** — Fast web fuzzing
- **SQLMap** — SQL injection automation
- **Nikto** — Web server scanning
- **Dalfox** — XSS vulnerability detection
- **Feroxbuster** — Directory and file enumeration

### Active Directory & Domain
- **CrackMapExec** — Active Directory exploitation
- **BloodHound** — AD visualization and analysis
- **Impacket** — Network protocol manipulation
- **Kerbrute** — Kerberos brute-forcing
- **Certipy** — Certificate-based AD attacks
- **LdapDomainDump** — LDAP enumeration

### Brute Force & Cracking
- **Hydra** — Credential brute-forcing
- **Hashcat** — Password hash cracking
- **John the Ripper** — Multi-purpose hash cracking

## Installation

### Prerequisites
- Python 3.8+
- Linux/Kali Linux (recommended)
- Virtual environment (venv)

### Quick Start

```bash
# Clone or navigate to project directory
cd spectre

# Make install script executable
chmod +x install.sh

# Run installer (will prompt for sudo password)
./install.sh

# Verify installation
spectre --help
```

The installer will:
1. Install Python dependencies
2. Create a global `spectre` command in `/usr/local/bin/`
3. Display help information

## Usage

### Basic Commands

#### Create a New Engagement
```bash
spectre new --target <IP/Domain> --name "My Engagement" --type external --scope "In-scope assets"
```

**Options:**
- `--target, -t` — Target IP, IP range, or domain (required)
- `--name, -n` — Engagement name
- `--type` — Engagement type: `external`, `internal`, `web`, `ad`
- `--scope, -s` — Scope definition

#### List All Engagements
```bash
spectre engagements
```

Shows all engagements with their IDs, names, targets, types, status, and active marker.

#### Switch Active Engagement
```bash
spectre use <engagement_id>
```

#### Run a Tool
```bash
spectre run <tool_name> --target <target> --flags "<flags>"
```

**Example:**
```bash
spectre run nmap --target 192.168.1.0/24 --flags "-sV -sC"
```

#### Get Attack Chain Suggestions
```bash
spectre dispatch <ports> --target <IP>
```

**Example:**
```bash
spectre dispatch 22,80,445,3389 --target 192.168.1.100
```

#### List Available Tools
```bash
spectre tools
```

Shows all integrated tools with installation status and descriptions.

#### Manage Findings
```bash
# List findings for current engagement
spectre findings

# Add a manual finding
spectre add-finding --title "SQL Injection Found" \
  --severity critical \
  --host 192.168.1.100 \
  --port 80 \
  --ttp T1190 \
  --evidence "<evidence details>"
```

#### Generate Report
```bash
spectre report --format md
# or
spectre report --format pdf --engagement <id>
```

#### View Engagement Status
```bash
spectre status
```

Displays current engagement summary with tool runs and finding statistics.

#### Delete an Engagement
```bash
spectre delete <engagement_id>
# Skip confirmation with --force
spectre delete <engagement_id> --force
```

## Project Structure

```
spectre/
├── cli/                      # Command-line interface
│   ├── __init__.py
│   └── main.py              # Main CLI entry point
├── core/                     # Core functionality
│   ├── executor.py          # Tool execution engine
│   ├── parser.py            # Result parsing
│   ├── port_dispatch.py     # Port-to-tool mapping
│   └── __init__.py
├── db/                       # Database layer
│   ├── store.py             # SQLite3 database interface
│   └── __init__.py
├── tools/                    # Tool implementations
│   ├── base.py              # Base tool class
│   ├── recon/               # Reconnaissance tools
│   ├── web/                 # Web testing tools
│   ├── ad/                  # Active Directory tools
│   ├── bruteforce/          # Credential tools
│   ├── exploit/             # Exploitation tools
│   └── __init__.py
├── report/                   # Reporting engine
│   ├── generator.py         # Report generation
│   ├── templates/           # Report templates
│   └── __init__.py
├── config.py                # Configuration file
├── requirements.txt         # Python dependencies
├── install.sh              # Installation script
└── README.md               # This file
```

## Database

SPECTRE stores all data in SQLite3 at `~/.spectre/spectre.db`:

- **engagements** — Engagement metadata
- **tool_runs** — Tool execution history
- **findings** — Discovered vulnerabilities and issues

Active engagement ID is stored in `~/.spectre/.active`.

## Dependencies

- **typer** — CLI framework
- **rich** — Terminal output formatting
- **jinja2** — Report templating

Install with:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to customize:
- Default tool locations
- Output directories
- Report templates
- Database paths

## Workflow Example

```bash
# 1. Create new engagement
spectre new --target 192.168.1.0/24 --name "Q1 2024 Pentest"

# 2. Run reconnaissance
spectre run nmap --flags "-sV -sC"
spectre run subfinder --target example.com

# 3. Check suggestions
spectre dispatch 22,80,443,3389

# 4. Run web tests
spectre run nuclei
spectre run ffuf

# 5. View findings
spectre findings
spectre status

# 6. Generate report
spectre report --format md

# 7. Cleanup
spectre delete 1 --force
```

## Notes

- All tool output is saved to the database for reporting
- Findings can be manually added if tools miss issues
- Reports are generated from findings and tool runs
- Use `--no-save` flag with `run` command to skip database logging

## License

Proprietary — Red Team Use Only

## Support

For issues or feature requests, contact the development team.
