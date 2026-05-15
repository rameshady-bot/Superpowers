"""
FFmpeg video assembler.

Builds and executes ONE ffmpeg subprocess call that:
  1. Trims each clip to its exact segment duration
  2. Scales/crops every clip to 1080x1920 portrait, 30fps
  3. Concatenates all 5 clips via the concat filter
  4. Overlays title text (first 4 s) and scripture reference (last 5 s)
  5. Mixes per-segment TTS audio (with cumulative time offsets)
  6. Mixes in background music at -18 dB under the voice (if provided)
  7. Outputs H.264 / AAC MP4, capped at 90 seconds
"""

import os
import subprocess
from pathlib import Path

# ── Font paths ─────────────────────────────────────────────────────────────────
_FONT_BOLD = os.environ.get(
    "FONT_BOLD",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)
_FONT_ITALIC = os.environ.get(
    "FONT_ITALIC",
    "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
)

_W, _H = 1080, 1920
_FPS = 30
_MAX_SECONDS = 90
_FFMPEG = os.environ.get("FFMPEG_BIN", "ffmpeg")


def _font(path: str) -> str:
    """Return path if it exists, else fall back to bold."""
    return path if Path(path).exists() else _FONT_BOLD


def _esc(text: str) -> str:
    """Escape characters that break FFmpeg drawtext filter expressions."""
    text = text.replace("\\", "\\\\")
    # Replace straight apostrophes with typographic ones (avoids shell quoting issues)
    text = text.replace("'", "’")
    text = text.replace(":", "\\:")
    text = text.replace("%", "\\%")
    text = text.replace("[", "\\[").replace("]", "\\]")
    return text


def _build_filter_complex(
    segments: list[dict],
    title: str,
    scripture: dict,
    music_idx: int | None,
) -> tuple[str, str, str]:
    """
    Return (filter_complex_string, video_output_label, audio_output_label).

    *music_idx* is the FFmpeg input index of the background music file,
    or None if no music is provided.
    """
    n = len(segments)
    total_dur = sum(s["duration_seconds"] for s in segments)
    parts: list[str] = []

    # ── 1. Per-segment video: trim → scale/crop → fps ─────────────────────────
    for i, seg in enumerate(segments):
        dur = seg["duration_seconds"]
        parts.append(
            f"[{i}:v]"
            f"trim=end={dur},setpts=PTS-STARTPTS,"
            f"scale={_W}:{_H}:force_original_aspect_ratio=increase,"
            f"crop={_W}:{_H},setsar=1,fps={_FPS}"
            f"[v{i}]"
        )

    # ── 2. Concatenate all video segments ─────────────────────────────────────
    concat_in = "".join(f"[v{i}]" for i in range(n))
    parts.append(f"{concat_in}concat=n={n}:v=1:a=0[vraw]")

    # ── 3. Title overlay — top-center, white bold, visible 0→4 s ─────────────
    title_esc = _esc(title)
    font_bold = _font(_FONT_BOLD)
    parts.append(
        f"[vraw]drawtext="
        f"fontfile='{font_bold}'"
        f":text='{title_esc}'"
        f":enable='between(t,0,4)'"
        f":fontsize=52"
        f":fontcolor=white"
        f":x=(w-text_w)/2"
        f":y=120"
        f":shadowx=3:shadowy=3:shadowcolor=black@0.8"
        f"[vtitle]"
    )

    # ── 4. Scripture reference overlay — bottom-center, italic, last 5 s ──────
    ref_esc = _esc(scripture["reference"])
    font_italic = _font(_FONT_ITALIC)
    t_start = max(0, total_dur - 5)
    parts.append(
        f"[vtitle]drawtext="
        f"fontfile='{font_italic}'"
        f":text='{ref_esc}'"
        f":enable='between(t,{t_start},{total_dur})'"
        f":fontsize=38"
        f":fontcolor=white"
        f":x=(w-text_w)/2"
        f":y=h-160"
        f":box=1:boxcolor=black@0.55:boxborderw=14"
        f"[vout]"
    )

    # ── 5. Per-segment audio (TTS or generated silence) ───────────────────────
    # Determine which TTS inputs are real (have an FFmpeg input index).
    # In _build_cmd we set seg["_tts_input_idx"] for existing files.
    offset_ms = 0
    audio_labels: list[str] = []

    for i, seg in enumerate(segments):
        dur = seg["duration_seconds"]
        tts_idx = seg.get("_tts_input_idx")  # set by _build_cmd, None if missing

        if tts_idx is not None:
            parts.append(
                f"[{tts_idx}:a]adelay={offset_ms}|{offset_ms}[a{i}]"
            )
        else:
            # Generate silence via filter source — no additional input needed
            parts.append(
                f"anullsrc=r=44100:cl=stereo,"
                f"atrim=end={dur},"
                f"adelay={offset_ms}|{offset_ms}"
                f"[a{i}]"
            )

        audio_labels.append(f"[a{i}]")
        offset_ms += int(dur * 1000)

    # ── 6. Mix all TTS streams ────────────────────────────────────────────────
    tts_mix_in = "".join(audio_labels)
    parts.append(
        f"{tts_mix_in}amix=inputs={n}:duration=longest:normalize=0[voice]"
    )

    # ── 7. Background music (optional) ────────────────────────────────────────
    if music_idx is not None:
        parts.append(
            f"[{music_idx}:a]aloop=loop=-1:size=2147483647,"
            f"volume=-18dB[bgm]"
        )
        parts.append(
            "[voice][bgm]amix=inputs=2:duration=first:normalize=0[aout]"
        )
        audio_out = "[aout]"
    else:
        audio_out = "[voice]"

    return ";".join(parts), "[vout]", audio_out


