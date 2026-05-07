from __future__ import annotations

import subprocess
import threading
from dataclasses import dataclass
from queue import Queue
from typing import Optional

import numpy as np

from livestt.core.ffmpeg import find_ffmpeg


@dataclass(frozen=True)
class AudioChunk:
    start_sec: float
    sample_rate: int
    audio: np.ndarray


class FfmpegAudioReader:
    def __init__(self, url: str, sample_rate: int = 16000, chunk_sec: float = 10.0):
        self.url = url
        self.sample_rate = sample_rate
        self.chunk_sec = chunk_sec
        self._proc: Optional[subprocess.Popen[bytes]] = None
        self._t: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._q: Queue[AudioChunk] = Queue(maxsize=32)
        self._err: Optional[str] = None

    @property
    def error(self) -> Optional[str]:
        return self._err

    def start(self) -> None:
        if self._t and self._t.is_alive():
            return
        self._stop.clear()
        ffmpeg = str(find_ffmpeg())
        cmd = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            self.url,
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(self.sample_rate),
            "-f",
            "s16le",
            "pipe:1",
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def stop(self) -> None:
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        if self._t:
            self._t.join(timeout=2)

    def read_chunk(self, timeout: float = 0.5) -> Optional[AudioChunk]:
        try:
            return self._q.get(timeout=timeout)
        except Exception:
            return None

    def _run(self) -> None:
        assert self._proc is not None
        assert self._proc.stdout is not None
        chunk_samples = int(self.sample_rate * self.chunk_sec)
        buf = bytearray()
        sample_cursor = 0
        bytes_per_sample = 2
        target_bytes = chunk_samples * bytes_per_sample

        while not self._stop.is_set():
            data = self._proc.stdout.read(4096)
            if not data:
                break
            buf.extend(data)
            while len(buf) >= target_bytes:
                raw = bytes(buf[:target_bytes])
                del buf[:target_bytes]
                pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                chunk_start = sample_cursor / self.sample_rate
                sample_cursor += chunk_samples
                try:
                    self._q.put(
                        AudioChunk(start_sec=chunk_start, sample_rate=self.sample_rate, audio=pcm),
                        timeout=1.0,
                    )
                except Exception:
                    pass

        if self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

        if self._proc.stderr:
            try:
                err = self._proc.stderr.read().decode("utf-8", errors="ignore").strip()
                if err:
                    self._err = err
            except Exception:
                pass
