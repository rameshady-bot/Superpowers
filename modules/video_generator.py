"""
Video generator — priority order:
  1. SadTalker (local, 100% free, needs GPU or CPU)
  2. D-ID free tier (5 free videos at signup)
  3. HeyGen free tier (1 credit at signup)

SadTalker setup: https://github.com/OpenTalker/SadTalker
  git clone https://github.com/OpenTalker/SadTalker.git
  cd SadTalker && pip install -r requirements.txt
  bash scripts/download_models.sh
  Set SADTALKER_PATH and SOURCE_IMAGE_PATH in .env
"""

import asyncio
import base64
import json
import logging
import os
import shutil
import time
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

HEYGEN_BASE = "https://api.heygen.com"
DID_BASE = "https://api.d-id.com"
COST_LOG = Path("logs/costs.log")

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
POLL_INTERVAL_S = 5
POLL_TIMEOUT_S = 600


def _log_cost(provider: str, cost: float, note: str = "") -> None:
    COST_LOG.parent.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with COST_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {provider.upper():<10} | video_generation   | ~${cost:.4f} | {note}\n")


class VideoGenerator:
    def __init__(self) -> None:
        self._sadtalker_path = os.environ.get("SADTALKER_PATH")
        self._source_image = os.environ.get("SOURCE_IMAGE_PATH")
        self._heygen_key = os.environ.get("HEYGEN_API_KEY")
        self._did_key = os.environ.get("DID_API_KEY")
        self._default_avatar = os.environ.get("HEYGEN_AVATAR_ID")
        self._did_presenter = os.environ.get("DID_PRESENTER_ID", "amy-jcwCkr1")

        if not self._sadtalker_path and not self._heygen_key and not self._did_key:
            raise EnvironmentError(
                "No video backend configured. Set SADTALKER_PATH (free) or "
                "HEYGEN_API_KEY / DID_API_KEY in .env"
            )

    async def generate(self, audio_path: Path, output_path: Path, avatar_id: str | None = None) -> Path:
        """Generate talking-head video. Tries free options first."""

        # ── 1. SadTalker (local, free) ──────────────────────────────────────
        if self._sadtalker_path:
            try:
                return await self._generate_sadtalker(audio_path, output_path)
            except Exception as exc:
                logger.warning("SadTalker failed (%s) — trying cloud fallback", exc)

        # ── 2. D-ID free tier ───────────────────────────────────────────────
        if self._did_key:
            try:
                return await self._generate_did(audio_path, output_path)
            except Exception as exc:
                logger.warning("D-ID failed (%s) — trying HeyGen", exc)

        # ── 3. HeyGen free tier ─────────────────────────────────────────────
        if self._heygen_key:
            return await self._generate_heygen(audio_path, output_path, avatar_id)

        raise RuntimeError("All video backends failed or are unconfigured.")

    # ── SadTalker ────────────────────────────────────────────────────────────

    async def _generate_sadtalker(self, audio_path: Path, output_path: Path) -> Path:
        sadtalker_dir = Path(self._sadtalker_path)
        if not sadtalker_dir.exists():
            raise FileNotFoundError(f"SADTALKER_PATH does not exist: {sadtalker_dir}")

        if not self._source_image:
            raise EnvironmentError("SOURCE_IMAGE_PATH not set — SadTalker needs a face photo")
        source_image = Path(self._source_image)
        if not source_image.exists():
            raise FileNotFoundError(f"SOURCE_IMAGE_PATH does not exist: {source_image}")

        # SadTalker outputs into a subfolder named by the image stem
        result_dir = output_path.parent / "sadtalker_tmp"
        result_dir.mkdir(parents=True, exist_ok=True)

        # Convert MP3 → WAV (SadTalker works better with WAV)
        wav_path = audio_path.with_suffix(".wav")
        await self._mp3_to_wav(audio_path, wav_path)

        python_bin = shutil.which("python") or "python3"
        cmd = [
            python_bin,
            str(sadtalker_dir / "inference.py"),
            "--driven_audio", str(wav_path),
            "--source_image", str(source_image),
            "--result_dir", str(result_dir),
            "--still",           # Less head movement — better for TikTok talking-head style
            "--preprocess", "full",
            "--face3dvis",
        ]

        logger.info("Running SadTalker: %s", " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(sadtalker_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)

        if proc.returncode != 0:
            raise RuntimeError(f"SadTalker failed:\n{stderr.decode(errors='replace')[-2000:]}")

        # Find generated video (SadTalker names it by timestamp)
        generated = sorted(result_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not generated:
            raise RuntimeError("SadTalker produced no MP4 output")
        raw = generated[-1]

        # Resize + letterbox to 1080×1920 (SadTalker outputs landscape by default)
        await self._reframe_to_vertical(raw, output_path)
        shutil.rmtree(result_dir, ignore_errors=True)
        wav_path.unlink(missing_ok=True)

        duration_s = await self._get_video_duration(output_path)
        _log_cost("sadtalker", 0.0, f"local free | duration={duration_s:.1f}s")
        self._validate_output(output_path, duration_s)
        logger.info("SadTalker video ready: %s", output_path)
        return output_path

    async def _mp3_to_wav(self, mp3: Path, wav: Path) -> None:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", str(mp3), str(wav),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()

    async def _reframe_to_vertical(self, src: Path, dst: Path) -> None:
        """Scale and pad the SadTalker output to 1080×1920 (9:16 vertical)."""
        import ffmpeg as ffmpeg_mod
        loop = asyncio.get_event_loop()

        def _run() -> None:
            (
                ffmpeg_mod.input(str(src))
                .output(
                    str(dst),
                    vf=(
                        "scale=1080:1920:force_original_aspect_ratio=decrease,"
                        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
                    ),
                    vcodec="libx264",
                    acodec="aac",
                    crf=18,
                    preset="fast",
                    movflags="+faststart",
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

        await loop.run_in_executor(None, _run)

    # ── D-ID free tier ────────────────────────────────────────────────────────

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
            "script": {"type": "audio", "ssml": False},
            "config": {"fluent": True, "pad_audio": 0, "result_format": "mp4"},
            "audio": {"type": "base64", "format": "mp3", "data": audio_b64},
        }

        logger.info("Submitting D-ID job (free tier, presenter=%s)", self._did_presenter)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{DID_BASE}/talks", headers=headers, json=payload)
            resp.raise_for_status()
            talk_id = resp.json()["id"]

        video_url = await self._poll_did(talk_id, headers)
        await self._download_video(video_url, output_path)

        duration_s = await self._get_video_duration(output_path)
        # D-ID free tier: ~5 free videos then $0.10/credit
        _log_cost("d-id", 0.0, f"free-tier | duration={duration_s:.1f}s")
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

    # ── HeyGen free tier ──────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=16), reraise=True)
    async def _generate_heygen(self, audio_path: Path, output_path: Path, avatar_id: str | None) -> Path:
        avatar = avatar_id or self._default_avatar
        if not avatar:
            raise EnvironmentError("HEYGEN_AVATAR_ID not set and no --avatar provided")

        audio_b64 = base64.b64encode(audio_path.read_bytes()).decode()
        headers = {"X-Api-Key": self._heygen_key, "Content-Type": "application/json"}
        payload = {
            "video_inputs": [{
                "character": {"type": "avatar", "avatar_id": avatar, "avatar_style": "normal"},
                "voice": {"type": "audio", "audio_base64": audio_b64, "audio_format": "mp3"},
            }],
            "dimension": {"width": TARGET_WIDTH, "height": TARGET_HEIGHT},
            "aspect_ratio": "9:16",
        }

        logger.info("Submitting HeyGen job (free tier, avatar=%s)", avatar)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{HEYGEN_BASE}/v2/video/generate", headers=headers, json=payload)
            resp.raise_for_status()
            video_id = resp.json()["data"]["video_id"]

        video_url = await self._poll_heygen(video_id, headers)
        await self._download_video(video_url, output_path)

        duration_s = await self._get_video_duration(output_path)
        _log_cost("heygen", 0.0, f"free-tier | duration={duration_s:.1f}s")
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
                if status == "completed":
                    return data["video_url"]
                if status in ("failed", "error"):
                    raise RuntimeError(f"HeyGen job failed: {data.get('error')}")
                await asyncio.sleep(POLL_INTERVAL_S)
        raise TimeoutError(f"HeyGen job did not complete within {POLL_TIMEOUT_S}s")

    # ── Shared helpers ────────────────────────────────────────────────────────

    async def _download_video(self, url: str, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with output_path.open("wb") as f:
                    async for chunk in resp.aiter_bytes(8192):
                        f.write(chunk)
        logger.info("Video downloaded: %s", output_path)

    async def _get_video_duration(self, video_path: Path) -> float:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(video_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        data = json.loads(stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return float(stream.get("duration", 0))
        return 0.0

    def _validate_output(self, video_path: Path, duration_s: float) -> None:
        if not video_path.exists() or video_path.stat().st_size < 100_000:
            raise ValueError(f"Output video missing or too small: {video_path}")
        if duration_s < 5:
            raise ValueError(f"Video duration too short: {duration_s}s")
        if duration_s > 65:
            logger.warning("Video duration %.1fs exceeds 60s TikTok limit", duration_s)
        logger.info("Video validation passed: duration=%.1fs path=%s", duration_s, video_path)
