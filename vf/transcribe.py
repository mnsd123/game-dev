"""Phiên âm từng từ bằng faster-whisper."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from vf.ffutil import ffprobe_json

DEFAULT_MODEL = os.environ.get("VF_WHISPER_MODEL", "large-v3")


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@lru_cache(maxsize=2)
def _model(name: str):
    from faster_whisper import WhisperModel

    return WhisperModel(name, device="auto", compute_type="auto")


def transcribe(path: Path, lang: str = "vi", model: str = DEFAULT_MODEL) -> list[Word]:
    """Trả [] nếu file không có tiếng (video chỉ có cảnh sản phẩm)."""
    data = ffprobe_json(path)
    if not any(s["codec_type"] == "audio" for s in data["streams"]):
        return []
    segments, _ = _model(model).transcribe(str(path), language=lang, word_timestamps=True)
    words: list[Word] = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append(Word(text, round(w.start, 3), round(w.end, 3)))
    return words