def _build_cmd(
    segments: list[dict],
    title: str,
    scripture: dict,
    output_path: Path,
    music_path: Path | None,
) -> list[str]:
    """Construct the full ffmpeg command as a list of strings."""
    cmd: list[str] = [_FFMPEG, "-y"]

    # ── Inputs: video clips ───────────────────────────────────────────────────
    for seg in segments:
        cmd += ["-i", str(seg["clip_path"])]

    # ── Inputs: TTS audio files (only if they exist) ──────────────────────────
    next_input_idx = len(segments)
    for seg in segments:
        tts = seg.get("tts_path")
        if tts and Path(tts).exists() and Path(tts).stat().st_size > 0:
            seg["_tts_input_idx"] = next_input_idx
            cmd += ["-i", str(tts)]
            next_input_idx += 1
        else:
            seg["_tts_input_idx"] = None

    # ── Input: background music (optional) ────────────────────────────────────
    music_input_idx: int | None = None
    if music_path and Path(music_path).exists():
        music_input_idx = next_input_idx
        cmd += ["-i", str(music_path)]

    # ── filter_complex ─────────────────────────────────────────────────────────
    fc, v_out, a_out = _build_filter_complex(segments, title, scripture, music_input_idx)

    cmd += [
        "-filter_complex", fc,
        "-map", v_out,
        "-map", a_out,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(_FPS),
        "-t", str(_MAX_SECONDS),
        "-movflags", "+faststart",
        str(output_path),
    ]

    return cmd


def assemble_video(
    segments: list[dict],
    title: str,
    scripture: dict,
    output_path: Path,
    music_path: Path | None = None,
    debug: bool = False,
    dry_run: bool = False,
) -> Path:
    """
    Build and execute the FFmpeg command.

    Parameters
    ----------
    segments  : enriched segment dicts (must include 'clip_path' and 'tts_path')
    title     : video title for on-screen overlay
    scripture : dict with 'reference' and 'text'
    output_path : where to write the final MP4
    music_path  : optional background music MP3/AAC
    debug     : if True, always print the full ffmpeg command
    dry_run   : if True, print the command but do NOT execute ffmpeg
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = _build_cmd(segments, title, scripture, output_path, music_path)
    cmd_str = " ".join(cmd)

    # Safety check — warn if command is unusually long (> 500 chars)
    if len(cmd_str) > 500:
        print(
            f"\n  [assembler] ⚠  FFmpeg command is {len(cmd_str)} characters "
            f"(> 500 threshold). Printing full command for review:"
        )
        print(f"\n{cmd_str}\n")
        if not debug and not dry_run:
            answer = input("  Continue? [y/N]: ").strip().lower()
            if answer != "y":
                raise RuntimeError("FFmpeg execution cancelled by user.")
    elif debug:
        print(f"\n  [assembler] FFmpeg command:\n{cmd_str}\n")

    if dry_run:
        print(f"\n  [assembler] --dry-run: skipping FFmpeg execution.")
        print(f"  Command ({len(cmd_str)} chars):\n{cmd_str}")
        return output_path

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n  [assembler] FFmpeg stderr:\n{result.stderr[-3000:]}")
        raise RuntimeError("FFmpeg failed — see stderr above")

    return output_path
