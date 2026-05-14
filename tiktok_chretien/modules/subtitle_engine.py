"""
Moteur de sous-titres : transcription Whisper → clips MoviePy synchronisés.

Whisper produit des timestamps précis mot par mot.
On regroupe ensuite les mots en lignes de 4-6 mots max pour lisibilité TikTok.
"""

import logging
from pathlib import Path
from typing import Optional

from moviepy import TextClip

logger = logging.getLogger(__name__)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAX_WORDS_PER_LINE = 5


class SubtitleEngine:
    def __init__(
        self,
        whisper_model: str = "base",
        font_path: str = FONT_PATH,
        font_size: int = 64,
        color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 3,
        video_width: int = 1080,
        y_position: float = 0.74,
    ):
        self.whisper_model = whisper_model
        self.font_path     = font_path
        self.font_size     = font_size
        self.color         = color
        self.stroke_color  = stroke_color
        self.stroke_width  = stroke_width
        self.video_width   = video_width
        self.y_position    = y_position
        self._model        = None

    # ── Transcription Whisper ─────────────────────────────────────────
    def transcribe(self, audio_path: Path) -> list[dict]:
        """
        Transcrit l'audio avec Whisper et retourne des segments mot-par-mot.
        Format : [{"start": float, "end": float, "text": str}, ...]
        """
        logger.info(f"Transcription Whisper ({self.whisper_model}) → {audio_path.name}")

        # Chargement paresseux du modèle
        if self._model is None:
            import whisper
            logger.info(f"Chargement modèle Whisper '{self.whisper_model}'…")
            self._model = whisper.load_model(self.whisper_model)

        import whisper
        result = self._model.transcribe(
            str(audio_path),
            language="fr",
            word_timestamps=True,
            verbose=False,
        )

        words = self._extract_words(result)
        groups = self._group_words(words, max_per_group=MAX_WORDS_PER_LINE)
        logger.info(f"{len(words)} mots → {len(groups)} blocs de sous-titres")
        return groups

    def transcribe_fallback(self, script: str, audio_duration: float) -> list[dict]:
        """
        Fallback sans Whisper : segmente le script proportionnellement à la durée.
        Utilisé si Whisper échoue ou n'est pas disponible.
        """
        logger.warning("Whisper indisponible — segmentation proportionnelle utilisée")

        sentences = []
        for s in script.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|"):
            s = s.strip()
            if s:
                sentences.append(s)

        if not sentences:
            return [{"start": 0.0, "end": audio_duration, "text": script}]

        total_chars = sum(len(s) for s in sentences)
        segments = []
        cursor = 0.0
        for s in sentences:
            dur = (len(s) / total_chars) * audio_duration
            segments.append({"start": round(cursor, 3), "end": round(cursor + dur, 3), "text": s})
            cursor += dur

        return segments

    @staticmethod
    def _extract_words(result: dict) -> list[dict]:
        words = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                text = w.get("word", "").strip()
                if text:
                    words.append({
                        "start": round(w["start"], 3),
                        "end":   round(w["end"],   3),
                        "text":  text,
                    })
        return words

    @staticmethod
    def _group_words(words: list[dict], max_per_group: int = 5) -> list[dict]:
        """Regroupe les mots en blocs de sous-titres de max_per_group mots."""
        if not words:
            return []
        groups = []
        i = 0
        while i < len(words):
            chunk = words[i: i + max_per_group]
            text  = " ".join(w["text"] for w in chunk).strip()
            groups.append({
                "start": chunk[0]["start"],
                "end":   chunk[-1]["end"],
                "text":  text,
            })
            i += max_per_group
        return groups

    # ── Construction des clips MoviePy ────────────────────────────────
    def build_clips(self, segments: list[dict]) -> list[TextClip]:
        """Crée un TextClip MoviePy pour chaque segment."""
        clips = []
        for seg in segments:
            text = seg["text"].strip()
            dur  = seg["end"] - seg["start"]
            if not text or dur <= 0.05:
                continue
            try:
                clip = (
                    TextClip(
                        font=self.font_path,
                        text=text,
                        font_size=self.font_size,
                        color=self.color,
                        stroke_color=self.stroke_color,
                        stroke_width=self.stroke_width,
                        method="caption",
                        size=(self.video_width - 80, None),
                        text_align="center",
                        duration=dur,
                    )
                    .with_start(seg["start"])
                    .with_position(("center", self.y_position), relative=True)
                )
                clips.append(clip)
            except Exception as e:
                logger.warning(f"Sous-titre ignoré '{text[:25]}…' : {e}")

        logger.info(f"{len(clips)}/{len(segments)} clips sous-titres créés")
        return clips

    def build_verset_clip(
        self,
        verset: str,
        duration: float,
        font_size: int = 42,
        color: str = "#FFD700",
    ) -> Optional[TextClip]:
        """Référence biblique dorée affichée en permanence en haut de l'écran."""
        if not verset:
            return None
        try:
            return (
                TextClip(
                    font=self.font_path,
                    text=verset,
                    font_size=font_size,
                    color=color,
                    stroke_color="black",
                    stroke_width=2,
                    method="caption",
                    size=(self.video_width - 80, None),
                    text_align="center",
                    duration=duration,
                )
                .with_start(0)
                .with_position(("center", 0.06), relative=True)
            )
        except Exception as e:
            logger.warning(f"Clip verset ignoré : {e}")
            return None
