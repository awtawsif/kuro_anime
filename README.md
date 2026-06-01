# Kuro Anime

**Terminal-based anime discovery and streaming tool.** Search anime, browse airing shows, view details, download episodes, and stream them — all from your terminal.

[![PyPI version](https://img.shields.io/pypi/v/kuro_anime?color=blue)](https://pypi.org/project/kuro_anime/)
[![Python version](https://img.shields.io/pypi/pyversions/kuro_anime)](https://pypi.org/project/kuro_anime/)
[![License](https://img.shields.io/pypi/l/kuro_anime)](LICENSE)

## Features

- **Search** — Find any anime by title; persistent short codes for instant lookups
- **Currently Airing** — Browse the latest releases with pagination
- **Detailed Info** — Synopsis, genres, relations, recommendations, metadata
- **Episode Listings** — Browse episodes with pagination and sort order
- **Streaming** — Interactive episode/quality picker → mpv
- **Download** — Extract video URLs or batch-download episodes
- **Doctor** — `kuro doctor` checks all system dependencies with install instructions
- **Shell Completion** — `kuro completion bash|zsh|fish` generates completion scripts
- **History** — `kuro history` tracks recent searches, watches, and downloads
- **Config Init** — `kuro init` generates a commented default configuration

## Installation

Requires **Python 3.10+**, **mpv** (for `kuro watch`), and **ffmpeg** (for `kuro download`).

```sh
pip install kuro-anime
```

To install from source:

```sh
git clone https://github.com/awtawsif/kuro_anime.git
cd kuro_anime
pip install .
```

## Configuration

A default config is auto-generated on first run. Edit `~/.kuro_anime/config.toml` to customize:

```toml
[defaults]
output_dir = "~/Videos"        # download destination
quality = "best"               # preferred resolution: "best", "1080", "720", etc.
language = "jpn"               # preferred audio language: "jpn", "eng", etc.
player = "mpv"                 # video player binary (mpv, vlc, iina, etc.)

[download]
filename_template = "{title} - EP{episode:02d}.mp4"
```

You can also run `kuro init --force` to regenerate the default config. CLI flags override config values when both are supplied.

## Quick Start

```sh
# Search for an anime (generates short codes)
kuro search "One Piece"

# View details using a short code
kuro detail onpi

# Browse episodes and watch
kuro watch onpi

# See what's currently airing
kuro airing --page 1
```

## Commands

Run `kuro <command> --help` for full usage. All commands accept `--json` for machine-readable output.

| Command | Description |
|---------|-------------|
| `search <query>` | Search anime by title (generates short codes) |
| `airing` | Browse currently airing anime |
| `detail <anime>` | Show synopsis, metadata, relations, recommendations |
| `episodes <anime>` | List episodes with pagination and sort |
| `watch <anime>` | Interactive episode/quality picker → mpv |
| `download <anime>` | Download episodes (single or batch) |
| `doctor` | Check system dependencies |
| `completion <shell>` | Generate shell completion (bash/zsh/fish) |
| `history` | Show recent searches, watches, downloads |
| `init` | Generate commented default config |

Identifiers can be a **short code** (`onpi`), a **UUID**, or a **kebab-case slug** (`one-piece`). Short codes persist across sessions.

## State

Persisted to `~/.kuro_anime/state.json`. Short codes, session mappings, a kwik-cache, and activity history live there. Delete the file to reset all state.

## FAQ

**"mpv not found"**: Install mpv — `sudo apt install mpv` (Debian/Ubuntu), `brew install mpv` (macOS), `sudo dnf install mpv` (Fedora).

**"ffmpeg not found"**: Install ffmpeg — `sudo apt install ffmpeg` (Debian/Ubuntu), `brew install ffmpeg` (macOS), `sudo dnf install ffmpeg` (Fedora).

**"Could not resolve"**: The identifier wasn't a short code, UUID, or matching slug. Run `kuro search <query>` first.

## License

[GNU General Public License v3.0](LICENSE)
