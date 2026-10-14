from pathlib import Path

import pytest

from vf.learn import HookStat, stats_markdown, summarize_reviews

HEAD = "variant,hook_type,hook_text,score,notes,views,retention_3s\n"


def _csv(tmp_path: Path, name: str, body: str, head: str = HEAD) -> Path:
    p = tmp_path / name
    p.write_text(head + body, encoding="utf-8-sig")
    return p


def test_two_csvs_averaged(tmp_path):
    a = _csv(tmp_path, "a.csv", "v1,pain,x,4,,1000,40%\nv2,question,y,2,,500,0.2\n")
    b = _csv(tmp_path, "b.csv", "v1,pain,z,5,,800,60%\nv2,cost_compare,w,3,,,\n")
    stats = {s.hook_type: s for s in summarize_reviews([a, b])}
    assert stats["pain"] == HookStat("pain", 2, 4.5, pytest.approx(0.5))
    assert stats["question"].avg_retention == pytest.approx(0.2)
    assert stats["cost_compare"].n == 1 and stats["cost_compare"].avg_retention is None


def test_sorted_by_score(tmp_path):
    a = _csv(tmp_path, "a.csv", "v1,pain,x,2,,,\nv2,question,y,5,,,\n")
    assert [s.hook_type for s in summarize_reviews([a])] == ["question", "pain"]


def test_unscored_rows_ignored(tmp_path):
    a = _csv(tmp_path, "a.csv", "v1,pain,x,,,,\nv2,pain,y,3,,,\n")
    (s,) = summarize_reviews([a])
    assert (s.n, s.avg_score) == (1, 3.0)


def test_missing_views_column_no_crash(tmp_path):
    a = _csv(tmp_path, "a.csv", "v1,pain,x,4,ok\n", head="variant,hook_type,hook_text,score,notes\n")
    (s,) = summarize_reviews([a])
    assert s.avg_retention is None and s.avg_score == 4.0


def test_markdown_table(tmp_path):
    a = _csv(tmp_path, "a.csv", "v1,pain,x,4,,,50%\n")
    md = stats_markdown(summarize_reviews([a]))
    assert "| pain | 1 | 4.00 | 50% |" in md
