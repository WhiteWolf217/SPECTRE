# SPECTRE v2.0

**Red Team Automation Platform — AI Agent**

SPECTRE is an intelligent red team automation framework powered by AI. It combines automated reconnaissance, intelligent planning, and dynamic tool execution to streamline penetration testing and security assessments.

## Features

- 🤖 **AI-Powered Agent**: ReAct-based agent with adaptive planning using Ollama (llama3.1:8b)
- 🎯 **Engagement Management**: Create, manage, and track security engagements
- 🔍 **Automated Reconnaissance**: Intelligent Nmap scanning with engagement-type-aware flags
- 📊 **Dynamic Planning**: Context-aware attack planning based on reconnaissance findings
- 🛠️ **Multi-Tool Support**: Integration with Nmap, Nuclei, Hydra, CrackMapExec, and more
- 💾 **Persistent Storage**: SQLite database for engagements, findings, and tool runs
- 📈 **Finding Tracking**: Organize and manage security findings per engagement
- 🎨 **Terminal UI**: Responsive Textual-based terminal interface

## Architecture

```
SPECTRE v2.0
├── UI (Textual)
│   └── Engagement Management, Command Interface, Output Display
├── Agent (ReAct Pattern)
│   ├── Phase 1: Reconnaissance (Nmap)
│   ├── Phase 2: Analysis & Adaptive Planning
│   ├── Phase 3: Confirmation
│   └── Phase 4: Execution
├── Tools
│   ├── Recon (Nmap)
│   ├── Web (Nuclei)
│   ├── Bruteforce (Hydra)
│   ├── Exploit (CVE)
│   └── AD (CrackMapExec)
├── Database (SQLite)
│   └── Engagements, Findings, Tool Runs
└── C2 (Sliver integration)
```

## Installation

### System Requirements

**Recommended (Primary Support):**
- **Linux** (Kali Linux, Ubuntu, Parrot OS preferred)
- 8GB+ RAM (for Ollama model + concurrent operations)
- 50GB+ disk space (for model + tool dependencies)
- Stable internet connection

**Also Supported:**
- **macOS** 10.14+ (some tool compatibility issues)
- **Windows 10/11** (limited tool support, use WSL2 recommended)

**Not Recommended:**
- Lightweight systems (<4GB RAM)
- Network-restricted environments

**OS Compatibility Note:**
| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Core SPECTRE | ✅ Full | ✅ Full | ✅ Full |
| Reconnaissance | ✅ Full | ✅ Full | ✅ Full |
| Web Tools | ✅ Full | ✅ Full | ✅ Full |
| AD/Bruteforce | ✅ Full | ⚠️ Limited | ⚠️ Limited |
| C2 Integration | ✅ Full | ✅ Full | ✅ Full |

### Prerequisites

- **Python 3.8+**
- **Ollama** (with **llama3.1:8b** model - REQUIRED)
  - Download from https://ollama.ai
  - This specific model is required for agent reasoning
- **Nmap** - Network reconnaissance
- **Nuclei** - Web vulnerability scanning
- **Hydra** - Credential brute forcing
- **CrackMapExec** - Windows/AD exploitation
- **Sliver C2** (optional) - Post-exploitation C2 framework

### Prerequisites (Detailed Setup)

#### OS-Specific Installation

**Linux (Ubuntu/Debian/Kali):**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip nmap curl git

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Install optional tools
sudo apt install hydra-gtk nuclei
```

**macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 nmap ollama

# Start Ollama daemon
brew services start ollama
```

**Windows (WSL2 Recommended):**
```powershell
# Enable WSL2
wsl --install

# Then follow Linux instructions in WSL2 terminal
# OR download Ollama from https://ollama.ai/download/windows
```

#### Ollama & LLM Model (CRITICAL)

1. **Install Ollama**
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Or download from https://ollama.ai
   ```

2. **Pull the Required Model**
   ```bash
   ollama pull llama3.1:8b
   ```
   - **Note**: This is the only tested/supported model for SPECTRE
   - Download size: ~4.7GB
   - First run will download the model automatically

3. **Verify Ollama is Running**
   ```bash
   curl http://localhost:11434/api/tags
   # Should show: llama3.1:8b in the models list
   ```

#### Other Tools

Install Nmap, Nuclei, Hydra, CrackMapExec according to their documentation or package manager:
```bash
# Ubuntu/Debian
sudo apt install nmap nuclei hydra

# macOS
brew install nmap
brew install nuclei  # May require installation from GitHub
```

1. **Start Ollama with llama3.1:8b**
   ```bash
   ollama run llama3.1:8b
   # Keep this running in a separate terminal
   # You should see: "Listening on 127.0.0.1:11434"
   ```

2. **Clone/Navigate to the project**
   ```bash
   cd /path/to/spectre
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Ollama connectivity** (optional but recommended)
   ```bash
   curl http://localhost:11434/api/tags
   ```

5. **Run SPECTRE**
   ```bash
   python spectre_ui.py
   ```

## Usage

### Via Terminal UI

Launch the application:
```bash
python spectre_ui.py
```

**Available Commands:**
- `new` - Create a new engagement
- `use <engagement_id>` - Select an engagement for operations
- `delete <engagement_id>` - Delete an engagement (requires "yes" confirmation)
- `delete <engagement_id> --force` - Force delete without confirmation
- `run` - Execute the AI agent for the current engagement
- `status` - Show current engagement status
- `findings` - List all findings for the current engagement
- `stop` - Stop the running agent
- `exit` - Exit SPECTRE

### Engagement Types

Each engagement has a specific type that guides reconnaissance and planning:

