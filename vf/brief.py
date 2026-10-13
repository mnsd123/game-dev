"""Schema brief.yaml cho mỗi lô."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

FORBIDDEN_PATH = Path("library/forbidden.txt")
PENDING_PATH = Path("library/claims_pending.txt")


class Brief(BaseModel):
    platform: Literal["tiktok", "reels", "shorts"]
    aspect: Literal["9:16", "1:1", "16:9"] = "9:16"
    target_seconds: int = Field(gt=0)
    variants: int = Field(default=3, ge=1, le=20)
    goal: Literal["awareness", "education", "conversion"]
    message: str
    cta: str
    audience: str = ""
    source_roles: dict[str, str] = {}
    must_keep: list[str] = []
    must_cut: list[str] = []
    hook_ideas: list[str] = []
    tone: str = ""
    forbidden: list[str] = []
    style: str = "default"


def read_phrase_list(path: Path) -> list[str]:
    """Mỗi dòng một cụm; bỏ dòng trống và dòng chú thích bắt đầu bằng #."""
    if not path or not Path(path).exists():
        return []
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


def _dedupe(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        key = item.strip()
        if key and key.casefold() not in {k.casefold() for k in seen}:
            seen[key] = None
    return list(seen)


def load_brief(
    path: Path,
    forbidden_path: Path = FORBIDDEN_PATH,
    pending_path: Path | None = PENDING_PATH,
) -> Brief:
    """Đọc brief; gộp `forbidden` của brief với forbidden.txt và claims_pending.txt, bỏ trùng."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    brief = Brief(**data)
    merged = brief.forbidden + read_phrase_list(forbidden_path)
    if pending_path is not None:
        merged += read_phrase_list(pending_path)
    return brief.model_copy(update={"forbidden": _dedupe(merged)})
