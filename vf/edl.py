"""Kịch bản dựng (edl.json): mỗi biến thể là hook + danh sách đoạn, mỗi đoạn tự khai nguồn."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, model_validator

from vf.probe import MediaInfo

HOOK_MAX_S = 3.0
DURATION_TOLERANCE_S = 0.05


Chapter = Literal["hook", "pain", "benefit", "result", "proof", "speed", "saving", "cta",
                  "problem", "solution"]  # problem ≈ pain, solution ≈ benefit (tên chương của skill v2)


class Segment(BaseModel):
    source: str  # tên file trong sources_dir
    start: float  # theo timeline của chính nguồn đó
    end: float
    chapter: Chapter | None = None  # nội dung đoạn — lint nhắc chương còn thiếu (tokens.content_checklist)
    protect: bool = False  # cảnh "tiền" (trước/sau, bật đèn, mở hộp): ≥ 2,5 s, không đặt chữ giữa khung đè miệng/răng
    rapid: bool = False  # chuỗi cắt nhanh có chủ đích: bỏ qua luật cảnh ≥ 1,2 s

    @property
    def duration(self) -> float:
        return self.end - self.start


Animation = Literal["pop", "word_by_word", "highlight", "slide", "none"]


class TextOverlay(BaseModel):
    text: str
    start: float  # theo timeline output
    end: float
    position: Literal["top", "center", "bottom"] = "top"
    style: Literal["hook", "commit", "label", "cta", "plain", "lower", "tag", "vox"] = "hook"
    animation: Animation = "pop"
    emphasis: list[str] = []  # từ được tô vệt highlight; rỗng + animation=highlight → tô cả câu
    y: float | None = None  # mép trên (0–1 chiều cao khung); None = theo position. Render tự chọn chỗ không che mặt
    sub: str = ""  # style lower: dòng phụ chữ thường dưới dòng chính (style guide mục 4)
    max_w: int | None = None  # bề rộng hộp tối đa (px) — render tự điền theo vùng an toàn, không ghi tay
    xc: float | None = None  # tâm ngang hộp (0–1) — render tự điền (lệch trái ở hàng cột nút), không ghi tay


class Still(BaseModel):
    """Khung hình tĩnh cắt từ nguồn để dán vào ảnh ghép (collage)."""
    source: str
    t: float  # giờ nguồn
    crop: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)  # x0, y0, x1, y1 (tỉ lệ khung nguồn)
    label: str = ""


class TimerRow(BaseModel):
    min: int
    title: str
    sub: str = ""
    color: Literal["blue", "red"] = "blue"
    at: float = 0.0


class Graphic(BaseModel):
    """Hiệu ứng minh hoạ vẽ bằng Remotion.
    light: vầng sáng màu + đồng hồ đếm phút (đèn xanh/đỏ). whiten: icon răng vàng → trắng, ghi "Hình minh họa".
    counter: thẻ toàn màn hình đếm "NGÀY 1 → 7" (label = dòng phụ).
    callout (Vox): khoanh tròn vẽ tay quanh (cx, cy, rx, ry) → mũi tên → nhãn bút dạ vàng `label`.
    collage (Vox): nền giấy toàn màn hình, dán các `stills` (ảnh cắt từ nguồn) nghiêng, nhãn bút dạ vàng.
    teeth: hàm răng vector — đèn xanh quét làm răng vàng → trắng, rồi đèn đỏ làm dịu nướu (ghi "Minh họa").
    shade: thang màu răng, con trỏ trượt từ `from_shade` → `to_shade` (chỉ dùng số người nói nói ra; label = nguồn,
      ví dụ "theo trải nghiệm của Giao").
    wipe: thanh gạt trước/sau toàn màn hình — 2 `stills` (trước, sau) cắt từ nguồn, vạch dọc quét lộ ảnh "sau".
    Mọi graphic tự nằm trong vùng an toàn TikTok (vf/safezone.py)."""
    kind: Literal["light", "whiten", "teeth", "counter", "callout", "collage", "shade", "wipe",
                  "light_timer", "kinetic", "end_card", "paper_swipe"]
    start: float  # theo timeline output
    end: float
    color: Literal["blue", "red"] = "blue"
    label: str = ""
    y: float | None = None  # mép trên thẻ; None = render tự chọn
    xc: float | None = None  # tâm ngang thẻ (0–1) — render tự điền theo vùng an toàn
    split: float = 0.56  # teeth: tỉ lệ thời lượng pha đèn xanh (phần còn lại là đèn đỏ)
    cx: float = 0.5  # callout: tâm vòng khoanh (tỉ lệ khung output, sau zoom)
    cy: float = 0.5
    rx: float = 0.25
    ry: float = 0.08
    stills: list[Still] = []
    from_shade: int = 10  # shade: mức trên thang màu lúc đầu (số lớn = vàng hơn)
    to_shade: int = 5  # shade: mức lúc sau
    rows: list[TimerRow] = []  # light_timer: 2 hàng (10′ xanh, 5′ đỏ); `at` = giây tính từ đầu thẻ
    words: list[str] = []  # kinetic: từng cụm chữ đập lên (cụm *như này* tô màu nhấn)
    sub: str = ""  # end_card: dòng phụ
    live: bool = False  # end_card: huy hiệu LIVE


class Effect(BaseModel):
    kind: Literal["zoom_punch", "shake", "flash", "sfx", "highlight", "zoom_to"]
    at: float  # theo timeline output
    duration: float = 0.3
    asset: str | None = None
    focus: tuple[float, float] = (0.5, 0.5)  # zoom_to: điểm phóng tới (tỉ lệ khung)
    zoom: float = 1.6  # zoom_to: độ phóng khi giữ
    track: Literal["teeth"] | None = None  # zoom_to: ống kính bám theo răng (render tự dò, vf/track.py)
    keyframes: list[tuple[float, float, float]] = []  # zoom_to: (giây từ `at`, cx, cy) — render điền khi có track


Preset = Literal["pink", "vox", "kinetic", "proof", "ugc", "gift", "routine", "reply"]  # tokens.json presets
PRESET_ALIASES = {"result_rewind": "proof", "beat": "kinetic"}  # tên preset cũ (v1.4)


class Variant(BaseModel):
    id: str
    hook_type: str
    preset: Preset | None = None  # một phong cách dựng cho cả biến thể, không trộn
    cutdown_of: str | None = None  # bản cắt ngắn của biến thể này (thời lượng theo brief.cutdown_seconds)
    hook: Segment
    segments: list[Segment]
    overlays: list[TextOverlay] = []
    graphics: list[Graphic] = []
    effects: list[Effect] = []
    captions: bool = False  # mặc định KHÔNG phụ đề toàn bộ lời; chỉ chữ động ở đoạn quan trọng
    music: str | None = None
    sfx_auto: bool = True  # tự gắn SFX từ library/brand/sfx/ theo hiệu ứng (vf/creative.py)
    rationale: str

    @model_validator(mode="before")
    @classmethod
    def _alias_preset(cls, data):
        if isinstance(data, dict) and data.get("preset") in PRESET_ALIASES:
            data = {**data, "preset": PRESET_ALIASES[data["preset"]]}
        return data

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
        for i, g in enumerate(self.graphics):
            if g.start < 0 or g.start >= g.end:
                raise ValueError(f"biến thể '{self.id}', graphics[{i}]: start phải < end")
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
