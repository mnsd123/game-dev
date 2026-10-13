"""Dựng một biến thể từ edl bằng ffmpeg."""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from vf.captions import remap_words, words_to_ass
from vf.edl import Effect, TextOverlay, Variant, output_duration
from vf.ffutil import run
from vf.probe import MediaInfo
from vf.qa import measure_lufs
from vf.transcribe import Word

W, H, FPS = 1080, 1920, 30
SOURCE_TARGET_LUFS = -16.0
MUSIC_BELOW_VOICE_DB = 18.0
JOIN_FADE_S = 0.04  # nửa của 0.08 s mỗi bên chỗ nối hai nguồn khác nhau
DECLICK_S = 0.01
FONT_EXTS = (".ttf", ".otf")
DEFAULT_BRAND = Path("library/brand")
DEFAULT_STYLE = Path("templates/caption_style.ass")


def _filter_path(p: Path) -> str:
    """Đường dẫn an toàn trong filtergraph (Windows có 'G:' và '\\')."""
    s = str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"'{s}'"


def find_font(brand: Path) -> Path:
    """Font brand (file .ttf/.otf đầu tiên trong library/brand), nếu chưa có thì dùng font hệ thống có dấu tiếng Việt."""
    if brand and Path(brand).is_dir():
        fonts = sorted(p for p in Path(brand).rglob("*") if p.suffix.lower() in FONT_EXTS)
        if fonts:
            return fonts[0]
    candidates = [Path("C:/Windows/Fonts/arialbd.ttf"), Path("/Library/Fonts/Arial Bold.ttf"),
                  Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")]
    if shutil.which("fc-match"):
        out = subprocess.run(["fc-match", "-f", "%{file}", "Arial:bold"], capture_output=True, text=True).stdout
        if out:
            candidates.insert(0, Path(out))
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Không tìm thấy font: hãy bỏ file .ttf/.otf vào library/brand/")


def resolve_asset(name: str, brand: Path) -> Path:
    for base in (Path(brand), Path(brand).parent / "assets", Path(".")):
        p = base / name
        if p.exists():
            return p
    raise FileNotFoundError(f"Không thấy file '{name}' trong {brand} hoặc library/assets/")


def _is_vertical(info: MediaInfo) -> bool:
    return info.width / info.height <= 0.65


def _fit(label_in: str, label_out: str, info: MediaInfo, i: int) -> list[str]:
    if _is_vertical(info):
        return [f"{label_in}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1{label_out}"]
    # nguồn ngang/vuông: nền blur + hình gốc giữ tỉ lệ ở giữa, không crop mất người nói
    return [
        f"{label_in}split=2[bg{i}][fg{i}]",
        f"[bg{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2[bgb{i}]",
        f"[fg{i}]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs{i}]",
        f"[bgb{i}][fgs{i}]overlay=(W-w)/2:(H-h)/2,setsar=1{label_out}",
    ]


def _between(e: Effect) -> str:
    return f"between(t,{e.at:.3f},{e.at + e.duration:.3f})"


def _effect_filters(effects: list[Effect]) -> list[str]:
    out: list[str] = []
    zooms = [e for e in effects if e.kind == "zoom_punch"]
    if zooms:
        z = "+".join(f"0.08*{_between(e)}*(t-{e.at:.3f})/{max(e.duration, 0.01):.3f}" for e in zooms)
        out.append(f"scale=w='2*trunc({W}*(1+{z})/2)':h='2*trunc({H}*(1+{z})/2)':eval=frame,crop={W}:{H}")
    shakes = [e for e in effects if e.kind == "shake"]
    if shakes:
        dx = "+".join(f"{_between(e)}*16*sin(90*t)" for e in shakes)
        dy = "+".join(f"{_between(e)}*16*cos(70*t)" for e in shakes)
        out.append(f"scale={W + 40}:{H + 72},crop={W}:{H}:x='20+{dx}':y='36+{dy}'")
    for e in effects:
        if e.kind == "flash":
            out.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.75:t=fill:enable='{_between(e)}'")
        elif e.kind == "highlight":
            out.append(f"drawbox=x=0:y=ih*0.44:w=iw:h=ih*0.12:color=yellow@0.35:t=fill:enable='{_between(e)}'")
    return out


OVERLAY_Y = {"top": "h*0.12", "center": "(h-text_h)/2", "bottom": "h*0.70"}


def _overlay_filter(o: TextOverlay, idx: int, font: Path, text_dir: Path) -> str:
    text_dir.mkdir(parents=True, exist_ok=True)
    tf = text_dir / f"overlay_{idx}.txt"
    tf.write_text("\n".join(textwrap.wrap(o.text, width=20)) or o.text, encoding="utf-8")
    size = 88 if o.style == "hook" else 64
    return (
        f"drawtext=fontfile={_filter_path(font)}:textfile={_filter_path(tf)}:expansion=none:"
        f"fontsize={size}:fontcolor=white:borderw=7:bordercolor=black:line_spacing=12:"
        f"x=(w-text_w)/2:y={OVERLAY_Y[o.position]}:enable='between(t,{o.start:.3f},{o.end:.3f})'"
    )


def source_gains(sources: dict[str, Path], infos: dict[str, MediaInfo], names: set[str]) -> dict[str, float]:
    """Gain (dB) đưa mỗi nguồn về -16 LUFS, đo một lần cho cả file."""
    gains = {}
    for name in names:
        lufs = measure_lufs(sources[name]) if infos[name].has_audio else -math.inf
        gains[name] = 0.0 if lufs < -60 else max(-20.0, min(20.0, SOURCE_TARGET_LUFS - lufs))
    return gains


def build_ffmpeg_cmd(
    sources: dict[str, Path],
    infos: dict[str, MediaInfo],
    v: Variant,
    ass: Path | None,
    brand: Path,
    out: Path,
    *,
    gains: dict[str, float] | None = None,
    text_dir: Path | None = None,
) -> list[str]:
    pieces = v.pieces()
    if gains is None:
        gains = source_gains(sources, infos, {p.source for p in pieces})
    text_dir = Path(text_dir) if text_dir else Path(tempfile.mkdtemp(prefix="vf-text-"))
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p in pieces:
        # seek theo từng đoạn: nhanh với file gốc dài, và mỗi đoạn có luồng riêng
        cmd += ["-ss", f"{p.start:.3f}", "-t", f"{p.duration:.3f}", "-i", str(sources[p.source])]
    fc: list[str] = []
    n = len(pieces)
    for i, p in enumerate(pieces):
        info = infos[p.source]
        fc += _fit(f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS},", f"[vf{i}]", info, i)
        fc.append(f"[vf{i}]trim=duration={p.duration:.3f},format=yuv420p[v{i}]")
        fade_in = JOIN_FADE_S if i > 0 and pieces[i - 1].source != p.source else DECLICK_S
        fade_out = JOIN_FADE_S if i < n - 1 and pieces[i + 1].source != p.source else DECLICK_S
        src = (f"[{i}:a]asetpts=PTS-STARTPTS," if info.has_audio else "anullsrc=r=48000:cl=stereo,")
        fc.append(
            f"{src}aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"volume={gains.get(p.source, 0.0):.2f}dB,apad,atrim=duration={p.duration:.3f},"
            f"afade=t=in:d={fade_in},afade=t=out:st={max(0.0, p.duration - fade_out):.3f}:d={fade_out}[a{i}]"
        )
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")

    vchain = _effect_filters(v.effects)
    font = find_font(brand) if v.overlays else None
    vchain += [_overlay_filter(o, k, font, text_dir) for k, o in enumerate(v.overlays)]
    if ass is not None and v.captions:
        vchain.append(f"subtitles=filename={_filter_path(ass)}:fontsdir={_filter_path(brand)}")
    vchain.append(f"fps={FPS},format=yuv420p")
    fc.append("[vc]" + ",".join(vchain) + "[vout]")

    total = output_duration(v)
    extra = n
    mix = ["[ac]"]
    if v.music:
        cmd += ["-stream_loop", "-1", "-i", str(resolve_asset(v.music, brand))]
        m_lufs = measure_lufs(resolve_asset(v.music, brand))
        m_gain = 0.0 if m_lufs < -60 else SOURCE_TARGET_LUFS - MUSIC_BELOW_VOICE_DB - m_lufs
        fc.append(f"[{extra}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total:.3f},"
                  f"volume={m_gain:.2f}dB,afade=t=out:st={max(0.0, total - 0.5):.3f}:d=0.5[mus]")
        mix.append("[mus]")
        extra += 1
    for k, e in enumerate(x for x in v.effects if x.kind == "sfx" and x.asset):
        cmd += ["-i", str(resolve_asset(e.asset, brand))]
        ms = int(e.at * 1000)
        fc.append(f"[{extra}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[sfx{k}]")
        mix.append(f"[sfx{k}]")
        extra += 1
    if len(mix) > 1:
        fc.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0[amix]")
        alabel = "[amix]"
    else:
        alabel = "[ac]"
    fc.append(f"{alabel}loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=duration={total:.3f}[aout]")

    cmd += [
        "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out),
    ]
    return cmd


def render_variant(
    sources: dict[str, Path],
    infos: dict[str, MediaInfo],
    v: Variant,
    out: Path,
    *,
    words_by_source: dict[str, list[Word]] | None = None,
    brand: Path = DEFAULT_BRAND,
    style_path: Path = DEFAULT_STYLE,
    work_dir: Path | None = None,
) -> Path:
    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix=f"vf-{v.id}-"))
    work.mkdir(parents=True, exist_ok=True)
    ass_path = None
    if v.captions:
        words = remap_words(words_by_source or {}, v.pieces())
        if words:
            ass_path = work / f"{v.id}.ass"
            ass_path.write_text(words_to_ass(words, style_path), encoding="utf-8")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out.with_name(out.stem + ".partial" + out.suffix)
    cmd = build_ffmpeg_cmd(sources, infos, v, ass_path, brand, tmp_out, text_dir=work / f"{v.id}_text")
    try:
        run(cmd)
    except Exception:
        tmp_out.unlink(missing_ok=True)
        raise
    tmp_out.replace(out)
    return out
