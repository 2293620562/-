import os
import sys
from pathlib import Path


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[3]


def find_ffmpeg() -> Path:
    env = os.environ.get("LIVESTT_FFMPEG")
    if env:
        p = Path(env)
        if p.exists():
            return p

    candidates = [
        app_base_dir() / "assets" / "ffmpeg" / "ffmpeg.exe",
        app_base_dir() / "assets" / "ffmpeg" / "ffmpeg",
    ]
    for c in candidates:
        if c.exists():
            return c

    return Path("ffmpeg")

