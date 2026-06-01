import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.table import Table
from rich.prompt import Prompt
from rich.markup import escape
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from kuro import state
from kuro.config_manager import get_config
from kuro.console import console, err_console
from kuro.exceptions import KuroError, ResolutionError, StreamError, DownloadError
from kuro.api import (
    fetch_anime_details,
    fetch_anime_search_results,
    fetch_episode_list,
    fetch_episode_streams,
)
from kuro.kwik import extract_hls_url
from kuro.player import play

UUID_RE = re.compile(r"^[a-f0-9-]{36}$")


def _slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _is_uuid(s: str) -> bool:
    return bool(UUID_RE.match(s))


def _generate_code(title: str, existing: set) -> str | None:
    words = re.findall(r"[a-zA-Z]+", title)
    if not words:
        alnum = re.sub(r"[^a-zA-Z0-9]", "", title)
        if not alnum:
            return None
        base = alnum[:4].lower()
    elif len(words) == 1:
        base = words[0][:4].lower()
    else:
        base = (words[0][:2] + words[1][:2]).lower()

    if base not in existing:
        return base

    n = 2
    while f"{base}{n}" in existing:
        n += 1
    return f"{base}{n}"


def _assign_code(title: str, session_id: str) -> str | None:
    existing_code = state.get_session_code(session_id)
    if existing_code:
        return existing_code

    existing = set(state.get_all_codes().keys())
    code = _generate_code(title, existing)
    if not code:
        return None

    state.save_code(code, session_id, title)
    return code


def _resolve_anime(identifier: str):
    info = state.get_code_info(identifier)
    if info:
        return info["session_id"], info["title"]

    if _is_uuid(identifier):
        details, error = fetch_anime_details(identifier)
        if not error:
            title = details.get("title", identifier)
            return identifier, title
        raise ResolutionError(
            f"Error resolving UUID: {error}",
            suggestion="Verify the UUID is correct and try again.",
        )

    results, error = fetch_anime_search_results(identifier)
    if error:
        raise ResolutionError(
            f"Error: {error}",
            suggestion="Check your internet connection and try again.",
        )

    if not results:
        raise ResolutionError(
            f"Could not resolve '{identifier}'.",
            suggestion=f"Try `kuro search {identifier}` first to find the correct ID.",
        )

    slug_map = {_slugify(r["title"]): r for r in results}
    if identifier in slug_map:
        r = slug_map[identifier]
        return r["session"], r["title"]

    if len(results) == 1:
        r = results[0]
        return r["session"], r["title"]

    table = Table(title="Multiple matches. Pick one:")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="white")
    table.add_column("Type")
    table.add_column("Episodes")
    table.add_column("Score")
    table.add_column("Status")
    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r.get("title", "N/A"),
            r.get("type", ""),
            str(r.get("episodes", "")),
            f'{r.get("score"):.2f}' if r.get("score") else "",
            r.get("status", ""),
        )
    console.print(table)
    choice = Prompt.ask(
        "Select", choices=[str(i) for i in range(1, len(results) + 1)]
    )
    r = results[int(choice) - 1]
    return r["session"], r["title"]


def _fetch_all_episodes(session_id: str, sort: str = "episode_asc", max_pages: int = 50):
    first_batch, pagination, error = fetch_episode_list(session_id, 1, sort)
    if error:
        err_console.print(f"[red]{error}[/]")
        return []
    all_ep = list(first_batch)
    last_page = min(pagination.get("last_page", 1), max_pages)
    if last_page <= 1:
        return all_ep

    with ThreadPoolExecutor(max_workers=4) as pool:
        fut_map = {
            pool.submit(fetch_episode_list, session_id, p, sort): p
            for p in range(2, last_page + 1)
        }
        for fut in as_completed(fut_map):
            batch, _, err = fut.result()
            if not err:
                all_ep.extend(batch)
    return all_ep


