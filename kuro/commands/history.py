import json
import sys
from datetime import datetime

import click
from rich.table import Table

from kuro import state
from kuro.cli import cli
from kuro.console import console


@cli.command()
@click.option("--limit", default=20, type=int, help="Number of entries to show")
@click.option("--clear", is_flag=True, help="Clear all history")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def history(limit, clear, json_output):
    """Show recent activity or clear history."""
    ctx = click.get_current_context()

    if clear:
        state.clear_history()
        console.print("[green]History cleared.[/]")
        return

    if ctx.parent.obj.get("json") or json_output:
        entries = state.get_history(limit)
        sys.stdout.write(json.dumps(entries) + "\n")
        return

    entries = state.get_history(limit)
    if not entries:
        console.print("[yellow]No history yet.[/]")
        console.print("Run [bold]kuro search[/], [bold]kuro watch[/], or [bold]kuro download[/] to get started.")
        return

    table = Table(title="Recent Activity")
    table.add_column("When", style="dim", width=16)
    table.add_column("Type", width=10)
    table.add_column("Title")

    for entry in entries:
        when = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
        table.add_row(when, entry["type"], entry["title"])

    console.print(table)
