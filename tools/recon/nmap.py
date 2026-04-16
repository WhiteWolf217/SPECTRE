from tools.base import BaseTool
from core.parser import Parser


class Nmap(BaseTool):
    name = "nmap"
    description = "Port scanner and service/OS detection"
    requires_confirmation = False

    def _run(self, target: str, flags: str = "-sV -sC") -> dict:
        cmd = ["nmap"] + flags.split() + [target]
        result = self._exec(cmd, timeout=600)
        if result["success"]:
            result["parsed"] = Parser.nmap(result["stdout"])
        return result
