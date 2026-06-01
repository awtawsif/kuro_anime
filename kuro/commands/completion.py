import click

from kuro.cli import cli


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """Print shell completion script.

    \b
    Usage:
      eval "$(kuro completion bash)"   # bash
      eval "$(kuro completion zsh)"    # zsh
      kuro completion fish | source    # fish
    """
    from click.shell_completion import BashComplete, ZshComplete, FishComplete

    cls = {"bash": BashComplete, "zsh": ZshComplete, "fish": FishComplete}[shell]
    script = cls(cli, {}, "kuro", "_KURO_COMPLETE").source()
    click.echo(script)
