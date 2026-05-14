import logging
import random
from pathlib import Path
from typing import Optional

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

import config

logger = logging.getLogger(__name__)

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


class VideoEditor:
    def __init__(self):
        self.w = config.VIDEO_WIDTH
        self.h = config.VIDEO_HEIGHT
        self.fps = config.VIDEO_FPS

    def get_background_video(self, titre: str) -> Optional[Path]:
        """Cherche une vidéo de fond dans assets/. Prend la première ou une aléatoire."""
        videos = [
            f for f in config.ASSETS_DIR.iterdir()
            if f.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        ]
        if not videos:
            logger.warning("Aucune vidéo de fond trouvée dans assets/ — fond noir utilisé")
            return None
        chosen = random.choice(videos)
        logger.info(f"Vidéo de fond : {chosen.name}")
        return chosen

    def _prepare_background(self, video_path: Optional[Path], duration: float) -> VideoFileClip:
        """Charge et recadre la vidéo en 9:16, boucle si trop courte."""
        if video_path is None:
            return ColorClip(size=(self.w, self.h), color=(0, 0, 0)).set_duration(duration)

        clip = VideoFileClip(str(video_path), audio=False)

        # Recadrage 9:16
        clip_ratio = clip.w / clip.h
        target_ratio = self.w / self.h

        if clip_ratio > target_ratio:
            # Trop large : rogner la largeur
            new_w = int(clip.h * target_ratio)
            x_offset = (clip.w - new_w) // 2
            clip = clip.crop(x1=x_offset, x2=x_offset + new_w)
        else:
            # Trop haut : rogner la hauteur
            new_h = int(clip.w / target_ratio)
            y_offset = (clip.h - new_h) // 2
            clip = clip.crop(y1=y_offset, y2=y_offset + new_h)

        clip = clip.resize((self.w, self.h))

        # Boucle si la vidéo est plus courte que l'audio
        if clip.duration < duration:
            repeats = int(duration / clip.duration) + 1
            clips = [clip] * repeats
            clip = concatenate_videoclips(clips).subclip(0, duration)
        else:
            clip = clip.subclip(0, duration)

        return clip.set_fps(self.fps)

    def _build_subtitle_clips(self, timings: list[dict]) -> list:
        """Crée les clips TextClip pour chaque segment de sous-titre."""
        subtitle_clips = []
        font_size = config.SUBTITLE_FONT_SIZE

        for seg in timings:
            text = seg.get("text", "").strip()
            if not text:
                continue

            duration = seg["end"] - seg["start"]
            if duration <= 0:
                continue

            try:
                txt_clip = (
                    TextClip(
                        text,
                        fontsize=font_size,
                        color=config.SUBTITLE_COLOR,
                        stroke_color=config.SUBTITLE_STROKE_COLOR,
                        stroke_width=config.SUBTITLE_STROKE_WIDTH,
                        font="DejaVu-Sans-Bold",
                        method="caption",
                        size=(self.w - 80, None),
                        align="center",
                    )
                    .set_start(seg["start"])
                    .set_duration(duration)
                    .set_position(("center", 0.75), relative=True)
                )
                subtitle_clips.append(txt_clip)
            except Exception as e:
                logger.warning(f"Sous-titre ignoré '{text[:20]}' : {e}")

        return subtitle_clips

    def render(self, titre: str, audio_path: Path, timings: list[dict]) -> Path:
        """Assemble la vidéo finale et l'exporte dans output/."""
        output_path = config.OUTPUT_DIR / f"{titre}.mp4"
        logger.info(f"Rendu vidéo → {output_path.name}")

        audio = AudioFileClip(str(audio_path))
        duration = audio.duration

        bg_video_path = self.get_background_video(titre)
        background = self._prepare_background(bg_video_path, duration)
        background = background.set_audio(audio)

        subtitle_clips = self._build_subtitle_clips(timings)

        layers = [background] + subtitle_clips
        final = CompositeVideoClip(layers, size=(self.w, self.h))

        final.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(config.TEMP_DIR / f"{titre}_temp_audio.m4a"),
            remove_temp=True,
            logger=None,
        )

        audio.close()
        final.close()
        background.close()

        logger.info(f"Vidéo exportée : {output_path} ({output_path.stat().st_size // (1024*1024)} Mo)")
        return output_path
