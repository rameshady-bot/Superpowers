"""
Video generator — HeyGen (primary) / D-ID (fallback) talking-head video.
Accepts an audio file for precise lip-sync and validates output quality.
"""

import asyncio
import base64
import logging
import os
import time
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

HEYGEN_BASE = "https://api.heygen.com"
DID_BASE = "https://api.d-id.com"
COST_LOG = Path("logs/costs.log")

# Approximate costs
HEYGEN_COST_PER_MIN = 0.50
DID_COST_PER_CREDIT = 0.10  # ~1 credit per 15s of video

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
MAX_LIPSYNC_DRIFT_MS = 200
POLL_INTERVAL_S = 5
POLL_TIMEOUT_S = 600


def _log_cost(provider: str, duration_s: float) -> None:
    COST_LOG.parent.mkdir(exist_ok=True)
    if provider == "heygen":
        cost = (duration_s / 60) * HEYGEN_COST_PER_MIN
    else:
        cost = (duration_s / 15) * DID_COST_PER_CREDIT
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with COST_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {provider.upper():<10} | video_generation   | ~${cost:.4f} | duration={duration_s:.1f}s\n")
    logger.info("%s cost logged: $%.4f", provider, cost)


class VideoGenerator:
    def __init__(self) -> None:
        self._heygen_key = os.environ.get("HEYGEN_API_KEY")
        self._did_key = os.environ.get("DID_API_KEY")
        self._default_avatar = os.environ.get("HEYGEN_AVATAR_ID")
        self._did_presenter = os.environ.get("DID_PRESENTER_ID", "amy-jcwCkr1")

        if not self._heygen_key and not self._did_key:
            raise EnvironmentError("Neither HEYGEN_API_KEY nor DID_API_KEY is set")

    async def generate(self, audio_path: Path, output_path: Path, avatar_id: str | None = None) -> Path:
        """Generate talking-head video with lip-sync from audio_path."""
        if self._heygen_key:
            try:
                return await self._generate_heygen(audio_path, output_path, avatar_id)
            except Exception as exc:
                logger.warning("HeyGen failed (%s) — falling back to D-ID", exc)

        if not self._did_key:
            raise RuntimeError("HeyGen failed and DID_API_KEY is not configured")
        return await self._generate_did(audio_path, output_path)

    # ── HeyGen ───────────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16), reraise=True)
    async def _generate_heygen(self, audio_path: Path, output_path: Path, avatar_id: str | None) -> Path:
        avatar = avatar_id or self._default_avatar
        if not avatar:
            raise EnvironmentError("HEYGEN_AVATAR_ID not set and no --avatar provided")

        audio_b64 = base64.b64encode(audio_path.read_bytes()).decode()
        headers = {
            "X-Api-Key": self._heygen_key,
            "Content-Type": "application/json",
        }
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": None,
                        "audio_base64": audio_b64,
                        "audio_format": "mp3",
                    },
                }
            ],
            "dimension": {"width": TARGET_WIDTH, "height": TARGET_HEIGHT},
            "aspect_ratio": "9:16",
        }

        logger.info("Submitting HeyGen job (avatar=%s)", avatar)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{HEYGEN_BASE}/v2/video/generate",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            video_id = resp.json()["data"]["video_id"]

        logger.info("HeyGen job submitted: video_id=%s", video_id)
        video_url = await self._poll_heygen(video_id, headers)
        await self._download_video(video_url, output_path)

        # Basic validation
        duration_s = await self._get_video_duration(output_path)
        _log_cost("heygen", duration_s)
        self._validate_output(output_path, duration_s)
        return output_path

    async def _poll_heygen(self, video_id: str, headers: dict) -> str:
        deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT_S
        async with httpx.AsyncClient(timeout=30.0) as client:
            while asyncio.get_event_loop().time() < deadline:
                resp = await client.get(
                    f"{HEYGEN_BASE}/v1/video_status.get",
                    headers=headers,
                    params={"video_id": video_id},
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                status = data.get("status")
                logger.info("HeyGen status: %s", status)
                if status == "completed":
                    return data["video_url"]
                if status in ("failed", "error"):
                    raise RuntimeError(f"HeyGen job failed: {data.get('error')}")
                await asyncio.sleep(POLL_INTERVAL_S)
        raise TimeoutError(f"HeyGen job did not complete within {POLL_TIMEOUT_S}s")

    # ── D-ID ─────────────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16), reraise=True)
    async def _generate_did(self, audio_path: Path, output_path: Path) -> Path:
        audio_b64 = base64.b64encode(audio_path.read_bytes()).decode()
        auth = base64.b64encode(f"{self._did_key}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
        }
        payload = {
            "source_url": f"https://create-images-results.d-id.com/{self._did_presenter}",
            "script": {
                "type": "audio",
                "audio_url": None,
                "ssml": False,
            },
            "config": {
                "fluent": True,
                "pad_audio": 0,
                "result_format": "mp4",
            },
            "audio": {
                "type": "base64",
                "format": "mp3",
                "data": audio_b64,
            },
        }

        logger.info("Submitting D-ID job (presenter=%s)", self._did_presenter)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{DID_BASE}/talks", headers=headers, json=payload)
            resp.raise_for_status()
            talk_id = resp.json()["id"]

        logger.info("D-ID job submitted: talk_id=%s", talk_id)
        video_url = await self._poll_did(talk_id, headers)
        await self._download_video(video_url, output_path)

        duration_s = await self._get_video_duration(output_path)
        _log_cost("d-id", duration_s)
        self._validate_output(output_path, duration_s)
        return output_path

    async def _poll_did(self, talk_id: str, headers: dict) -> str:
        deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT_S
        async with httpx.AsyncClient(timeout=30.0) as client:
            while asyncio.get_event_loop().time() < deadline:
                resp = await client.get(f"{DID_BASE}/talks/{talk_id}", headers=headers)
                resp.raise_for_status()
                data = resp.json()
                status = data.get("status")
                logger.info("D-ID status: %s", status)
                if status == "done":
                    return data["result_url"]
                if status == "error":
                    raise RuntimeError(f"D-ID job failed: {data.get('error')}")
                await asyncio.sleep(POLL_INTERVAL_S)
        raise TimeoutError(f"D-ID job did not complete within {POLL_TIMEOUT_S}s")

    # ── Shared helpers ───────────────────────────────────────────────────────

    async def _download_video(self, url: str, output_path: Path) -> None:
        logger.info("Downloading video from %s", url)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with output_path.open("wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
        logger.info("Video downloaded: %s", output_path)

    async def _get_video_duration(self, video_path: Path) -> float:
        """Use ffprobe to get video duration in seconds."""
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(video_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        import json
        data = json.loads(stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return float(stream.get("duration", 0))
        return 0.0

    def _validate_output(self, video_path: Path, duration_s: float) -> None:
        """Raise if output video doesn't meet minimum quality bars."""
        if not video_path.exists() or video_path.stat().st_size < 100_000:
            raise ValueError(f"Output video missing or too small: {video_path}")
        if duration_s < 5:
            raise ValueError(f"Video duration too short: {duration_s}s")
        if duration_s > 65:
            logger.warning("Video duration %s exceeds 60s TikTok limit", duration_s)
        logger.info("Video validation passed: duration=%.1fs path=%s", duration_s, video_path)
