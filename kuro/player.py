import shutil
import subprocess
import sys


from kuro.exceptions import PlayerNotFoundError


def play(url: str):
    mpv = shutil.which("mpv")
    if not mpv:
        raise PlayerNotFoundError(
            "mpv not found. Install it:\n"
            "  apt:  sudo apt install mpv\n"
            "  brew: brew install mpv\n"
            "  choco: choco install mpv"
        )

    subprocess.run([mpv, f"--referrer=https://kwik.cx/", url])
