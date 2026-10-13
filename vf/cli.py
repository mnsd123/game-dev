"""CLI điều phối: vf new | analyze | render."""
from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict
from pathlib import Path

import typer

from vf.analyze import analyze_all, list_videos, load_words, source_work_dir
from vf.brief import load_brief, read_phrase_list
from vf.config import load_config
from vf.learn import stats_markdown, summarize_reviews
from vf.edl import Variant, load_edl, output_duration
from vf.paths import BRAND_DIR, BRIEF_TEMPLATE, CAPTION_STYLE, FORBIDDEN_PATH, PENDING_PATH
from vf.probe import MediaInfo
from vf.qa import ClaimViolation, check_output, contact_sheet
from vf.render import render_variant
from vf.style import reference_frames, shot_stats
from vf.transcribe import transcribe

app = typer.Typer(help="Video factory cho Smilee: phân tích nguồn, dựng biến thể, QA.", no_args_is_help=True)

REVIEW_COLUMNS = ["variant", "hook_type", "hook_text", "score", "notes", "views", "retention_3s"]
USER_COLUMNS = ["score", "notes", "views", "retention_3s"]

ConfigOpt = typer.Option(Path("vf.toml"), "--config", help="File cấu hình (drive_root)")
JobsOpt = typer.Option(Path("jobs"), "--jobs-dir", help="Thư mục chứa jobs/<lô>/")
WorkOpt = typer.Option(Path("work"), "--work-dir", help="Thư mục file tạm (không nằm trong Drive)")


@app.command()
def new(lo: str, jobs_dir: Path = JobsOpt) -> None:
    """Tạo jobs/<lô>/brief.yaml từ mẫu để người dùng điền."""
    dst = jobs_dir / lo / "brief.yaml"
    if dst.exists():
        typer.echo(f"Đã có {dst}, không ghi đè.")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(BRIEF_TEMPLATE, dst)
    typer.echo(f"Đã tạo {dst}. Hãy điền brief rồi chạy: vf analyze {lo}")


@app.command()
def analyze(
    lo: str,
    config: Path = ConfigOpt,
    jobs_dir: Path = JobsOpt,
    work_dir: Path = WorkOpt,
    no_transcribe: bool = typer.Option(False, "--no-transcribe", help="Bỏ phiên âm (nguồn chỉ có hình)"),
) -> None:
    """Chuẩn hoá, phiên âm, tìm khoảng lặng cho mọi file trong 'source gốc'."""
    cfg = load_config(config)
    if not cfg.sources_dir.is_dir():
        raise typer.BadParameter(f"Không thấy thư mục nguồn: {cfg.sources_dir}")
    kwargs = {"transcriber": None} if no_transcribe else {}
    infos = analyze_all(cfg.sources_dir, work_dir, **kwargs)
    (jobs_dir / lo).mkdir(parents=True, exist_ok=True)
    for name, info in infos.items():
        typer.echo(f"{name}: {info.duration:.1f} s, {info.width}x{info.height}, "
                   f"{'có tiếng' if info.has_audio else 'KHÔNG có tiếng'}")
    typer.echo(f"Xong. Transcript: {work_dir}/<tên nguồn>/transcript.json")


def _load_infos(sources_dir: Path, work_dir: Path) -> tuple[dict[str, Path], dict[str, MediaInfo]]:
    sources, infos = {}, {}
    for src in sorted(p for p in sources_dir.iterdir() if p.is_file()):
        d = source_work_dir(work_dir, src.name)
        if (d / "info.json").exists() and (d / "normalized.mp4").exists():
            sources[src.name] = d / "normalized.mp4"
            infos[src.name] = MediaInfo(**json.loads((d / "info.json").read_text(encoding="utf-8")))
    return sources, infos


def _hook_text(v: Variant, words_by_source) -> str:
    hook_end = v.hook.duration
    texts = [o.text for o in v.overlays if o.start < hook_end]
    if texts:
        return texts[0]
    words = words_by_source.get(v.hook.source, [])
    return " ".join(w.text for w in words if v.hook.start <= w.start and w.end <= v.hook.end)


def _write_review(path: Path, rows: list[dict]) -> None:
    old = {}
    if path.exists():
        with open(path, encoding="utf-8-sig", newline="") as f:
            old = {r["variant"]: r for r in csv.DictReader(f)}
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        w.writeheader()
        for row in rows:
            prev = old.get(row["variant"], {})
            w.writerow({**row, **{c: prev.get(c, "") for c in USER_COLUMNS}})


