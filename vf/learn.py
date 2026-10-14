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


# ---------------------------------------------------------------- skill v2: theo preset × hook × độ dài

METRIC_COLUMNS = ["view_2s", "view_6s", "avg_watch_s", "ctr", "cvr", "cost_per_order"]


def length_bucket(text: str | None) -> str:
    s = _float(text)
    if s is None:
        return "—"
    return "≤45 s" if s <= 45 else "46–75 s" if s <= 75 else ">75 s"


def _rows(csv_paths: list[Path]) -> list[dict]:
    out = []
    for path in csv_paths:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _float(row.get("score")) is not None:
                    out.append({**row, "_lo": Path(path).parent.name})
    return out


def group_markdown(csv_paths: list[Path], title: str, key) -> str:
    """Bảng điểm TB + retention 3 s TB + số liệu TikTok TB theo một khoá (thiếu cột → —, không lỗi)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in _rows(csv_paths):
        groups[key(r)].append(r)
    head = ["Nhóm", "Số bản", "Điểm TB", "Giữ chân 3 s", *METRIC_COLUMNS]
    lines = [f"### {title}", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]

    def avg(rows, col, ratio=False):
        vals = [(_ratio if ratio else _float)(r.get(col)) for r in rows]
        vals = [v for v in vals if v is not None]
        return None if not vals else sum(vals) / len(vals)

    for name, rows in sorted(groups.items(), key=lambda kv: -(avg(kv[1], "score") or 0)):
        ret = avg(rows, "retention_3s", ratio=True)
        cells = [name or "—", str(len(rows)), f"{avg(rows, 'score'):.2f}", "—" if ret is None else f"{ret:.0%}"]
        for col in METRIC_COLUMNS:
            v = avg(rows, col)
            cells.append("—" if v is None else f"{v:.3g}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def stats_report(csv_paths: list[Path]) -> str:
    """library/learnings-stats.md: theo kiểu hook, preset, preset × hook, nhóm độ dài, top 3 biến thể."""
    rows = _rows(csv_paths)
    top = sorted(rows, key=lambda r: -(_float(r.get("score")) or 0))[:3]
    parts = [
        "# Số liệu học từ các lô đã chấm (vf learn --write)", "",
        "Lô: " + ", ".join(sorted({r["_lo"] for r in rows})), "",
        group_markdown(csv_paths, "Theo kiểu hook", lambda r: (r.get("hook_type") or "").strip()), "",
        group_markdown(csv_paths, "Theo preset", lambda r: (r.get("preset") or "").strip()), "",
        group_markdown(csv_paths, "Theo preset × kiểu hook",
                       lambda r: f"{(r.get('preset') or '—').strip()} × {(r.get('hook_type') or '').strip()}"), "",
        group_markdown(csv_paths, "Theo độ dài", lambda r: length_bucket(r.get("length_s"))), "",
        "### Top 3 biến thể", "",
        *[f"- {r['_lo']}/{r['variant']} — {r.get('score')}đ — {r.get('preset') or '—'} · {r.get('hook_type')} · "
          f"\"{r.get('hook_text', '')}\" — {r.get('notes', '')}" for r in top],
    ]
    return "\n".join(parts) + "\n"
