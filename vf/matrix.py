"""Sinh biến thể số lượng cho GMV Max: hooks × bodies × ctas × presets (khối `matrix` trong edl.json).

Mỗi phần (hook/body/cta) khai thời gian chữ/đồ hoạ/hiệu ứng tính từ đầu phần đó (0 = đầu phần);
khi ghép, thời gian được dời theo vị trí phần trong video. Không ghi đè biến thể đã có cùng id."""
from __future__ import annotations

import json
from pathlib import Path

from vf.edl import Variant


def _dur(segs: list[dict]) -> float:
    return sum(s["end"] - s["start"] for s in segs)


def _shift(items: list[dict], dt: float, keys: tuple[str, ...]) -> list[dict]:
    out = []
    for it in items:
        it = dict(it)
        for k in keys:
            if k in it and it[k] is not None:
                it[k] = round(it[k] + dt, 3)
        out.append(it)
    return out


def expand(edl: dict) -> list[dict]:
    """Biến thể mới (dict theo schema Variant) từ edl["matrix"]."""
    m = edl.get("matrix") or {}
    presets = m.get("presets") or ["ugc"]
    out = []
    for h in m.get("hooks", []):
        for b in m.get("bodies", []):
            for c in m.get("ctas", []):
                for pr in presets:
                    parts = [([h["hook"]], h), (b.get("segments", []), b), (c.get("segments", []), c)]
                    overlays, graphics, effects, t = [], [], [], 0.0
                    for segs, part in parts:
                        overlays += _shift(part.get("overlays", []), t, ("start", "end"))
                        graphics += _shift(part.get("graphics", []), t, ("start", "end"))
                        effects += _shift(part.get("effects", []), t, ("at",))
                        t += _dur(segs)
                    v = {
                        "id": f"{edl['job']}_{h['id']}_{b['id']}_{c['id']}_{pr}",
                        "hook_type": h.get("hook_type", "pain"),
                        "preset": pr,
                        "hook": h["hook"],
                        "segments": b.get("segments", []) + c.get("segments", []),
                        "overlays": overlays, "graphics": graphics, "effects": effects,
                        "rationale": f"ma trận GMV Max: hook {h['id']} × thân {b['id']} × CTA {c['id']} × {pr}",
                    }
                    Variant(**v)  # kiểm schema ngay (hook ≤ 3 s, thời gian hợp lệ)
                    out.append(v)
    return out


def expand_file(path: Path) -> list[str]:
    """Thêm biến thể ma trận vào edl.json; trả về id đã thêm."""
    path = Path(path)
    edl = json.loads(path.read_text(encoding="utf-8"))
    have = {v["id"] for v in edl.get("variants", [])}
    new = [v for v in expand(edl) if v["id"] not in have]
    edl.setdefault("variants", []).extend(new)
    path.write_text(json.dumps(edl, ensure_ascii=False, indent=1), encoding="utf-8")
    return [v["id"] for v in new]

