#!/usr/bin/env python3
"""
Christian Encouragement Video Generator
========================================
Usage:
    python generate.py [--scripture-index N] [--output NAME]

Environment variables:
    PEXELS_API_KEY   required — your Pexels API key
    BG_MUSIC_PATH    optional — path to a royalty-free MP3 for background music
    FFMPEG_BIN       optional — ffmpeg binary path (default: ffmpeg)
    FFPROBE_BIN      optional — ffprobe binary path (default: ffprobe)
"""

import argparse
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Allow running from the package directory directly
sys.path.insert(0, str(Path(__file__).parent))

from config import MAX_DURATION_S, OUTPUT_DIR, TEMP_DIR, CLIP_DURATION_S
from ffmpeg_utils import (
    add_scripture_overlay,
    assemble_final,
    concat_clips,
    mix_audio,
    normalize_clip,
    probe_duration,
)
from pexels_client import fetch_clips
from scriptures import ENCOURAGEMENTS, SCRIPTURES
from tts import build_voiceover_script, generate_voiceover


def clean_temp() -> None:
    """Remove all files from the temp directory."""
    for f in TEMP_DIR.iterdir():
        if f.is_file():
            f.unlink()


def pick_content(scripture_index: int | None) -> tuple[dict, dict]:
    """Return (encouragement, scripture) for today's video."""
    if scripture_index is not None:
        scripture = SCRIPTURES[scripture_index % len(SCRIPTURES)]
    else:
        # Deterministic daily selection — same run on the same day = same verse
        day_seed = int(datetime.now().strftime("%Y%j"))
        scripture = SCRIPTURES[day_seed % len(SCRIPTURES)]

    encouragement = random.choice(ENCOURAGEMENTS)
    return encouragement, scripture


def calculate_clip_count(target_duration: float) -> int:
    """How many clips do we need to cover *target_duration* seconds?"""
    return max(1, int(target_duration / CLIP_DURATION_S) + 1)


def run(args: argparse.Namespace) -> Path:
    print("\n✝  Christian Encouragement Video Generator")
    print("=" * 48)

    # ── 1. Select content ────────────────────────────────────────────────────
    encouragement, scripture = pick_content(args.scripture_index)
    print(f"\n[1/7] Content selected")
    print(f"      Encouragement : {encouragement['text'][:60]}…")
    print(f"      Scripture     : {scripture['reference']}")

    # ── 2. Generate voice-over ───────────────────────────────────────────────
    print("\n[2/7] Generating French voice-over (gTTS)…")
    script = build_voiceover_script(encouragement, scripture)
    vo_path = generate_voiceover(script)
    vo_duration = probe_duration(vo_path)
    print(f"      Voice-over duration: {vo_duration:.1f}s")

    # Cap at MAX_DURATION_S
    target_duration = min(vo_duration + 3.0, MAX_DURATION_S)  # +3s breathing room

    # ── 3. Fetch nature clips from Pexels ────────────────────────────────────
    num_clips = calculate_clip_count(target_duration)
    print(f"\n[3/7] Fetching {num_clips} nature clip(s) from Pexels…")
    raw_clips = fetch_clips(num_clips=num_clips)

    if not raw_clips:
        raise RuntimeError(
            "No clips downloaded from Pexels. "
            "Check your PEXELS_API_KEY and network connection."
        )
    print(f"      Downloaded {len(raw_clips)} clip(s).")

    # ── 4. Normalise clips ───────────────────────────────────────────────────
    print("\n[4/7] Normalising clips to 1080×1920 @ 30fps…")
    norm_clips = [normalize_clip(clip, i) for i, clip in enumerate(raw_clips)]

    # ── 5. Concatenate clips ─────────────────────────────────────────────────
    print("\n[5/7] Concatenating clips…")
    concat = concat_clips(norm_clips)

    # ── 6. Add Scripture text overlay ────────────────────────────────────────
    print("\n[6/7] Burning Scripture overlay…")
    video_with_text = add_scripture_overlay(
        concat,
        scripture["reference"],
        scripture["text"],
        vo_duration,
    )

    # ── 7. Mix audio and assemble final video ────────────────────────────────
    print("\n[7/7] Mixing audio and assembling final MP4…")
    video_duration = probe_duration(video_with_text)
    audio = mix_audio(vo_path, video_duration)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = args.output or f"encouragement_{timestamp}.mp4"
    if not output_name.endswith(".mp4"):
        output_name += ".mp4"
    output_path = OUTPUT_DIR / output_name

    assemble_final(video_with_text, audio, output_path)

    # ── Done ─────────────────────────────────────────────────────────────────
    size_mb = output_path.stat().st_size / (1024 * 1024)
    final_dur = probe_duration(output_path)
    print(f"\n{'='*48}")
    print(f"✅  Video ready!")
    print(f"    Path     : {output_path}")
    print(f"    Duration : {final_dur:.1f}s")
    print(f"    Size     : {size_mb:.1f} MB")
    print(f"    Scripture: {scripture['reference']}")
    print(f"{'='*48}\n")

    if not args.keep_temp:
        clean_temp()

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a vertical Christian encouragement video (1080×1920, ≤90s)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--scripture-index",
        type=int,
        default=None,
        help="Index into the scripture pool (0-based). Defaults to today's daily verse.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output filename (placed in output/). Defaults to encouragement_YYYYMMDD_HHMMSS.mp4",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep intermediate files in temp/ (useful for debugging).",
    )

    args = parser.parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
