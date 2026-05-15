#!/usr/bin/env python3
"""
Christian Encouragement Video Generator
========================================
Generates a vertical 1080x1920 MP4 (≤ 90 s) from a single CLI command.

Usage:
    python main.py --theme "Ne pas avoir peur"
    python main.py --theme "La paix de Dieu" --no-music --debug
    python main.py --theme "L'amour de Dieu" --dry-run

Required environment variables (set in .env):
    PEXELS_API_KEY      Free key from https://www.pexels.com/api/
    ANTHROPIC_API_KEY   Key from https://console.anthropic.com/
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Load .env before any pipeline imports so env vars are available
_ENV_FILE = Path(__file__).parent / ".env"
if _ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE)
    except ImportError:
        # Manually parse simple KEY=value lines if python-dotenv is missing
        with open(_ENV_FILE) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

# Add project root to path for pipeline imports
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.content_generator import generate_script
from pipeline.logger import log_run
from pipeline.pexels_fetcher import fetch_clip
from pipeline.tts_generator import generate_tts
from pipeline.video_assembler import assemble_video


def _slug(text: str) -> str:
    """Convert theme text to a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:40]


def _output_path(theme: str) -> Path:
    """Return a unique output path that never overwrites an existing file."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"video_{_slug(theme)}_{ts}.mp4"
    return output_dir / filename


def _wipe_temp() -> None:
    """Remove all files from temp/ (called only on successful run)."""
    temp_dir = Path(__file__).parent / "temp"
    if not temp_dir.exists():
        return
    for f in temp_dir.iterdir():
        if f.is_file():
            f.unlink()
    print("  [main] temp/ wiped.")


def _step(name: str, fn, *args, **kwargs):
    """Execute *fn* and print ✅/❌ status.  Re-raises on failure."""
    try:
        result = fn(*args, **kwargs)
        print(f"✅ {name} completed")
        return result
    except Exception as exc:
        print(f"❌ {name} failed — {exc}")
        raise


def run(args: argparse.Namespace) -> None:
    print()
    print("✝  Christian Encouragement Video Generator")
    print("=" * 52)
    print(f"   Theme    : {args.theme}")
    print(f"   Language : {args.lang}")
    print(f"   Music    : {'disabled' if args.no_music else 'enabled (if BG_MUSIC_PATH set)'}")
    print(f"   Debug    : {args.debug}")
    print(f"   Dry-run  : {args.dry_run}")
    print("=" * 52)
    print()

    started_at = datetime.now()
    output_path = _output_path(args.theme)
    music_path: Path | None = None

    if not args.no_music:
        bg = os.environ.get("BG_MUSIC_PATH", "")
        if bg and Path(bg).exists():
            music_path = Path(bg)
            print(f"  [main] background music: {music_path}")
        else:
            print("  [main] BG_MUSIC_PATH not set or file not found — proceeding without music")

    # ── Step 1: Generate script via Anthropic ─────────────────────────────────
    print("\n── Step 1/5: Generating script (Anthropic API) ──")
    script = _step("Script generation", generate_script, args.theme)

    title = script["title"]
    scripture = script["scripture"]
    segments_meta = script["narration_segments"]
    total_planned = sum(s["duration_seconds"] for s in segments_meta)

    print(f"   Title    : {title}")
    print(f"   Scripture: {scripture['reference']}")
    print(f"   Duration : {total_planned}s across {len(segments_meta)} segments")
    print(f"   Music mood: {script['background_music_mood']}")

    # ── Step 2: Validate JSON schema ──────────────────────────────────────────
    # (validation already performed inside generate_script — this is the confirmation)
    print("\n── Step 2/5: Schema validation ──")
    print(f"✅ Schema validation completed (5 segments, {total_planned}s total)")

    # ── Step 3: Fetch video clips from Pexels ─────────────────────────────────
    print("\n── Step 3/5: Fetching Pexels clips ──")
    segments: list[dict] = []
    for seg in segments_meta:
        clip_path = _step(
            f"Clip fetch (segment {seg['segment_id']}: '{seg['visual_keyword']}')",
            fetch_clip,
            seg["visual_keyword"],
            seg["duration_seconds"],
            seg["segment_id"],
        )
        segments.append({**seg, "clip_path": clip_path, "tts_path": None})

    # ── Step 4: Generate TTS voice-overs ─────────────────────────────────────
    print("\n── Step 4/5: Generating French TTS voice-overs ──")
    for i, seg in enumerate(segments):
        tts_path = generate_tts(seg["text"], seg["segment_id"])
        if tts_path:
            print(f"✅ TTS segment {seg['segment_id']} completed")
        else:
            print(f"⚠  TTS segment {seg['segment_id']} failed — segment will be silent")
        segments[i]["tts_path"] = tts_path

    # ── Step 5: Assemble final video ──────────────────────────────────────────
    print("\n── Step 5/5: Assembling video (FFmpeg) ──")
    _step(
        "Video assembly",
        assemble_video,
        segments,
        title,
        scripture,
        output_path,
        music_path=music_path,
        debug=args.debug,
        dry_run=args.dry_run,
    )

    # ── Logging & cleanup ─────────────────────────────────────────────────────
    if not args.dry_run:
        duration = sum(s["duration_seconds"] for s in segments)
        log_run(
            theme=args.theme,
            title=title,
            output_path=output_path,
            duration=duration,
            segments_count=len(segments),
            status="success",
            timestamp=started_at,
        )
        _wipe_temp()

    elapsed = (datetime.now() - started_at).total_seconds()
    print()
    print("=" * 52)
    if args.dry_run:
        print("✅  Dry-run complete — no video written.")
    else:
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✅  Video ready!")
        print(f"   Output   : {output_path}")
        print(f"   Duration : {sum(s['duration_seconds'] for s in segments)}s")
        print(f"   Size     : {size_mb:.1f} MB")
    print(f"   Elapsed  : {elapsed:.1f}s")
    print("=" * 52)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a French Christian encouragement video (1080×1920, ≤ 90s)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--theme",
        required=True,
        help='Video theme in French, e.g. "Ne pas avoir peur"',
    )
    parser.add_argument(
        "--lang",
        default="fr",
        help="Language code for TTS (default: fr)",
    )
    parser.add_argument(
        "--no-music",
        action="store_true",
        help="Disable background music even if BG_MUSIC_PATH is set",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the full FFmpeg command before executing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all steps except FFmpeg execution — shows the command only",
    )

    args = parser.parse_args()

    try:
        run(args)
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[FATAL] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
