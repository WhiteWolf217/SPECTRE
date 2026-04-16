from rich.console import Console
from rich.table import Table

console = Console()

# MITRE ATT&CK tagged port → tool chain map
PORT_CHAINS = {
    21: {
        "service": "FTP",
        "ttps": ["T1190", "T1078"],
        "chain": [
            {"tool": "nmap",         "desc": "FTP version + anon check",         "flags": "--script ftp-anon,ftp-syst,ftp-vsftpd-backdoor -p 21", "destructive": False},
            {"tool": "hydra",        "desc": "FTP credential brute force",        "flags": "-L users.txt -P passwords.txt ftp://{target}",          "destructive": True},
        ]
    },
    22: {
        "service": "SSH",
        "ttps": ["T1190", "T1078"],
        "chain": [
            {"tool": "nmap",         "desc": "SSH version + auth methods",        "flags": "--script ssh-auth-methods,ssh-hostkey -p 22",            "destructive": False},
            {"tool": "hydra",        "desc": "SSH credential brute force",        "flags": "-L users.txt -P passwords.txt ssh://{target}",           "destructive": True},
        ]
    },
    25: {
        "service": "SMTP",
        "ttps": ["T1596", "T1114"],
        "chain": [
            {"tool": "nmap",         "desc": "SMTP user enum + open relay check", "flags": "--script smtp-enum-users,smtp-open-relay -p 25",          "destructive": False},
            {"tool": "theHarvester", "desc": "Email OSINT for target domain",     "flags": "-d {domain} -b all",                                     "destructive": False},
        ]
    },
    80: {
        "service": "HTTP",
        "ttps": ["T1190", "T1595"],
        "chain": [
            {"tool": "whatweb",      "desc": "Tech stack fingerprint",            "flags": "{target}",                                               "destructive": False},
            {"tool": "nuclei",       "desc": "CVE + vuln template scan",          "flags": "-u http://{target} -severity critical,high,medium",      "destructive": False},
            {"tool": "ffuf",         "desc": "Directory fuzzing",                 "flags": "-u http://{target}/FUZZ -w /usr/share/wordlists/dirb/common.txt", "destructive": False},
            {"tool": "nikto",        "desc": "Web server misconfig scan",         "flags": "-h http://{target}",                                     "destructive": False},
            {"tool": "sqlmap",       "desc": "SQL injection scan",                "flags": "-u http://{target} --forms --dbs --batch",               "destructive": True},
            {"tool": "dalfox",       "desc": "XSS scanning",                      "flags": "url http://{target}",                                    "destructive": False},
        ]
    },
    443: {
        "service": "HTTPS",
        "ttps": ["T1190", "T1595"],
        "chain": [
            {"tool": "whatweb",      "desc": "Tech stack fingerprint",            "flags": "https://{target}",                                       "destructive": False},
            {"tool": "nuclei",       "desc": "CVE + vuln template scan",          "flags": "-u https://{target} -severity critical,high,medium",     "destructive": False},
            {"tool": "ffuf",         "desc": "Directory fuzzing",                 "flags": "-u https://{target}/FUZZ -w /usr/share/wordlists/dirb/common.txt", "destructive": False},
            {"tool": "nikto",        "desc": "Web server misconfig scan",         "flags": "-h https://{target}",                                    "destructive": False},
            {"tool": "sqlmap",       "desc": "SQL injection scan",                "flags": "-u https://{target} --forms --dbs --batch",              "destructive": True},
            {"tool": "dalfox",       "desc": "XSS scanning",                      "flags": "url https://{target}",                                   "destructive": False},
        ]
    },
    389: {
        "service": "LDAP",
        "ttps": ["T1087", "T1069"],
        "chain": [
            {"tool": "nmap",            "desc": "LDAP info enum",                "flags": "--script ldap-rootdse,ldap-search -p 389",               "destructive": False},
            {"tool": "ldapdomaindump",  "desc": "LDAP anonymous dump",           "flags": "-u '' -p '' ldap://{target}",                            "destructive": False},
            {"tool": "bloodhound",      "desc": "AD graph collection",           "flags": "-c All -d {domain} -u {user} -p {pass} --zip",           "destructive": False},
            {"tool": "certipy",         "desc": "AD CS template enum",           "flags": "find -u {user}@{domain} -p {pass} -dc-ip {target}",      "destructive": False},
        ]
    },
    445: {
        "service": "SMB",
        "ttps": ["T1021", "T1135", "T1557"],
        "chain": [
            {"tool": "nmap",          "desc": "SMB vuln scan (EternalBlue etc)", "flags": "--script smb-vuln-* -p 445",                             "destructive": False},
            {"tool": "crackmapexec",  "desc": "SMB enum + signing check",        "flags": "smb {target}",                                           "destructive": False},
            {"tool": "crackmapexec",  "desc": "Null session share enum",         "flags": "smb {target} --shares",                                  "destructive": False},
            {"tool": "crackmapexec",  "desc": "User enumeration",                "flags": "smb {target} --users",                                   "destructive": False},
            {"tool": "impacket",      "desc": "secretsdump (needs creds)",        "flags": "secretsdump {domain}/{user}:{pass}@{target}",            "destructive": True},
        ]
    },
    1433: {
        "service": "MSSQL",
        "ttps": ["T1190", "T1505"],
        "chain": [
            {"tool": "nmap",         "desc": "MSSQL info enum",                  "flags": "--script ms-sql-info,ms-sql-empty-password -p 1433",      "destructive": False},
            {"tool": "crackmapexec", "desc": "MSSQL auth check",                 "flags": "mssql {target} -u sa -p ''",                             "destructive": False},
            {"tool": "sqlmap",       "desc": "MSSQL injection test",             "flags": "-d 'mssql://{target}/master' --dbs --batch",             "destructive": True},
        ]
    },
    3306: {
        "service": "MySQL",
        "ttps": ["T1190"],
        "chain": [
            {"tool": "nmap",   "desc": "MySQL info + empty password check",      "flags": "--script mysql-info,mysql-empty-password -p 3306",        "destructive": False},
            {"tool": "hydra",  "desc": "MySQL credential brute",                 "flags": "-L users.txt -P passwords.txt mysql://{target}",          "destructive": True},
        ]
    },
    3389: {
        "service": "RDP",
        "ttps": ["T1021.001", "T1110"],
        "chain": [
            {"tool": "nmap",         "desc": "RDP vuln scan (BlueKeep etc)",     "flags": "--script rdp-vuln-ms12-020,rdp-enum-encryption -p 3389",  "destructive": False},
            {"tool": "nuclei",       "desc": "BlueKeep CVE-2019-0708 check",     "flags": "-u rdp://{target}:3389 -t cves/",                        "destructive": False},
            {"tool": "hydra",        "desc": "RDP credential spray",             "flags": "-L users.txt -P passwords.txt rdp://{target}",            "destructive": True},
        ]
    },
    5985: {
        "service": "WinRM",
        "ttps": ["T1021.006"],
        "chain": [
            {"tool": "crackmapexec", "desc": "WinRM auth check",                 "flags": "winrm {target}",                                         "destructive": False},
            {"tool": "crackmapexec", "desc": "WinRM login with creds",           "flags": "winrm {target} -u {user} -p {pass}",                     "destructive": True},
        ]
    },
    5986: {
        "service": "WinRM (SSL)",
        "ttps": ["T1021.006"],
        "chain": [
            {"tool": "crackmapexec", "desc": "WinRM SSL auth check",             "flags": "winrm {target} --ssl",                                   "destructive": False},
        ]
    },
    8080: {
        "service": "HTTP-ALT",
        "ttps": ["T1190"],
        "chain": [
            {"tool": "whatweb",  "desc": "Tech fingerprint",                     "flags": "http://{target}:8080",                                   "destructive": False},
            {"tool": "nuclei",   "desc": "Vuln scan",                            "flags": "-u http://{target}:8080",                                "destructive": False},
            {"tool": "ffuf",     "desc": "Directory fuzzing",                    "flags": "-u http://{target}:8080/FUZZ -w /usr/share/wordlists/dirb/common.txt", "destructive": False},
        ]
    },
}


