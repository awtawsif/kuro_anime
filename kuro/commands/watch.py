import json
import sys
from pathlib import Path

import click

from kuro.cli import cli
from kuro.console import err_console
from kuro.exceptions import KuroError


@cli.command()
@click.argument("anime")
@click.argument("episode_id", required=False, type=int)
@click.option("--episode", "-e", "episode_opt", default=None, type=int, help="Episode number (alternative to positional arg)")
def watch(anime, episode_id, episode_opt):
    ctx = click.get_current_context()
    try:
        if ctx.parent.obj.get("json"):
            from kuro._helpers import _resolve_anime
            session_id, title = _resolve_anime(anime)
            sys.stdout.write(json.dumps({"session_id": session_id, "title": title}) + "\n")
            return
        from kuro._helpers import _resolve_and_play
        _resolve_and_play(anime, episode_id or episode_opt, do_play=True)
    except KuroError as e:
        err_console.print(f"[red]{e}[/]")
        sys.exit(1)


@cli.command()
@click.argument("anime")
@click.argument("episode_id", required=False, type=int)
@click.option("--episode", "-e", "episode_opt", default=None, type=int, help="Episode number (alternative to positional arg)")
@click.option("--output", "-o", default=None, help="Output directory (default: ~/Videos/{title}/)")
@click.option("--batch", "-b", default=None, help="Download episode range (e.g. 1-10, 1,3,5)")
def download(anime, episode_id, episode_opt, output, batch):
    ctx = click.get_current_context()
    try:
        if ctx.parent.obj.get("json"):
            from kuro._helpers import _resolve_anime
            session_id, title = _resolve_anime(anime)
            sys.stdout.write(json.dumps({"session_id": session_id, "title": title}) + "\n")
            return

        out_dir = Path(output) if output else None

        if batch:
            from kuro._helpers import _parse_episode_range, _batch_download
            _batch_download(anime, _parse_episode_range(batch), out_dir)
        else:
            from kuro._helpers import _download_single
            _download_single(anime, episode_id or episode_opt, out_dir)
    except KuroError as e:
        err_console.print(f"[red]{e}[/]")
        sys.exit(1)
