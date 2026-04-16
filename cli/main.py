#!/usr/bin/env python3
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
from tools.exploit.cve import CVESearch, CVEAutoScan
from tools.evasion.evasion import EvasionTool

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
[dim]Red Team Automation Platform — Manual[/dim]
"""

# ─── Tool registry ─────────────────────────────────────────────────────────────
TOOLS = {
    # recon
    "nmap":           Nmap(),
    "subfinder":      Subfinder(),
    "amass":          Amass(),
    "whatweb":        WhatWeb(),
    "theharvester":   TheHarvester(),
    "whois":          Whois(),
    # web
    "nuclei":         Nuclei(),
    "ffuf":           Ffuf(),
    "sqlmap":         Sqlmap(),
    "nikto":          Nikto(),
    "dalfox":         Dalfox(),
    "feroxbuster":    Feroxbuster(),
    # ad
    "crackmapexec":   CrackMapExec(),
    "bloodhound":     BloodHound(),
    "impacket":       Impacket(),
    "kerbrute":       Kerbrute(),
    "certipy":        Certipy(),
    "ldapdomaindump": LdapDomainDump(),
    # bruteforce
    "hydra":          Hydra(),
    "hashcat":        Hashcat(),
    "john":           John(),
    # cve
    "cve-search":     CVESearch(),
    "cve-autoscan":   CVEAutoScan(),
}

TOOL_CATEGORIES = {
    "nmap": "recon", "subfinder": "recon", "amass": "recon",
    "whatweb": "recon", "theharvester": "recon", "whois": "recon",
    "nuclei": "web", "ffuf": "web", "sqlmap": "web",
    "nikto": "web", "dalfox": "web", "feroxbuster": "web",
    "crackmapexec": "ad", "bloodhound": "ad", "impacket": "ad",
    "kerbrute": "ad", "certipy": "ad", "ldapdomaindump": "ad",
    "hydra": "bruteforce", "hashcat": "bruteforce", "john": "bruteforce",
    "cve-search": "cve", "cve-autoscan": "cve",
}

SEVERITY_COLORS = {
    "critical": "bold red",
    "high":     "red",
    "medium":   "yellow",
    "low":      "cyan",
    "info":     "dim",
}

# ─── State helpers ─────────────────────────────────────────────────────────────
def get_active_eid() -> Optional[int]:
    state_file = os.path.expanduser("~/.spectre/.active")
    if os.path.exists(state_file):
        with open(state_file) as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None
    return None

def set_active_eid(eid: int):
    os.makedirs(os.path.expanduser("~/.spectre"), exist_ok=True)
    with open(os.path.expanduser("~/.spectre/.active"), "w") as f:
        f.write(str(eid))

def clear_active_eid():
    state_file = os.path.expanduser("~/.spectre/.active")
    if os.path.exists(state_file):
        os.remove(state_file)

def resolve_eid(eid: Optional[int]) -> Optional[int]:
    """Return provided eid or fall back to active engagement."""
    return eid if eid is not None else get_active_eid()

# ─── Commands ──────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def banner(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        console.print(BANNER)


# ── new ────────────────────────────────────────────────────────────────────────
@app.command("new")
def new_engagement(
    target: str = typer.Option(..., "--target", "-t", help="Target IP, range, or domain"),
    name:   str = typer.Option("",  "--name",   "-n", help="Engagement name"),
    type_:  str = typer.Option("external", "--type",  help="external | internal | web | ad"),
    scope:  str = typer.Option("",  "--scope",  "-s",  help="Scope definition"),
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


# ── engagements ────────────────────────────────────────────────────────────────
@app.command("engagements")
def list_engagements():
    """List all engagements with finding counts."""
    active = get_active_eid()
    engagements = store.list_engagements()
    if not engagements:
        console.print("[yellow]No engagements found. Run: spectre new --target <ip>[/yellow]")
        return

    table = Table(title="Engagements", border_style="red", header_style="bold magenta")
    table.add_column("ID",       style="cyan", width=5)
    table.add_column("Name",                   width=22)
    table.add_column("Target",                 width=18)
    table.add_column("Type",     style="dim",  width=10)
    table.add_column("Findings",               width=16)
    table.add_column("Runs",                   width=6)
    table.add_column("Status",                 width=10)
    table.add_column("Active",                 width=10)

    for e in engagements:
        findings = store.list_findings(e["id"])
        runs     = store.list_tool_runs(e["id"])

        crit  = sum(1 for f in findings if f.get("severity") == "critical")
        high  = sum(1 for f in findings if f.get("severity") == "high")
        med   = sum(1 for f in findings if f.get("severity") == "medium")
        total = len(findings)

        finding_str = f"{total} total"
        if crit: finding_str += f"  [bold red]{crit}C[/bold red]"
        if high: finding_str += f"  [red]{high}H[/red]"
        if med:  finding_str += f"  [yellow]{med}M[/yellow]"

        is_active = "[bold green]✅ ACTIVE[/bold green]" if e["id"] == active else ""

        table.add_row(
            str(e["id"]),
            e["name"],
            e["target"],
            e["type"],
            finding_str,
            str(len(runs)),
            e["status"],
            is_active,
        )

    console.print(table)
    console.print("[dim]Switch: spectre use <ID>  |  Target specific: spectre run <tool> -e <ID>[/dim]")


# ── use ────────────────────────────────────────────────────────────────────────
@app.command("use")
def use_engagement(eid: int = typer.Argument(..., help="Engagement ID to switch to")):
    """Switch active engagement."""
    eng = store.get_engagement(eid)
    if not eng:
        console.print(f"[red]Engagement {eid} not found.[/red]")
        raise typer.Exit(1)
    set_active_eid(eid)
    console.print(f"[green][+] Active engagement:[/green] #{eid} — {eng['name']} ({eng['target']})")


# ── delete ─────────────────────────────────────────────────────────────────────
@app.command("delete")
def delete_engagement(
    eid:   int  = typer.Argument(..., help="Engagement ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an engagement and all associated findings and tool runs."""
    eng = store.get_engagement(eid)
    if not eng:
        console.print(f"[red]Engagement {eid} not found.[/red]")
        raise typer.Exit(1)

    findings = store.list_findings(eid)
    runs     = store.list_tool_runs(eid)

    if not force:
        console.print(Panel(
            f"[bold yellow]⚠  About to delete:[/bold yellow]\n\n"
            f"  Engagement: [white]#{eid} — {eng['name']}[/white]\n"
            f"  Target:     [white]{eng['target']}[/white]\n"
            f"  Findings:   [red]{len(findings)}[/red]\n"
            f"  Tool runs:  [red]{len(runs)}[/red]\n\n"
            f"[dim]This cannot be undone.[/dim]",
            title="[bold red]DELETE CONFIRMATION[/bold red]",
            border_style="red"
        ))
        if not typer.confirm("Confirm deletion?"):
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(0)

    success = store.delete_engagement(eid)

    if success:
        # Clear .active if the deleted engagement was active
        if get_active_eid() == eid:
            clear_active_eid()
            console.print("[yellow][!] Active engagement cleared — run 'spectre use <ID>' to set a new one.[/yellow]")
        console.print(f"[green][+] Engagement #{eid} '{eng['name']}' deleted.[/green]")
    else:
        console.print(f"[red][-] Failed to delete engagement #{eid}.[/red]")
        raise typer.Exit(1)


