import shutil
import subprocess
import sys


from kuro.exceptions import PlayerNotFoundError


def play(url: str, player_bin: str | None = None):
    bin_name = player_bin or "mpv"
    player = shutil.which(bin_name)
    if not player:
        raise PlayerNotFoundError(
            f"'{bin_name}' not found. Install it:\n"
            "  apt:  sudo apt install mpv\n"
            "  brew: brew install mpv\n"
            "  dnf:  sudo dnf install mpv\n"
            "  pacman: sudo pacman -S mpv\n"
            "  choco: choco install mpv"
        )

    subprocess.run([player, f"--referrer=https://kwik.cx/", url])
