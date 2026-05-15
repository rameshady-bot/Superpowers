"""Runtime configuration — values can be overridden via environment variables."""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

for _d in (ASSETS_DIR, OUTPUT_DIR, TEMP_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── API keys ───────────────────────────────────────────────────────────────────
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# ── Video dimensions ───────────────────────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
MAX_DURATION_S = 90          # hard ceiling for the final video
CLIP_DURATION_S = 15         # target duration per nature clip

# ── Voice-over ─────────────────────────────────────────────────────────────────
TTS_LANG = "fr"              # French
TTS_SLOW = False

# ── FFmpeg ─────────────────────────────────────────────────────────────────────
FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_BIN", "ffprobe")
VIDEO_BITRATE = "4M"
AUDIO_BITRATE = "192k"

# ── Music ──────────────────────────────────────────────────────────────────────
# Optional: point to a local royalty-free MP3.  Leave empty to skip background music.
BG_MUSIC_PATH = os.getenv("BG_MUSIC_PATH", str(ASSETS_DIR / "background_music.mp3"))
BG_MUSIC_VOLUME = 0.25       # relative to voice-over (1.0 = equal)

# ── Text overlay ───────────────────────────────────────────────────────────────
FONT_PATH = os.getenv(
    "FONT_PATH",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
FONT_SIZE = 52
FONT_COLOR = "white"
TEXT_BOX_COLOR = "black@0.55"
TEXT_MARGIN = 60             # px from left/right edges
