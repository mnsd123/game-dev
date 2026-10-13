"""Dựng một biến thể từ edl bằng ffmpeg."""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from vf.captions import remap_words, words_to_ass
from vf.edl import Effect, TextOverlay, Variant, output_duration
from vf.ffutil import run
from vf.paths import BRAND_DIR, CAPTION_STYLE, LIBRARY
from vf.probe import MediaInfo
from vf.brief import FORBIDDEN_PATH, PENDING_PATH, read_phrase_list
from vf.qa import ClaimViolation, check_claims, measure_lufs
from vf.transcribe import Word

W, H, FPS = 1080, 1920, 30
SOURCE_TARGET_LUFS = -16.0
BROLL_TARGET_LUFS = -26.0  # nguồn không có lời nói: chỉ giảm, không bao giờ tăng (tránh đẩy tiếng ồn nền)
MUSIC_BELOW_VOICE_DB = 18.0
JOIN_FADE_S = 0.04  # nửa của 0.08 s mỗi bên chỗ nối hai nguồn khác nhau
DECLICK_S = 0.01
FONT_EXTS = (".ttf", ".otf")
DEFAULT_BRAND = BRAND_DIR
DEFAULT_STYLE = CAPTION_STYLE
DEFAULT_STYLE_GUIDE = LIBRARY / "style-guide.md"


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
        out = subprocess.run(["fc-match", "-f", "%{file}", "Arial:bold"], capture_output=True, encoding="utf-8", errors="replace").stdout
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
        zw, zh = f"2*trunc({W}*(1+{z})/2)", f"2*trunc({H}*(1+{z})/2)"
        # crop không thấy kích thước đổi theo khung → tính tâm trực tiếp từ cùng biểu thức zoom
        out.append(f"scale=w='{zw}':h='{zh}':eval=frame,crop={W}:{H}:x='({zw}-{W})/2':y='({zh}-{H})/2'")
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


def source_gains(
    sources: dict[str, Path], infos: dict[str, MediaInfo], names: set[str], speech: set[str] | None = None
) -> dict[str, float]:
    """Gain (dB) đưa nguồn có lời nói về -16 LUFS, đo một lần cho cả file.
    `speech`: các nguồn có lời nói; None = coi mọi nguồn là có lời nói."""
    gains = {}
    for name in names:
        lufs = measure_lufs(sources[name]) if infos[name].has_audio else -math.inf
        if lufs < -60:
            gains[name] = 0.0
        elif speech is None or name in speech:
            gains[name] = max(-20.0, min(20.0, SOURCE_TARGET_LUFS - lufs))
        else:
            gains[name] = max(-20.0, min(0.0, BROLL_TARGET_LUFS - lufs))
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
    speech: set[str] | None = None,
    overlay: Path | None = None,
) -> list[str]:
    """`overlay`: video chữ động nền trong suốt (Remotion) chồng lên hình; khi có thì không vẽ drawtext."""
    pieces = v.pieces()
    if gains is None:
        gains = source_gains(sources, infos, {p.source for p in pieces}, speech)
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

    total = output_duration(v)
    extra = n
    vchain = _effect_filters(v.effects)
    if overlay is not None:
        # hiệu ứng (zoom, rung) chỉ áp vào hình quay; chữ động chồng lên sau nên không bị zoom theo
        cmd += ["-i", str(overlay)]
        fc.append("[vc]" + ",".join(vchain or ["null"]) + "[vfx]")
        fc.append(f"[{extra}:v]setpts=PTS-STARTPTS,fps={FPS}[ovl]")
        vchain = [f"[vfx][ovl]overlay=0:0:format=auto:eof_action=pass"]
        extra += 1
    else:
        font = find_font(brand) if v.overlays else None
        vchain += [_overlay_filter(o, k, font, text_dir) for k, o in enumerate(v.overlays)]
    if ass is not None and v.captions:
        vchain.append(f"subtitles=filename={_filter_path(ass)}:fontsdir={_filter_path(brand)}")
    vchain.append(f"fps={FPS},format=yuv420p")
    if overlay is not None:
        fc.append(vchain[0] + "," + ",".join(vchain[1:]) + "[vout]")
    else:
        fc.append("[vc]" + ",".join(vchain) + "[vout]")
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
    forbidden: list[str] | None = None,
    motion: bool | None = None,
) -> Path:
    """Kiểm tra claim trên mọi overlay + phụ đề TRƯỚC khi render; vi phạm → ClaimViolation, không tạo file.
    Overlay = chữ trong edl + cam kết tự phát hiện trong lời nói (library/commitments.txt).
    motion=None: dùng Remotion nếu đã cài, không thì vẽ chữ tĩnh bằng drawtext."""
    from vf.motion import plan_overlays, remotion_available, render_overlay

    if forbidden is None:
        forbidden = read_phrase_list(FORBIDDEN_PATH) + read_phrase_list(PENDING_PATH)
    v = v.model_copy(update={"overlays": plan_overlays(v, words_by_source or {})})
    words = remap_words(words_by_source or {}, v.pieces()) if v.captions else []
    texts = [o.text for o in v.overlays] + ([" ".join(w.text for w in words)] if words else [])
    hits = check_claims(texts, forbidden)
    if hits:
        raise ClaimViolation(f"biến thể '{v.id}': chữ trên màn hình chứa cụm cấm/chưa có bằng chứng: {hits}")
    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix=f"vf-{v.id}-"))
    work.mkdir(parents=True, exist_ok=True)
    ass_path = None
    if v.captions:
        if words:
            ass_path = work / f"{v.id}.ass"
            ass_path.write_text(words_to_ass(words, style_path), encoding="utf-8")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = out.with_name(out.stem + ".partial" + out.suffix)
    spoken = {name for name, ws in (words_by_source or {}).items() if ws}
    speech = spoken or None  # chưa có transcript nào → không đoán, coi mọi nguồn là có lời nói
    overlay_path = None
    if v.overlays and (remotion_available() if motion is None else motion):
        overlay_path = render_overlay(v, DEFAULT_STYLE_GUIDE, work / f"{v.id}_overlay.mov", brand=brand,
                                      props_path=work / f"{v.id}_overlay.json")
    cmd = build_ffmpeg_cmd(sources, infos, v, ass_path, brand, tmp_out, text_dir=work / f"{v.id}_text",
                           speech=speech, overlay=overlay_path)
    try:
        run(cmd)
    except Exception:
        tmp_out.unlink(missing_ok=True)
        raise
    tmp_out.replace(out)
    return out