- **External**: Full network scan with aggressive flags (-A -p- -T4)
- **Internal**: Internal network assessment (-A -p- -T3)
- **Web**: Web application testing (specific web ports with -sV -sC)
- **AD**: Active Directory assessment (Windows ports with -sV -sC)

## Configuration

Configuration files are located in `~/.spectre/`:
- `spectre.db` - SQLite database with engagements and findings

### Environment Variables

- `OLLAMA_API_URL` - Ollama API endpoint (default: `http://localhost:11434`)
  - **REQUIRED**: Ollama must be running on this endpoint
  - Example: `export OLLAMA_API_URL=http://192.168.1.100:11434`
  
- `OLLAMA_MODEL` - Model to use (default: `llama3.1:8b`)
  - **IMPORTANT**: Only llama3.1:8b is tested and supported
  - Other models may produce unexpected results
  - Example: `export OLLAMA_MODEL=llama3.1:8b`
  
- `SPECTRE_DB_PATH` - Database location (default: `~/.spectre/spectre.db`)
  - SQLite database for engagements and findings
  - Example: `export SPECTRE_DB_PATH=/custom/path/spectre.db`

#### .env File Setup (Optional)

Create `.env` file in project root:
```
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
SPECTRE_DB_PATH=~/.spectre/spectre.db
```

## Project Structure

```
spectre/
├── ui/
│   └── app.py                 # Terminal UI (Textual)
├── agent/
│   ├── core.py                # Agent logic & workflow
│   ├── llm.py                 # Ollama API wrapper
│   ├── planner.py             # Attack planning
│   ├── memory.py              # Agent memory management
│   └── prompts.py             # LLM prompts
├── tools/
│   ├── base.py                # Base tool class
│   ├── recon/nmap.py          # Nmap reconnaissance
│   ├── web/nuclei.py          # Web scanning
│   ├── bruteforce/hydra.py    # Credential brute force
│   ├── exploit/cve.py         # CVE exploitation
│   └── ad/cme.py              # Active Directory tools
├── core/
│   ├── executor.py            # Tool execution engine
│   ├── parser.py              # Output parsing
│   └── port_dispatch.py       # Port-based tool routing
├── db/
│   └── store.py               # SQLite database layer
├── c2/
│   └── sliver.py              # Sliver C2 integration
├── report/
│   ├── generator.py           # Report generation
│   └── templates/             # Report templates
└── cli/
    └── main.py                # CLI interface
```

## Workflow

### Standard Red Team Assessment

1. **Create Engagement**: Define target, type, and scope
   ```
   spectre> new
   ```

2. **Select Engagement**: Set active engagement
   ```
   spectre> use 1
   ```

3. **Run Agent**: Execute automated reconnaissance and planning
   ```
   spectre> run
   ```
   - Phase 1: Agent performs Nmap scan
   - Phase 2: Analyzes results and creates adaptive plan
   - Phase 3: Awaits confirmation for tool execution
   - Phase 4: Executes planned tools and gathers findings

4. **Review Findings**: Check discovered vulnerabilities
   ```
   spectre> findings
   ```

5. **Manage Engagements**: Track and clean up
   ```
   spectre> status
   spectre> delete 1 --force
   ```

## AI Agent Details

### ReAct Pattern Implementation

The agent follows the Reasoning + Acting pattern:

1. **Reasoning**: Analyze reconnaissance output and determine next steps
2. **Acting**: Execute tools based on reasoning
3. **Observation**: Process tool output
4. **Iteration**: Loop until objective complete

### Adaptive Planning

- Agent respects engagement type during planning
- Nmap flags optimized per engagement context
- Plans adapted based on actual reconnaissance findings
- Timeout: 300 seconds for LLM processing (accommodates large nmap scans)

## Requirements

See [requirements.txt](requirements.txt) for full dependency list.

Key dependencies:
- `textual` - Terminal UI framework
- `requests` - HTTP client for Ollama API
- `python-dotenv` - Environment configuration

## Troubleshooting

### Ollama Connection Failed
- **Error**: `Connection refused` or `Failed to connect to Ollama`
- **Solution**: 
  1. Start Ollama: `ollama run llama3.1:8b`
  2. Verify it's running: `curl http://localhost:11434/api/tags`
  3. Check port 11434 isn't blocked by firewall
  4. On macOS/Linux, restart Ollama service if needed

### Wrong Ollama Model
- **Error**: Agent responds with unexpected output or crashes
- **Solution**:
  1. Verify you're using llama3.1:8b: `ollama list`
  2. Pull the correct model: `ollama pull llama3.1:8b`
  3. Check `OLLAMA_MODEL` environment variable isn't overridden

### Agent Takes Too Long
- **Cause**: Ollama model still loading or large network scans
- **Solution**:
  - First run of llama3.1:8b may take 30-60 seconds
  - Wait for model to fully load before running agent
  - Check: `curl http://localhost:11434/api/tags`
  - Increase LLM timeout if needed (default: 300s)

### Nmap Scan Hangs
- Verify network connectivity to target
- Check firewall rules aren't blocking the scan
- Increase timeout if targeting large networks

### Database Locked
- Ensure only one SPECTRE instance is running
- Delete `~/.spectre/spectre.db` to reset (data will be lost)

## Contributing

Contributions are welcome! Areas for enhancement:
- Additional tool integrations
- Improved LLM prompting strategies
- Report template customization
- Multi-threading optimization

## License

Proprietary - SPECTRE v2.0

## Disclaimer

SPECTRE is designed for authorized security testing only. Unauthorized access to computer systems is illegal. Always obtain explicit permission before conducting security assessments.

---

**Questions?** Check the [troubleshooting section](#troubleshooting) or review agent logs in the UI.
