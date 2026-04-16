#!/bin/bash
# SPECTRE Phase 1 — Install Script for Kali Linux

set -e

echo "[*] Installing SPECTRE Phase 1..."

# Python deps
pip3 install -r requirements.txt --break-system-packages

# Create global command
chmod +x cli/main.py
sudo ln -sf "$(pwd)/cli/main.py" /usr/local/bin/spectre

echo "[+] Done. Run: spectre --help"
