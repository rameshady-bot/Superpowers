# TikTok Christian Video Generator

Automated pipeline for generating short-form faith-based video content in French, optimized for TikTok's algorithm. Produces realistic talking-head videos with burned-in captions from a single CLI command.

---

## Architecture

```
main.py (orchestrator)
├── modules/script_generator.py     ← Claude API → 150–200 word French scripts
├── modules/audio_generator.py      ← ElevenLabs → warm French voiceover MP3
├── modules/video_generator.py      ← HeyGen (primary) / D-ID (fallback) → lip-sync video
├── modules/caption_burner.py       ← Whisper + FFmpeg → burned-in subtitles
├── modules/content_calendar.py     ← SQLite → theme/verse deduplication tracking
└── modules/metadata_builder.py     ← title, hashtags, optimal post time JSON
```

---

## Required API Accounts

| Service | Purpose | Signup |
|---------|---------|--------|
| **Anthropic** | Script generation (Claude) | platform.anthropic.com |
| **ElevenLabs** | French voiceover synthesis | elevenlabs.io |
| **HeyGen** | Talking-head video (primary) | heygen.com |
| **D-ID** | Talking-head video (fallback) | d-id.com |

---

## Prerequisites

- Python 3.11+
- FFmpeg installed and on PATH: `ffmpeg -version`
- openai-whisper (requires torch): installed via requirements.txt

```bash
# Install FFmpeg (Ubuntu/Debian)
sudo apt install ffmpeg

# Install FFmpeg (macOS)
brew install ffmpeg
```

---

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd Superpowers

# 2. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and fill in your API keys

# 5. Run the pipeline
python main.py --theme "anxiété" --verse "Phil 4:6"
```

---

## CLI Reference

```bash
python main.py --theme "THEME" --verse "VERSE_REF"

# Options:
#   --theme     Topic/emotion to address (e.g. "anxiété", "solitude", "espoir")
#   --verse     Bible verse reference (e.g. "Phil 4:6", "Ps 23:1", "Rom 8:28")
#   --dry-run   Generate script and audio only, skip video (no API cost for video)
#   --date      Override output date folder (default: today, format YYYY-MM-DD)
#   --avatar    HeyGen avatar ID to use (overrides default from .env)
```

---

## Output Structure

Each run produces a dated folder:

```
output/
└── 2024-01-15/
    ├── script.txt                    ← Generated French script
    ├── audio.mp3                     ← ElevenLabs voiceover
    ├── raw_video.mp4                 ← HeyGen/D-ID talking-head (1080×1920)
    ├── final_video_with_captions.mp4 ← FFmpeg-burned captions, ready for review
    └── metadata.json                 ← Title, hashtags, optimal post times
```

---

## .env Template

```env
# Anthropic (Claude) — script generation
ANTHROPIC_API_KEY=sk-ant-...

# ElevenLabs — voiceover
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...        # French voice ID from your ElevenLabs account

# HeyGen — primary video generation
HEYGEN_API_KEY=...
HEYGEN_AVATAR_ID=...           # Licensed avatar ID from HeyGen

# D-ID — fallback video generation
DID_API_KEY=...
DID_PRESENTER_ID=amy-jcwCkr1   # Default D-ID presenter

# Optional overrides
MAX_RETRIES=3                  # API retry attempts (default: 3)
LOG_LEVEL=INFO                 # DEBUG | INFO | WARNING
```

See `.env.example` for the full template.

---

## Content Calendar

A SQLite database (`content_calendar.db`) tracks all generated content.

```bash
# View recent entries
python -c "from modules.content_calendar import ContentCalendar; ContentCalendar().show_recent()"

# Update engagement score after posting
python -c "
from modules.content_calendar import ContentCalendar
ContentCalendar().update_engagement('2024-01-15', score=8.5)
"
```

The pipeline **warns** (and stops) if the same verse or theme was used in the last 14 days.

---

## Optimal Posting Times (FR Christian Audience)

Based on TikTok engagement data for French faith-based content:

| Slot | Day | Time (CET) | Rationale |
|------|-----|-----------|-----------|
| 1 | Sunday | 09:00–10:00 | Pre-church / morning devotion |
| 2 | Wednesday | 12:00–13:00 | Midweek encouragement |
| 3 | Friday | 18:30–19:30 | End-of-week wind-down |

These are embedded in every `metadata.json` output.

---

## Logs & Cost Tracking

All API calls and cost estimates are logged to `logs/costs.log`:

```
2024-01-15 09:12:01 | ANTHROPIC  | script_generation  | ~$0.003
2024-01-15 09:12:08 | ELEVENLABS | audio_generation   | ~$0.015
2024-01-15 09:12:45 | HEYGEN     | video_generation   | ~$0.500
```

---

## Human Review Gate

The pipeline **always stops before marking a video as final**. You will be prompted:

```
============================================================
  HUMAN REVIEW REQUIRED
  Video: output/2024-01-15/final_video_with_captions.mp4
  Duration: 42s | Resolution: 1080x1920 | Lip-sync: PASS
  
  Please review the video before marking it ready to post.
  Approve? [y/N]:
============================================================
```

Only after manual approval is `metadata.json` updated with `"status": "approved"`.

---

## License

MIT
