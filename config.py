import os

# Paths
HOME_DIR    = os.path.expanduser("~/.spectre")
DB_PATH     = os.path.join(HOME_DIR, "spectre.db")
REPORTS_DIR = os.path.join(HOME_DIR, "reports")

# Default wordlists (Kali paths)
WORDLIST_COMMON   = "/usr/share/wordlists/dirb/common.txt"
WORDLIST_ROCKYOU  = "/usr/share/wordlists/rockyou.txt"
WORDLIST_USERS    = "/usr/share/seclists/Usernames/top-usernames-shortlist.txt"

# Tool timeouts (seconds)
TIMEOUT_SHORT  = 60
TIMEOUT_MEDIUM = 300
TIMEOUT_LONG   = 600
TIMEOUT_CRACK  = 3600
