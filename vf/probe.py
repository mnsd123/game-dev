"""Đọc thông số video và chuẩn hoá về H.264 30 fps CFR."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vf.ffutil import ffprobe_json, run

HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}


@dataclass(frozen=True)
class MediaInfo:
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    codec: str


def _rate(text: str) -> float:
    num, _, den = text.partition("/")
    return float(num) / float(den) if den and float(den) else float(num or 0)


def _rotation(stream: dict) -> int:
    for sd in stream.get("side_data_list", []):
        if "rotation" in sd:
            return int(sd["rotation"])
    return int(stream.get("tags", {}).get("rotate", 0))


def probe(path: Path) -> MediaInfo:
    """Thông số video; width/height là kích thước HIỂN THỊ (đã tính cờ xoay)."""
    data = ffprobe_json(path)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise ValueError(f"{path}: không có luồng hình")
    w, h = int(video["width"]), int(video["height"])
    if abs(_rotation(video)) % 180 == 90:
        w, h = h, w
    fps = _rate(video.get("avg_frame_rate", "0/0")) or _rate(video.get("r_frame_rate", "0/0"))
    return MediaInfo(
        duration=float(data["format"].get("duration", 0.0)),
        width=w,
        height=h,
        fps=round(fps, 3),
        has_audio=any(s["codec_type"] == "audio" for s in data["streams"]),
        codec=video["codec_name"],
    )


def _video_filter(stream: dict) -> str:
    chain = []
    if stream.get("color_transfer") in HDR_TRANSFERS:
        # iPhone quay HDR (HLG/PQ 10-bit) → tone map về SDR bt709 để màu không bị nhạt
        chain.append(
            "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
            "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv"
        )
    chain += ["fps=30", "format=yuv420p"]
    return ",".join(chain)


def normalize(src: Path, dst: Path) -> Path:
    """Chuyển về H.264 yuv420p, 30 fps CFR, AAC 48 kHz stereo; áp cờ xoay vào hình."""
    data = ffprobe_json(src)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in data["streams"])
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-map", "0:v:0"]
    if has_audio:
        cmd += ["-map", "0:a:0"]
    cmd += [
        "-vf", _video_filter(video), "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
    ]
    if has_audio:
        cmd += ["-af", "aresample=async=1:first_pts=0", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    cmd += ["-map_metadata", "-1", "-movflags", "+faststart", str(dst)]
    run(cmd)
    return dst
