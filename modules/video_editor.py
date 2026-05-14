"""
Assemblage vidéo final : fond réel + voix off + musique + sous-titres.
Utilise MoviePy 2.x.
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
    afx,
)

import config

logger = logging.getLogger(__name__)


class VideoEditor:
    def __init__(self):
        self.w = config.VIDEO_WIDTH
        self.h = config.VIDEO_HEIGHT
        self.fps = config.VIDEO_FPS

    # ── 1. Fond vidéo ──────────────────────────────────────────────────
    def _prepare_background(self, video_path: Path, duration: float) -> VideoFileClip:
        """Charge, recadre en 9:16, boucle si nécessaire, coupe à la durée cible."""
        logger.info(f"Chargement fond vidéo : {video_path.name}")
        clip = VideoFileClip(str(video_path), audio=False)

        # Recadrage 9:16 sans déformation
        clip_ratio = clip.w / clip.h
        target_ratio = self.w / self.h
        if clip_ratio > target_ratio:
            new_w = int(clip.h * target_ratio)
            x1 = (clip.w - new_w) // 2
            clip = clip.cropped(x1=x1, x2=x1 + new_w)
        else:
            new_h = int(clip.w / target_ratio)
            y1 = (clip.h - new_h) // 2
            clip = clip.cropped(y1=y1, y2=y1 + new_h)

        clip = clip.resized((self.w, self.h))

        # Boucle si la vidéo est trop courte
        if clip.duration < duration:
            loops = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip] * loops)

        return clip.subclipped(0, duration).with_fps(self.fps)

    # ── 2. Piste audio (voix + musique) ───────────────────────────────
    def _build_audio(
        self,
        voiceover_path: Path,
        music_path: Optional[Path],
        duration: float,
    ) -> CompositeAudioClip:
        """Mélange voix off et musique de fond avec volumes configurables."""
        voice = AudioFileClip(str(voiceover_path)).with_volume_scaled(
            config.VOICEOVER_VOLUME
        )

        if music_path is None:
            return voice

        music = AudioFileClip(str(music_path))

        # Boucle la musique si trop courte
        if music.duration < duration:
            loops = int(duration / music.duration) + 1
            from moviepy import concatenate_audioclips
            music = concatenate_audioclips([music] * loops)

        music = (
            music.subclipped(0, duration)
            .with_volume_scaled(config.MUSIC_VOLUME)
            .audio_fadein(1.5)
            .audio_fadeout(2.0)
        )

        return CompositeAudioClip([music, voice])

    # ── 3. Sous-titres ─────────────────────────────────────────────────
    def _build_subtitle_clips(self, segments: list[dict]) -> list:
        clips = []
        for seg in segments:
            text = seg["text"].strip()
            dur = seg["end"] - seg["start"]
            if not text or dur <= 0:
                continue
            try:
                clip = (
                    TextClip(
                        font=config.FONT_PATH,
                        text=text,
                        font_size=config.SUBTITLE_FONT_SIZE,
                        color=config.SUBTITLE_COLOR,
                        stroke_color=config.SUBTITLE_STROKE_COLOR,
                        stroke_width=config.SUBTITLE_STROKE_WIDTH,
                        method="caption",
                        size=(self.w - 100, None),
                        text_align="center",
                        duration=dur,
                    )
                    .with_start(seg["start"])
                    .with_position(("center", config.SUBTITLE_Y_RATIO), relative=True)
                )
                clips.append(clip)
            except Exception as e:
                logger.warning(f"Sous-titre ignoré '{text[:30]}…' : {e}")
        logger.info(f"{len(clips)} sous-titres assemblés")
        return clips

    def _build_verset_clip(self, verset: str, duration: float) -> Optional[TextClip]:
        """Référence biblique en doré, affichée en permanence en haut."""
        if not verset:
            return None
        try:
            return (
                TextClip(
                    font=config.FONT_PATH,
                    text=verset,
                    font_size=config.VERSET_FONT_SIZE,
                    color=config.VERSET_COLOR,
                    stroke_color="black",
                    stroke_width=2,
                    method="caption",
                    size=(self.w - 100, None),
                    text_align="center",
                    duration=duration,
                )
                .with_start(0)
                .with_position(("center", 0.06), relative=True)
            )
        except Exception as e:
            logger.warning(f"Clip verset ignoré : {e}")
            return None

    # ── 4. Assemblage & export ─────────────────────────────────────────
    def render(
        self,
        titre: str,
        video_path: Path,
        voiceover_path: Path,
        music_path: Optional[Path],
        segments: list[dict],
        verset: str = "",
    ) -> Path:
        """
        Assemble tous les éléments et exporte le MP4 final dans output/.

        Args:
            titre:          Identifiant slug (nom de fichier sans extension).
            video_path:     Chemin du fond vidéo source.
            voiceover_path: Chemin du fichier WAV de voix off.
            music_path:     Chemin de la musique de fond (None = sans musique).
            segments:       Liste [{start, end, text}] pour les sous-titres.
            verset:         Référence biblique affichée en haut (peut être vide).

        Returns:
            Chemin du fichier MP4 exporté.
        """
        output_path = config.OUTPUT_DIR / f"{titre}.mp4"
        logger.info(f"Assemblage vidéo → {output_path.name}")

        # Durée = durée de la voix off
        voice_clip = AudioFileClip(str(voiceover_path))
        duration = voice_clip.duration
        voice_clip.close()
        logger.info(f"Durée cible : {duration:.1f}s")

        background  = self._prepare_background(video_path, duration)
        audio_track = self._build_audio(voiceover_path, music_path, duration)
        background  = background.with_audio(audio_track)

        subtitle_clips = self._build_subtitle_clips(segments)
        verset_clip    = self._build_verset_clip(verset, duration)

        layers = [background]
        if verset_clip:
            layers.append(verset_clip)
        layers.extend(subtitle_clips)

        final = CompositeVideoClip(layers, size=(self.w, self.h))

        logger.info("Export en cours (libx264 / aac)…")
        final.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(config.TEMP_DIR / f"{titre}_tmp_audio.m4a"),
            remove_temp=True,
            logger=None,
        )

        final.close()
        background.close()

        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Vidéo exportée : {output_path} ({size_mb:.1f} Mo)")
        return output_path
