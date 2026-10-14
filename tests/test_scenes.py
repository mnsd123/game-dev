from vf.edl import Segment, TextOverlay
from vf.placement import _overlap, best_y, text_box
from vf.scenes import JUMP_ZOOM, PieceVideo, micro_shots, plan_piece_video

SRC = "a.mp4"
CUTS = {SRC: [10.0, 20.0, 30.0]}


def _p(start, end):
    return Segment(source=SRC, start=start, end=end)


def test_micro_shot_at_head_and_tail_held():
    pv = plan_piece_video([_p(9.8, 20.3)], CUTS)[0]
    assert pv.head == 0.2 and pv.tail == 0.3


def test_long_fragment_kept():
    assert plan_piece_video([_p(9.0, 15.0)], CUTS)[0] == PieceVideo()


def test_jump_cut_in_same_shot_alternates_zoom():
    vids = plan_piece_video([_p(11.0, 13.0), _p(14.0, 16.0), _p(17.0, 19.0)], CUTS)
    assert [v.zoom for v in vids] == [1.0, JUMP_ZOOM, 1.0]


def test_contiguous_or_new_shot_not_zoomed():
    vids = plan_piece_video([_p(11.0, 13.0), _p(13.0, 15.0), _p(21.0, 25.0)], CUTS)
    assert [v.zoom for v in vids] == [1.0, 1.0, 1.0]


def test_micro_shots_notes():
    assert len(micro_shots([_p(9.8, 15.0)], CUTS)) == 1


def test_text_box_wraps_long_text():
    short = text_box(TextOverlay(text="15 phút", start=0, end=1, style="label"))
    long_ = text_box(TextOverlay(text="Quà 20/10 cho bạn gái tặng gì cho đúng gu?", start=0, end=1, style="hook"))
    assert long_[1] > short[1]


def test_best_y_avoids_face():
    face_top = ([(0.2, 0.0, 0.8, 0.45)], None)
    y = best_y([face_top], 0.6, 0.08, 0.10, [])  # nửa dưới chỉ rộng ~0.61 (cột nút phải 300 px)
    assert y >= 0.45 and _overlap((0.1, y, 0.9, y + 0.08), face_top[0][0]) == 0


def test_strip_text_on_sources_with_burned_in_text():
    from vf.edl import Graphic, Variant
    from vf.motion import strip_text

    v = Variant(
        id="x", hook_type="pain", rationale="",
        hook=Segment(source="text.mp4", start=0, end=2),
        segments=[Segment(source=SRC, start=0, end=3)],
        overlays=[TextOverlay(text="hook", start=0, end=1.5), TextOverlay(text="cta", start=3, end=4.5)],
        graphics=[Graphic(kind="light", label="Đèn xanh", start=1, end=2.5),
                  Graphic(kind="whiten", label="", start=3, end=4)],
    )
    out = strip_text(v, {"text.mp4"})
    assert [o.text for o in out.overlays] == ["cta"]
    assert out.graphics[0].label == "" and len(out.graphics) == 2
    assert strip_text(v, set()) == v


def test_jump_zoom_keeps_square_pixels(sample_video, tmp_path):
    """Phóng to khi cắt nhảy không được đổi SAR, không thì concat lỗi (lo-02 v1)."""
    from vf.edl import Variant
    from vf.ffutil import run
    from vf.probe import probe
    from vf.render import build_ffmpeg_cmd

    v = Variant(id="z", hook_type="pain", rationale="", hook=Segment(source=SRC, start=0.0, end=0.8),
                segments=[Segment(source=SRC, start=1.2, end=2.0)])
    out = tmp_path / "o.mp4"
    cmd = build_ffmpeg_cmd({SRC: sample_video}, {SRC: probe(sample_video)}, v, None, tmp_path, out,
                           gains={SRC: 0.0}, videos=[PieceVideo(), PieceVideo(zoom=JUMP_ZOOM)])
    run(cmd)
    assert out.exists() and probe(out).width == 1080


def test_strip_text_keeps_overlays_inside_text_free_window():
    from vf.edl import Variant
    from vf.motion import strip_text

    v = Variant(id="x", hook_type="pain", rationale="",
                hook=Segment(source="t.mp4", start=10.0, end=12.0), segments=[Segment(source="t.mp4", start=20.0, end=24.0)],
                overlays=[TextOverlay(text="ok", start=2.5, end=3.5), TextOverlay(text="chặn", start=0.2, end=1.0)])
    out = strip_text(v, {"t.mp4"}, {"t.mp4": [(20.0, 22.0)]})
    assert [o.text for o in out.overlays] == ["ok"]


def test_zoom_focus_follows_keyframes():
    from vf.edl import Effect
    from vf.render import _focus_expr

    e = Effect(kind="zoom_to", at=2.0, duration=1.0, keyframes=[(0, 0.6, 0.55), (1.0, 0.4, 0.5)])
    ex = _focus_expr(e, 1)
    assert ex.startswith("if(lt(t,2.000),0.600") and "0.400" in ex
    assert _focus_expr(Effect(kind="zoom_to", at=0, focus=(0.3, 0.7)), 2) == "0.700"