def _pick_episode(session_id: str):
    page = 1
    sort = "episode_desc"
    all_ep: list[dict] = []
    ep_by_num: dict[int, dict] = {}
    total_pages = 1

    def load(p: int) -> tuple[list[dict], int]:
        nonlocal page, total_pages
        page = p
        with console.status(f"Fetching page {p}..."):
            batch, pag, err = fetch_episode_list(session_id, p, sort)
        if err:
            raise KuroError(err)
        total_pages = pag.get("last_page", 1)
        all_ep.extend(batch)
        for e in batch:
            ep_by_num[int(e["episode"])] = e
        return batch, pag.get("total", 0)

    batch, total_count = load(1)
    if not all_ep:
        raise KuroError(
            "No episodes found for this anime.",
            suggestion="The anime may not have been released yet.",
        )

    while True:
        console.print(f"[dim]Episodes loaded: {len(ep_by_num)} / {total_count}  (page {page}/{total_pages})[/]")
        table = Table()
        table.add_column("#", style="cyan")
        for ep in batch:
            table.add_row(str(ep.get("episode", "?")))
        console.print(table)

        nav = []
        if page < total_pages:
            nav.append("n=next")
        if page > 1:
            nav.append("p=prev")
        if len(ep_by_num) < total_count:
            nav.append("a=load all")
        nav_str = f" ({', '.join(nav)})" if nav else " (all loaded)"

        choice = Prompt.ask(f"Enter episode number or range{nav_str}")

        if choice == "n" and page < total_pages:
            batch, _ = load(page + 1)
            continue
        if choice == "p" and page > 1:
            batch, _ = load(page - 1)
            continue
        if choice == "a" and len(ep_by_num) < total_count:
            for p in range(page + 1, total_pages + 1):
                load(p)
            console.print(f"[dim]Loaded all {len(ep_by_num)} episodes.[/]")
            continue

        range_match = re.match(r"^(\d+)-(\d+)$", choice)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if any(n not in ep_by_num for n in range(start, end + 1)):
                for p in range(page + 1, total_pages + 1):
                    load(p)
            filtered = [ep_by_num[n] for n in range(start, end + 1) if n in ep_by_num]
            if not filtered:
                err_console.print(f"[red]No episodes in range {start}-{end}.[/]")
                continue
            t = Table()
            t.add_column("#", style="cyan")
            for ep in filtered:
                t.add_row(str(ep.get("episode", "?")))
            console.print(t)
            sub = Prompt.ask("Enter episode number")
            if int(sub) in ep_by_num:
                return ep_by_num[int(sub)]["session"]
            err_console.print(f"[red]Episode {sub} not found in range.[/]")
            continue

        ep_num = int(choice)
        if ep_num in ep_by_num:
            return ep_by_num[ep_num]["session"]

        if len(ep_by_num) < total_count:
            with console.status(f"Searching for episode {ep_num}..."):
                for p in range(page + 1, total_pages + 1):
                    load(p)
            if ep_num in ep_by_num:
                return ep_by_num[ep_num]["session"]
        err_console.print(f"[red]Episode {choice} not found.[/]")


def _pick_best_by_resolution(
    items: list[dict], preferred_language: str | None = None,
) -> dict:
    if preferred_language:
        matching = [i for i in items if i.get("audio") == preferred_language]
        if matching:
            return max(matching, key=lambda i: int(i.get("resolution", 0) or 0))
    return max(items, key=lambda i: int(i.get("resolution", 0) or 0))


def _pick_quality(
    items: list[dict], preferred: str | None = None,
    preferred_language: str | None = None,
) -> dict:
    if len(items) == 1:
        return items[0]

    if preferred and preferred != "best":
        for item in items:
            if str(item.get("resolution", "")) == preferred:
                if not preferred_language or item.get("audio") == preferred_language:
                    return item
        for item in items:
            if str(item.get("resolution", "")) == preferred:
                return item

    if preferred == "best":
        return _pick_best_by_resolution(items, preferred_language)

    from collections import OrderedDict

    groups = OrderedDict()
    for i, item in enumerate(items):
        audio = item.get('audio', 'unknown')
        fansub = item.get('fansub', '')
        groups.setdefault((audio, fansub), []).append((i + 1, item))

    console.print("\n[bold]Available qualities:[/]")
    for (audio, fansub), group in groups.items():
        parts = [f"[{audio or '?'}]"]
        if fansub:
            parts.append(fansub)
        header = escape(" ".join(parts))
        console.print(f"  [bold]{header}:[/]")
        for idx, item in group:
            console.print(f"    {idx}. {item.get('resolution', '?')}p")

    choice = Prompt.ask(
        "Select",
        choices=[str(i) for i in range(1, len(items) + 1)],
    )
    return items[int(choice) - 1]


