"""
Caption burner — Whisper transcription + FFmpeg burned-in subtitles.
White bold text with black stroke, bottom-center; Bible verse highlighted in yellow.
"""

import asyncio
import json
import logging
import re
import tempfile
from pathlib import Path

import ffmpeg
import whisper

logger = logging.getLogger(__name__)

# Caption style constants
FONT_SIZE = 36
FONT_COLOR = "white"
STROKE_COLOR = "black"
STROKE_WIDTH = 2.5
VERSE_COLOR = "yellow"
MARGIN_V = 80          # px from bottom
LINE_MAX_CHARS = 42    # wrap threshold for readability


def _wrap_text(text: str, max_chars: int = LINE_MAX_CHARS) -> list[str]:
    """Word-wrap a segment's text to fit within max_chars per line."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _ts_to_ass(seconds: float) -> str:
    """Convert float seconds to ASS timestamp h:mm:ss.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _build_ass(segments: list[dict], verse: str, video_width: int = 1080, video_height: int = 1920) -> str:
    """Build an ASS subtitle file with verse segments highlighted in yellow."""

    # Normalise verse text for matching (strip ref like "Phil 4:6")
    verse_text_clean = re.sub(r"\s*\(.*?\)\s*", "", verse).strip().lower()
    verse_words = set(verse_text_clean.split())

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{FONT_SIZE},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{STROKE_WIDTH},0,2,10,10,{MARGIN_V},1
Style: Verse,Arial,{FONT_SIZE},&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{STROKE_WIDTH},0,2,10,10,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for seg in segments:
        start = _ts_to_ass(seg["start"])
        end = _ts_to_ass(seg["end"])
        text = seg["text"].strip()

        # Determine if this segment contains verse words (simple heuristic)
        seg_words = set(text.lower().split())
        is_verse = len(seg_words & verse_words) >= 3

        style = "Verse" if is_verse else "Default"
        lines = _wrap_text(text)
        ass_text = r"\N".join(lines)
        events.append(f"Dialogue: 0,{start},{end},{style},,0,0,0,,{ass_text}")

    return header + "\n".join(events) + "\n"


class CaptionBurner:
    def __init__(self, whisper_model: str = "base") -> None:
        logger.info("Loading Whisper model '%s'…", whisper_model)
        self._model = whisper.load_model(whisper_model)

    async def burn(
        self,
        video_path: Path,
        audio_path: Path,
        verse: str,
        output_path: Path,
    ) -> Path:
        """Transcribe audio with Whisper, build ASS subtitles, burn into video."""
        logger.info("Transcribing audio: %s", audio_path)

        # Whisper is CPU-bound — run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._model.transcribe(
                str(audio_path),
                language="fr",
                word_timestamps=False,
                verbose=False,
            ),
        )

        segments = result.get("segments", [])
        if not segments:
            raise RuntimeError("Whisper returned no segments — audio may be silent or corrupt")

        logger.info("Whisper transcribed %d segments", len(segments))

        # Build ASS subtitle file
        ass_content = _build_ass(segments, verse=verse)

        with tempfile.NamedTemporaryFile(suffix=".ass", mode="w", encoding="utf-8", delete=False) as tmp:
            tmp.write(ass_content)
            ass_path = Path(tmp.name)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            await self._burn_subtitles(video_path, ass_path, output_path)
        finally:
            ass_path.unlink(missing_ok=True)

        logger.info("Captioned video saved: %s", output_path)
        return output_path

    async def _burn_subtitles(self, video_path: Path, ass_path: Path, output_path: Path) -> None:
        """Run FFmpeg to hard-burn ASS subtitles into the video."""
        loop = asyncio.get_event_loop()

        def _run() -> None:
            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(output_path),
                    vf=f"ass={ass_path}",
                    vcodec="libx264",
                    acodec="aac",
                    crf=18,                 # High quality
                    preset="fast",
                    movflags="+faststart",  # Web-optimised MP4
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

        try:
            await loop.run_in_executor(None, _run)
        except ffmpeg.Error as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
            raise RuntimeError(f"FFmpeg caption burn failed:\n{stderr}") from exc
