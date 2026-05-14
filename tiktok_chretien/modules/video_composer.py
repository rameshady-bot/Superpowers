"""
Composition vidéo finale : fond 9:16 + audio mixé + sous-titres + verset.

Pipeline :
  1. Charger la vidéo de fond
  2. Recadrer automatiquement en 9:16 (crop centré)
  3. Boucler si la vidéo est plus courte que l'audio
  4. Attacher la piste audio mixée
  5. Superposer sous-titres + verset
  6. Exporter en MP4 (libx264 / aac)
"""

import logging
from pathlib import Path
from typing import Optional

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)

logger = logging.getLogger(__name__)


class VideoComposer:
    def __init__(
        self,
        width: int  = 1080,
        height: int = 1920,
        fps: int    = 30,
    ):
        self.width  = width
        self.height = height
        self.fps    = fps

    # ── 1. Fond vidéo 9:16 ───────────────────────────────────────────
    def prepare_background(
        self, video_path: Path, duration: float
    ) -> VideoFileClip:
        """
        Charge la vidéo, la recadre en 9:16 (crop centré), boucle si nécessaire.
        """
        logger.info(f"Fond vidéo : {video_path.name}")
        clip = VideoFileClip(str(video_path), audio=False)

        # ── Recadrage 9:16 ──────────────────────────────────────────
        target_ratio = self.width / self.height
        clip_ratio   = clip.w / clip.h

        if clip_ratio > target_ratio:
            # Trop large → rogner sur la largeur
            new_w = int(clip.h * target_ratio)
            x1    = (clip.w - new_w) // 2
            clip  = clip.cropped(x1=x1, x2=x1 + new_w)
        elif clip_ratio < target_ratio:
            # Trop haut → rogner sur la hauteur
            new_h = int(clip.w / target_ratio)
            y1    = (clip.h - new_h) // 2
            clip  = clip.cropped(y1=y1, y2=y1 + new_h)

        clip = clip.resized((self.width, self.height))

        # ── Boucle ──────────────────────────────────────────────────
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip  = concatenate_videoclips([clip] * loops)
            logger.info(f"Vidéo bouclée pour atteindre {duration:.1f}s")

        return clip.subclipped(0, duration).with_fps(self.fps)

    # ── 2. Assemblage final ───────────────────────────────────────────
    def compose(
        self,
        video_path: Path,
        audio_track: CompositeAudioClip,
        subtitle_clips: list[TextClip],
        verset_clip: Optional[TextClip],
        output_path: Path,
        temp_dir: Path,
    ) -> Path:
        """
        Assemble et exporte la vidéo finale.

        Args:
            video_path:     Fond vidéo source.
            audio_track:    Piste audio mixée (voix + musique).
            subtitle_clips: Liste de TextClip synchronisés.
            verset_clip:    Clip de référence biblique (peut être None).
            output_path:    Chemin de sortie du MP4.
            temp_dir:       Dossier pour les fichiers temporaires ffmpeg.

        Returns:
            Chemin du fichier MP4 exporté.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Durée = durée de l'audio
        duration = audio_track.duration
        logger.info(f"Composition {self.width}×{self.height} — {duration:.1f}s")

        background = self.prepare_background(video_path, duration)
        background = background.with_audio(audio_track)

        layers = [background]
        if verset_clip:
            layers.append(verset_clip)
        layers.extend(subtitle_clips)

        final = CompositeVideoClip(layers, size=(self.width, self.height))

        stem = output_path.stem
        temp_audio = temp_dir / f"{stem}_tmp_audio.m4a"

        logger.info(f"Export → {output_path.name}")
        final.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(temp_audio),
            remove_temp=True,
            logger=None,
        )

        final.close()
        background.close()

        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Vidéo exportée : {output_path.name} ({size_mb:.1f} Mo)")
        return output_path
