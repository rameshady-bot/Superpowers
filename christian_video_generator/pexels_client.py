"""Pexels API client — fetches vertical nature video clips."""

import json
import os
import time
from pathlib import Path

import requests

from config import PEXELS_API_KEY, TEMP_DIR, VIDEO_HEIGHT, VIDEO_WIDTH

_BASE = "https://api.pexels.com/videos"

NATURE_QUERIES = [
    "nature sunrise",
    "mountain landscape",
    "ocean waves",
    "forest light",
    "river stream",
    "field flowers",
    "waterfall nature",
    "sky clouds",
    "green forest",
    "peaceful lake",
]


def _headers() -> dict:
    if not PEXELS_API_KEY:
        raise EnvironmentError(
            "PEXELS_API_KEY is not set. "
            "Export it before running: export PEXELS_API_KEY=your_key"
        )
    return {"Authorization": PEXELS_API_KEY}


def _pick_file(video_files: list[dict]) -> dict | None:
    """Return the best available file — prefer portrait, else landscape HD."""
    portrait = [
        f for f in video_files
        if f.get("width", 0) < f.get("height", 0)
        and f.get("height", 0) >= 1080
    ]
    if portrait:
        return max(portrait, key=lambda f: f.get("height", 0))

    hd = [f for f in video_files if f.get("height", 0) >= 720]
    if hd:
        return max(hd, key=lambda f: f.get("width", 0))

    return video_files[0] if video_files else None


def search_videos(query: str, per_page: int = 5) -> list[dict]:
    """Return raw Pexels video objects for *query*."""
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": "portrait",
        "size": "large",
    }
    resp = requests.get(f"{_BASE}/search", headers=_headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("videos", [])


def download_clip(video: dict, dest_dir: Path = TEMP_DIR) -> Path | None:
    """Download the best file from a Pexels video object, return local path."""
    chosen = _pick_file(video.get("video_files", []))
    if not chosen:
        return None

    url = chosen["link"]
    ext = url.split("?")[0].rsplit(".", 1)[-1] or "mp4"
    filename = dest_dir / f"pexels_{video['id']}.{ext}"

    if filename.exists() and filename.stat().st_size > 0:
        return filename

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(filename, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)

    return filename


def fetch_clips(
    num_clips: int = 4,
    queries: list[str] | None = None,
) -> list[Path]:
    """
    Fetch *num_clips* unique nature clips from Pexels.

    Cycles through *queries* until enough clips are collected or queries
    are exhausted.  Returns local file paths.
    """
    queries = queries or NATURE_QUERIES
    collected: list[Path] = []
    seen_ids: set[int] = set()

    for query in queries:
        if len(collected) >= num_clips:
            break
        try:
            videos = search_videos(query, per_page=5)
        except Exception as exc:
            print(f"  [pexels] search failed for '{query}': {exc}")
            continue

        for video in videos:
            if len(collected) >= num_clips:
                break
            vid_id = video.get("id")
            if vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)

            print(f"  [pexels] downloading clip {len(collected)+1}/{num_clips} "
                  f"(id={vid_id}, query='{query}') …")
            try:
                path = download_clip(video)
                if path:
                    collected.append(path)
            except Exception as exc:
                print(f"  [pexels] download failed: {exc}")

        time.sleep(0.5)  # be polite to the API

    return collected
