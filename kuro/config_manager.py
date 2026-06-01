import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib

CONFIG_DIR = Path.home() / ".kuro_anime"
CONFIG_FILE = CONFIG_DIR / "config.toml"

_cache: Optional["KuroConfig"] = None


@dataclass
class KuroConfig:
    output_dir: Path = Path.home() / "Videos"
    quality: str = "best"
    player: str = "mpv"
    filename_template: str = "{title} - EP{episode:02d}.mp4"


def _defaults() -> KuroConfig:
    return KuroConfig()


def _load_from_file() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def get_config() -> KuroConfig:
    global _cache
    if _cache is not None:
        return _cache

    raw = _load_from_file()
    cfg = _defaults()

    defaults = raw.get("defaults", {})
    if "output_dir" in defaults:
        cfg.output_dir = Path(os.path.expanduser(defaults["output_dir"]))
    if "quality" in defaults:
        cfg.quality = defaults["quality"]
    if "player" in defaults:
        cfg.player = defaults["player"]

    download = raw.get("download", {})
    if "filename_template" in download:
        cfg.filename_template = download["filename_template"]

    _cache = cfg
    return cfg
