from __future__ import annotations

import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
ASSETS = ROOT / "assets"


def _download_ffmpeg_windows() -> None:
    url = os.environ.get(
        "LIVESTT_FFMPEG_ZIP",
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    )
    out_dir = ASSETS / "ffmpeg"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        zpath = Path(td) / "ffmpeg.zip"
        urlretrieve(url, zpath)
        with zipfile.ZipFile(zpath, "r") as zf:
            zf.extractall(Path(td) / "unz")
        exe = next((Path(td) / "unz").rglob("ffmpeg.exe"), None)
        if exe is None:
            raise RuntimeError("ffmpeg.exe 未在压缩包中找到")
        shutil.copy2(exe, out_dir / "ffmpeg.exe")


def _download_models() -> None:
    whisper_dir = MODELS / "whisper"
    speaker_dir = MODELS / "speaker"
    whisper_dir.mkdir(parents=True, exist_ok=True)
    speaker_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=os.environ.get("LIVESTT_WHISPER_REPO", "Systran/faster-whisper-small"),
        local_dir=whisper_dir,
        local_dir_use_symlinks=False,
        ignore_patterns=["*.msgpack", "*.h5", "*.onnx_data"],
    )

    snapshot_download(
        repo_id=os.environ.get("LIVESTT_SPEAKER_REPO", "speechbrain/spkrec-ecapa-voxceleb"),
        local_dir=speaker_dir,
        local_dir_use_symlinks=False,
    )


def main() -> int:
    MODELS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    if sys.platform.startswith("win"):
        _download_ffmpeg_windows()
    _download_models()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

