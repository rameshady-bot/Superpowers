"""
Mixage audio : voix off + musique de fond.

Principes :
  - Voix à 100% du volume
  - Musique à 15% (configurable) pour ne pas écraser la voix
  - Fade-in / fade-out sur la musique
  - La durée totale = durée de la voix off
"""

import logging
from pathlib import Path
from typing import Optional

from moviepy import AudioFileClip, CompositeAudioClip, concatenate_audioclips

logger = logging.getLogger(__name__)


class AudioMixer:
    def __init__(
        self,
        voice_volume: float = 1.0,
        music_volume: float = 0.15,
        music_fadein: float = 1.5,
        music_fadeout: float = 2.0,
    ):
        """
        Args:
            voice_volume:  Volume de la voix (0.0 → 1.0)
            music_volume:  Volume de la musique (0.0 → 1.0)
            music_fadein:  Durée du fondu d'entrée musique (secondes)
            music_fadeout: Durée du fondu de sortie musique (secondes)
        """
        self.voice_volume  = voice_volume
        self.music_volume  = music_volume
        self.music_fadein  = music_fadein
        self.music_fadeout = music_fadeout

    def mix(
        self,
        voice_path: Path,
        music_path: Optional[Path],
    ) -> CompositeAudioClip:
        """
        Mélange la voix off et la musique de fond.
        La durée du mix = durée de la voix off.

        Args:
            voice_path: Fichier audio de la voix off (WAV ou MP3)
            music_path: Fichier audio de la musique (None = voix seule)

        Returns:
            CompositeAudioClip prêt à être attaché à la vidéo
        """
        voice = AudioFileClip(str(voice_path)).with_volume_scaled(self.voice_volume)
        duration = voice.duration
        logger.info(f"Durée voix off : {duration:.1f}s")

        if music_path is None:
            logger.info("Pas de musique — voix seule")
            return voice

        music = self._prepare_music(music_path, duration)
        logger.info(
            f"Mix : voix={self.voice_volume:.0%} "
            f"musique={self.music_volume:.0%} "
            f"durée={duration:.1f}s"
        )
        return CompositeAudioClip([music, voice])

    def _prepare_music(self, music_path: Path, duration: float) -> AudioFileClip:
        """Charge, boucle, ajuste le volume et applique les fondus."""
        music = AudioFileClip(str(music_path))

        # Boucle si la musique est plus courte que la voix
        if music.duration < duration:
            loops = int(duration / music.duration) + 1
            music = concatenate_audioclips([music] * loops)
            logger.info(f"Musique bouclée {loops}x pour couvrir {duration:.1f}s")

        # Coupe à la durée exacte
        music = music.subclipped(0, duration)

        # Volume + fondus
        music = (
            music
            .with_volume_scaled(self.music_volume)
            .audio_fadein(self.music_fadein)
            .audio_fadeout(self.music_fadeout)
        )

        return music
