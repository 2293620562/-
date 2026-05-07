from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import torch
from speechbrain.pretrained import EncoderClassifier

from livestt.core.ffmpeg import app_base_dir


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


@dataclass
class SpeakerState:
    centroid: Optional[np.ndarray]
    count: int


class SpeakerAssigner:
    def __init__(
        self,
        model_dir: Optional[Path] = None,
        sample_rate: int = 16000,
        min_sec: float = 1.0,
        new_speaker_threshold: float = 0.72,
    ):
        self.model_dir = model_dir or (app_base_dir() / "models" / "speaker")
        self.sample_rate = sample_rate
        self.min_sec = min_sec
        self.new_speaker_threshold = new_speaker_threshold
        self._clf: Optional[EncoderClassifier] = None
        self._speakers: Dict[int, SpeakerState] = {}
        self._next_id = 1
        self._last_id: Optional[int] = None

    def ensure_loaded(self) -> None:
        if self._clf is not None:
            return
        if not self.model_dir.exists():
            raise FileNotFoundError(f"说话人模型目录不存在: {self.model_dir}")
        self._clf = EncoderClassifier.from_hparams(
            source=str(self.model_dir),
            savedir=str(self.model_dir),
            run_opts={"device": "cpu"},
        )

    def reset(self) -> None:
        self._speakers.clear()
        self._next_id = 1
        self._last_id = None

    def embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        self.ensure_loaded()
        assert self._clf is not None
        if audio.size < int(self.sample_rate * self.min_sec):
            return None
        wav = torch.from_numpy(audio.astype(np.float32)).unsqueeze(0)
        if wav.abs().max().item() > 1.5:
            wav = wav / 32768.0
        with torch.inference_mode():
            emb = self._clf.encode_batch(wav).squeeze(0).squeeze(0).cpu().numpy()
        return emb.astype(np.float32)

    def assign(self, audio: np.ndarray) -> Tuple[int, float]:
        emb = self.embedding(audio)
        if emb is None:
            if self._last_id is not None:
                return self._last_id, 0.0
            sid = self._next_id
            self._speakers[sid] = SpeakerState(centroid=None, count=0)
            self._next_id += 1
            self._last_id = sid
            return sid, 0.0

        best_id = 0
        best_sim = -1.0
        for sid, st in self._speakers.items():
            sim = _cosine(emb, st.centroid) if st.count > 0 and st.centroid is not None else -1.0
            if sim > best_sim:
                best_sim = sim
                best_id = sid

        if best_id == 0 or best_sim < self.new_speaker_threshold:
            sid = self._next_id
            self._speakers[sid] = SpeakerState(centroid=emb, count=1)
            self._next_id += 1
            self._last_id = sid
            return sid, 1.0

        st = self._speakers[best_id]
        if st.centroid is None or st.count == 0:
            st.centroid = emb
            st.count = 1
        else:
            st.centroid = (st.centroid * st.count + emb) / float(st.count + 1)
            st.count += 1
        self._last_id = best_id
        return best_id, best_sim
