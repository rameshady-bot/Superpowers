"""
Audio generator — priority order:
  1. ElevenLabs free tier (10 000 chars/month) — warm, natural French
  2. gTTS (Google TTS) — completely free, unlimited, decent quality for FR

Quota is tracked locally in logs/elevenlabs_quota.json (resets on the 1st of each month).
When ElevenLabs free quota is 80% used, a warning is printed.
When exhausted, falls back to gTTS automatically.
"""

import json
import logging
import os
import time
from datetime import date
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
COST_LOG = Path("logs/costs.log")
QUOTA_FILE = Path("logs/elevenlabs_quota.json")

FREE_TIER_MONTHLY_CHARS = 10_000
WARN_AT_CHARS = 8_000          # Warn at 80% of free quota


# ── Quota tracker ─────────────────────────────────────────────────────────────

def _load_quota() -> dict:
    QUOTA_FILE.parent.mkdir(exist_ok=True)
    if QUOTA_FILE.exists():
        data = json.loads(QUOTA_FILE.read_text())
        # Reset on new month
        if data.get("month") != date.today().strftime("%Y-%m"):
            return {"month": date.today().strftime("%Y-%m"), "chars_used": 0}
        return data
    return {"month": date.today().strftime("%Y-%m"), "chars_used": 0}


def _save_quota(data: dict) -> None:
    QUOTA_FILE.write_text(json.dumps(data, indent=2))


def _record_elevenlabs_usage(char_count: int) -> int:
    """Add char_count to monthly usage. Returns new total."""
    quota = _load_quota()
    quota["chars_used"] += char_count
    _save_quota(quota)
    return quota["chars_used"]


def _chars_remaining() -> int:
    quota = _load_quota()
    return max(0, FREE_TIER_MONTHLY_CHARS - quota["chars_used"])


def _log_cost(provider: str, char_count: int, voice_id: str = "") -> None:
    COST_LOG.parent.mkdir(exist_ok=True)
    cost = 0.0  # free tier
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with COST_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {provider.upper():<10} | audio_generation   | ~${cost:.4f} | chars={char_count} | voice={voice_id}\n")


# ── ElevenLabs ────────────────────────────────────────────────────────────────

class AudioGenerator:
    def __init__(self) -> None:
        self._elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        self._voice_id = os.environ.get("ELEVENLABS_VOICE_ID")

    async def generate(self, script: str, output_path: Path) -> Path:
        """
        Generate audio. Uses ElevenLabs if free quota remains, else falls back to gTTS.
        """
        remaining = _chars_remaining()
        char_count = len(script)

        if self._elevenlabs_key and self._voice_id and remaining >= char_count:
            if remaining < WARN_AT_CHARS + char_count:
                logger.warning(
                    "ElevenLabs free quota low: %d chars remaining this month", remaining
                )
            try:
                return await self._generate_elevenlabs(script, output_path)
            except Exception as exc:
                logger.warning("ElevenLabs failed (%s) — falling back to gTTS", exc)
        else:
            if self._elevenlabs_key and remaining < char_count:
                logger.warning(
                    "ElevenLabs free quota exhausted (%d chars left, need %d) — using gTTS",
                    remaining, char_count,
                )
            else:
                logger.info("ElevenLabs not configured — using gTTS (free)")

        return await self._generate_gtts(script, output_path)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16), reraise=True)
    async def _generate_elevenlabs(self, script: str, output_path: Path) -> Path:
        logger.info("ElevenLabs TTS: %d chars, voice=%s", len(script), self._voice_id)

        url = f"{ELEVENLABS_BASE}/text-to-speech/{self._voice_id}"
        headers = {
            "xi-api-key": self._elevenlabs_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.75,
                "style": 0.35,
                "use_speaker_boost": True,
            },
            "output_format": "mp3_44100_128",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        used = _record_elevenlabs_usage(len(script))
        _log_cost("elevenlabs", len(script), self._voice_id)
        logger.info(
            "ElevenLabs audio saved: %s | quota used this month: %d/%d chars",
            output_path, used, FREE_TIER_MONTHLY_CHARS,
        )
        return output_path

    async def _generate_gtts(self, script: str, output_path: Path) -> Path:
        """gTTS — Google Text-to-Speech, completely free and unlimited."""
        try:
            from gtts import gTTS
        except ImportError:
            raise RuntimeError("gTTS not installed. Run: pip install gTTS")

        logger.info("gTTS TTS: %d chars (free, no quota)", len(script))

        loop = __import__("asyncio").get_event_loop()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def _run() -> None:
            tts = gTTS(text=script, lang="fr", slow=False)
            tts.save(str(output_path))

        await loop.run_in_executor(None, _run)

        _log_cost("gtts", len(script))
        logger.info("gTTS audio saved: %s", output_path)
        return output_path

    def quota_status(self) -> dict:
        quota = _load_quota()
        used = quota["chars_used"]
        return {
            "month": quota["month"],
            "chars_used": used,
            "chars_remaining": max(0, FREE_TIER_MONTHLY_CHARS - used),
            "chars_total_free": FREE_TIER_MONTHLY_CHARS,
            "percent_used": round(used / FREE_TIER_MONTHLY_CHARS * 100, 1),
        }
