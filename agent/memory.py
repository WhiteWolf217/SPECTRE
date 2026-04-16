from datetime import datetime
from typing import Optional


class AgentMemory:
    """
    Tracks everything the agent knows about the current engagement session.
    Passed to the LLM as context on each turn so it remembers what it found.

    Keeps:
    - Full message history (user/assistant turns)
    - Tool runs and their results
    - Findings discovered
    - Open ports found
    - Credentials found
    - Notes (agent observations)
    """

    def __init__(self, target: str, goal: str, engagement_type: str):
        self.target          = target
        self.goal            = goal
        self.engagement_type = engagement_type
        self.started_at      = datetime.now().isoformat()

        # Conversation history — list of {"role": ..., "content": ...}
        self.messages: list = []

        # Tool run log
        self.tool_runs: list = []

        # Findings discovered
        self.findings: list = []

        # Open ports discovered
        self.open_ports: list = []

        # Credentials found
        self.credentials: list = []

        # Agent notes/observations
        self.notes: list = []

    # ── Message history ────────────────────────────────────────────────────────

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages(self) -> list:
        return self.messages.copy()

    # ── Tool runs ──────────────────────────────────────────────────────────────

    def add_tool_run(self, tool_name: str, args: dict, result: dict):
        self.tool_runs.append({
            "tool":      tool_name,
            "args":      args,
            "success":   result.get("success", False),
            "timestamp": datetime.now().isoformat(),
            # Store truncated stdout to keep memory lean
            "summary":   result.get("stdout", "")[:500],
        })

    # ── Findings ──────────────────────────────────────────────────────────────

    def add_finding(self, title: str, severity: str, description: str,
                    ttp: str = "", host: str = "", port=None, evidence: str = ""):
        self.findings.append({
            "title":       title,
            "severity":    severity,
            "description": description,
            "ttp":         ttp,
            "host":        host,
            "port":        port,
            "evidence":    evidence,
            "timestamp":   datetime.now().isoformat(),
        })

    # ── Open ports ────────────────────────────────────────────────────────────

    def add_open_ports(self, ports: list):
        """Add newly discovered open ports, avoid duplicates."""
        for p in ports:
            if p not in self.open_ports:
                self.open_ports.append(p)

    # ── Credentials ───────────────────────────────────────────────────────────

    def add_credential(self, username: str, password: str = "",
                       hash_: str = "", service: str = "", host: str = ""):
        self.credentials.append({
            "username":  username,
            "password":  password,
            "hash":      hash_,
            "service":   service,
            "host":      host,
            "timestamp": datetime.now().isoformat(),
        })

    # ── Notes ─────────────────────────────────────────────────────────────────

    def add_note(self, note: str):
        self.notes.append({
            "note":      note,
            "timestamp": datetime.now().isoformat(),
        })

    # ── Summary ───────────────────────────────────────────────────────────────

    def summary(self) -> str:
        """
        Returns a concise text summary of everything known so far.
        Fed into the agent prompt on each turn.
        """
        lines = []

        if self.open_ports:
            lines.append(f"Open ports found: {', '.join(str(p) for p in self.open_ports)}")

        if self.credentials:
            cred_list = [
                f"{c['username']}:{c['password'] or c['hash']} ({c['service']} on {c['host']})"
                for c in self.credentials
            ]
            lines.append(f"Credentials found: {'; '.join(cred_list)}")

        if self.findings:
            sev_map = {"critical": [], "high": [], "medium": [], "low": [], "info": []}
            for f in self.findings:
                sev_map.get(f["severity"], sev_map["info"]).append(f["title"])
            for sev, titles in sev_map.items():
                if titles:
                    lines.append(f"{sev.upper()} findings: {', '.join(titles)}")

        if self.tool_runs:
            last = self.tool_runs[-1]
            lines.append(f"Last tool run: {last['tool']} ({'success' if last['success'] else 'failed'})")

        if self.notes:
            lines.append(f"Notes: {'; '.join(n['note'] for n in self.notes[-3:])}")

        return "\n".join(lines) if lines else "Nothing discovered yet."

    def stats(self) -> dict:
        return {
            "tool_runs":   len(self.tool_runs),
            "findings":    len(self.findings),
            "open_ports":  len(self.open_ports),
            "credentials": len(self.credentials),
            "messages":    len(self.messages),
        }
