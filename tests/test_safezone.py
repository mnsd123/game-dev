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
        box = ((1 - w) / 2, o.y, (1 + w) / 2, o.y + h)
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
    assert "hook" in notes and "CTA" in notes and "âm thanh" in notes
    good = _v(music="m.mp3", overlays=[TextOverlay(text="Răng vàng?", start=0.2, end=2),
                                         TextOverlay(text="Bấm giỏ hàng", start=22, end=24, style="cta")])
    assert lint_variant(good) == []


def test_lint_batch_duplicate_hooks():
    a, b = _v(id="a"), _v(id="b")
    c = _v(id="c", hook=Segment(source=SRC, start=10, end=12))
    assert lint_batch([a, b, c]) == {"b": ["hook trùng với a — đổi câu/khung hình mở đầu"]}
