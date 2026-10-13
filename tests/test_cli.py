import csv
import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vf.cli import app

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


@pytest.fixture
def project(tmp_path, sample_video, sample_video_b):
    drive = tmp_path / "EDIT"
    src = drive / "source gốc"
    src.mkdir(parents=True)
    shutil.copy(sample_video, src / "nguon_a.mp4")
    shutil.copy(sample_video_b, src / "nguon_b.mp4")
    cfg = tmp_path / "vf.toml"
    cfg.write_text(f'drive_root = "{drive.as_posix()}"\n', encoding="utf-8")
    job = tmp_path / "jobs" / "lo-mau"
    job.mkdir(parents=True)
    shutil.copy(ROOT / "templates" / "brief.yaml", job / "brief.yaml")
    shutil.copy(ROOT / "templates" / "edl.example.json", job / "edl.json")
    args = ["--config", str(cfg), "--jobs-dir", str(tmp_path / "jobs"), "--work-dir", str(tmp_path / "work")]
    return dict(drive=drive, job=job, args=args, tmp=tmp_path)


def _invoke(cmd, project, *extra):
    r = runner.invoke(app, [cmd, "lo-mau", *project["args"], *extra])
    return r


def test_analyze_then_render(project):
    r = _invoke("analyze", project, "--no-transcribe")
    assert r.exit_code == 0, r.output
    r = _invoke("render", project)
    assert r.exit_code == 0, r.output
    out = project["drive"] / "out" / "lo-mau"
    mp4s = sorted(p.name for p in out.glob("*.mp4"))
    assert mp4s == ["v1-noi-dau.mp4", "v2-cau-hoi.mp4", "v3-chi-phi.mp4"]
    assert len(list(out.glob("*_sheet.png"))) == 3
    qa = json.loads((out / "qa.json").read_text(encoding="utf-8"))
    assert {q["variant"] for q in qa} == {"v1-noi-dau", "v2-cau-hoi", "v3-chi-phi"}
    assert all(q["size_ok"] and q["duration_ok"] for q in qa)
    with open(out / "review.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert list(rows[0]) == ["variant", "hook_type", "hook_text", "score", "notes", "views", "retention_3s"]
    assert rows[0]["hook_text"] == "Cười mà phải che miệng?"


def test_render_keeps_existing_scores(project):
    _invoke("analyze", project, "--no-transcribe")
    _invoke("render", project)
    out = project["drive"] / "out" / "lo-mau" / "review.csv"
    rows = list(csv.DictReader(open(out, encoding="utf-8-sig", newline="")))
    rows[0]["score"], rows[0]["notes"] = "4", "hook ổn"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    assert _invoke("render", project).exit_code == 0
    rows = list(csv.DictReader(open(out, encoding="utf-8-sig", newline="")))
    assert (rows[0]["score"], rows[0]["notes"]) == ("4", "hook ổn")


def test_forbidden_overlay_fails_that_variant(project):
    edl_path = project["job"] / "edl.json"
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    edl["variants"][1]["overlays"][0]["text"] = "Trắng thần kỳ"
    edl_path.write_text(json.dumps(edl, ensure_ascii=False), encoding="utf-8")
    _invoke("analyze", project, "--no-transcribe")
    r = _invoke("render", project)
    assert r.exit_code != 0
    out = project["drive"] / "out" / "lo-mau"
    assert not (out / "v2-cau-hoi.mp4").exists()
    assert "thần kỳ" in r.output


def test_new_job_creates_brief(project):
    r = runner.invoke(app, ["new", "lo-02", "--jobs-dir", str(project["tmp"] / "jobs")])
    assert r.exit_code == 0, r.output
    assert (project["tmp"] / "jobs" / "lo-02" / "brief.yaml").exists()


def test_learn_prints_stats(tmp_path):
    out = tmp_path / "EDIT" / "out" / "lo-01"
    out.mkdir(parents=True)
    (out / "review.csv").write_text(
        "variant,hook_type,hook_text,score,notes,views,retention_3s\nv1,pain,x,4,,,50%\n", encoding="utf-8-sig")
    cfg = tmp_path / "vf.toml"
    cfg.write_text(f'drive_root = "{(tmp_path / "EDIT").as_posix()}"\n', encoding="utf-8")
    r = runner.invoke(app, ["learn", "--config", str(cfg)])
    assert r.exit_code == 0, r.output
    assert "| pain | 1 | 4.00 | 50% |" in r.output
    assert "lo-01" in r.output
