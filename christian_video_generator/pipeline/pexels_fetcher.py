"""
Pexels video fetcher.

Downloads portrait nature clips for each script segment.
Enforces a hard limit of 15 API calls per process invocation.
"""

import os
from pathlib import Path

import requests

_SEARCH_URL = "https://api.pexels.com/videos/search"
_FALLBACK_KEYWORD = "nature sunrise"
_MAX_API_CALLS = 15

# Module-level counter — shared across all calls in a single run.
_api_calls_made: int = 0


def _headers() -> dict:
    key = os.environ.get("PEXELS_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "PEXELS_API_KEY is not set. "
            "Add it to your .env file or export it before running."
        )
    return {"Authorization": key}


def _check_quota() -> None:
    global _api_calls_made
    if _api_calls_made >= _MAX_API_CALLS:
        raise RuntimeError(
            f"Pexels API call limit reached ({_MAX_API_CALLS} calls per run). "
            "Aborting to avoid excessive API usage."
        )


def _search(keyword: str, min_duration: int) -> dict | None:
    """
    Search Pexels for a portrait video matching *keyword* with
    duration >= min_duration.  Returns a Pexels video object or None.
    """
    global _api_calls_made
    _check_quota()

    params = {
        "query": keyword,
        "per_page": 5,
        "orientation": "portrait",
    }
    resp = requests.get(_SEARCH_URL, headers=_headers(), params=params, timeout=30)
    _api_calls_made += 1
    resp.raise_for_status()

    videos = resp.json().get("videos", [])
    result_count = len(videos)

    chosen = None
    for v in videos:
        if v.get("duration", 0) >= min_duration - 2:
            chosen = v
            break

    vid_id = chosen["id"] if chosen else None
    print(
        f"  [pexels] search '{keyword}' → {result_count} results, "
        f"selected id={vid_id} (call {_api_calls_made}/{_MAX_API_CALLS})"
    )
    return chosen


def _best_file(video: dict) -> str | None:
    """Return the download URL of the best portrait-friendly video file."""
    files = video.get("video_files", [])

    # Prefer portrait files with height >= 1080
    portrait = [
        f for f in files
        if f.get("width", 0) < f.get("height", 0) and f.get("height", 0) >= 1080
    ]
    if portrait:
        return max(portrait, key=lambda f: f.get("height", 0))["link"]

    # Fall back to best available landscape (FFmpeg will crop)
    hd = [f for f in files if f.get("height", 0) >= 720]
    if hd:
        return max(hd, key=lambda f: f.get("height", 0) * f.get("width", 0))["link"]

    return files[0]["link"] if files else None


def _download(url: str, dest: Path) -> None:
    """Stream-download video to *dest*."""
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)


def fetch_clip(keyword: str, duration_seconds: int, segment_id: int) -> Path:
    """
    Fetch one portrait video clip matching *keyword* and *duration_seconds*.

    Falls back to 'nature sunrise' if no match found for the original keyword.
    Raises RuntimeError if neither keyword yields a usable clip.
    Raises RuntimeError if the 15-call limit would be exceeded.

    Returns the local path of the downloaded MP4.
    """
    temp_dir = Path(__file__).parent.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dest = temp_dir / f"clip_{segment_id}.mp4"

    # Skip download if a valid file already exists (re-run / debug scenario)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [pexels] clip_{segment_id}.mp4 already in temp — skipping download")
        return dest

    video = _search(keyword, duration_seconds)

    if video is None and keyword != _FALLBACK_KEYWORD:
        print(f"  [pexels] no match for '{keyword}' — trying fallback '{_FALLBACK_KEYWORD}'")
        video = _search(_FALLBACK_KEYWORD, duration_seconds)

    if video is None:
        raise RuntimeError(
            f"Pexels returned no usable clip for segment {segment_id} "
            f"(tried '{keyword}' and fallback '{_FALLBACK_KEYWORD}')"
        )

    url = _best_file(video)
    if not url:
        raise RuntimeError(
            f"Pexels video id={video['id']} has no downloadable files"
        )

    print(f"  [pexels] downloading segment {segment_id} from {url[:60]}…")
    _download(url, dest)
    print(f"  [pexels] saved → {dest} ({dest.stat().st_size // 1024} KB)")
    return dest
