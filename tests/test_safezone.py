from vf.creative import auto_sfx, lint_batch, lint_variant
from vf.edl import Effect, Graphic, Segment, TextOverlay, Variant
from vf.placement import BOTTOM_MAX, TOP_MIN, fit_callout, place, safe_text_w_px, text_box
from vf.safezone import SAFE

SRC = "a.mp4"


def _v(**kw):
    base = dict(id="x", hook_type="pain", rationale="", hook=Segment(source=SRC, start=0, end=2),
                segments=[Segment(source=SRC, start=2, end=30)])
    return Variant(**{**base, **kw})


def test_safe_zone_numbers():
    assert round(SAFE.y0, 3) == 0.125 and round(SAFE.y1, 3) == 0.656
    assert SAFE.rail_w == 300 and round(SAFE.center_x(0.5, 0.6), 3) == 0.417  # nửa dưới: lệch trái
    # dưới hàng cột nút, hộp căn giữa hẹp hơn
    assert SAFE.max_centered_w(0.5, 0.6) < SAFE.max_centered_w(0.2, 0.3)
    assert SAFE.violations((0.2, 0.2, 0.8, 0.3)) == []
    assert "dưới" in SAFE.violations((0.2, 0.6, 0.8, 0.7))
    assert "phải (cột nút)" in SAFE.violations((0.1, 0.5, 0.9, 0.6))


def test_place_keeps_everything_inside_safe_zone():
    long_text = "Niềng răng xong việc đầu tiên cần làm là gì vậy mọi người ơi"
    overlays = [
        TextOverlay(text=long_text, start=0, end=2, position="bottom", style="hook"),
        TextOverlay(text="Bấm giỏ hàng", start=3, end=5, position="bottom", style="cta"),
        TextOverlay(text="Sát đáy", start=6, end=7, y=0.9, style="label"),  # y ghi tay ngoài vùng an toàn
        TextOverlay(text="RĂNG Ố VÀNG", sub="thấy rõ luôn", start=8, end=9, position="bottom", style="lower"),
    ]
    graphics = [Graphic(kind="teeth", start=10, end=12, y=0.8), Graphic(kind="shade", start=13, end=15)]
    ovs, gs, notes = place([], [], {}, overlays, graphics, faces=False)
    for o in ovs:
        w, h = text_box(o, o.max_w)
        box = (o.xc - w / 2, o.y, o.xc + w / 2, o.y + h)
        assert SAFE.violations(box) == [], (o.text, box)
        assert o.max_w <= safe_text_w_px(o.y, o.y + h) + 1
    for g in gs:
        assert TOP_MIN - 1e-6 <= g.y
    assert any("Sát đáy" in n for n in notes) and any("teeth" in n for n in notes)


def test_callout_pulled_inside():
    g = fit_callout(Graphic(kind="callout", start=0, end=1, cx=0.95, cy=0.9, rx=0.3, ry=0.1))
    assert SAFE.violations((g.cx - g.rx, g.cy - g.ry, g.cx + g.rx, g.cy + g.ry)) == []
    assert g.cy + g.ry <= BOTTOM_MAX + 1e-6


def test_auto_sfx_uses_existing_files_only(tmp_path):
    sfx = tmp_path / "sfx"
    sfx.mkdir()
    (sfx / "whoosh.wav").write_bytes(b"")
    v = _v(effects=[Effect(kind="zoom_to", at=3.0), Effect(kind="sfx", at=7.0, asset="x.wav"),
                    Effect(kind="zoom_punch", at=7.05)],
           graphics=[Graphic(kind="callout", start=3, end=4)])
    out = auto_sfx(v, sfx)
    assert [(e.at, e.asset) for e in out] == [(3.0, "sfx/whoosh.wav")]  # không có marker.wav; 7.05 trùng sfx tay
    assert auto_sfx(v.model_copy(update={"sfx_auto": False}), sfx) == []


def test_lint_flags_late_cta_missing_hook_text_and_silence():
    v = _v(overlays=[TextOverlay(text="Bấm giỏ hàng", start=29, end=31, style="cta")])
    notes = " | ".join(lint_variant(v))
    assert "hook" in notes and "CTA" in notes and "âm thanh" in notes and "chapter" in notes


def test_lint_clean_variant_with_all_chapters():
    chapters = ["pain", "benefit", "result", "proof", "speed", "saving", "cta"]
    segs = [Segment(source=SRC, start=2 + 7 * i, end=9 + 7 * i, chapter=c) for i, c in enumerate(chapters)]
    total = 2 + 7 * len(chapters)  # 51 s
    overlays = [TextOverlay(text="Răng vàng?", start=0.2, end=2.0)]
    overlays += [TextOverlay(text=f"ý {i}", start=t, end=t + 1.5, position="top") for i, t in enumerate(range(4, total - 4, 3))]
    overlays += [TextOverlay(text="Bấm giỏ hàng", start=0.7 * total, end=0.7 * total + 1.5, style="cta"),
                 TextOverlay(text="Bấm giỏ hàng", start=total - 2.5, end=total, style="cta")]
    v = _v(music="m.mp3", segments=segs, overlays=overlays)
    assert lint_variant(v) == []


def test_lint_v2_rules_protect_scene_and_missing_chapters():
    v = _v(music="m.mp3", segments=[Segment(source=SRC, start=2, end=3, chapter="proof", protect=True),
                                    Segment(source=SRC, start=3, end=50, chapter="cta")],
           overlays=[TextOverlay(text="Trước", start=2.1, end=3.5, position="center")])
    notes = " | ".join(lint_variant(v))
    assert "protect" in notes and "ngắn hơn 1.2" in notes and "chữ giữa khung đè cảnh protect" in notes
    assert "còn thiếu nỗi đau" in notes


def test_auto_fix_extends_short_text():
    from vf.creative import auto_fix

    v = _v(overlays=[TextOverlay(text="mảng bám ngả vàng thấy rõ luôn", start=1, end=1.5)])
    fixed, notes = auto_fix(v)
    assert fixed.overlays[0].end == 1 + 0.6 + 0.25 * 7 and notes  # 7 từ


def test_whip_and_paper_transitions():
    from vf.creative import chapter_cuts, transition_graphics

    v = _v(preset="vox", segments=[Segment(source=SRC, start=2, end=6, chapter="pain"),
                                   Segment(source=SRC, start=6, end=9),
                                   Segment(source=SRC, start=9, end=12, chapter="proof")])
    assert chapter_cuts(v) == [2.0, 9.0]  # hook→pain, pain→proof (đoạn không ghi chương = chương trước)
    assert [g.kind for g in transition_graphics(v)] == ["paper_swipe", "paper_swipe"]
    assert transition_graphics(v.model_copy(update={"preset": "pink"})) == []


def test_preset_aliases_and_ugc_has_no_auto_sfx(tmp_path):
    (tmp_path / "pop.wav").write_bytes(b"")
    v = _v(preset="beat", overlays=[TextOverlay(text="x", start=0, end=2)])
    assert v.preset == "kinetic" and auto_sfx(v, tmp_path)
    assert auto_sfx(v.model_copy(update={"preset": "ugc"}), tmp_path) == []


def test_lint_batch_duplicate_hooks():
    a, b = _v(id="a"), _v(id="b")
    c = _v(id="c", hook=Segment(source=SRC, start=10, end=12))
    assert lint_batch([a, b, c]) == {"b": ["hook trùng với a — đổi câu/khung hình mở đầu"]}
