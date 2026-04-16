from tools.base import BaseTool
from core.parser import Parser


class Subfinder(BaseTool):
    name = "subfinder"
    description = "Subdomain enumeration"
    requires_confirmation = False

    def _run(self, domain: str, flags: str = "-silent") -> dict:
        cmd = ["subfinder", "-d", domain] + flags.split()
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.subfinder(result["stdout"])
        return result


class Amass(BaseTool):
    name = "amass"
    description = "Deep subdomain + OSINT enumeration"
    requires_confirmation = False

    def _run(self, domain: str, flags: str = "enum -passive") -> dict:
        cmd = ["amass"] + flags.split() + ["-d", domain]
        result = self._exec(cmd, timeout=600)
        if result["success"]:
            result["parsed"] = Parser.subfinder(result["stdout"])  # same format
        return result


class WhatWeb(BaseTool):
    name = "whatweb"
    description = "Web technology fingerprinting"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "-a 3") -> dict:
        cmd = ["whatweb"] + flags.split() + [target]
        result = self._exec(cmd, timeout=120)
        if result["success"]:
            result["parsed"] = Parser.whatweb(result["stdout"])
        return result


class TheHarvester(BaseTool):
    name = "theHarvester"
    description = "Email, domain, and IP OSINT"
    requires_confirmation = False

    def _run(self, domain: str, sources: str = "all") -> dict:
        cmd = ["theHarvester", "-d", domain, "-b", sources]
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Whois(BaseTool):
    name = "whois"
    description = "Domain registration info"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "") -> dict:
        cmd = ["whois"] + (flags.split() if flags else []) + [target]
        result = self._exec(cmd, timeout=30)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result
