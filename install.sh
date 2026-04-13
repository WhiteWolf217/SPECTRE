#!/bin/bash
# SPECTRE Phase 1 — Install Script for Kali Linux

set -e

echo "[*] Installing SPECTRE Phase 1..."

# Python deps
pip3 install -r requirements.txt --break-system-packages

# Create global command with proper shebang pointing to the venv python
VENV_PYTHON=$(python3 -c "import sys; print(sys.executable)")
chmod +x cli/main.py
(echo "#!${VENV_PYTHON}"; tail -n +2 cli/main.py) | sudo tee /usr/local/bin/spectre > /dev/null
sudo chmod +x /usr/local/bin/spectre

echo "[+] Done. Run: spectre --help"
