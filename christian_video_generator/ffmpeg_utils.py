"""FFmpeg helpers — all subprocess calls live here."""

import json
import subprocess
from pathlib import Path

from config import (
    AUDIO_BITRATE,
    BG_MUSIC_PATH,
    BG_MUSIC_VOLUME,
    CLIP_DURATION_S,
    FFMPEG_BIN,
    FFPROBE_BIN,
    FONT_COLOR,
    FONT_PATH,
    FONT_SIZE,
    MAX_DURATION_S,
    TEMP_DIR,
    TEXT_BOX_COLOR,
    TEXT_MARGIN,
    VIDEO_BITRATE,
    VIDEO_FPS,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)


def _run(cmd: list[str], label: str = "") -> None:
    tag = f"[ffmpeg:{label}]" if label else "[ffmpeg]"
    print(f"  {tag} {' '.join(str(c) for c in cmd[:6])} …")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed ({label}):\n{result.stderr[-2000:]}"
        )


def probe_duration(path: Path) -> float:
    """Return media duration in seconds using ffprobe."""
    cmd = [
        FFPROBE_BIN, "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}:\n{result.stderr}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def normalize_clip(src: Path, index: int, duration: float = CLIP_DURATION_S) -> Path:
    """
    Resize + crop a clip to 1080×1920, trim to *duration* seconds,
    normalise frame rate.  Returns path of processed file.
    """
    dest = TEMP_DIR / f"norm_{index:02d}.mp4"
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    # scale so the shortest side fills the target, then crop centre
    vf = (
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"fps={VIDEO_FPS}"
    )
    cmd = [
        FFMPEG_BIN, "-y",
        "-ss", "0",
        "-i", str(src),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        str(dest),
    ]
    _run(cmd, f"norm_{index:02d}")
    return dest


def concat_clips(clip_paths: list[Path]) -> Path:
    """Concatenate normalised clips into a single silent video."""
    list_file = TEMP_DIR / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in clip_paths)
    )
    dest = TEMP_DIR / "concat.mp4"
    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(dest),
    ]
    _run(cmd, "concat")
    return dest


def _escape_drawtext(text: str) -> str:
    """Escape characters that break FFmpeg drawtext expressions."""
    replacements = [
        ("\\", "\\\\"),
        ("'",  "’"),   # replace straight apostrophe with typographic one
        (":",  "\\:"),
        ("%",  "\\%"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _wrap_text(text: str, max_chars: int = 38) -> str:
    """Simple word-wrap so long scripture lines fit on screen."""
    words = text.split()
    lines, current = [], []
    for word in words:
        if sum(len(w) for w in current) + len(current) + len(word) > max_chars:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def add_scripture_overlay(
    video: Path,
    reference: str,
    scripture_text: str,
    voiceover_duration: float,
) -> Path:
    """
    Burn Scripture reference + text onto the video with a semi-transparent box.
    Text appears in the lower third and fades out before the end.
    """
    dest = TEMP_DIR / "with_text.mp4"

    wrapped = _wrap_text(scripture_text, max_chars=38)
    lines = wrapped.split("\n")

    # Build a stacked drawtext filter: reference line then scripture lines
    text_filters = []
    line_height = FONT_SIZE + 12
    total_lines = 1 + len(lines)  # reference + scripture lines
    block_height = total_lines * line_height + 40

    # y start: 75 % down the screen
    y_start = int(VIDEO_HEIGHT * 0.72)

    # Reference line (slightly larger, bolder look via colour)
    ref_escaped = _escape_drawtext(reference)
    text_filters.append(
        f"drawtext=fontfile='{FONT_PATH}'"
        f":text='{ref_escaped}'"
        f":fontcolor=yellow"
        f":fontsize={FONT_SIZE}"
        f":x=(w-text_w)/2"
        f":y={y_start}"
        f":box=1:boxcolor={TEXT_BOX_COLOR}:boxborderw=12"
    )

    for i, line in enumerate(lines):
        line_escaped = _escape_drawtext(line)
        y_pos = y_start + line_height * (i + 1)
        text_filters.append(
            f"drawtext=fontfile='{FONT_PATH}'"
            f":text='{line_escaped}'"
            f":fontcolor={FONT_COLOR}"
            f":fontsize={FONT_SIZE - 6}"
            f":x=(w-text_w)/2"
            f":y={y_pos}"
            f":box=1:boxcolor={TEXT_BOX_COLOR}:boxborderw=10"
        )

    vf = ",".join(text_filters)

    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(video),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-an",
        str(dest),
    ]
    _run(cmd, "overlay")
    return dest


def mix_audio(voiceover: Path, video_duration: float) -> Path:
    """
    Create a final audio track: voice-over + optional background music.
    If BG_MUSIC_PATH doesn't exist, returns voiceover padded to video_duration.
    """
    dest = TEMP_DIR / "final_audio.aac"
    bg = Path(BG_MUSIC_PATH)

    if bg.exists():
        # Loop music, lower its volume, mix with voice-over
        filter_complex = (
            f"[1:a]aloop=loop=-1:size=2e+09,volume={BG_MUSIC_VOLUME}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[out]"
        )
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(voiceover),
            "-i", str(bg),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(video_duration),
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            str(dest),
        ]
    else:
        # Pad silence so audio matches video length
        pad = max(0.0, video_duration - probe_duration(voiceover))
        filter_complex = (
            f"[0:a]apad=pad_dur={pad:.2f}[out]"
        )
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(voiceover),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(video_duration),
            "-c:a", "aac", "-b:a", AUDIO_BITRATE,
            str(dest),
        ]

    _run(cmd, "audio_mix")
    return dest


def assemble_final(
    video_with_text: Path,
    audio: Path,
    output_path: Path,
) -> Path:
    """Mux video + audio into the final MP4, capped at MAX_DURATION_S."""
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(video_with_text),
        "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-t", str(MAX_DURATION_S),
        "-c:v", "libx264", "-preset", "fast", "-b:v", VIDEO_BITRATE,
        "-c:a", "aac", "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run(cmd, "assemble")
    return output_path
