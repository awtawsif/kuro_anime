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

Create `~/.kuro_anime/config.toml` to customize defaults:

```toml
[defaults]
output_dir = "~/Videos"        # download destination
quality = "best"               # or "1080", "720", etc.
player = "mpv"                 # video player binary

[download]
filename_template = "{title} - EP{episode:02d}.mp4"
```

CLI flags override config values when both are supplied.

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

### `kuro search <query>`

Search anime by title. Displays results with short codes and saves them to state.

```sh
kuro search "Frieren"
```

### `kuro airing [--page N]`

Browse currently airing anime with pagination. Assigns short codes for each entry.

```sh
kuro airing --page 1
```

### `kuro detail <anime-id>`

Show full anime info: synopsis, metadata, relations, and recommendations.

Anime IDs can be a **short code** (`onpi`), a **UUID** (`37aeb550-...`), or a **kebab-case slug** (`one-piece`). Short codes persist across sessions and never require re-searching.

```sh
kuro detail onpi       # short code
kuro detail one-piece  # slug
```

### `kuro episodes <anime-id> [--page N] [--sort episode_asc|episode_desc]`

List episodes with pagination.

```sh
kuro episodes onpi --page 1 --sort episode_desc
```

### `kuro watch <anime-id> [episode_id] [--episode / -e]`

Interactive episode and quality picker. Extracts the video URL and streams it via mpv.

```sh
kuro watch onpi
kuro watch onpi --episode 5  # skip to episode 5
```

### `kuro download <anime-id> [episode_id] [--episode / -e] [--output / -o] [--batch / -b]`

Download video files. Auto-named `{Title} - EP{num:02d}.mp4`.

```sh
kuro download onpi                           # interactive picker
kuro download onpi -b 1-10                   # batch episodes 1-10
kuro download onpi -b 1-5,8,10-12 -o ./eps/  # batch with custom dir
```

### `kuro doctor`

Check all system dependencies and configuration. Prints a summary table with pass/fail per check.

```sh
kuro doctor
```

### `kuro completion bash|zsh|fish`

Print a shell completion script. Source it in your shell config:

```sh
eval "$(kuro completion bash)"   # bash
eval "$(kuro completion zsh)"    # zsh
kuro completion fish | source    # fish
```

All commands accept `--json` for machine-readable JSON output.

## State

Persisted to `~/.kuro_anime/state.json`. Short codes, session mappings, and a kwik-cache live there. Delete the file to reset all state.

## FAQ

**"mpv not found"**: Install mpv — `sudo apt install mpv` (Debian/Ubuntu), `brew install mpv` (macOS), `sudo dnf install mpv` (Fedora).

**"ffmpeg not found"**: Install ffmpeg — `sudo apt install ffmpeg` (Debian/Ubuntu), `brew install ffmpeg` (macOS), `sudo dnf install ffmpeg` (Fedora).

**"Could not resolve"**: The identifier wasn't a short code, UUID, or matching slug. Run `kuro search <query>` first.

## License

[GNU General Public License v3.0](LICENSE)