def _resolve_and_play(anime: str, raw_episode: str | None, do_play: bool):
    session_id, title = _resolve_anime(anime)
    episode_id = _resolve_episode_number(session_id, int(raw_episode)) if raw_episode else _pick_episode(session_id)

    with console.status("Fetching streams..."):
        streams, error = fetch_episode_streams(session_id, episode_id)

    if error:
        raise StreamError(
            error,
            suggestion="Check your internet connection and try again.",
        )
    if not streams:
        raise StreamError(
            "No streams found.",
            suggestion="This episode may not have been released yet.",
        )

    cfg = get_config()
    selected = _pick_quality(streams, cfg.quality, cfg.language)
    kwik_url = selected["kwik_url"]

    with console.status("Extracting video URL..."):
        try:
            video_url = extract_hls_url(kwik_url)
        except Exception as e:
            raise StreamError(
                f"Failed to extract video URL: {e}",
                suggestion="Try updating yt-dlp: pip install -U yt-dlp",
            )

    if do_play:
        label = f"{selected.get('resolution', '?')}p"
        console.print(f"[green]Streaming {label}...[/]")
        state.add_history_entry("watch", anime, title, session_id)
        play(video_url, cfg.player)
    else:
        console.print(f"\n[bold green]Video URL:[/] {video_url}")


def _sanitize_filename(title: str) -> str:
    s = title.lower().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_-]", "", s)
    return s.strip("_")


def _parse_episode_range(range_str: str) -> list[int]:
    nums: list[int] = []
    for part in range_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            nums.extend(range(int(a), int(b) + 1))
        else:
            nums.append(int(part))
    return sorted(set(nums))


def _resolve_episode_number(session_id: str, episode_num: int) -> str:
    all_ep = _fetch_all_episodes(session_id)
    for ep in all_ep:
        if int(ep.get("episode", 0)) == episode_num:
            return ep["session"]
    raise KuroError(
        f"Episode {episode_num} not found.",
        suggestion="Use `kuro episodes <anime>` to list available episodes.",
    )


def _format_size(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


_ytdlp_cache: bool | None = None

def _ytdlp_available() -> bool:
    global _ytdlp_cache
    if _ytdlp_cache is None:
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
            _ytdlp_cache = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            _ytdlp_cache = False
    return _ytdlp_cache

YTDLP_PROGRESS_RE = re.compile(
    r"\[download\]\s+(\d+(?:\.\d+)?)%"
)


def _notify(title: str, message: str):
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", title, message], capture_output=True)


def _download_one(video_url: str, output_path: Path, label: str, resume: bool = False):
    if not _ytdlp_available():
        raise DownloadError(
            "yt-dlp is required for downloads.\n"
            "  Install: pip install yt-dlp pycryptodomex"
        )

    if not shutil.which("ffmpeg"):
        raise DownloadError(
            "ffmpeg not found (required by yt-dlp for merging).\n"
            "  apt:  sudo apt install ffmpeg\n"
            "  brew: brew install ffmpeg\n"
            "  dnf:  sudo dnf install ffmpeg\n"
            "  pacman: sudo pacman -S ffmpeg\n"
            "  choco: choco install ffmpeg"
        )

    argv = ["yt-dlp",
            "--referer", "https://kwik.cx/",
            "--newline",
            "--no-mtime"]
    if resume:
        argv += ["--continue", "-c"]
    argv += ["-o", str(output_path), video_url]
    proc = subprocess.Popen(argv,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True,
    )

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
    )

    with progress:
        task = progress.add_task(f"[cyan]Downloading {label}...", total=100)

        for line in proc.stdout:
            m = YTDLP_PROGRESS_RE.search(line)
            if m:
                progress.update(task, completed=float(m.group(1)))

        proc.wait()

    if proc.returncode != 0:
        raise DownloadError(
            f"Download failed (exit code {proc.returncode})",
            suggestion="Check your internet connection and available disk space.",
        )

    size = _format_size(output_path.stat().st_size)
    console.print(f"[green]Downloaded:[/] {output_path.name} ({size})")
    state.add_history_entry("download", label, output_path.name, "")
    _notify("Download Complete", f"{output_path.name} ({size})")


