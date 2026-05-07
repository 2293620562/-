from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from faster_whisper import WhisperModel

from livestt.core.ffmpeg import app_base_dir


@dataclass(frozen=True)
class TextSegment:
    start_sec: float
    end_sec: float
    text: str


class WhisperTranscriber:
    def __init__(
        self,
        model_dir: Optional[Path] = None,
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None,
    ):
        self.model_dir = model_dir or (app_base_dir() / "models" / "whisper")
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model: Optional[WhisperModel] = None

    def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Whisper模型目录不存在: {self.model_dir}")
        self._model = WhisperModel(
            str(self.model_dir),
            device=self.device,
            compute_type=self.compute_type,
        )

    def transcribe(self, audio, chunk_start_sec: float) -> Iterable[TextSegment]:
        self.ensure_loaded()
        assert self._model is not None
        segments, _info = self._model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
            beam_size=5,
        )
        for s in segments:
            txt = (s.text or "").strip()
            if not txt:
                continue
            yield TextSegment(
                start_sec=chunk_start_sec + float(s.start),
                end_sec=chunk_start_sec + float(s.end),
                text=txt,
            )

