#!/home/whitewolf/Desktop/tools/venv/bin/python3
import sys
import os

# Resolve symlink to get the real path
script_path = os.path.realpath(__file__)
project_root = os.path.dirname(os.path.dirname(script_path))
sys.path.insert(0, project_root)

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from typing import Optional

from db.store import Store
from core.executor import Executor
from core.port_dispatch import display_dispatch
from report.generator import ReportGenerator

# Tool imports
from tools.recon.nmap import Nmap
from tools.recon.recon import Subfinder, Amass, WhatWeb, TheHarvester, Whois
from tools.web.web import Nuclei, Ffuf, Sqlmap, Nikto, Dalfox, Feroxbuster
from tools.ad.ad import CrackMapExec, BloodHound, Impacket, Kerbrute, Certipy, LdapDomainDump
from tools.bruteforce.bruteforce import Hydra, Hashcat, John

app = typer.Typer(
    name="spectre",
    help="[bold red]SPECTRE[/bold red] — Red Team Automation Platform",
    rich_markup_mode="rich",
    no_args_is_help=True
)

console = Console()
store = Store()

BANNER = """
[bold red]
███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗  
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝  
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝[/bold red]
[dim]Red Team Automation Platform — Phase 1[/dim]
"""

# ─── Tool registry ────────────────────────────────────────────────────────────
TOOLS = {
    # recon
    "nmap":            Nmap(),
    "subfinder":       Subfinder(),
    "amass":           Amass(),
    "whatweb":         WhatWeb(),
    "theharvester":    TheHarvester(),
    "whois":           Whois(),
    # web
    "nuclei":          Nuclei(),
    "ffuf":            Ffuf(),
    "sqlmap":          Sqlmap(),
    "nikto":           Nikto(),
    "dalfox":          Dalfox(),
    "feroxbuster":     Feroxbuster(),
    # ad
    "crackmapexec":    CrackMapExec(),
    "bloodhound":      BloodHound(),
    "impacket":        Impacket(),
    "kerbrute":        Kerbrute(),
    "certipy":         Certipy(),
    "ldapdomaindump":  LdapDomainDump(),
    # bruteforce
    "hydra":           Hydra(),
    "hashcat":         Hashcat(),
    "john":            John(),
}

# ─── State: active engagement ─────────────────────────────────────────────────
def get_active_eid() -> Optional[int]:
    state_file = os.path.expanduser("~/.spectre/.active")
    if os.path.exists(state_file):
        with open(state_file) as f:
            return int(f.read().strip())
    return None

def set_active_eid(eid: int):
    os.makedirs(os.path.expanduser("~/.spectre"), exist_ok=True)
    with open(os.path.expanduser("~/.spectre/.active"), "w") as f:
        f.write(str(eid))

# ─── Commands ─────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def banner(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print(BANNER)


@app.command("new")
def new_engagement(
    target: str = typer.Option(..., "--target", "-t", help="Target IP, range, or domain"),
    name:   str = typer.Option("", "--name",   "-n", help="Engagement name"),
    type_:  str = typer.Option("external", "--type", help="external | internal | web | ad"),
    scope:  str = typer.Option("", "--scope",  "-s", help="Scope definition"),
):
    """Start a new engagement."""
    console.print(BANNER)
    if not name:
        name = f"engagement_{target}"
    eid = store.new_engagement(name=name, target=target, eng_type=type_, scope=scope)
    set_active_eid(eid)
    console.print(Panel(
        f"[bold green]Engagement created[/bold green]\n\n"
        f"  ID:     [cyan]{eid}[/cyan]\n"
        f"  Name:   [white]{name}[/white]\n"
        f"  Target: [white]{target}[/white]\n"
        f"  Type:   [white]{type_}[/white]",
        title="[bold red]SPECTRE[/bold red]",
        border_style="red"
    ))


@app.command("engagements")
def list_engagements():
    """List all engagements."""
    active = get_active_eid()
    engagements = store.list_engagements()
    if not engagements:
        console.print("[yellow]No engagements found. Run: spectre new --target <ip>[/yellow]")
        return

    table = Table(title="Engagements", border_style="red", header_style="bold magenta")
    table.add_column("ID",     width=5)
    table.add_column("Name",   width=25)
    table.add_column("Target", width=20)
    table.add_column("Type",   width=10)
    table.add_column("Status", width=10)
    table.add_column("Active", width=8)

    for e in engagements:
        is_active = "✅" if e["id"] == active else ""
        table.add_row(
            str(e["id"]), e["name"], e["target"],
            e["type"], e["status"], is_active
        )
    console.print(table)


