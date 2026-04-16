import re
import json


class Parser:
    """Parses raw CLI output from tools into structured dicts."""

    @staticmethod
    def nmap(raw: str) -> dict:
        """Parse nmap output into structured port/service data."""
        result = {"hosts": []}
        current_host = None

        for line in raw.splitlines():
            # Detect host
            host_match = re.match(r"Nmap scan report for (.+)", line)
            if host_match:
                current_host = {
                    "host": host_match.group(1).strip(),
                    "open_ports": [],
                    "os": ""
                }
                result["hosts"].append(current_host)

            # Detect open port
            port_match = re.match(r"(\d+)/(tcp|udp)\s+open\s+(\S+)\s*(.*)", line)
            if port_match and current_host:
                current_host["open_ports"].append({
                    "port": int(port_match.group(1)),
                    "proto": port_match.group(2),
                    "service": port_match.group(3),
                    "version": port_match.group(4).strip()
                })

            # Detect OS
            os_match = re.match(r"OS details: (.+)", line)
            if os_match and current_host:
                current_host["os"] = os_match.group(1).strip()

        return result

    @staticmethod
    def subfinder(raw: str) -> dict:
        """Parse subfinder output - one subdomain per line."""
        subdomains = [line.strip() for line in raw.splitlines() if line.strip()]
        return {"subdomains": subdomains, "count": len(subdomains)}

    @staticmethod
    def whatweb(raw: str) -> dict:
        """Parse whatweb output into tech fingerprint."""
        result = {"targets": []}
        for line in raw.splitlines():
            if line.strip():
                result["targets"].append({"raw": line.strip()})
        return result

    @staticmethod
    def crackmapexec(raw: str) -> dict:
        """Parse CME output for SMB/LDAP/WinRM results."""
        result = {"hosts": [], "findings": []}
        for line in raw.splitlines():
            if "SMB" in line or "LDAP" in line or "WINRM" in line:
                result["hosts"].append({"raw": line.strip()})
            if "[+]" in line:
                result["findings"].append(line.strip())
        return result

    @staticmethod
    def nuclei(raw: str) -> dict:
        """Parse nuclei findings."""
        findings = []
        for line in raw.splitlines():
            # nuclei output format: [template-id] [severity] target
            match = re.match(r"\[(.+?)\]\s+\[(.+?)\]\s+(.+)", line)
            if match:
                findings.append({
                    "template": match.group(1),
                    "severity": match.group(2),
                    "target": match.group(3).strip()
                })
        return {"findings": findings, "count": len(findings)}

    @staticmethod
    def ffuf(raw: str) -> dict:
        """Parse ffuf directory fuzzing output."""
        results = []
        for line in raw.splitlines():
            # Look for status code lines
            match = re.search(r"\[Status: (\d+).*Words: (\d+).*Lines: (\d+)\].*:: (.+)", line)
            if match:
                results.append({
                    "status": int(match.group(1)),
                    "words": match.group(2),
                    "lines": match.group(3),
                    "path": match.group(4).strip()
                })
        return {"results": results, "count": len(results)}

    @staticmethod
    def generic(raw: str) -> dict:
        """Fallback parser - just wraps raw output."""
        return {"raw": raw, "lines": raw.splitlines()}
