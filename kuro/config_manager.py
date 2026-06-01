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

DEFAULT_CONFIG_CONTENT = """# Kuro Anime Configuration
# Edit this file to change default settings. Unused fields can be deleted.
# See https://github.com/awtawsif/kuro_anime for full documentation.

[defaults]
# Directory where downloads are saved (default: ~/Videos)
output_dir = "~/Videos"

# Preferred resolution: "best", "1080", "720", etc.
quality = "best"

# Preferred audio language: "jpn", "eng", etc.
language = "jpn"

# Video player binary (e.g. mpv, vlc, iina)
player = "mpv"

[download]
# Filename template. Available variables: {title}, {episode}, {label}, {quality}
filename_template = "{title} - EP{episode:02d}.mp4"

# Resume partial downloads (default: false)
resume = false
"""


@dataclass
class KuroConfig:
    output_dir: Path = Path.home() / "Videos"
    quality: str = "best"
    language: str = "jpn"
    player: str = "mpv"
    filename_template: str = "{title} - EP{episode:02d}.mp4"
    resume: bool = False


def _defaults() -> KuroConfig:
    return KuroConfig()


def write_default_config(overwrite: bool = False):
    if CONFIG_FILE.exists() and not overwrite:
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(DEFAULT_CONFIG_CONTENT)


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

    if not CONFIG_FILE.exists():
        write_default_config()

    raw = _load_from_file()
    cfg = _defaults()

    defaults = raw.get("defaults", {})
    if "output_dir" in defaults:
        cfg.output_dir = Path(os.path.expanduser(defaults["output_dir"]))
    if "quality" in defaults:
        cfg.quality = defaults["quality"]
    if "language" in defaults:
        cfg.language = defaults["language"]
    if "player" in defaults:
        cfg.player = defaults["player"]

    download = raw.get("download", {})
    if "filename_template" in download:
        cfg.filename_template = download["filename_template"]
    if "resume" in download:
        cfg.resume = download["resume"]

    _cache = cfg
    return cfg
