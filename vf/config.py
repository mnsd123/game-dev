"""Đọc cấu hình vf.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

SOURCES_DIRNAME = "source gốc"
REFERENCES_DIRNAME = "video tham khảo"
OUT_DIRNAME = "out"


@dataclass(frozen=True)
class Config:
    drive_root: Path
    sources_dir: Path
    references_dir: Path
    out_dir: Path


def load_config(path: Path = Path("vf.toml")) -> Config:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    if "drive_root" not in data:
        raise ValueError(f"{path}: thiếu khoá 'drive_root'")
    root = Path(data["drive_root"]).expanduser()
    return Config(
        drive_root=root,
        sources_dir=root / SOURCES_DIRNAME,
        references_dir=root / REFERENCES_DIRNAME,
        out_dir=root / OUT_DIRNAME,
    )
