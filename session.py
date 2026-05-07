from __future__ import annotations

import threading
from pathlib import Path
from typing import List, Optional

import numpy as np
from PySide6 import QtCore

from livestt.core.audio_stream import FfmpegAudioReader
from livestt.core.exporter import Exporter
from livestt.core.link_resolver import resolve_link
from livestt.core.speaker import SpeakerAssigner
from livestt.core.transcriber import WhisperTranscriber
from livestt.core.types import TranscriptEntry


class StreamSession(QtCore.QObject):
    segment_ready = QtCore.Signal(object)
    status_changed = QtCore.Signal(str)
    error = QtCore.Signal(str)
    stopped = QtCore.Signal()

    def __init__(
        self,
        name: str,
        url: str,
        whisper_model_dir: Optional[Path] = None,
        speaker_model_dir: Optional[Path] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.name = name
        self.url = url
        self.reader = FfmpegAudioReader(url=url)
        self.transcriber = WhisperTranscriber(model_dir=whisper_model_dir)
        self.speaker = SpeakerAssigner(model_dir=speaker_model_dir)
        self.exporter = Exporter()
        self._t: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._entries: List[TranscriptEntry] = []

    @property
    def entries(self) -> List[TranscriptEntry]:
        return list(self._entries)

    def start(self) -> None:
        if self._t and self._t.is_alive():
            return
        self._entries.clear()
        self.speaker.reset()
        self._stop.clear()
        self._t = threading.Thread(target=self._run, daemon=True)
        self.status_changed.emit("准备中")
        self._t.start()

    def stop(self) -> None:
        self._stop.set()
        self.reader.stop()
        self.status_changed.emit("已停止")

    def export_srt(self, path: Path) -> None:
        self.exporter.export_srt(self._entries, path)

    def export_txt(self, path: Path) -> None:
        self.exporter.export_txt(self._entries, path)

    def export_summary(self, path: Path) -> None:
        self.exporter.export_summary(self._entries, path)

    def _run(self) -> None:
        try:
            self.status_changed.emit("解析链接中")
            r = resolve_link(self.url)
            self.reader.url = r.stream_url
            self.status_changed.emit("拉流中")
            self.reader.start()
            self.status_changed.emit("运行中")
            while not self._stop.is_set():
                chunk = self.reader.read_chunk(timeout=0.5)
                if chunk is None:
                    if self.reader.error:
                        raise RuntimeError(self.reader.error)
                    continue

                for seg in self._transcribe_with_speaker(chunk.audio, chunk.sample_rate, chunk.start_sec):
                    self._entries.append(seg)
                    self.segment_ready.emit(seg)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.reader.stop()
            self.stopped.emit()

    def _transcribe_with_speaker(
        self, audio: np.ndarray, sample_rate: int, chunk_start: float
    ) -> List[TranscriptEntry]:
        out: List[TranscriptEntry] = []
        for s in self.transcriber.transcribe(audio, chunk_start_sec=chunk_start):
            rel_start = max(0.0, s.start_sec - chunk_start)
            rel_end = max(rel_start, s.end_sec - chunk_start)
            i0 = int(rel_start * sample_rate)
            i1 = min(int(rel_end * sample_rate), audio.size)
            seg_audio = audio[i0:i1]
            sid, _sim = self.speaker.assign(seg_audio)
            speaker = f"S{sid}"
            out.append(
                TranscriptEntry(
                    start_sec=s.start_sec,
                    end_sec=s.end_sec,
                    speaker=speaker,
                    text=s.text,
                )
            )
        return out
