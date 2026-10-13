"""Chạy phân tích cho mọi file nguồn: chuẩn hoá, phiên âm, khoảng lặng."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from vf.probe import MediaInfo, normalize, probe
from vf.silence import detect_silences, keep_ranges
from vf.transcribe import Word, transcribe

VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".webm", ".mts"}


def list_videos(folder: Path) -> list[Path]:
    return sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS)


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _fresh(out: Path, src: Path) -> bool:
    return out.exists() and out.stat().st_mtime >= src.stat().st_mtime


def source_work_dir(work_dir: Path, source_name: str) -> Path:
    """work/<tên file nguồn kèm đuôi>/ — 'clip.mov' và 'clip.mp4' không dùng chung kết quả."""
    return Path(work_dir) / source_name


def analyze_source(
    src: Path, work_dir: Path, transcriber: Callable[[Path], list[Word]] | None = transcribe
) -> MediaInfo:
    """Ghi work/<tên-nguồn>/{normalized.mp4, transcript.json, silences.json, keep.json}.
    Bỏ qua bước đã có kết quả mới hơn file nguồn (chạy lại nhanh).
    transcriber=None: bỏ phiên âm (ghi transcript rỗng kèm dấu 'transcript.skipped' để lần sau phiên âm lại)."""
    d = source_work_dir(work_dir, src.name)
    d.mkdir(parents=True, exist_ok=True)
    norm = d / "normalized.mp4"
    info = None
    if _fresh(norm, src):
        try:
            info = probe(norm)
        except Exception:  # file dở dang từ lần chạy bị ngắt
            info = None
    if info is None:
        normalize(src, norm)
        info = probe(norm)
    tr, skipped = d / "transcript.json", d / "transcript.skipped"
    if transcriber is None:
        if not tr.exists() or skipped.exists():
            _write_json(tr, [])
            skipped.touch()
    elif not _fresh(tr, norm) or skipped.exists():
        _write_json(tr, [asdict(w) for w in transcriber(norm)])
        skipped.unlink(missing_ok=True)
    silences = detect_silences(norm)
    _write_json(d / "silences.json", [asdict(r) for r in silences])
    _write_json(d / "keep.json", [asdict(r) for r in keep_ranges(info.duration, silences)])
    _write_json(d / "info.json", asdict(info))
    return info


def analyze_all(
    sources_dir: Path, work_dir: Path, transcriber: Callable[[Path], list[Word]] | None = transcribe
) -> dict[str, MediaInfo]:
    """Khoá = tên file nguồn (kèm đuôi), đúng như `Segment.source` và `brief.source_roles`."""
    return {src.name: analyze_source(src, work_dir, transcriber) for src in list_videos(sources_dir)}


def load_words(work_dir: Path, source_name: str) -> list[Word]:
    p = source_work_dir(work_dir, source_name) / "transcript.json"
    if not p.exists():
        return []
    return [Word(**w) for w in json.loads(p.read_text(encoding="utf-8"))]
