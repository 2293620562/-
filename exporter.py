from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, List

from livestt.core.types import TranscriptEntry


def _srt_time(sec: float) -> str:
    if sec < 0:
        sec = 0
    ms = int(round(sec * 1000.0))
    h = ms // 3600000
    ms -= h * 3600000
    m = ms // 60000
    ms -= m * 60000
    s = ms // 1000
    ms -= s * 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _sentences(text: str) -> List[str]:
    parts = re.split(r"[。！？!?;\n\r]+", text)
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out


def _tokens(s: str) -> List[str]:
    out: List[str] = []
    for w in re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", s):
        if re.fullmatch(r"[\u4e00-\u9fff]", w):
            out.append(w)
        else:
            out.append(w.lower())
    return out


_STOP = {
    "的",
    "了",
    "是",
    "我",
    "你",
    "他",
    "她",
    "它",
    "们",
    "在",
    "和",
    "与",
    "就",
    "都",
    "也",
    "啊",
    "嗯",
    "哦",
    "then",
    "and",
    "the",
    "a",
    "to",
    "of",
    "in",
    "for",
    "on",
    "is",
    "are",
}


class Exporter:
    def export_srt(self, entries: Iterable[TranscriptEntry], path: Path) -> None:
        lines: List[str] = []
        for idx, e in enumerate(entries, start=1):
            lines.append(str(idx))
            lines.append(f"{_srt_time(e.start_sec)} --> {_srt_time(e.end_sec)}")
            lines.append(f"{e.speaker}: {e.text}")
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")

    def export_txt(self, entries: Iterable[TranscriptEntry], path: Path) -> None:
        lines: List[str] = []
        for e in entries:
            lines.append(f"[{_srt_time(e.start_sec)}-{_srt_time(e.end_sec)}] {e.speaker}: {e.text}")
        path.write_text("\n".join(lines), encoding="utf-8")

    def export_summary(self, entries: Iterable[TranscriptEntry], path: Path) -> None:
        by_spk = defaultdict(list)
        all_text = []
        for e in entries:
            by_spk[e.speaker].append(e.text)
            all_text.append(e.text)
        full = "\n".join(all_text).strip()
        summary = self._extractive_summary(full)
        keywords = self._keywords(full)

        lines: List[str] = []
        lines.append("关键词:")
        lines.append(" ".join(keywords))
        lines.append("")
        lines.append("摘要:")
        lines.extend(summary)
        lines.append("")
        lines.append("按说话人整理:")
        for spk in sorted(by_spk.keys()):
            lines.append("")
            lines.append(f"{spk}:")
            lines.extend(by_spk[spk])
        path.write_text("\n".join(lines), encoding="utf-8")

    def _extractive_summary(self, text: str, max_sentences: int = 5) -> List[str]:
        sents = _sentences(text)
        if not sents:
            return []
        freq = Counter(t for s in sents for t in _tokens(s) if t not in _STOP)
        scored = []
        for i, s in enumerate(sents):
            toks = [t for t in _tokens(s) if t not in _STOP]
            score = sum(freq.get(t, 0) for t in toks)
            scored.append((score, i, s))
        top = sorted(scored, key=lambda x: (-x[0], x[1]))[: max_sentences]
        top_sorted = sorted(top, key=lambda x: x[1])
        return [t[2] for t in top_sorted]

    def _keywords(self, text: str, k: int = 15) -> List[str]:
        freq = Counter(t for t in _tokens(text) if t not in _STOP)
        return [w for w, _c in freq.most_common(k)]
