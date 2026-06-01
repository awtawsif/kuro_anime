import importlib.metadata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str


def check_mpv() -> CheckResult:
    mpv = shutil.which("mpv")
    if mpv:
        return CheckResult("mpv", True, f"Found: {mpv}")
    return CheckResult(
        "mpv", False,
        "Not found. Install:\n"
        "  apt:  sudo apt install mpv\n"
        "  brew: brew install mpv\n"
        "  dnf:  sudo dnf install mpv\n"
        "  pacman: sudo pacman -S mpv\n"
        "  choco: choco install mpv",
    )


def check_ffmpeg() -> CheckResult:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return CheckResult("ffmpeg", True, f"Found: {ffmpeg}")
    return CheckResult(
        "ffmpeg", False,
        "Not found (required by yt-dlp for downloads). Install:\n"
        "  apt:  sudo apt install ffmpeg\n"
        "  brew: brew install ffmpeg\n"
        "  dnf:  sudo dnf install ffmpeg\n"
        "  pacman: sudo pacman -S ffmpeg\n"
        "  choco: choco install ffmpeg",
    )


def check_ytdlp_cli() -> CheckResult:
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"],
            capture_output=True, text=True, check=True,
        )
        version = result.stdout.strip()
        return CheckResult("yt-dlp (CLI)", True, f"Found: {version}")
    except FileNotFoundError:
        return CheckResult(
            "yt-dlp (CLI)", False,
            "Not found. Install: pip install yt-dlp",
        )
    except subprocess.CalledProcessError as e:
        return CheckResult(
            "yt-dlp (CLI)", False,
            f"Error running yt-dlp: {e}",
        )


def check_ytdlp_module() -> CheckResult:
    try:
        import yt_dlp
        version = getattr(yt_dlp, "__version__", "unknown")
        return CheckResult("yt-dlp (Python module)", True, f"Found: {version}")
    except ImportError:
        return CheckResult(
            "yt-dlp (Python module)", False,
            "Not installed. Run: pip install yt-dlp pycryptodomex",
        )


def check_curl_cffi() -> CheckResult:
    try:
        import curl_cffi
        version = getattr(curl_cffi, "__version__", "unknown")
        return CheckResult("curl_cffi", True, f"Found: {version}")
    except ImportError:
        return CheckResult(
            "curl_cffi", False,
            "Not installed. Run: pip install curl_cffi",
        )


def check_python_version() -> CheckResult:
    v = sys.version_info
    ok = v.major >= 3 and v.minor >= 10
    return CheckResult(
        "Python version", ok,
        f"{v.major}.{v.minor}.{v.micro} ({'OK' if ok else '3.10+ required'})",
    )


def check_config() -> CheckResult:
    config_path = Path.home() / ".kuro_anime" / "config.toml"
    if config_path.exists():
        return CheckResult("Config file", True, f"Found: {config_path}")
    return CheckResult(
        "Config file", True,
        f"Not present (using defaults). Create: {config_path}",
    )


def check_all() -> list[CheckResult]:
    return [
        check_python_version(),
        check_mpv(),
        check_ffmpeg(),
        check_ytdlp_cli(),
        check_ytdlp_module(),
        check_curl_cffi(),
        check_config(),
    ]
