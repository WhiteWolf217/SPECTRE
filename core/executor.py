from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
import json

console = Console()


class Executor:
    """
    Central executor. All tool runs go through here.
    Handles confirmation prompts, output display, and DB saving.
    """

    def __init__(self, db_store=None, engagement_id=None):
        self.db = db_store
        self.engagement_id = engagement_id

    def run(self, tool, save=True, **kwargs) -> dict:
        """
        Run a tool. Prompts for confirmation if destructive.
        Saves output to DB if store is available.
        """
        # Show what we're about to run
        console.print(f"\n[bold cyan][*] Running:[/bold cyan] [white]{tool.name}[/white]")

        # Confirmation gate for destructive tools
        if tool.requires_confirmation:
            console.print(f"[bold yellow][!] WARNING:[/bold yellow] This tool is destructive/noisy.")
            confirm = console.input("[bold red]Confirm execution? (yes/no): [/bold red]")
            if confirm.strip().lower() != "yes":
                console.print("[yellow][-] Skipped.[/yellow]")
                return {"success": False, "stderr": "Skipped by operator", "stdout": "", "returncode": -1, "command": "", "elapsed_seconds": 0, "timestamp": ""}

        # Execute
        result = tool.run(**kwargs)

        # Display result
        self._display(result)

        # Save to DB
        if save and self.db and self.engagement_id:
            self.db.save_tool_run(
                engagement_id=self.engagement_id,
                tool_name=tool.name,
                kwargs=kwargs,
                result=result
            )

        return result

    def _display(self, result: dict):
        if result["success"]:
            console.print(f"[bold green][+] Done[/bold green] ({result['elapsed_seconds']}s)")
            if result["stdout"]:
                console.print(Panel(
                    result["stdout"],
                    title=f"[green]{result['command']}[/green]",
                    border_style="green",
                    expand=False
                ))
        else:
            console.print(f"[bold red][-] Failed:[/bold red] {result['stderr']}")
            if result.get("command"):
                console.print(f"[dim]Command: {result['command']}[/dim]")