def _download_single(anime: str, raw_episode: str | None, output_dir: Path | None, resume: bool = False):
    cfg = get_config()
    resume = resume or cfg.resume
    session_id, title = _resolve_anime(anime)

    if output_dir is None:
        output_dir = cfg.output_dir / _sanitize_filename(title)
    output_dir.mkdir(parents=True, exist_ok=True)

    episode_id = _resolve_episode_number(session_id, int(raw_episode)) if raw_episode else _pick_episode(session_id)

    with console.status("Fetching episode info..."):
        all_ep = _fetch_all_episodes(session_id)

    ep_num = None
    for ep in all_ep:
        if ep.get("session") == episode_id:
            ep_num = int(ep.get("episode", 0))
            break

    label = f"EP{ep_num:02d}" if ep_num else "episode"
    safe_title = _sanitize_filename(title)

    with console.status("Fetching streams..."):
        streams, error = fetch_episode_streams(session_id, episode_id)

    if error:
        raise DownloadError(
            error,
            suggestion="Check your internet connection and try again.",
        )
    if not streams:
        raise DownloadError(
            "No streams found.",
            suggestion="This episode may not have been released yet.",
        )

    selected = _pick_quality(streams, cfg.quality, cfg.language)

    with console.status("Extracting video URL..."):
        try:
            video_url = extract_hls_url(selected["kwik_url"])
        except Exception as e:
            raise DownloadError(
                f"Failed to extract video URL: {e}",
                suggestion="Try updating yt-dlp: pip install -U yt-dlp",
            )

    console.print(f"[dim]URL: {video_url}[/]")

    output_path = output_dir / cfg.filename_template.format(
        title=safe_title, episode=ep_num or 0, label=label,
        quality=f"{selected.get('resolution', '?')}p",
    )
    _download_one(video_url, output_path, label, resume)


def _batch_download(anime: str, episodes: list[int], output_dir: Path | None, resume: bool = False):
    cfg = get_config()
    resume = resume or cfg.resume
    session_id, title = _resolve_anime(anime)

    if output_dir is None:
        output_dir = cfg.output_dir / _sanitize_filename(title)

    output_dir.mkdir(parents=True, exist_ok=True)

    with console.status("Fetching episodes..."):
        all_ep = _fetch_all_episodes(session_id)

    if not all_ep:
        raise DownloadError(
            "No episodes found.",
            suggestion="The anime may not have been released yet.",
        )

    ep_map = {int(e.get("episode", 0)): e for e in all_ep}
    safe_title = _sanitize_filename(title)

    def _pick_best(items: list[dict]) -> dict:
        pref = cfg.quality
        if pref and pref != "best":
            for item in items:
                if str(item.get("resolution", "")) == pref:
                    if not cfg.language or item.get("audio") == cfg.language:
                        return item
            for item in items:
                if str(item.get("resolution", "")) == pref:
                    return item
        return _pick_best_by_resolution(items, cfg.language)

    for ep_num in episodes:
        ep = ep_map.get(ep_num)
        if not ep:
            err_console.print(f"[yellow]Episode {ep_num} not found, skipping.[/]")
            continue

        ep_session = ep.get("session")
        label = f"EP{ep_num:02d}"

        with console.status(f"Fetching streams for {label}..."):
            streams, error = fetch_episode_streams(session_id, ep_session)

        if error:
            err_console.print(f"[red]{label}: {error}[/]")
            continue
        if not streams:
            err_console.print(f"[red]{label}: No streams found.[/]")
            continue

        selected = _pick_best(streams)

        with console.status(f"Extracting video URL for {label}..."):
            try:
                video_url = extract_hls_url(selected["kwik_url"])
            except Exception as e:
                err_console.print(f"[red]{label}: Failed to extract URL: {e}[/]")
                continue

        console.print(f"[dim]{label} URL: {video_url}[/]")

        output_path = output_dir / cfg.filename_template.format(
            title=safe_title, episode=ep_num, label=label,
            quality=f"{selected.get('resolution', '?')}p",
        )
        _download_one(video_url, output_path, label, resume)

    console.print(f"\n[green]Batch download complete. Files saved to: {output_dir}[/]")
    _notify("Batch Download Complete", f"{title}: {len(episodes)} episode(s) saved to {output_dir}")
