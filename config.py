import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# ── API ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ── TikTok ───────────────────────────────────────────────────────────
TIKTOK_CLIENT_KEY    = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN  = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_MODE          = os.getenv("TIKTOK_MODE", "playwright")  # "api" | "playwright"

# ── Voix (espeak-ng hors ligne) ───────────────────────────────────────
VOICE_ID   = os.getenv("VOICE_ID", "fr")          # code langue espeak-ng
VOICE_RATE = int(os.getenv("VOICE_RATE", "145"))   # mots/min
VOICE_PITCH = int(os.getenv("VOICE_PITCH", "50"))  # 0-99

# ── Vidéo ─────────────────────────────────────────────────────────────
VIDEO_WIDTH  = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS    = int(os.getenv("VIDEO_FPS", "30"))

MUSIC_VOLUME     = float(os.getenv("MUSIC_VOLUME", "0.18"))   # 0.0 → 1.0
VOICEOVER_VOLUME = float(os.getenv("VOICEOVER_VOLUME", "1.0"))

SUBTITLE_FONT_SIZE    = int(os.getenv("SUBTITLE_FONT_SIZE", "62"))
SUBTITLE_COLOR        = os.getenv("SUBTITLE_COLOR", "white")
SUBTITLE_STROKE_COLOR = os.getenv("SUBTITLE_STROKE_COLOR", "black")
SUBTITLE_STROKE_WIDTH = int(os.getenv("SUBTITLE_STROKE_WIDTH", "3"))
SUBTITLE_Y_RATIO      = float(os.getenv("SUBTITLE_Y_RATIO", "0.72"))

VERSET_FONT_SIZE = int(os.getenv("VERSET_FONT_SIZE", "44"))
VERSET_COLOR     = os.getenv("VERSET_COLOR", "#FFD700")

FONT_PATH = os.getenv(
    "FONT_PATH",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
)

# ── Dossiers ─────────────────────────────────────────────────────────
ASSETS_DIR  = BASE_DIR / os.getenv("ASSETS_DIR",  "assets")
VIDEOS_DIR  = BASE_DIR / os.getenv("VIDEOS_DIR",  "assets/videos")
MUSIC_DIR   = BASE_DIR / os.getenv("MUSIC_DIR",   "assets/music")
TEMP_DIR    = BASE_DIR / os.getenv("TEMP_DIR",    "temp")
OUTPUT_DIR  = BASE_DIR / os.getenv("OUTPUT_DIR",  "output")
SESSIONS_DIR = BASE_DIR / os.getenv("SESSIONS_DIR", "sessions")
LOGS_DIR    = BASE_DIR / os.getenv("LOGS_DIR",    "logs")

for _d in [VIDEOS_DIR, MUSIC_DIR, TEMP_DIR, OUTPUT_DIR, SESSIONS_DIR, LOGS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}
