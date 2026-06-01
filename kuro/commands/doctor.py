import sys

from rich.table import Table
from rich.text import Text

from kuro.cli import cli
from kuro.console import console, err_console
from kuro.doctor import check_all


@cli.command()
def doctor():
    """Check system dependencies and configuration."""
    results = check_all()
    passed = 0
    failed = 0

    table = Table(title="Kuro Anime System Check")
    table.add_column("Check", style="bold")
    table.add_column("Status", width=8)
    table.add_column("Detail")

    for r in results:
        status = Text("PASS", style="green") if r.ok else Text("FAIL", style="red bold")
        if r.ok:
            passed += 1
        else:
            failed += 1
        table.add_row(r.name, status, r.message)

    console.print(table)

    if failed:
        err_console.print(
            f"\n[red bold]✗ {failed} check(s) failed.[/] "
            "[yellow]Fix the issues above and re-run.[/]"
        )
        sys.exit(1)
    else:
        console.print(f"\n[green bold]✓ All {passed} checks passed.[/]")
