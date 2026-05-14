"""
Génération de la voix off.

Stratégie en cascade :
  1. edge-tts CLI  (voix neurale de qualité, nécessite internet)
  2. espeak-ng CLI (voix synthétique hors ligne, toujours disponible)

La cascade garantit qu'une voix est toujours produite.
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceGenerator:
    def __init__(
        self,
        voice_primary: str = "fr-FR-DeniseNeural",
        voice_fallback: str = "fr",
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ):
        """
        Args:
            voice_primary:  Voix edge-tts (liste : edge-tts --list-voices)
            voice_fallback: Code langue espeak-ng (fr | fr-be | en | es)
            rate:           Vitesse edge-tts (+10% | -10% | +0%)
            pitch:          Hauteur edge-tts (+5Hz | -5Hz | +0Hz)
        """
        self.voice_primary  = voice_primary
        self.voice_fallback = voice_fallback
        self.rate           = rate
        self.pitch          = pitch

    def generate(self, text: str, output_path: Path) -> Path:
        """
        Génère un fichier audio WAV/MP3 depuis le texte.
        Essaie edge-tts puis bascule sur espeak-ng si échec.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mp3_path = output_path.with_suffix(".mp3")

        logger.info(f"Voix off → {output_path.name}")

        # Tentative 1 : edge-tts (qualité neurale)
        if self._try_edge_tts(text, mp3_path):
            return mp3_path

        # Tentative 2 : espeak-ng (hors ligne)
        wav_path = output_path.with_suffix(".wav")
        if self._try_espeak(text, wav_path):
            return wav_path

        raise RuntimeError(
            "Impossible de générer la voix off.\n"
            "Vérifiez qu'espeak-ng est installé : sudo apt install espeak-ng"
        )

    # ── edge-tts ─────────────────────────────────────────────────────
    def _try_edge_tts(self, text: str, output_path: Path) -> bool:
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "edge_tts",
                    "--voice", self.voice_primary,
                    "--rate",  self.rate,
                    "--pitch", self.pitch,
                    "--text",  text,
                    "--write-media", str(output_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, "PYTHONWARNINGS": "ignore"},
            )
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                size_kb = output_path.stat().st_size // 1024
                logger.info(f"edge-tts OK — {self.voice_primary} — {size_kb} Ko")
                return True
            logger.warning(f"edge-tts échoué : {result.stderr[:200]}")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("edge-tts timeout (60s)")
            return False
        except FileNotFoundError:
            logger.warning("edge-tts introuvable")
            return False
        except Exception as e:
            logger.warning(f"edge-tts erreur : {e}")
            return False

    # ── espeak-ng ─────────────────────────────────────────────────────
    def _try_espeak(self, text: str, output_path: Path) -> bool:
        try:
            result = subprocess.run(
                [
                    "espeak-ng",
                    "-v", self.voice_fallback,
                    "-s", "145",
                    "-p", "50",
                    "-w", str(output_path),
                    text,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                size_kb = output_path.stat().st_size // 1024
                logger.info(f"espeak-ng OK — voix {self.voice_fallback} — {size_kb} Ko")
                return True
            logger.warning(f"espeak-ng échoué (code {result.returncode}) : {result.stderr[:200]}")
            return False
        except FileNotFoundError:
            logger.warning("espeak-ng introuvable — installez : sudo apt install espeak-ng")
            return False
        except Exception as e:
            logger.warning(f"espeak-ng erreur : {e}")
            return False

    def list_voices(self) -> list[str]:
        """Retourne la liste des voix edge-tts disponibles."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "edge_tts", "--list-voices"],
                capture_output=True, text=True, timeout=15,
            )
            return [
                line.split()[0] for line in result.stdout.splitlines()
                if line.startswith("fr-")
            ]
        except Exception:
            return []
