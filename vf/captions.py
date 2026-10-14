"""Phụ đề: ánh xạ từ về timeline output rồi xuất ASS karaoke."""
from __future__ import annotations

from pathlib import Path

from vf.edl import Segment
from vf.transcribe import Word

EPS = 1e-6
MAX_GAP_S = 0.6  # khoảng nghỉ dài hơn mức này thì sang dòng mới


def remap_words(words_by_source: dict[str, list[Word]], pieces: list[Segment]) -> list[Word]:
    """Giữ từ nằm trọn trong đoạn của đúng nguồn, dịch sang timeline output; từ bị cắt ngang mép thì bỏ."""
    out: list[Word] = []
    offset = 0.0
    for seg in pieces:
        for w in words_by_source.get(seg.source, []):
            if w.start >= seg.start - EPS and w.end <= seg.end + EPS:
                shift = offset - seg.start
                out.append(Word(w.text, round(w.start + shift, 3), round(w.end + shift, 3)))
        offset += seg.end - seg.start
    return out


def _ts(t: float) -> str:
    cs = max(0, int(round(t * 100)))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _clean(text: str) -> str:
    return text.replace("{", "").replace("}", "").replace("\\", "").replace("\n", " ").strip()


def _group(words: list[Word], max_words: int) -> list[list[Word]]:
    lines: list[list[Word]] = []
    for w in words:
        if lines and len(lines[-1]) < max_words and w.start - lines[-1][-1].end <= MAX_GAP_S:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def words_to_ass(words: list[Word], style_path: Path, max_words: int = 4) -> str:
    """3–4 từ/dòng; từ đang nói đổi màu bằng \\k (Secondary → Primary)."""
    header = Path(style_path).read_text(encoding="utf-8").rstrip("\n")
    events = []
    for line in _group(words, max_words):
        parts = []
        cursor = line[0].start
        for w in line:
            # thời lượng \k tính cả khoảng nghỉ trước từ để màu chạy đúng nhịp
            k = max(1, int(round((w.end - cursor) * 100)))
            parts.append(f"{{\\k{k}}}{_clean(w.text)}")
            cursor = w.end
        text = " ".join(parts)
        events.append(f"Dialogue: 0,{_ts(line[0].start)},{_ts(line[-1].end)},Caption,,0,0,0,,{text}")
    return header + "\n" + "\n".join(events) + ("\n" if events else "")
