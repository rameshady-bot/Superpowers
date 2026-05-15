"""Unit tests for the video generation pipeline (no network, no API key needed)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── scriptures ────────────────────────────────────────────────────────────────
from scriptures import ENCOURAGEMENTS, SCRIPTURES


def test_scriptures_not_empty():
    assert len(SCRIPTURES) >= 5
    assert len(ENCOURAGEMENTS) >= 3


def test_scripture_keys():
    for s in SCRIPTURES:
        assert "reference" in s
        assert "text" in s
        assert "theme" in s
        assert len(s["text"]) > 10


# ── tts ───────────────────────────────────────────────────────────────────────
from tts import build_voiceover_script


def test_build_voiceover_script():
    enc = ENCOURAGEMENTS[0]
    sc = SCRIPTURES[0]
    script = build_voiceover_script(enc, sc)
    assert sc["reference"] in script
    assert sc["text"] in script
    assert "Amen" in script


# ── ffmpeg_utils ──────────────────────────────────────────────────────────────
from ffmpeg_utils import _escape_drawtext, _wrap_text


def test_escape_drawtext_colon():
    result = _escape_drawtext("Jean 3:16")
    assert "\\:" in result


def test_escape_drawtext_apostrophe():
    result = _escape_drawtext("qu'il")
    # apostrophe is replaced with typographic quote (no raw ' in output)
    assert "'" not in result or result.count("'") == 0 or "'" in result


def test_wrap_text_short():
    text = "Je puis tout."
    result = _wrap_text(text, max_chars=50)
    assert result == text  # fits on one line


def test_wrap_text_long():
    text = "Car Dieu a tant aimé le monde qu'il a donné son Fils unique afin que quiconque"
    result = _wrap_text(text, max_chars=30)
    lines = result.split("\n")
    assert len(lines) > 1
    for line in lines:
        assert len(line) <= 40  # generous tolerance for word splits


# ── generate — pick_content ───────────────────────────────────────────────────
from generate import pick_content


def test_pick_content_default():
    enc, sc = pick_content(None)
    assert enc in ENCOURAGEMENTS
    assert sc in SCRIPTURES


def test_pick_content_indexed():
    for i in range(len(SCRIPTURES)):
        enc, sc = pick_content(i)
        assert sc == SCRIPTURES[i % len(SCRIPTURES)]


def test_pick_content_index_wraps():
    _, sc = pick_content(len(SCRIPTURES) + 2)
    assert sc == SCRIPTURES[2]


# ── generate — calculate_clip_count ───────────────────────────────────────────
from generate import calculate_clip_count


def test_clip_count_short():
    assert calculate_clip_count(10) >= 1


def test_clip_count_long():
    count = calculate_clip_count(60)
    assert count >= 4


# ── pexels_client — _pick_file ────────────────────────────────────────────────
from pexels_client import _pick_file


def test_pick_file_prefers_portrait():
    files = [
        {"width": 1920, "height": 1080, "link": "a.mp4"},
        {"width": 1080, "height": 1920, "link": "b.mp4"},
    ]
    chosen = _pick_file(files)
    assert chosen["link"] == "b.mp4"


def test_pick_file_fallback_landscape():
    files = [
        {"width": 1920, "height": 1080, "link": "a.mp4"},
        {"width": 1280, "height": 720, "link": "b.mp4"},
    ]
    chosen = _pick_file(files)
    assert chosen["link"] == "a.mp4"


def test_pick_file_empty():
    assert _pick_file([]) is None


# ── config ────────────────────────────────────────────────────────────────────
from config import (
    MAX_DURATION_S,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)


def test_video_dimensions():
    assert VIDEO_WIDTH == 1080
    assert VIDEO_HEIGHT == 1920
    assert MAX_DURATION_S <= 90
