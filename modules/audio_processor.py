import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

import edge_tts

import config

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, voice: str = None):
        self.voice = voice or config.VOICE_NAME

    def generate_audio(self, text: str, titre: str) -> Path:
        """Génère un fichier MP3 depuis le texte via edge-tts."""
        output_path = config.TEMP_DIR / f"{titre}_audio.mp3"
        logger.info(f"Synthèse vocale → {output_path.name}")

        asyncio.run(self._synthesize(text, output_path))

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"La génération audio a échoué : {output_path}")

        logger.info(f"Audio généré ({output_path.stat().st_size // 1024} Ko)")
        return output_path

    async def _synthesize(self, text: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))

    def get_timings(self, audio_path: Path, titre: str) -> list[dict]:
        """
        Transcrit l'audio avec whisper-timestamped pour obtenir les timecodes.
        Retourne une liste de segments : [{start, end, text}, ...]
        """
        timings_path = config.TEMP_DIR / f"{titre}_timings.json"
        logger.info(f"Transcription whisper → {timings_path.name}")

        try:
            import whisper_timestamped as whisper

            model = whisper.load_model("tiny")
            result = whisper.transcribe(
                model,
                str(audio_path),
                language=config.VIDEO_LANGUAGE,
                verbose=False,
            )

            segments = []
            for seg in result.get("segments", []):
                # Priorité aux mots si disponibles
                words = seg.get("words", [])
                if words:
                    for w in words:
                        segments.append({
                            "start": round(w["start"], 3),
                            "end": round(w["end"], 3),
                            "text": w["text"].strip(),
                        })
                else:
                    segments.append({
                        "start": round(seg["start"], 3),
                        "end": round(seg["end"], 3),
                        "text": seg["text"].strip(),
                    })

            timings_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2))
            logger.info(f"{len(segments)} segments extraits")
            return segments

        except ImportError:
            logger.warning("whisper-timestamped non disponible, utilisation des timings fallback")
            return self._fallback_timings(audio_path)

    def _fallback_timings(self, audio_path: Path) -> list[dict]:
        """
        Fallback : découpe le texte en segments de durée égale si whisper absent.
        Nécessite pydub pour lire la durée.
        """
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(str(audio_path))
            total_duration = len(audio) / 1000.0
        except Exception:
            total_duration = 60.0

        return [{"start": 0.0, "end": total_duration, "text": ""}]

    def process(self, script: str, titre: str) -> tuple[Path, list[dict]]:
        """Point d'entrée principal : génère audio + timings."""
        audio_path = self.generate_audio(script, titre)
        timings = self.get_timings(audio_path, titre)
        return audio_path, timings
