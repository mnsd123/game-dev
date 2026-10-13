"""Kịch bản dựng (edl.json): mỗi biến thể là hook + danh sách đoạn, mỗi đoạn tự khai nguồn."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, model_validator

from vf.probe import MediaInfo

HOOK_MAX_S = 3.0
DURATION_TOLERANCE_S = 0.05


class Segment(BaseModel):
    source: str  # tên file trong sources_dir
    start: float  # theo timeline của chính nguồn đó
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


Animation = Literal["pop", "word_by_word", "highlight", "slide", "none"]


class TextOverlay(BaseModel):
    text: str
    start: float  # theo timeline output
    end: float
    position: Literal["top", "center", "bottom"] = "top"
    style: Literal["hook", "commit", "label", "cta", "plain"] = "hook"
    animation: Animation = "pop"
    emphasis: list[str] = []  # từ được tô vệt highlight; rỗng + animation=highlight → tô cả câu


class Effect(BaseModel):
    kind: Literal["zoom_punch", "shake", "flash", "sfx", "highlight"]
    at: float  # theo timeline output
    duration: float = 0.3
    asset: str | None = None


class Variant(BaseModel):
    id: str
    hook_type: str
    hook: Segment
    segments: list[Segment]
    overlays: list[TextOverlay] = []
    effects: list[Effect] = []
    captions: bool = False  # mặc định KHÔNG phụ đề toàn bộ lời; chỉ chữ động ở đoạn quan trọng
    music: str | None = None
    rationale: str

    def pieces(self) -> list[Segment]:
        """Thứ tự phát trong output: hook rồi tới segments."""
        return [self.hook, *self.segments]

    @model_validator(mode="after")
    def _check(self) -> "Variant":
        for label, seg in self.labeled_pieces():
            if seg.start < 0 or seg.start >= seg.end:
                raise ValueError(f"biến thể '{self.id}', {label}: start ({seg.start}) phải ≥ 0 và < end ({seg.end})")
        if self.hook.duration > HOOK_MAX_S + 1e-6:
            raise ValueError(f"biến thể '{self.id}', hook dài {self.hook.duration:.2f} s > {HOOK_MAX_S} s")
        for i, o in enumerate(self.overlays):
            if o.start < 0 or o.start >= o.end:
                raise ValueError(f"biến thể '{self.id}', overlays[{i}]: start phải < end")
        return self

    def labeled_pieces(self) -> list[tuple[str, Segment]]:
        return [("hook", self.hook)] + [(f"segments[{i}]", s) for i, s in enumerate(self.segments)]


class EDL(BaseModel):
    job: str
    variants: list[Variant]

    @model_validator(mode="after")
    def _unique_ids(self) -> "EDL":
        ids = [v.id for v in self.variants]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"id biến thể bị trùng: {sorted(dup)}")
        return self


def output_duration(v: Variant) -> float:
    return sum(s.duration for s in v.pieces())


def validate_sources(edl: EDL, infos: dict[str, MediaInfo]) -> None:
    for v in edl.variants:
        for label, seg in v.labeled_pieces():
            if seg.source not in infos:
                raise ValueError(
                    f"biến thể '{v.id}', {label}: nguồn '{seg.source}' không có trong source gốc "
                    f"(có: {sorted(infos)})"
                )
            dur = infos[seg.source].duration
            if seg.end > dur + DURATION_TOLERANCE_S:
                raise ValueError(
                    f"biến thể '{v.id}', {label}: end {seg.end} vượt độ dài nguồn '{seg.source}' ({dur:.2f} s)"
                )


def load_edl(path: Path, infos: dict[str, MediaInfo]) -> EDL:
    edl = EDL(**json.loads(Path(path).read_text(encoding="utf-8")))
    validate_sources(edl, infos)
    return edl
