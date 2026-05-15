"""French voice-over generation using gTTS."""

from pathlib import Path

from gtts import gTTS

from config import TEMP_DIR, TTS_LANG, TTS_SLOW


def generate_voiceover(text: str, filename: str = "voiceover.mp3") -> Path:
    """Synthesise *text* to speech and save to TEMP_DIR/*filename*."""
    dest = TEMP_DIR / filename
    tts = gTTS(text=text, lang=TTS_LANG, slow=TTS_SLOW)
    tts.save(str(dest))
    print(f"  [tts] voice-over saved → {dest}")
    return dest


def build_voiceover_script(encouragement: dict, scripture: dict) -> str:
    """Combine encouragement + scripture into the spoken narration."""
    lines = [
        encouragement["text"],
        "",
        f"{scripture['reference']} — {scripture['text']}",
        "",
        "Que Dieu vous bénisse et vous garde. Amen.",
    ]
    return "\n".join(lines)
