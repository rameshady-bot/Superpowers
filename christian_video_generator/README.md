# Christian Encouragement Video Generator

Automated pipeline that turns a single French theme phrase into a
vertical 1080×1920 MP4 (≤ 90 s) — combining AI-written script,
Pexels nature footage, French TTS voice-over, Scripture overlay,
and optional background music.

## Architecture

```
christian_video_generator/
├── main.py                   ← CLI entry point
├── pipeline/
│   ├── content_generator.py  ← Anthropic API → JSON script
│   ├── pexels_fetcher.py     ← Pexels API → nature MP4 clips
│   ├── tts_generator.py      ← gTTS → French MP3 voice-overs
│   ├── video_assembler.py    ← FFmpeg → final 1080×1920 MP4
│   └── logger.py             ← openpyxl → output/videos_log.xlsx
├── output/                   ← final videos + Excel log (never deleted)
├── temp/                     ← intermediate files (wiped on success)
├── assets/                   ← optional: background music MP3
├── requirements.txt
└── .env.example
```

## Setup

### 1 — Clone and install dependencies

```bash
git clone <repo-url>
cd christian_video_generator
pip install -r requirements.txt
```

### 2 — Install FFmpeg

**Ubuntu / Debian**
```bash
sudo apt-get install -y ffmpeg
```

**macOS**
```bash
brew install ffmpeg
```

**Windows** — Download from https://ffmpeg.org/download.html and add to PATH.

### 3 — Get a free Pexels API key

1. Go to https://www.pexels.com/api/
2. Sign up for a free account
3. Click **"Your API Key"** in the dashboard
4. Copy the key — the free tier allows 200 requests/hour and 20 000/month

### 4 — Get an Anthropic API key

1. Go to https://console.anthropic.com/
2. Create an account and navigate to **API Keys**
3. Create a new key and copy it

### 5 — Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your keys:
nano .env
```

`.env` contents:

```ini
PEXELS_API_KEY=your_pexels_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional background music (royalty-free MP3)
# BG_MUSIC_PATH=/absolute/path/to/music.mp3
```

> **Never commit `.env` to git.** It is listed in `.gitignore`.

---

## Usage

### Basic run

```bash
python main.py --theme "Ne pas avoir peur"
```

### With all options

```bash
python main.py \
  --theme "La paix de Dieu" \
  --lang fr \
  --no-music \
  --debug
```

### Dry-run (shows FFmpeg command, skips execution)

```bash
python main.py --theme "L'amour de Dieu" --dry-run
```

### CLI flags

| Flag | Description |
|---|---|
| `--theme TEXT` | **(required)** Video theme in French |
| `--lang CODE` | TTS language code (default: `fr`) |
| `--no-music` | Skip background music even if `BG_MUSIC_PATH` is set |
| `--debug` | Print the full FFmpeg command before running it |
| `--dry-run` | Run all steps except FFmpeg — shows command only |

---

## Output

- **Video**: `output/video_{theme_slug}_{YYYYMMDD_HHMMSS}.mp4`
- **Log**: `output/videos_log.xlsx` (one row per run, never overwritten)

---

## API limits

| Service | Free tier |
|---|---|
| Pexels | 200 req/hour, 20 000/month |
| Anthropic | Pay-per-token (see console.anthropic.com) |

The pipeline enforces a hard cap of **15 Pexels API calls per run** and
raises `RuntimeError` if this would be exceeded.

---

## Troubleshooting

**`PEXELS_API_KEY is not set`** — Make sure `.env` exists and contains the key,
or `export PEXELS_API_KEY=...` before running.

**`gTTS 403 Forbidden`** — This happens when Google TTS is rate-limited or
network access is blocked.  The pipeline continues with silent segments and does
not crash.

**`FFmpeg failed`** — Run with `--debug` to see the full command and
stderr output.

**Font not found** — Override `FONT_BOLD` and `FONT_ITALIC` in `.env` with
paths to `.ttf` files present on your system.
