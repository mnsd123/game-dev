import json
import shutil

import pytest
from typer.testing import CliRunner

from vf.cli import app
from vf.style import ShotStats, reference_frames, shot_stats


def test_shot_stats_three_colors(sample_video):
    s = shot_stats(sample_video)
    assert isinstance(s, ShotStats)
    assert s.n_cuts == 2
    assert s.cuts == pytest.approx([1.7, 3.4], abs=0.05)
    assert s.avg_shot_s == pytest.approx(5.0 / 3, abs=0.05)


def test_reference_frames_count(sample_video, tmp_path):
    frames = reference_frames(sample_video, tmp_path / "frames", every_s=1.0)
    assert abs(len(frames) - 5) <= 1
    assert all(f.exists() for f in frames)


def test_vf_style_writes_work_files(sample_video, sample_video_b, tmp_path):
    ref = tmp_path / "EDIT" / "video tham khảo"
    ref.mkdir(parents=True)
    shutil.copy(sample_video, ref / "snaptik_1.mp4")
    shutil.copy(sample_video_b, ref / "snaptik_2.mp4")
    cfg = tmp_path / "vf.toml"
    cfg.write_text(f'drive_root = "{(tmp_path / "EDIT").as_posix()}"\n', encoding="utf-8")
    work = tmp_path / "work"
    r = CliRunner().invoke(app, ["style", "--config", str(cfg), "--work-dir", str(work), "--no-transcribe"])
    assert r.exit_code == 0, r.output
    for name in ("snaptik_1", "snaptik_2"):
        d = work / "style" / name
        stats = json.loads((d / "stats.json").read_text(encoding="utf-8"))
        assert {"duration", "n_cuts", "avg_shot_s", "cuts"} <= set(stats)
        assert list((d / "frames").glob("*.jpg"))
        assert (d / "transcript.json").exists()
    assert json.loads((work / "style" / "snaptik_1" / "stats.json").read_text())["n_cuts"] == 2