@app.command()
def render(
    lo: str,
    config: Path = ConfigOpt,
    jobs_dir: Path = JobsOpt,
    work_dir: Path = WorkOpt,
    only: list[str] = typer.Option([], "--only", help="Chỉ render các biến thể này (id)"),
) -> None:
    """Đọc jobs/<lô>/edl.json, render từng biến thể vào <drive>/out/<lô>/, QA và ghi review.csv."""
    cfg = load_config(config)
    job = jobs_dir / lo
    brief_path = job / "brief.yaml"
    if brief_path.exists():
        brief = load_brief(brief_path, FORBIDDEN_PATH, PENDING_PATH)
        forbidden, target = brief.forbidden, brief.target_seconds
    else:
        forbidden, target = read_phrase_list(FORBIDDEN_PATH) + read_phrase_list(PENDING_PATH), None
    sources, infos = _load_infos(cfg.sources_dir, work_dir)
    if not infos:
        raise typer.BadParameter(f"Chưa có kết quả phân tích trong {work_dir}. Chạy: vf analyze {lo}")
    edl = load_edl(job / "edl.json", infos)
    words = {name: load_words(work_dir, name) for name in infos}
    out_dir = cfg.out_dir / lo
    out_dir.mkdir(parents=True, exist_ok=True)

    qa_path = out_dir / "qa.json"
    qa_by_id = {q["variant"]: q for q in json.loads(qa_path.read_text(encoding="utf-8"))} if qa_path.exists() else {}
    failures: list[str] = []
    rows = []
    for v in edl.variants:
        rows.append({"variant": v.id, "hook_type": v.hook_type, "hook_text": _hook_text(v, words)})
        if only and v.id not in only:
            continue
        out = out_dir / f"{v.id}.mp4"
        try:
            render_variant(sources, infos, v, out, words_by_source=words, brand=BRAND_DIR,
                           style_path=CAPTION_STYLE, work_dir=work_dir / "_render" / lo, forbidden=forbidden)
        except ClaimViolation as e:
            out.unlink(missing_ok=True)
            failures.append(str(e))
            typer.echo(f"CHẶN {v.id}: {e}", err=True)
            qa_by_id.pop(v.id, None)
            continue
        except Exception as e:  # lỗi ffmpeg của một biến thể không chặn các biến thể khác
            failures.append(f"{v.id}: {e}")
            typer.echo(f"LỖI {v.id}: {e}", err=True)
            qa_by_id.pop(v.id, None)
            continue
        report = check_output(out, output_duration(v))
        if target and abs(output_duration(v) - target) > 0.1 * target:
            report.notes.append(f"Tổng {output_duration(v):.1f} s lệch quá 10% so với brief ({target} s)")
        contact_sheet(out, out_dir / f"{v.id}_sheet.png")
        qa_by_id[v.id] = {"variant": v.id, **report.to_dict()}
        status = "OK" if report.duration_ok and report.size_ok and report.loudness_ok else "CẦN XEM"
        typer.echo(f"{status} {v.id} ({v.hook_type}, {output_duration(v):.1f} s): {v.rationale}")
        for n in report.notes:
            typer.echo(f"   - {n}")

    qa_path.write_text(json.dumps(list(qa_by_id.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    _write_review(out_dir / "review.csv", rows)
    typer.echo(f"Output: {out_dir}")
    if failures:
        raise typer.Exit(code=1)


@app.command()
def learn(config: Path = ConfigOpt) -> None:
    """Tổng hợp mọi <drive>/out/*/review.csv theo kiểu hook (đầu vào cho skill video-learnings)."""
    cfg = load_config(config)
    csvs = sorted(cfg.out_dir.glob("*/review.csv"))
    if not csvs:
        typer.echo(f"Chưa có review.csv nào trong {cfg.out_dir}")
        raise typer.Exit(code=1)
    typer.echo("Lô: " + ", ".join(p.parent.name for p in csvs))
    typer.echo(stats_markdown(summarize_reviews(csvs)))


@app.command()
def style(
    config: Path = ConfigOpt,
    work_dir: Path = WorkOpt,
    every_s: float = typer.Option(1.0, "--every", help="Lấy 1 khung hình mỗi bao nhiêu giây"),
    no_transcribe: bool = typer.Option(False, "--no-transcribe"),
    threshold: float = typer.Option(0.3, "--threshold", help="Ngưỡng dò cắt cảnh (thấp hơn = nhạy hơn)"),
) -> None:
    """Đo nhịp cắt, lấy khung hình, phiên âm mọi video trong 'video tham khảo' → work/style/<tên>/."""
    cfg = load_config(config)
    refs = list_videos(cfg.references_dir) if cfg.references_dir.is_dir() else []
    if not refs:
        raise typer.BadParameter(f"Không có video trong {cfg.references_dir}")
    for ref in refs:
        d = work_dir / "style" / ref.stem
        d.mkdir(parents=True, exist_ok=True)
        stats = shot_stats(ref, threshold)
        (d / "stats.json").write_text(json.dumps(asdict(stats), ensure_ascii=False, indent=1), encoding="utf-8")
        frames = reference_frames(ref, d / "frames", every_s)
        words = [] if no_transcribe else transcribe(ref)
        (d / "transcript.json").write_text(
            json.dumps([asdict(w) for w in words], ensure_ascii=False, indent=1), encoding="utf-8")
        typer.echo(f"{ref.name}: {stats.duration:.1f} s, {stats.n_cuts} cắt cảnh, "
                   f"TB {stats.avg_shot_s:.2f} s/cảnh, {len(frames)} khung hình")
    typer.echo(f"Xong: {work_dir / 'style'}")


if __name__ == "__main__":
    app()
