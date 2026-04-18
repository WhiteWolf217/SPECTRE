import asyncio
import re
import threading
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Input, Label, ListItem,
    ListView, RichLog, Static, Button, RadioSet, RadioButton
)
from textual.screen import Screen
from textual.binding import Binding
from textual import work
from rich.text import Text
from rich.panel import Panel

from db.store import Store
from agent.core import AgentCore
from agent.llm import OllamaClient


# ─── Severity colour map ───────────────────────────────────────────────────────
SEV_STYLE = {
    "critical": "bold red",
    "high":     "red",
    "medium":   "yellow",
    "low":      "cyan",
    "info":     "dim",
}


class NewEngagementScreen(Screen):
    """Dialog for creating a new engagement."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #dialog {
        width: 75;
        height: auto;
        max-height: 30;
        background: #1a1a1a;
        border: solid #cc0000;
        padding: 1;
        overflow: auto;
    }
    
    #dialog-title {
        color: #cc0000;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .field-label {
        color: #888888;
        text-style: italic;
        margin-top: 1;
    }
    
    Input {
        background: #0d0d0d;
        border: solid #666666;
        color: #ffffff;
        width: 100%;
        margin-bottom: 1;
    }
    
    Input:focus {
        border: solid #cc0000;
    }
    
    RadioSet {
        margin: 1 0;
        width: 100%;
    }
    
    RadioButton {
        color: #888888;
        margin: 0 0 1 0;
    }
    
    RadioButton.--radio-selected {
        color: #cc0000;
    }
    
    #buttons {
        margin-top: 2;
        height: auto;
        width: 100%;
    }
    
    Button {
        background: #2a0000;
        color: #cc0000;
        border: solid #cc0000;
        margin-right: 2;
        margin-bottom: 1;
        width: 15;
        height: 3;
    }
    
    Button:hover {
        background: #cc0000;
        color: #0d0d0d;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.result = None
    
    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("[bold red]New Engagement[/bold red]", id="dialog-title")
            yield Label("IP or Domain:", classes="field-label")
            yield Input(placeholder="e.g., 10.10.10.5 or example.com", id="target")
            yield Label("Engagement Name (optional):", classes="field-label")
            yield Input(placeholder="e.g., Test Engagement", id="name")
            yield Label("Engagement Type:", classes="field-label")
            with RadioSet(id="type"):
                yield RadioButton("External - Public-facing targets", value="external", id="type-external")
                yield RadioButton("Internal - Corporate network, LAN", value="internal", id="type-internal")
                yield RadioButton("Web - Web application testing", value="web", id="type-web")
                yield RadioButton("AD - Active Directory testing", value="ad", id="type-ad")
            with Horizontal(id="buttons"):
                yield Button("Create", id="btn-create")
                yield Button("Cancel", id="btn-cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            target = self.query_one("#target", Input).value.strip()
            name = self.query_one("#name", Input).value.strip()
            radio_set = self.query_one("#type", RadioSet)
            eng_type = radio_set.pressed_button.value if radio_set.pressed_button else "external"
            
            if not target:
                return
            
            # Use target as name if not provided
            if not name:
                name = target
            
            # Create engagement
            eid = self.store.new_engagement(name, target, eng_type)
            self.result = eid
            self.dismiss(eid)
        elif event.button.id == "btn-cancel":
            self.dismiss()
    
    def action_cancel(self) -> None:
        self.dismiss()


class EngagementItem(ListItem):
    """A single engagement in the sidebar list."""

    def __init__(self, eid: int, name: str, target: str, is_active: bool = False):
        super().__init__()
        self.eid       = eid
        self.eng_name  = name
        self.target    = target
        self.is_active = is_active

    def compose(self) -> ComposeResult:
        marker = "▶ " if self.is_active else "  "
        yield Label(f"{marker}#{self.eid} {self.eng_name}\n  [dim]{self.target}[/dim]")


class SpectreUI(App):
    """
    SPECTRE v2.0 — Terminal UI

    Layout:
    ┌──────────────┬──────────────────────────────┐
    │  Sidebar     │  Agent Chat Panel            │
    │  ──────────  │  ──────────────────────────  │
    │  Engagements │  [output scrollback]         │
    │              │                              │
    │  Findings    │  [input bar]                 │
    └──────────────┴──────────────────────────────┘
    """

    CSS = """
    Screen {
        background: #0d0d0d;
    }

    #sidebar {
        width: 28;
        background: #111111;
        border-right: solid #2a0000;
        padding: 0 1;
    }

    #sidebar-title {
        color: #cc0000;
        text-style: bold;
        padding: 1 0 0 0;
    }

    #sidebar-section {
        color: #666666;
        text-style: italic;
        padding: 1 0 0 0;
    }

    ListView {
        background: #111111;
        border: none;
        height: auto;
        max-height: 16;
    }

    ListItem {
        background: #111111;
        padding: 0 1;
    }

    ListItem:hover {
        background: #1a0000;
    }

    ListItem.--highlight {
        background: #2a0000;
    }

    #findings-panel {
        height: auto;
        max-height: 12;
        padding: 0 0 1 0;
    }

    #main-panel {
        padding: 0 1;
    }

    #chat-log {
        height: 1fr;
        border: solid #2a0000;
        background: #0a0a0a;
        padding: 0 1;
        scrollbar-size: 1 1;
    }

    #input-area {
        height: 3;
        padding: 1 0 0 0;
    }

    #agent-input {
        border: solid #cc0000;
        background: #0d0d0d;
        color: #ffffff;
    }

    #agent-input:focus {
        border: solid #ff0000;
    }

    #status-bar {
        height: 1;
        background: #1a0000;
        color: #cc0000;
        padding: 0 1;
    }

    Button {
        background: #2a0000;
        color: #cc0000;
        border: solid #cc0000;
        min-width: 12;
        height: 3;
        margin: 1 0;
    }

    Button:hover {
        background: #cc0000;
        color: #0d0d0d;
    }

    Header {
        background: #1a0000;
        color: #cc0000;
    }

    Footer {
        background: #1a0000;
        color: #666666;
    }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_engagement", "New Engagement"),
        Binding("ctrl+r", "refresh",        "Refresh"),
        Binding("ctrl+q", "quit",           "Quit"),
        Binding("escape", "cancel_agent",   "Stop Agent"),
    ]

    TITLE = "SPECTRE — Red Team Platform"
    SUB_TITLE = "v2.0 | AI Agent"

    def __init__(self):
        super().__init__()
        self.store         = Store()
        self.active_eid    = self._get_active_eid()
        self.agent_running = False
        self.llm           = OllamaClient()
        self._pending_delete = None

    # ── Layout ─────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal():
            # Left sidebar
            with Vertical(id="sidebar"):
                yield Static("SPECTRE", id="sidebar-title")
                yield Static("─" * 24, classes="divider")
                yield Static("ENGAGEMENTS", id="sidebar-engagements")
                yield ListView(id="engagement-list")
                yield Static("─" * 24, classes="divider")
                yield Static("FINDINGS", id="sidebar-findings")
                with ScrollableContainer(id="findings-panel"):
                    yield Static("No findings yet.", id="findings-summary")
                yield Static("─" * 24, classes="divider")
                with Horizontal():
                    yield Button("+ New", id="btn-new", variant="default")
                    yield Button("✕ Delete", id="btn-delete", variant="default")

            # Main agent panel
            with Vertical(id="main-panel"):
                yield Static(id="status-bar")
                yield RichLog(id="chat-log", highlight=False, markup=True, wrap=True, auto_scroll=True, max_lines=500)
                with Horizontal(id="input-area"):
                    yield Input(
                        placeholder="Enter goal or command... (e.g. 'enumerate 10.10.10.5')",
                        id="agent-input"
                    )

        yield Footer()

    def on_mount(self) -> None:
        self._refresh_engagements()
        self._refresh_findings()
        self._update_status()
        self._print_banner()

        # Check Ollama
        if not self.llm.is_available():
            self._log(
                "[red]⚠  Ollama not available. Make sure it's running:[/red]\n"
                "   [dim]ollama serve[/dim]\n"
                "   [dim]ollama pull llama3.1:8b[/dim]"
            )
        else:
            self._log("[green][+] Ollama connected — llama3.1:8b ready[/green]")

        # Show guidance
        self._log(
            "\n[cyan][*] Quick Start:[/cyan]\n"
            "  • Press [bold]Ctrl+N[/bold] to create a new engagement\n"
            "  • Click [bold]+ New[/bold] or [bold]✕ Delete[/bold] buttons in sidebar\n"
            "  • Target can be: IP address (e.g., 10.10.10.5) or domain (e.g., example.com)\n"
            "  • For domains: Use 'enumerate <domain>' to discover subdomains and IPs\n"
            "  • For IPs: Use 'enumerate <ip>' for network scanning\n"
            "  • Available: subfinder, amass, nmap, nuclei, and more\n"
            "\n[cyan][*] Commands:[/cyan]\n"
            "  • [bold]use <id>[/bold] - Switch to engagement\n"
            "  • [bold]delete [id][/bold] - Delete engagement (asks for confirmation)\n"
            "  • [bold]delete --force [id][/bold] - Force delete without confirmation\n"
            "  • [bold]status[/bold] - Show current engagement status\n"
            "  • [bold]findings[/bold] - List all findings\n"
            "  • [bold]stop[/bold] - Stop running agent\n"
            "  • [bold]exit/quit[/bold] - Exit SPECTRE"
        )

        if self.active_eid:
            eng = self.store.get_engagement(self.active_eid)
            if eng:
                self._log(
                    f"\n[cyan][*] Active engagement:[/cyan] #{self.active_eid} "
                    f"— {eng['name']} ([white]{eng['target']}[/white])"
                )
        else:
            self._log("[yellow][!] No active engagement. Press Ctrl+N to create one.[/yellow]")

    # ── Event handlers ─────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input from the agent input bar."""
        text = event.value.strip()
        if not text:
            return

        # Clear input
        self.query_one("#agent-input", Input).value = ""

        # ── Confirmation gate (tool execution yes/no) ──────────────────────
        if hasattr(self, "_pending_confirm") and self._pending_confirm:
            self._pending_confirm(text)
            return

        # ── Operator instruction gate (what should agent do) ───────────────
        if hasattr(self, "_pending_instruction") and self._pending_instruction:
            self._pending_instruction(text)
            return

        # Check if pending delete confirmation
        if hasattr(self, "_pending_delete") and self._pending_delete:
            self._handle_delete_confirmation(text)
            return

        # Built-in commands
        if text.lower() in ("exit", "quit", "q"):
            self.exit()
            return

        if text.lower() == "stop":
            self.agent_running = False
            self._log("[yellow][!] Agent stopped.[/yellow]")
            return

        if text.lower().startswith("use "):
            try:
                eid = int(text.split()[1])
                self._switch_engagement(eid)
            except (ValueError, IndexError):
                self._log("[red]Usage: use <engagement_id>[/red]")
            return

        if text.lower().startswith("delete"):
            parts = text.split()
            force = "--force" in text or "-f" in text
            
            # Extract engagement ID if provided
            eid = None
            for part in parts[1:]:
                if part not in ("--force", "-f"):
                    try:
                        eid = int(part)
                        break
                    except ValueError:
                        pass
            
            if eid:
                self._delete_engagement_ui(eid, force=force)
            else:
                if self.active_eid:
                    self._delete_engagement_ui(self.active_eid, force=force)
                else:
                    self._log("[red]No active engagement to delete.[/red]")

        if text.lower() == "status":
            self._show_status()
            return

        if text.lower() == "findings":
            self._show_findings()
            return

        # Everything else — treat as agent goal
        if not self.active_eid:
            self._log("[red][-] No active engagement. Create one with Ctrl+N[/red]")
            return

        self._log(f"\n[bold cyan]>[/bold cyan] {text}")
        self._run_agent(text)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Switch engagement when clicked in sidebar."""
        item = event.item
        if isinstance(item, EngagementItem):
            self._switch_engagement(item.eid)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.action_new_engagement()
        elif event.button.id == "btn-delete":
            if self.active_eid:
                self._delete_engagement_ui(self.active_eid, force=True)
            else:
                self._log("[red]No active engagement to delete.[/red]")

    def action_refresh(self) -> None:
        self.active_eid = self._get_active_eid()
        self._refresh_engagements()
        self._refresh_findings()
        self._update_status()
        self._log("[dim]Refreshed.[/dim]")

    def action_cancel_agent(self) -> None:
        if self.agent_running:
            self.agent_running = False
            self._log("[yellow][!] Agent interrupted.[/yellow]")

    def action_new_engagement(self) -> None:
        """Show new engagement dialog."""
        def on_engagement_created(eid: Optional[int]) -> None:
            if eid:
                self._set_active_eid(eid)
                self.active_eid = eid
                self._refresh_engagements()
                self._refresh_findings()
                self._update_status()
                self._log(f"[green][+] Engagement #{eid} created. Switched to new engagement.[/green]")
        
        self.push_screen(NewEngagementScreen(self.store), on_engagement_created)

    # ── Agent runner ───────────────────────────────────────────────────────────

    @work(thread=True)
    def _run_agent(self, goal: str) -> None:
        """Run the agent in a background thread so UI stays responsive."""
        if self.agent_running:
            self._log("[yellow][!] Agent already running. Type 'stop' to cancel.[/yellow]")
            return

        self.agent_running = True
        self._update_status("Agent running...")

        try:
            agent = AgentCore(
                store=self.store,
                engagement_id=self.active_eid,
                on_thought   = lambda msg: self._log(
                    f"[dim]THOUGHT:[/dim] "
                    + re.sub(r"</?(?:tool_call|finding)>", "", msg).strip()
                ),
                on_tool_call = lambda tc:  self._log(
                    f"\n[bold yellow][?] Tool call:[/bold yellow]\n"
                    f"  Tool:   [cyan]{tc.get('tool')}[/cyan]\n"
                    f"  Target: [white]{tc.get('args', {}).get('target', '')}[/white]\n"
                    f"  Flags:  [dim]{tc.get('args', {}).get('flags', '')}[/dim]\n"
                    f"  TTP:    [magenta]{tc.get('ttp', '')}[/magenta]\n"
                    f"  Why:    {tc.get('reason', '')}"
                ),
                on_finding        = lambda f: self._on_finding(f),
                on_done           = lambda msg: self._log(f"\n[bold green][+] DONE:[/bold green] {msg}"),
                request_input_fn  = self._request_operator_instruction,
            )

            memory = agent.run(
                goal=goal,
                confirm_fn=self._confirm_tool,
            )

            stats = memory.stats()
            self._log(
                f"\n[bold green]═══ Session Complete ═══[/bold green]\n"
                f"  Tool runs:  {stats['tool_runs']}\n"
                f"  Findings:   {stats['findings']}\n"
                f"  Open ports: {stats['open_ports']}"
            )
            self._refresh_findings()

        except Exception as e:
            self._log(f"[red][-] Agent error: {e}[/red]")
        finally:
            self.agent_running = False
            self._update_status()

    def _confirm_tool(self, tool_name: str, args: dict) -> bool:
        """
        Synchronous confirmation gate for tool execution.
        Shows prompt in chat log and waits for operator input.
        Since we're in a thread, we use threading.Event to block.
        """
        result    = {"confirmed": False}
        event     = threading.Event()

        self._log(
            f"\n[bold red][?] CONFIRM TOOL EXECUTION[/bold red]\n"
            f"  [cyan]{tool_name}[/cyan] on [white]{args.get('target', '')}[/white]\n"
            f"  [dim]Type 'yes' to run, 'no' to skip[/dim]"
        )

        # Temporarily hijack input to get confirmation
        def handle_confirm(text: str):
            result["confirmed"] = text.strip().lower() in ("yes", "y")
            event.set()

        # Store original handler and replace temporarily
        self._pending_confirm = handle_confirm
        event.wait(timeout=120)  # 2 min timeout
        self._pending_confirm = None

        if result["confirmed"]:
            self._log(f"[green][+] Running {tool_name}...[/green]")
        else:
            self._log(f"[yellow][-] Skipped {tool_name}[/yellow]")

        return result["confirmed"]

    def _request_operator_instruction(self) -> str:
        """
        Block the agent thread and wait for the operator to type
        what they want the agent to do next.
        Uses threading.Event to pause until input is submitted.
        """
        result = {"value": "test all services"}
        event  = threading.Event()

        self._log(
            "\n[bold cyan]┌─ What should the agent do? ──────────────────────────┐[/bold cyan]\n"
            "[bold cyan]│[/bold cyan] Examples: 'run hydra on ssh', 'scan for web vulns'   [bold cyan]│[/bold cyan]\n"
            "[bold cyan]└──────────────────────────────────────────────────────┘[/bold cyan]"
        )

        def handle_instruction(text: str):
            result["value"] = text.strip() or "test all services"
            event.set()

        self._pending_instruction = handle_instruction
        event.wait(timeout=120)  # 2 min timeout — defaults to "test all services"
        self._pending_instruction = None

        self._log(f"[bold cyan]>[/bold cyan] {result['value']}")
        return result["value"]

    def on_input_submitted_confirm(self, text: str) -> None:
        """Route confirm responses if a confirmation is pending."""
        if hasattr(self, "_pending_confirm") and self._pending_confirm:
            self._pending_confirm(text)
            return

    # ── Sidebar helpers ────────────────────────────────────────────────────────

    def _refresh_engagements(self) -> None:
        lv = self.query_one("#engagement-list", ListView)
        lv.clear()
        for eng in self.store.list_engagements():
            lv.append(EngagementItem(
                eid=eng["id"],
                name=eng["name"],
                target=eng["target"],
                is_active=(eng["id"] == self.active_eid),
            ))

    def _refresh_findings(self) -> None:
        if not self.active_eid:
            return
        findings = self.store.list_findings(self.active_eid)
        counts   = {}
        for f in findings:
            s = f.get("severity", "info")
            counts[s] = counts.get(s, 0) + 1

        parts = []
        for sev in ("critical", "high", "medium", "low", "info"):
            if counts.get(sev):
                style = SEV_STYLE.get(sev, "white")
                parts.append(f"[{style}]{counts[sev]}{sev[0].upper()}[/{style}]")

        summary = "  ".join(parts) if parts else "[dim]No findings yet.[/dim]"
        self.query_one("#findings-summary", Static).update(summary)

    def _switch_engagement(self, eid: int) -> None:
        eng = self.store.get_engagement(eid)
        if not eng:
            self._log(f"[red]Engagement {eid} not found.[/red]")
            return
        self.active_eid = eid
        self._set_active_eid(eid)
        self._refresh_engagements()
        self._refresh_findings()
        self._update_status()
        self._log(
            f"[green][+] Switched to:[/green] #{eid} — {eng['name']} "
            f"([white]{eng['target']}[/white])"
        )

    def _delete_engagement_ui(self, eid: int, force: bool = False) -> None:
        """Delete an engagement after confirmation (or immediately if force=True)."""
        eng = self.store.get_engagement(eid)
        if not eng:
            self._log(f"[red]Engagement {eid} not found.[/red]")
            return
        
        if force:
            # Force delete without confirmation
            success = self.store.delete_engagement(eid)
            
            if success:
                # Clear active if deleted engagement was active
                if self.active_eid == eid:
                    self.active_eid = None
                    self._set_active_eid(None)
                    self._log("[yellow][!] Active engagement cleared.[/yellow]")
                
                self._refresh_engagements()
                self._refresh_findings()
                self._update_status()
                self._log(f"[green][+] Engagement #{eid} '{eng['name']}' deleted.[/green]")
            else:
                self._log(f"[red][-] Failed to delete engagement #{eid}.[/red]")
        else:
            # Ask for confirmation
            findings = self.store.list_findings(eid)
            runs = self.store.list_tool_runs(eid)
            
            self._log(
                f"\n[bold red]⚠  CONFIRM DELETE[/bold red]\n"
                f"  Engagement: #{eid} — {eng['name']}\n"
                f"  Target:     {eng['target']}\n"
                f"  Findings:   {len(findings)}\n"
                f"  Tool runs:  {len(runs)}\n"
                f"  [dim]Type 'yes' to confirm deletion or any other text to cancel[/dim]"
            )
            
            # Store delete request
            self._pending_delete = eid

    def _handle_delete_confirmation(self, text: str) -> None:
        """Handle delete confirmation response."""
        if text.strip().lower() == "yes":
            eid = self._pending_delete
            eng = self.store.get_engagement(eid)
            
            success = self.store.delete_engagement(eid)
            
            if success:
                # Clear active if deleted engagement was active
                if self.active_eid == eid:
                    self.active_eid = None
                    self._set_active_eid(None)
                    self._log("[yellow][!] Active engagement cleared.[/yellow]")
                
                self._refresh_engagements()
                self._refresh_findings()
                self._update_status()
                self._log(f"[green][+] Engagement #{eid} '{eng['name']}' deleted.[/green]")
            else:
                self._log(f"[red][-] Failed to delete engagement #{eid}.[/red]")
        else:
            self._log("[yellow][-] Deletion cancelled.[/yellow]")
        
        self._pending_delete = None

    # ── Chat log helpers ───────────────────────────────────────────────────────

    def _log(self, message: str) -> None:
        """Thread-safe log to chat panel."""
        import threading
        if threading.current_thread() == threading.main_thread():
            self._log_main(message)
        else:
            self.call_from_thread(self._log_main, message)

    def _log_main(self, message: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write(message)

    def _print_banner(self) -> None:
        self.query_one("#chat-log", RichLog).write(
            "[bold red]\n"
            "███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗\n"
            "██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝\n"
            "███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗  \n"
            "╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝  \n"
            "███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗\n"
            "╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝[/bold red]\n"
            "[dim]Red Team Automation Platform — v2.0 | AI Agent[/dim]\n"
        )

    def _update_status(self, msg: str = "") -> None:
        bar = self.query_one("#status-bar", Static)
        if msg:
            bar.update(f" ⚡ {msg}")
        elif self.active_eid:
            eng = self.store.get_engagement(self.active_eid)
            if eng:
                bar.update(
                    f" Engagement: #{self.active_eid} {eng['name']} "
                    f"| Target: {eng['target']} "
                    f"| Model: llama3.1:8b"
                )
        else:
            bar.update(" No active engagement")

    def _show_status(self) -> None:
        if not self.active_eid:
            self._log("[yellow]No active engagement.[/yellow]")
            return
        eng      = self.store.get_engagement(self.active_eid)
        findings = self.store.list_findings(self.active_eid)
        runs     = self.store.list_tool_runs(self.active_eid)
        self._log(
            f"\n[bold]Status — #{self.active_eid} {eng['name']}[/bold]\n"
            f"  Target:    {eng['target']}\n"
            f"  Type:      {eng['type']}\n"
            f"  Tool runs: {len(runs)}\n"
            f"  Findings:  {len(findings)}"
        )

    def _show_findings(self) -> None:
        if not self.active_eid:
            self._log("[yellow]No active engagement.[/yellow]")
            return
        findings = self.store.list_findings(self.active_eid)
        if not findings:
            self._log("[yellow]No findings yet.[/yellow]")
            return
        self._log(f"\n[bold]Findings — #{self.active_eid}[/bold]")
        for f in findings:
            sev   = f.get("severity", "info")
            style = SEV_STYLE.get(sev, "white")
            self._log(
                f"  [{style}][{sev.upper()}][/{style}] "
                f"{f['title']} — [dim]{f.get('host', '')}[/dim]"
            )

    def _on_finding(self, f: dict) -> None:
        sev   = f.get("severity", "info")
        style = SEV_STYLE.get(sev, "white")
        self._log(
            f"\n[bold {style}]◆ FINDING: {f.get('title')}[/bold {style}]\n"
            f"  Severity: [{style}]{sev.upper()}[/{style}]\n"
            f"  TTP:      {f.get('ttp', 'N/A')}\n"
            f"  Host:     {f.get('host', 'N/A')}\n"
            f"  {f.get('description', '')[:120]}"
        )
        self._refresh_findings()

    # ── State helpers ──────────────────────────────────────────────────────────

    def _get_active_eid(self) -> Optional[int]:
        import os
        path = os.path.expanduser("~/.spectre/.active")
        if os.path.exists(path):
            try:
                return int(open(path).read().strip())
            except ValueError:
                return None
        return None

    def _set_active_eid(self, eid: int) -> None:
        import os
        os.makedirs(os.path.expanduser("~/.spectre"), exist_ok=True)
        with open(os.path.expanduser("~/.spectre/.active"), "w") as f:
            f.write(str(eid))


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    app = SpectreUI()
    app.run()


if __name__ == "__main__":
    main()
