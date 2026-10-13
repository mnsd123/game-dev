"""Tổng hợp điểm chấm trong review.csv theo kiểu hook."""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HookStat:
    hook_type: str
    n: int
    avg_score: float
    avg_retention: float | None  # tỷ lệ 0–1


def _float(text: str | None) -> float | None:
    t = (text or "").strip().replace(",", ".").rstrip("%")
    try:
        return float(t) if t else None
    except ValueError:
        return None


def _ratio(text: str | None) -> float | None:
    """'45%', '45' hoặc '0.45' → 0.45."""
    value = _float(text)
    if value is None:
        return None
    return value / 100 if (text or "").strip().endswith("%") or value > 1 else value


def summarize_reviews(csv_paths: list[Path]) -> list[HookStat]:
    """Chỉ tính dòng đã có điểm; retention_3s nhận '45%', '0.45' hoặc '45'. Xếp theo điểm giảm dần."""
    scores: dict[str, list[float]] = defaultdict(list)
    retention: dict[str, list[float]] = defaultdict(list)
    for path in csv_paths:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                hook = (row.get("hook_type") or "").strip()
                score = _float(row.get("score"))
                if not hook or score is None:
                    continue
                scores[hook].append(score)
                r = _ratio(row.get("retention_3s"))
                if r is not None:
                    retention[hook].append(r)
    stats = [
        HookStat(h, len(s), round(sum(s) / len(s), 3),
                 round(sum(retention[h]) / len(retention[h]), 4) if retention[h] else None)
        for h, s in scores.items()
    ]
    return sorted(stats, key=lambda s: (-s.avg_score, -s.n, s.hook_type))


def stats_markdown(stats: list[HookStat]) -> str:
    lines = ["| Kiểu hook | Số lần chấm | Điểm TB | Giữ chân 3 s TB |", "|---|---|---|---|"]
    for s in stats:
        ret = "—" if s.avg_retention is None else f"{s.avg_retention:.0%}"
        lines.append(f"| {s.hook_type} | {s.n} | {s.avg_score:.2f} | {ret} |")
    return "\n".join(lines)
