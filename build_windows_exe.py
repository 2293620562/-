from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "livestt" / "app.py"


def main() -> int:
    onefile = os.environ.get("LIVESTT_ONEFILE", "0") == "1"
    dist = ROOT / "dist"
    build = ROOT / "build"
    dist.mkdir(exist_ok=True)
    build.mkdir(exist_ok=True)

    add_data = []
    models = ROOT / "models"
    assets = ROOT / "assets"
    if models.exists():
        add_data.append(f"{models}{os.pathsep}models")
    if assets.exists():
        add_data.append(f"{assets}{os.pathsep}assets")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "LiveSTT",
        "--windowed",
    ]
    if onefile:
        cmd.append("--onefile")

    for d in add_data:
        cmd.extend(["--add-data", d])

    cmd.extend(
        [
            "--collect-submodules",
            "speechbrain",
            "--collect-submodules",
            "torchaudio",
            "--collect-submodules",
            "torch",
            "--collect-submodules",
            "yt_dlp",
            str(SRC),
        ]
    )

    subprocess.check_call(cmd, cwd=ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
