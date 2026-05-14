"""
Génération de la voix off via espeak-ng (hors ligne, aucune clé API).
Compatible Linux/Mac/Windows avec espeak-ng installé.
"""

import json
import logging
import subprocess
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class AudioProcessor:
    def generate_voiceover(self, script: str, titre: str) -> Path:
        """
        Génère un fichier WAV depuis le script via espeak-ng.
        Retourne le chemin du fichier audio.
        """
        path = config.TEMP_DIR / f"{titre}_voix.wav"
        logger.info(f"Synthèse vocale → {path.name}")

        result = subprocess.run(
            [
                "espeak-ng",
                "-v", config.VOICE_ID,
                "-s", str(config.VOICE_RATE),
                "-p", str(config.VOICE_PITCH),
                "-w", str(path),
                script,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"espeak-ng a échoué (code {result.returncode}) : {result.stderr.strip()}\n"
                f"Installez espeak-ng : sudo apt install espeak-ng"
            )

        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(
                f"espeak-ng n'a produit aucun fichier audio : {path}\n"
                f"Vérifiez que la voix '{config.VOICE_ID}' est disponible."
            )

        size_kb = path.stat().st_size // 1024
        logger.info(f"Audio généré : {size_kb} Ko")
        return path

    def get_segments(self, script: str, audio_duration: float) -> list[dict]:
        """
        Découpe le script en segments synchronisés sur la durée audio.
        Chaque segment = une phrase ou un groupe de mots courts.
        """
        # Découpage par ponctuations
        raw = (
            script
            .replace(". ", ".|")
            .replace("! ", "!|")
            .replace("? ", "?|")
            .replace(", ", ", ")
        )
        phrases = [p.strip() for p in raw.split("|") if p.strip()]

        if not phrases:
            return [{"start": 0.0, "end": audio_duration, "text": script}]

        # Durée proportionnelle au nombre de caractères (plus naturel qu'équirépartition)
        lengths = [max(len(p), 1) for p in phrases]
        total = sum(lengths)
        segments = []
        cursor = 0.0
        for phrase, length in zip(phrases, lengths):
            dur = (length / total) * audio_duration
            segments.append({
                "start": round(cursor, 3),
                "end": round(cursor + dur, 3),
                "text": phrase,
            })
            cursor += dur

        # Sauvegarder pour debug
        seg_path = config.TEMP_DIR / f"segments_debug.json"
        seg_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2))

        logger.info(f"{len(segments)} segments de sous-titres générés")
        return segments

    def process(self, script: str, titre: str) -> tuple[Path, list[dict]]:
        """Point d'entrée principal : voix off + segments."""
        audio_path = self.generate_voiceover(script, titre)

        from moviepy import AudioFileClip
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        audio.close()

        segments = self.get_segments(script, duration)
        return audio_path, segments