@app.command("use")
def use_engagement(eid: int = typer.Argument(..., help="Engagement ID to switch to")):
    """Switch active engagement."""
    eng = store.get_engagement(eid)
    if not eng:
        console.print(f"[red]Engagement {eid} not found.[/red]")
        raise typer.Exit(1)
    set_active_eid(eid)
    console.print(f"[green][+] Active engagement set to:[/green] {eng['name']} ({eng['target']})")


@app.command("delete")
def delete_engagement(
    eid: int = typer.Argument(..., help="Engagement ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an engagement and all associated data."""
    eng = store.get_engagement(eid)
    if not eng:
        console.print(f"[red]Engagement {eid} not found.[/red]")
        raise typer.Exit(1)

    if not force:
        console.print(f"[yellow]⚠ Delete engagement #{eid} '{eng['name']}'?[/yellow]")
        if not typer.confirm("This will remove all findings and tool runs"):
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    store.delete_engagement(eid)

    # Clear active engagement if it was deleted
    if get_active_eid() == eid:
        state_file = os.path.expanduser("~/.spectre/.active")
        if os.path.exists(state_file):
            os.remove(state_file)

    console.print(f"[green][+] Engagement #{eid} deleted.[/green]")


@app.command("run")
def run_tool(
    tool_name: str = typer.Argument(..., help="Tool to run"),
    target:    str = typer.Option("",  "--target", "-t", help="Target"),
    flags:     str = typer.Option("",  "--flags",  "-f", help="Tool flags/arguments"),
    nosave:    bool = typer.Option(False, "--no-save",    help="Don't save to DB"),
):
    """Run a specific tool."""
    eid = get_active_eid()
    if not eid:
        console.print("[red]No active engagement. Run: spectre new --target <ip>[/red]")
        raise typer.Exit(1)

    tool = TOOLS.get(tool_name.lower())
    if not tool:
        console.print(f"[red]Unknown tool: {tool_name}[/red]")
        console.print(f"[dim]Available: {', '.join(TOOLS.keys())}[/dim]")
        raise typer.Exit(1)

    eng = store.get_engagement(eid)
    effective_target = target or eng["target"]

    executor = Executor(
        db_store=None if nosave else store,
        engagement_id=eid
    )

    # Build kwargs based on tool type
    kwargs = {"target": effective_target}
    if flags:
        kwargs["flags"] = flags

    executor.run(tool, save=not nosave, **kwargs)


@app.command("dispatch")
def dispatch_ports(
    ports: str = typer.Argument(..., help="Comma-separated open ports e.g. 22,80,445,3389"),
    target: str = typer.Option("", "--target", "-t", help="Target IP (uses engagement target if blank)"),
):
    """Show attack chain suggestions for open ports."""
    eid = get_active_eid()
    effective_target = target
    if not effective_target and eid:
        eng = store.get_engagement(eid)
        effective_target = eng["target"] if eng else "{target}"

    port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]
    display_dispatch(port_list, effective_target)


@app.command("tools")
def list_tools():
    """List all available tools and their status."""
    table = Table(title="Available Tools", border_style="red", header_style="bold magenta")
    table.add_column("Tool",        width=20)
    table.add_column("Category",    width=12)
    table.add_column("Description", width=40)
    table.add_column("Installed",   width=10)
    table.add_column("⚠ Confirm",   width=10)

    categories = {
        "nmap": "recon", "subfinder": "recon", "amass": "recon",
        "whatweb": "recon", "theharvester": "recon", "whois": "recon",
        "nuclei": "web", "ffuf": "web", "sqlmap": "web",
        "nikto": "web", "dalfox": "web", "feroxbuster": "web",
        "crackmapexec": "ad", "bloodhound": "ad", "impacket": "ad",
        "kerbrute": "ad", "certipy": "ad", "ldapdomaindump": "ad",
        "hydra": "bruteforce", "hashcat": "bruteforce", "john": "bruteforce",
    }

    for name, tool in TOOLS.items():
        installed = "[green]✅[/green]" if tool.check_installed() else "[red]❌[/red]"
        confirm = "[red]YES[/red]" if tool.requires_confirmation else "[dim]no[/dim]"
        table.add_row(
            name,
            categories.get(name, "misc"),
            tool.description,
            installed,
            confirm
        )
    console.print(table)


@app.command("findings")
def list_findings(
    eid: Optional[int] = typer.Option(None, "--engagement", "-e", help="Engagement ID (default: active)")
):
    """List findings for current engagement."""
    engagement_id = eid or get_active_eid()
    if not engagement_id:
        console.print("[red]No active engagement.[/red]")
        raise typer.Exit(1)

    findings = store.list_findings(engagement_id)
    if not findings:
        console.print("[yellow]No findings recorded yet.[/yellow]")
        return

    SEVERITY_COLORS = {
        "critical": "bold red", "high": "red",
        "medium": "yellow", "low": "cyan", "info": "dim"
    }

    table = Table(title=f"Findings — Engagement {engagement_id}", border_style="red", header_style="bold magenta")
    table.add_column("ID",       width=5)
    table.add_column("Severity", width=10)
    table.add_column("Title",    width=35)
    table.add_column("Host",     width=18)
    table.add_column("TTP",      width=14)
    table.add_column("Tool",     width=14)

    for f in findings:
        sev = f.get("severity", "info")
        color = SEVERITY_COLORS.get(sev, "white")
        table.add_row(
            str(f["id"]),
            f"[{color}]{sev.upper()}[/{color}]",
            f["title"],
            f.get("host", ""),
            f.get("ttp", ""),
            f.get("tool", ""),
        )
    console.print(table)


@app.command("add-finding")
def add_finding(
    title:       str = typer.Option(..., "--title",    "-t",  help="Finding title"),
    severity:    str = typer.Option("medium", "--severity", "-s", help="critical|high|medium|low|info"),
    description: str = typer.Option("", "--desc",     "-d",  help="Description"),
    ttp:         str = typer.Option("", "--ttp",             help="MITRE ATT&CK TTP e.g. T1190"),
    host:        str = typer.Option("", "--host",            help="Affected host"),
    port:        Optional[int] = typer.Option(None, "--port", help="Affected port"),
    tool:        str = typer.Option("", "--tool",            help="Tool that found it"),
    evidence:    str = typer.Option("", "--evidence",        help="Evidence snippet"),
):
    """Manually add a finding to the current engagement."""
    eid = get_active_eid()
    if not eid:
        console.print("[red]No active engagement.[/red]")
        raise typer.Exit(1)

    fid = store.add_finding(
        engagement_id=eid, title=title, description=description,
        severity=severity, ttp=ttp, evidence=evidence,
        host=host, port=port, tool=tool
    )
    console.print(f"[green][+] Finding added:[/green] ID {fid} — {title} [{severity.upper()}]")


@app.command("report")
def generate_report(
    format_: str = typer.Option("md", "--format", "-f", help="md | pdf"),
    eid: Optional[int] = typer.Option(None, "--engagement", "-e", help="Engagement ID"),
):
    """Generate penetration test report."""
    engagement_id = eid or get_active_eid()
    if not engagement_id:
        console.print("[red]No active engagement.[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan][*] Generating {format_.upper()} report...[/cyan]")
    gen = ReportGenerator(store)
    path = gen.generate(engagement_id, output_format=format_)
    console.print(f"[bold green][+] Report saved:[/bold green] {path}")


@app.command("status")
def status():
    """Show current engagement status."""
    eid = get_active_eid()
    if not eid:
        console.print("[yellow]No active engagement. Run: spectre new --target <ip>[/yellow]")
        return

    eng = store.get_engagement(eid)
    findings = store.list_findings(eid)
    runs = store.list_tool_runs(eid)

    sev_counts = {}
    for f in findings:
        s = f.get("severity", "info")
        sev_counts[s] = sev_counts.get(s, 0) + 1

    console.print(Panel(
        f"[bold]Engagement:[/bold] {eng['name']}\n"
        f"[bold]Target:[/bold]     {eng['target']}\n"
        f"[bold]Type:[/bold]       {eng['type']}\n\n"
        f"[bold]Tool Runs:[/bold]  {len(runs)}\n"
        f"[bold]Findings:[/bold]   {len(findings)} total  "
        f"[red]{sev_counts.get('critical',0)}C[/red] "
        f"[red]{sev_counts.get('high',0)}H[/red] "
        f"[yellow]{sev_counts.get('medium',0)}M[/yellow] "
        f"[cyan]{sev_counts.get('low',0)}L[/cyan]",
        title=f"[bold red]SPECTRE[/bold red] — Engagement #{eid}",
        border_style="red"
    ))


if __name__ == "__main__":
    app()
