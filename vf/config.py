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
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(
                f"{path}: file cấu hình sai cú pháp ({e}). Đường dẫn Windows hãy viết bằng dấu / "
                "(drive_root = \"G:/My Drive/EDIT\") hoặc đặt trong dấu nháy đơn "
                "(drive_root = 'G:\\My Drive\\EDIT')."
            ) from e
    if "drive_root" not in data:
        raise ValueError(f"{path}: thiếu khoá 'drive_root'")
    root = Path(data["drive_root"]).expanduser()
    return Config(
        drive_root=root,
        sources_dir=root / SOURCES_DIRNAME,
        references_dir=root / REFERENCES_DIRNAME,
        out_dir=root / OUT_DIRNAME,
    )
