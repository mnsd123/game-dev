"""Thông số thiết kế dùng chung (library/brand/tokens.json): vùng an toàn, cỡ chữ, thời gian, âm thanh, preset, font.
Python đọc ở đây; Remotion nhận qua props `tokens`."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from vf.paths import BRAND_DIR

TOKENS_PATH = BRAND_DIR / "tokens.json"


@lru_cache(maxsize=4)
def load_tokens(path: Path = TOKENS_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Thiếu {p} — chép từ PHỤ LỤC B của skill smilee-video")
    return json.loads(p.read_text(encoding="utf-8"))


def preset(name: str | None) -> dict:
    """Thông số preset (mặc định pink)."""
    presets = {k: v for k, v in load_tokens()["presets"].items() if not k.startswith("_")}
    return presets.get(name or "pink", presets["pink"])


def preset_names() -> list[str]:
    return [k for k in load_tokens()["presets"] if not k.startswith("_")]


def font_file(role: str = "main", brand: Path = BRAND_DIR) -> Path | None:
    """File font đầu tiên có thật theo thứ tự ưu tiên trong tokens.fonts[role]."""
    for rel in load_tokens().get("fonts", {}).get(role, []):
        p = Path(brand) / rel
        if p.exists():
            return p
    return None
