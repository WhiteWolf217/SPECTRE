from tools.base import BaseTool
from core.parser import Parser


class CrackMapExec(BaseTool):
    name = "crackmapexec"
    description = "SMB/LDAP/WinRM/MSSQL enumeration and spraying"
    requires_confirmation = False  # set True per-run for --exec

    def _run(self, proto: str, target: str, flags: str = "") -> dict:
        cmd = ["crackmapexec", proto, target] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=120)
        if result["success"]:
            result["parsed"] = Parser.crackmapexec(result["stdout"])
        return result


class BloodHound(BaseTool):
    name = "bloodhound-python"
    description = "Active Directory attack path collection"
    requires_confirmation = False

    def _run(self, domain: str, user: str, password: str, dc_ip: str, flags: str = "-c All --zip") -> dict:
        cmd = ["bloodhound-python", "-d", domain, "-u", user, "-p", password, "--dc", dc_ip] + flags.split()
        result = self._exec(cmd, timeout=600)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Impacket(BaseTool):
    name = "impacket-secretsdump"
    description = "Dump credentials via Impacket"
    requires_confirmation = True  # destructive

    def _run(self, target: str, flags: str = "") -> dict:
        cmd = ["impacket-secretsdump"] + (flags.split() if flags else []) + [target]
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Kerbrute(BaseTool):
    name = "kerbrute"
    description = "Kerberos user enumeration and brute force"
    requires_confirmation = False

    def _run(self, mode: str, domain: str, dc_ip: str, wordlist: str, flags: str = "") -> dict:
        # mode: userenum | passwordspray | bruteuser
        cmd = ["kerbrute", mode, "--dc", dc_ip, "--domain", domain, wordlist] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class Certipy(BaseTool):
    name = "certipy"
    description = "AD Certificate Services attack tool"
    requires_confirmation = False

    def _run(self, mode: str, flags: str = "") -> dict:
        # mode: find | auth | req | shadow | relay | forge
        cmd = ["certipy", mode] + (flags.split() if flags else [])
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result


class LdapDomainDump(BaseTool):
    name = "ldapdomaindump"
    description = "LDAP enumeration and domain dump"
    requires_confirmation = False

    def _run(self, target: str, user: str = "", password: str = "", flags: str = "") -> dict:
        cmd = ["ldapdomaindump"]
        if user:
            cmd += ["-u", user]
        if password:
            cmd += ["-p", password]
        cmd += (flags.split() if flags else []) + [f"ldap://{target}"]
        result = self._exec(cmd, timeout=300)
        if result["success"]:
            result["parsed"] = Parser.generic(result["stdout"])
        return result
