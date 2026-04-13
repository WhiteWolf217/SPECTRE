from tools.base import BaseTool
from core.parser import Parser


class Hydra(BaseTool):
    name = "hydra"
    description = "Online credential brute force"
    requires_confirmation = True  # always destructive/noisy

    def _run(self, target: str, proto: str, userlist: str, passlist: str, flags: str = "-t 4") -> dict:
        cmd = ["hydra", "-L", userlist, "-P", passlist] + flags.split() + [f"{proto}://{target}"]
        result = self._exec(cmd, timeout=600)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Hashcat(BaseTool):
    name = "hashcat"
    description = "Offline GPU/CPU hash cracking"
    requires_confirmation = False

    def _run(self, hashfile: str, wordlist: str, mode: str = "0", flags: str = "") -> dict:
        # mode 0=MD5, 1000=NTLM, 13100=Kerberoast, 1800=sha512crypt etc
        cmd = ["hashcat", "-m", mode, hashfile, wordlist] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=3600)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class John(BaseTool):
    name = "john"
    description = "Offline hash cracking (John the Ripper)"
    requires_confirmation = False

    def _run(self, hashfile: str, wordlist: str = "/usr/share/wordlists/rockyou.txt", flags: str = "") -> dict:
        cmd = ["john", f"--wordlist={wordlist}"] + (flags.split() if flags else []) + [hashfile]
        result = self._exec(cmd, timeout=3600)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result
