import logging
from importlib.metadata import version, PackageNotFoundError

import click

from kuro.config import API_HEADERS
from kuro.console import console, err_console

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

try:
    _version = version("kuro_anime")
except PackageNotFoundError:
    _version = "unknown"


@click.group()
@click.version_option(version=_version, prog_name="kuro")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output as JSON")
@click.pass_context
def cli(ctx, json_output):
    ctx.ensure_object(dict)["json"] = json_output
    if "YUhBIBrskG3DbXfMe7ZH" in API_HEADERS.get("Cookie", ""):
        err_console.print(
            "[yellow]Warning: Default cookies in use. They may expire.[/]"
        )


import kuro.commands  # noqa: E402 — register commands via side-effect
