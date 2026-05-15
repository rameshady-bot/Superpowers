"""
French TTS generator using gTTS.

Returns None on any gTTS failure so the pipeline continues with a
silent segment rather than aborting the entire run.
"""

from pathlib import Path


def generate_tts(text: str, segment_id: int) -> Path | None:
    """
    Synthesise *text* in French and save to temp/tts_{segment_id}.mp3.

    Returns the Path on success, or None if gTTS raises any exception.
    Failures are logged but never re-raised.
    """
    try:
        from gtts import gTTS
    except ImportError:
        print(f"  [tts] segment {segment_id}: gTTS not installed — segment will be silent")
        return None

    temp_dir = Path(__file__).parent.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dest = temp_dir / f"tts_{segment_id}.mp3"

    try:
        tts = gTTS(text=text, lang="fr", slow=False)
        tts.save(str(dest))
        print(f"  [tts] segment {segment_id} → {dest}")
        return dest
    except Exception as exc:
        print(f"  [tts] segment {segment_id} failed: {exc} — segment will be silent")
        # Remove any partial file so the assembler does not use a corrupt file
        if dest.exists():
            dest.unlink()
        return None
