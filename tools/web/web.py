from tools.base import BaseTool
from core.parser import Parser


class Nuclei(BaseTool):
    name = "nuclei"
    description = "Template-based vulnerability scanner"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "-severity critical,high,medium") -> dict:
        cmd = ["nuclei", "-u", target] + flags.split()
        result = self._exec(cmd, timeout=600)
        if result["success"]:
            result["parsed"] = Parser.nuclei(result["stdout"])
        return result


class Ffuf(BaseTool):
    name = "ffuf"
    description = "Web fuzzer - directories, vhosts, parameters"
    requires_confirmation = False

    def _run(self, target: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", flags: str = "") -> dict:
        cmd = ["ffuf", "-u", target, "-w", wordlist] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.ffuf(result["stdout"])
        return result


class Sqlmap(BaseTool):
    name = "sqlmap"
    description = "SQL injection detection and exploitation"
    requires_confirmation = True  # destructive

    def _run(self, target: str, flags: str = "--forms --dbs --batch") -> dict:
        cmd = ["sqlmap", "-u", target] + flags.split()
        result = self._exec(cmd, timeout=600)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Nikto(BaseTool):
    name = "nikto"
    description = "Web server misconfiguration scanner"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "") -> dict:
        cmd = ["nikto", "-h", target] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Dalfox(BaseTool):
    name = "dalfox"
    description = "XSS scanner"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "") -> dict:
        cmd = ["dalfox", "url", target] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Feroxbuster(BaseTool):
    name = "feroxbuster"
    description = "Fast content discovery"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "--silent") -> dict:
        cmd = ["feroxbuster", "-u", target] + flags.split()
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result