def dispatch(open_ports: list, target: str = "{target}") -> dict:
    """
    Given a list of open ports, return suggested attack chains.
    """
    chains = {}
    for port in open_ports:
        if port in PORT_CHAINS:
            entry = PORT_CHAINS[port].copy()
            # Substitute target into flags
            for step in entry["chain"]:
                step["flags"] = step["flags"].replace("{target}", target)
            chains[port] = entry
    return chains


def display_dispatch(open_ports: list, target: str = "{target}"):
    """Pretty-print the dispatch table using Rich."""
    chains = dispatch(open_ports, target)

    if not chains:
        console.print("[yellow]No known attack chains for discovered ports.[/yellow]")
        return

    console.print(f"\n[bold cyan]═══ ATTACK CHAIN DISPATCH ═══[/bold cyan]")
    console.print(f"[dim]Target: {target}[/dim]\n")

    for port, data in chains.items():
        table = Table(
            title=f"Port {port} — {data['service']}  [dim]TTPs: {', '.join(data['ttps'])}[/dim]",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan"
        )
        table.add_column("#",       style="dim",    width=3)
        table.add_column("Tool",    style="cyan",   width=16)
        table.add_column("Action",  style="white",  width=35)
        table.add_column("⚠",       style="yellow", width=5)

        for i, step in enumerate(data["chain"], 1):
            destructive = "[red]YES[/red]" if step["destructive"] else "[green]no[/green]"
            table.add_row(str(i), step["tool"], step["desc"], destructive)

        console.print(table)
        console.print()
