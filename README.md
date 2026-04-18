# SPECTRE
### Red Team Automation Platform — v2.0

```
███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗  
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝  
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝
```

SPECTRE is an AI-powered red team automation platform for authorized penetration testing. v2.0 introduces a fully autonomous AI agent that plans, proposes, and executes attack chains using local LLMs — with operator confirmation before every tool run.

> **For authorized penetration testing only. Never use against systems you do not have explicit written permission to test.**

---

## What's New in v2.0

| | v1.0 | v2.0 |
|---|---|---|
| Tool execution | Manual CLI only | AI-driven + CLI |
| Attack planning | Manual | Auto-generated from nmap output |
| Findings | Manual entry | Auto-saved with TTP mapping |
| Interface | CLI | CLI + Terminal UI |
| C2 integration | None | Sliver (read-only) |

---

## Features

### AI Agent (ReAct Loop)
- Runs fully offline via **Ollama** (`llama3.1:8b`)
- Automatic nmap recon on engagement start
- Generates context-aware ATT&CK-mapped attack plan from scan results
- Think → Act → Observe loop with up to 20 iterations
- **Operator confirmation gate** — nothing executes without your `y`
- Auto-saves findings to DB with MITRE TTP mapping

### 23 Tools Across 5 Categories

| Category | Tools |
|----------|-------|
| Recon | nmap, subfinder, amass, whatweb, theharvester, whois |
| Web | nuclei, ffuf, sqlmap, nikto, dalfox, feroxbuster |
| Active Directory | crackmapexec, bloodhound, impacket, kerbrute, certipy, ldapdomaindump |
| Bruteforce | hydra, hashcat, john |
| CVE | cve-search, cve-autoscan |

### Terminal UI
- Full TUI built with **Textual**
- Live agent output with thought / tool call / finding distinction
- Sidebar engagement and findings summary
- Operator instruction input mid-session
- Keyboard shortcuts: `Ctrl+N` new engagement, `Ctrl+R` refresh, `ESC` stop agent

### Sliver C2 Integration (Optional)
- Read-only connection to a running Sliver server
- Session and beacon enumeration
- Privilege detection (SYSTEM / root)
- Context-aware post-exploitation suggestions mapped to TTPs

### Engagement Management
- Multiple concurrent engagements
- Types: external, internal, web, AD
- Per-engagement findings, tool run history, scope tracking
- SQLite-backed persistent storage
- Report generation (Markdown / PDF)

---

## Requirements

- Python 3.10+
- Kali Linux or similar (tools must be installed on the system)
- Ollama running locally

---

## Installation

```bash
# Clone the repo
git clone https://github.com/WhiteWolf217/SPECTRE.git
cd SPECTRE

# Install Python dependencies
pip install -r requirements.txt --break-system-packages

# Install Ollama and pull the model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# Create global CLI command
chmod +x install.sh
sudo bash install.sh
```

---

## Usage

### CLI

```bash
# Create a new engagement
spectre new --target 10.10.10.5 --name "Lab Test" --type external

# Run the AI agent
spectre agent --goal "find all open services and critical vulns"

# Run a specific tool manually
spectre run nmap --flags "-A -p-"
spectre run hydra --flags "-l root -P /usr/share/wordlists/rockyou.txt ssh"

# View findings
spectre findings

# Show ATT&CK-mapped suggestions for open ports
spectre dispatch 22,80,445,3389

# Generate report
spectre report --format md
spectre report --format pdf

# Manage engagements
spectre engagements
spectre use 2
spectre delete 2
```

### Terminal UI

```bash
python spectre_ui.py
```

| Keybind | Action |
|---------|--------|
| `Ctrl+N` | New engagement |
| `Ctrl+R` | Refresh |
| `ESC` | Stop agent |
| `Ctrl+Q` | Quit |

**UI commands (type in the input bar):**

```
use <id>              — switch engagement
delete <id>           — delete engagement
status                — show engagement summary
findings              — list all findings
stop                  — stop running agent
```

### Agent Workflow

```
1. spectre new --target <ip> --type external
2. python spectre_ui.py  (or: spectre agent --goal "...")
3. Type your goal: "find all critical vulns"
4. Agent runs nmap automatically
5. Agent generates ATT&CK-mapped attack plan
6. Type what to do: "run hydra on ssh"
7. Agent proposes tool call → you confirm y/n
8. Tool executes, output fed back to agent
9. Agent extracts findings and plans next step
10. spectre report --format pdf
```

---

## Project Structure

```
spectre/
├── agent/
│   ├── core.py          # ReAct agent loop
│   ├── llm.py           # Ollama client
│   ├── memory.py        # Session memory
│   ├── planner.py       # Attack plan generator
│   └── prompts.py       # System prompts
├── c2/
│   └── sliver.py        # Sliver C2 integration
├── cli/
│   └── main.py          # CLI entry point (typer)
├── core/
│   ├── executor.py      # Tool runner (subprocess)
│   ├── parser.py        # Output parsers (nmap etc.)
│   └── port_dispatch.py # Port → ATT&CK mapping
├── db/
│   └── store.py         # SQLite store
├── report/
│   └── generator.py     # Report generator
├── tools/
│   ├── recon/
│   ├── web/
│   ├── ad/
│   ├── bruteforce/
│   └── exploit/
├── ui/
│   └── app.py           # Textual TUI
├── spectre_ui.py        # UI entry point
├── config.py            # Paths, timeouts, wordlists
└── requirements.txt
```

---

## Sliver C2 Setup (Optional)

```bash
pip install sliver-py --break-system-packages

# Export config from your Sliver server
sliver-client export-config

# Default config path expected by SPECTRE:
# ~/.sliver-client/configs/default.cfg
```

---

## Disclaimer

SPECTRE is intended for **authorized security testing only**. The authors are not responsible for any misuse or damage caused by this tool. Always obtain explicit written permission before testing any system. Unauthorized use may violate computer crime laws in your jurisdiction.

---

## License

MIT License — see [LICENSE](LICENSE) for details.