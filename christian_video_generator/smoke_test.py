#!/usr/bin/env python3
"""
Smoke test — runs the complete pipeline without a Pexels API key.

Instead of downloading clips from Pexels, we generate a synthetic
colour-bar video using FFmpeg and inject it directly.

Usage:
    python smoke_test.py
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import FFMPEG_BIN, TEMP_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH
from ffmpeg_utils import (
    add_scripture_overlay,
    assemble_final,
    concat_clips,
    mix_audio,
    normalize_clip,
    probe_duration,
)
from generate import pick_content
from tts import build_voiceover_script


def make_synthetic_clip(index: int, duration: float = 5.0) -> Path:
    """Generate a colour-bar test pattern clip via FFmpeg (no download needed)."""
    dest = TEMP_DIR / f"synthetic_{index:02d}.mp4"
    if dest.exists():
        return dest

    colours = ["red", "green", "blue", "orange", "purple"]
    colour = colours[index % len(colours)]

    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "lavfi",
        "-i", f"color=c={colour}:size={VIDEO_WIDTH}x{VIDEO_HEIGHT}:rate={VIDEO_FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast",
        str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Synthetic clip generation failed:\n{result.stderr[-1000:]}")
    return dest


def make_synthetic_audio(duration: float = 10.0) -> Path:
    """Generate a sine-tone MP3 via FFmpeg (no network needed)."""
    dest = TEMP_DIR / "smoke_vo.mp3"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-c:a", "libmp3lame", "-q:a", "4",
        str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Synthetic audio failed:\n{result.stderr[-1000:]}")
    return dest


def run_smoke_test() -> None:
    print("\n  Christian Video Generator — SMOKE TEST")
    print("=" * 48)
    print("  (Uses synthetic colour bars + sine tone; no network needed)")
    print()

    # 1. Content
    encouragement, scripture = pick_content(0)
    print(f"[1/7] Scripture  : {scripture['reference']}")

    # 2. Voice-over (synthetic in smoke test; real gTTS used in generate.py)
    print("[2/7] Generating synthetic audio (gTTS skipped — no network)…")
    vo_path = make_synthetic_audio(duration=10.0)
    vo_duration = probe_duration(vo_path)
    print(f"      Duration: {vo_duration:.1f}s")

    # 3. Synthetic clips (2 × 5 s to keep the test fast)
    print("[3/7] Creating synthetic clips…")
    raw_clips = [make_synthetic_clip(i) for i in range(2)]

    # 4. Normalise
    print("[4/7] Normalising…")
    norm_clips = [normalize_clip(c, i) for i, c in enumerate(raw_clips)]

    # 5. Concat
    print("[5/7] Concatenating…")
    concat = concat_clips(norm_clips)

    # 6. Text overlay
    print("[6/7] Adding Scripture overlay…")
    video_with_text = add_scripture_overlay(
        concat,
        scripture["reference"],
        scripture["text"],
        vo_duration,
    )

    # 7. Mix audio + assemble
    print("[7/7] Assembling final video…")
    video_duration = probe_duration(video_with_text)
    audio = mix_audio(vo_path, video_duration)

    output = Path(__file__).parent / "output" / "smoke_test_output.mp4"
    assemble_final(video_with_text, audio, output)

    size_kb = output.stat().st_size / 1024
    dur = probe_duration(output)

    print()
    print("=" * 48)
    print("✅  Smoke test PASSED")
    print(f"    Output   : {output}")
    print(f"    Duration : {dur:.1f}s")
    print(f"    Size     : {size_kb:.0f} KB")
    print("=" * 48)
    print()


if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as exc:
        print(f"\n[FAIL] {exc}")
        sys.exit(1)
