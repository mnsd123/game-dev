from pathlib import Path

import pytest

from vf.captions import remap_words, words_to_ass
from vf.edl import Segment
from vf.transcribe import Word

STYLE = Path(__file__).resolve().parents[1] / "templates" / "caption_style.ass"


def test_remap_across_two_sources():
    words = {"A": [Word("răng", 1.0, 1.2)], "B": [Word("trắng", 0.5, 0.7)]}
    pieces = [Segment(source="A", start=0.9, end=1.5), Segment(source="B", start=0.4, end=0.9)]
    out = remap_words(words, pieces)
    assert [(w.text, w.start, w.end) for w in out] == [("răng", 0.1, 0.3), ("trắng", 0.7, 0.9)]


def test_remap_drops_words_cut_at_edge():
    words = {"A": [Word("cắt", 0.8, 1.0), Word("giữ", 1.1, 1.3), Word("cắt2", 1.4, 1.6)]}
    out = remap_words(words, [Segment(source="A", start=0.9, end=1.5)])
    assert [w.text for w in out] == ["giữ"]


def test_remap_same_source_used_twice():
    words = {"A": [Word("một", 0.1, 0.2), Word("hai", 2.1, 2.2)]}
    pieces = [Segment(source="A", start=2.0, end=2.5), Segment(source="A", start=0.0, end=0.5)]
    out = remap_words(words, pieces)
    assert [(w.text, w.start) for w in out] == [("hai", 0.1), ("một", 0.6)]


def test_ass_keeps_vietnamese_diacritics():
    ass = words_to_ass([Word("Răng", 0.0, 0.3), Word("trắng", 0.3, 0.6), Word("sáng", 0.6, 1.0)], STYLE)
    dialogue = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
    assert len(dialogue) == 1
    plain = dialogue[0].split(",", 9)[9]
    import re
    assert re.sub(r"\{[^}]*\}", "", plain) == "Răng trắng sáng"
    assert "\\k" in plain


def test_ass_groups_max_words():
    words = [Word(f"w{i}", i * 0.2, i * 0.2 + 0.2) for i in range(9)]
    ass = words_to_ass(words, STYLE, max_words=4)
    assert sum(l.startswith("Dialogue:") for l in ass.splitlines()) == 3


def test_ass_empty_is_valid():
    ass = words_to_ass([], STYLE)
    assert "[Script Info]" in ass and "[Events]" in ass and "Format:" in ass
    assert "Dialogue:" not in ass
