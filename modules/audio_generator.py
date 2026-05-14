"""
Audio generator — ElevenLabs API to produce warm French voiceover at 130–145 WPM.
"""

import logging
import os
import time
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
COST_LOG = Path("logs/costs.log")

# ElevenLabs pricing: ~$0.30 per 1000 chars (Starter plan)
COST_PER_CHAR = 0.00030


def _log_cost(char_count: int, voice_id: str) -> None:
    COST_LOG.parent.mkdir(exist_ok=True)
    cost = char_count * COST_PER_CHAR
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with COST_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | ELEVENLABS | audio_generation   | ~${cost:.4f} | voice={voice_id} | chars={char_count}\n")
    logger.info("ElevenLabs cost logged: $%.4f", cost)


class AudioGenerator:
    def __init__(self) -> None:
        self._api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise EnvironmentError("ELEVENLABS_API_KEY not set in environment")

        self._voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
        if not self._voice_id:
            raise EnvironmentError("ELEVENLABS_VOICE_ID not set in environment")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        reraise=True,
    )
    async def generate(self, script: str, output_path: Path) -> Path:
        """Synthesize speech from script and write MP3 to output_path."""
        logger.info("Generating audio: %d chars, voice=%s", len(script), self._voice_id)

        url = f"{ELEVENLABS_BASE}/text-to-speech/{self._voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.55,        # Warm, natural variation
                "similarity_boost": 0.75,
                "style": 0.35,            # Slightly expressive but not theatrical
                "use_speaker_boost": True,
                # speed is controlled by stability + pacing; ~0.9x for 130–145 WPM
            },
            "output_format": "mp3_44100_128",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        _log_cost(char_count=len(script), voice_id=self._voice_id)
        logger.info("Audio saved: %s (%d bytes)", output_path, len(response.content))

        return output_path

    async def get_available_voices(self) -> list[dict]:
        """Return voices list for voice selection/debugging."""
        url = f"{ELEVENLABS_BASE}/voices"
        headers = {"xi-api-key": self._api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        return response.json().get("voices", [])
