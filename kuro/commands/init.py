import click

from kuro.cli import cli
from kuro.config_manager import CONFIG_FILE, write_default_config
from kuro.console import console, err_console


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing config")
def init(force):
    """Generate a default configuration file."""
    if CONFIG_FILE.exists() and not force:
        err_console.print(
            f"[yellow]Config already exists at {CONFIG_FILE}.[/]\n"
            f"Use [bold]kuro init --force[/] to overwrite."
        )
        return

    write_default_config(overwrite=force)
    console.print(f"[green]Config written to {CONFIG_FILE}[/]")
    console.print("Edit this file to customize defaults, then run any kuro command.")
