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
    y = best_y([face_top], 0.8, 0.08, 0.10, [])
    assert y >= 0.45 and _overlap((0.1, y, 0.9, y + 0.08), face_top[0][0]) == 0
