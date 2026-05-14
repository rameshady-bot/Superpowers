import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_MODE = os.getenv("TIKTOK_MODE", "playwright")

VOICE_NAME = os.getenv("VOICE_NAME", "fr-FR-DeniseNeural")
VIDEO_LANGUAGE = os.getenv("VIDEO_LANGUAGE", "fr")

ASSETS_DIR = BASE_DIR / os.getenv("ASSETS_DIR", "assets")
TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
SESSIONS_DIR = BASE_DIR / os.getenv("SESSIONS_DIR", "sessions")
LOGS_DIR = BASE_DIR / os.getenv("LOGS_DIR", "logs")

for d in [ASSETS_DIR, TEMP_DIR, OUTPUT_DIR, SESSIONS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

SUBTITLE_FONT_SIZE = 70
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_STROKE_WIDTH = 3