# ── run ────────────────────────────────────────────────────────────────────────
@app.command("run")
def run_tool(
    tool_name: str           = typer.Argument(...,  help="Tool to run"),
    target:    str           = typer.Option("",    "--target", "-t", help="Override target"),
    flags:     str           = typer.Option("",    "--flags",  "-f", help="Tool flags/arguments"),
    nosave:    bool          = typer.Option(False,  "--no-save",     help="Don't save to DB"),
    eid:       Optional[int] = typer.Option(None,  "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """Run a specific tool against an engagement."""
    engagement_id = resolve_eid(eid)
    if not engagement_id:
        console.print("[red]No active engagement. Run: spectre new --target <ip>[/red]")
        raise typer.Exit(1)

    tool = TOOLS.get(tool_name.lower())
    if not tool:
        console.print(f"[red]Unknown tool: {tool_name}[/red]")
        console.print(f"[dim]Available: {', '.join(TOOLS.keys())}[/dim]")
        raise typer.Exit(1)

    eng = store.get_engagement(engagement_id)
    if not eng:
        console.print(f"[red]Engagement {engagement_id} not found.[/red]")
        raise typer.Exit(1)

    effective_target = target or eng["target"]
    console.print(f"[dim]Engagement:[/dim] #{engagement_id} — {eng['name']} ({eng['target']})")

    executor = Executor(
        db_store=None if nosave else store,
        engagement_id=engagement_id
    )

    kwargs = {"target": effective_target}
    if flags:
        kwargs["flags"] = flags

    executor.run(tool, save=not nosave, **kwargs)


# ── dispatch ───────────────────────────────────────────────────────────────────
@app.command("dispatch")
def dispatch_ports(
    ports:  str           = typer.Argument(..., help="Comma-separated open ports e.g. 22,80,445,3389"),
    target: str           = typer.Option("",   "--target", "-t", help="Override target IP"),
    eid:    Optional[int] = typer.Option(None, "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """Show ATT&CK-mapped attack chain suggestions for open ports."""
    engagement_id = resolve_eid(eid)
    effective_target = target
    if not effective_target and engagement_id:
        eng = store.get_engagement(engagement_id)
        effective_target = eng["target"] if eng else "{target}"

    port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]
    display_dispatch(port_list, effective_target)


# ── cve ────────────────────────────────────────────────────────────────────────
@app.command("cve")
def cve_search(
    product: str           = typer.Argument(...,   help="Product name e.g. openssh, apache, samba"),
    version: str           = typer.Option("",      "--version", "-v", help="Version e.g. 2.4.49"),
    auto:    bool          = typer.Option(False,   "--auto",    "-a", help="Auto-scan from last nmap run"),
    save:    bool          = typer.Option(True,    "--save/--no-save", help="Auto-save critical/high as findings"),
    eid:     Optional[int] = typer.Option(None,    "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """Search NVD for CVEs by product/version, or auto-scan from last nmap output."""
    from core.parser import Parser

    engagement_id = resolve_eid(eid)

    if auto:
        if not engagement_id:
            console.print("[red]No active engagement for auto-scan.[/red]")
            raise typer.Exit(1)

        runs = store.list_tool_runs(engagement_id)
        nmap_run = next((r for r in reversed(runs) if r["tool_name"] == "nmap"), None)

        if not nmap_run:
            console.print("[red]No nmap run found. Run nmap first:[/red] spectre run nmap")
            raise typer.Exit(1)

        console.print("[cyan][*] Auto-scanning CVEs from last nmap run...[/cyan]")
        nmap_parsed = Parser.nmap(nmap_run["stdout"])
        scanner = CVEAutoScan()
        result  = scanner.run(nmap_parsed=nmap_parsed)

    else:
        console.print(f"[cyan][*] Searching CVEs:[/cyan] {product} {version}".strip())
        searcher = CVESearch()
        result   = searcher.run(product=product, version=version)

    if not result["success"]:
        console.print(f"[red][-] {result['stderr']}[/red]")
        raise typer.Exit(1)

    cves = result.get("parsed", {}).get("cves", [])
    if not cves:
        console.print("[yellow]No CVEs found.[/yellow]")
        return

    table = Table(
        title=f"CVE Results — {product} {version}".strip(),
        border_style="red",
        header_style="bold magenta"
    )
    table.add_column("CVE ID",     style="cyan", width=18)
    table.add_column("CVSS",                     width=6)
    table.add_column("Severity",                 width=10)
    table.add_column("Published", style="dim",   width=12)
    table.add_column("Description",              width=55)

    saved = 0
    for cve in cves:
        sev   = cve.get("severity", "info")
        score = cve.get("cvss_score", 0.0)
        color = SEVERITY_COLORS.get(sev, "white")
        desc  = cve.get("description", "")
        desc_short = desc[:75] + "..." if len(desc) > 75 else desc

        table.add_row(
            cve["cve_id"],
            f"{score:.1f}",
            f"[{color}]{sev.upper()}[/{color}]",
            cve.get("published", ""),
            desc_short,
        )

        # Auto-save critical and high as findings
        if save and engagement_id and sev in ("critical", "high"):
            refs = "\n".join(cve.get("references", []))
            store.add_finding(
                engagement_id = engagement_id,
                title         = f"{cve['cve_id']} — {product} {version}".strip(),
                description   = desc,
                severity      = sev,
                ttp           = "T1190",
                evidence      = f"CVSS: {score}\nReferences:\n{refs}",
                host          = cve.get("host", ""),
                port          = cve.get("port"),
                tool          = "cve-search",
            )
            saved += 1

    console.print(table)
    console.print(f"\n[dim]Total: {len(cves)} CVEs found[/dim]")
    if saved:
        console.print(f"[green][+] {saved} critical/high CVEs auto-saved as findings[/green]")
    elif engagement_id and save:
        console.print("[dim]No critical/high CVEs to auto-save.[/dim]")


# ── tools ──────────────────────────────────────────────────────────────────────
@app.command("tools")
def list_tools():
    """List all available tools and their installation status."""
    table = Table(title="Available Tools", border_style="red", header_style="bold magenta")
    table.add_column("Tool",        width=16)
    table.add_column("Category",    width=12)
    table.add_column("Description", width=42)
    table.add_column("Installed",   width=10)
    table.add_column("⚠ Confirm",   width=10)

    for name, tool in TOOLS.items():
        installed = "[green]✅[/green]" if tool.check_installed() else "[red]❌[/red]"
        confirm   = "[red]YES[/red]"   if tool.requires_confirmation else "[dim]no[/dim]"
        table.add_row(
            name,
            TOOL_CATEGORIES.get(name, "misc"),
            tool.description,
            installed,
            confirm,
        )
    console.print(table)


# ── findings ───────────────────────────────────────────────────────────────────
@app.command("findings")
def list_findings(
    eid: Optional[int] = typer.Option(None, "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """List findings for an engagement."""
    engagement_id = resolve_eid(eid)
    if not engagement_id:
        console.print("[red]No active engagement.[/red]")
        raise typer.Exit(1)

    eng = store.get_engagement(engagement_id)
    if not eng:
        console.print(f"[red]Engagement {engagement_id} not found.[/red]")
        raise typer.Exit(1)

    findings = store.list_findings(engagement_id)
    if not findings:
        console.print("[yellow]No findings recorded yet.[/yellow]")
        return

    table = Table(
        title=f"Findings — #{engagement_id} {eng['name']} ({eng['target']})",
        border_style="red",
        header_style="bold magenta"
    )
    table.add_column("ID",       width=5)
    table.add_column("Severity", width=10)
    table.add_column("Title",    width=36)
    table.add_column("Host",     width=18)
    table.add_column("Port",     width=6)
    table.add_column("TTP",      width=12)
    table.add_column("Tool",     width=14)

    for f in findings:
        sev   = f.get("severity", "info")
        color = SEVERITY_COLORS.get(sev, "white")
        table.add_row(
            str(f["id"]),
            f"[{color}]{sev.upper()}[/{color}]",
            f["title"],
            f.get("host", ""),
            str(f.get("port", "") or ""),
            f.get("ttp", ""),
            f.get("tool", ""),
        )
    console.print(table)


# ── add-finding ────────────────────────────────────────────────────────────────
@app.command("add-finding")
def add_finding(
    title:       str           = typer.Option(...,      "--title",    "-t", help="Finding title"),
    severity:    str           = typer.Option("medium", "--severity", "-s", help="critical|high|medium|low|info"),
    description: str           = typer.Option("",       "--desc",     "-d", help="Description"),
    ttp:         str           = typer.Option("",       "--ttp",            help="MITRE ATT&CK TTP e.g. T1190"),
    host:        str           = typer.Option("",       "--host",           help="Affected host"),
    port:        Optional[int] = typer.Option(None,     "--port",           help="Affected port"),
    tool:        str           = typer.Option("",       "--tool",           help="Tool that found it"),
    evidence:    str           = typer.Option("",       "--evidence",       help="Evidence snippet"),
    eid:         Optional[int] = typer.Option(None,     "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """Manually add a finding to an engagement."""
    engagement_id = resolve_eid(eid)
    if not engagement_id:
        console.print("[red]No active engagement.[/red]")
        raise typer.Exit(1)

    fid = store.add_finding(
        engagement_id=engagement_id,
        title=title,
        description=description,
        severity=severity,
        ttp=ttp,
        evidence=evidence,
        host=host,
        port=port,
        tool=tool,
    )
    console.print(f"[green][+] Finding added:[/green] ID {fid} — {title} [{severity.upper()}]")


# ── report ─────────────────────────────────────────────────────────────────────
@app.command("report")
def generate_report(
    format_: str           = typer.Option("md",  "--format", "-f", help="md | pdf"),
    eid:     Optional[int] = typer.Option(None,  "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """Generate a penetration test report."""
    engagement_id = resolve_eid(eid)
    if not engagement_id:
        console.print("[red]No active engagement.[/red]")
        raise typer.Exit(1)

    eng = store.get_engagement(engagement_id)
    if not eng:
        console.print(f"[red]Engagement {engagement_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan][*] Generating {format_.upper()} report for:[/cyan] #{engagement_id} — {eng['name']}")
    gen  = ReportGenerator(store)
    path = gen.generate(engagement_id, output_format=format_)
    console.print(f"[bold green][+] Report saved:[/bold green] {path}")


# ── status ─────────────────────────────────────────────────────────────────────
@app.command("status")
def status(
    eid: Optional[int] = typer.Option(None, "--engagement", "-e", help="Engagement ID (default: active)"),
):
    """Show engagement status summary."""
    engagement_id = resolve_eid(eid)
    if not engagement_id:
        console.print("[yellow]No active engagement. Run: spectre new --target <ip>[/yellow]")
        return

    eng      = store.get_engagement(engagement_id)
    findings = store.list_findings(engagement_id)
    runs     = store.list_tool_runs(engagement_id)

    if not eng:
        console.print(f"[red]Engagement {engagement_id} not found.[/red]")
        raise typer.Exit(1)

    sev_counts = {}
    for f in findings:
        s = f.get("severity", "info")
        sev_counts[s] = sev_counts.get(s, 0) + 1

    last_run = runs[-1]["tool_name"] if runs else "none"

    console.print(Panel(
        f"[bold]Engagement:[/bold] #{engagement_id} — {eng['name']}\n"
        f"[bold]Target:[/bold]     {eng['target']}\n"
        f"[bold]Type:[/bold]       {eng['type']}\n"
        f"[bold]Scope:[/bold]      {eng.get('scope') or 'not defined'}\n\n"
        f"[bold]Tool Runs:[/bold]  {len(runs)}  [dim](last: {last_run})[/dim]\n"
        f"[bold]Findings:[/bold]   {len(findings)} total  "
        f"[bold red]{sev_counts.get('critical', 0)}C[/bold red]  "
        f"[red]{sev_counts.get('high', 0)}H[/red]  "
        f"[yellow]{sev_counts.get('medium', 0)}M[/yellow]  "
        f"[cyan]{sev_counts.get('low', 0)}L[/cyan]  "
        f"[dim]{sev_counts.get('info', 0)}I[/dim]",
        title="[bold red]SPECTRE[/bold red] — Status",
        border_style="red"
    ))


if __name__ == "__main__":
    app()
