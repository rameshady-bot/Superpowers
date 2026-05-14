#!/usr/bin/env python3
"""
Pipeline de génération de vidéos chrétiennes TikTok.

Usage :
  python main.py                                      # thème par défaut
  python main.py --theme "la paix"                    # thème unique
  python main.py --batch                              # tous les thèmes du catalogue
  python main.py --theme "espoir" --whisper tiny      # modèle Whisper léger
  python main.py --list-themes                        # afficher les thèmes disponibles

Dépendances système :
  sudo apt install espeak-ng ffmpeg
"""

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Dossiers ─────────────────────────────────────────────────────────
BASE         = Path(__file__).parent
VIDEOS_DIR   = BASE / os.getenv("VIDEOS_DIR",  "assets/videos")
MUSIC_DIR    = BASE / os.getenv("MUSIC_DIR",   "assets/music")
TEMP_DIR     = BASE / os.getenv("TEMP_DIR",    "temp")
OUTPUT_DIR   = BASE / os.getenv("OUTPUT_DIR",  "output")
SESSIONS_DIR = BASE / os.getenv("SESSIONS_DIR","sessions")

for d in [VIDEOS_DIR, MUSIC_DIR, TEMP_DIR, OUTPUT_DIR, SESSIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Config vidéo ─────────────────────────────────────────────────────
VIDEO_W  = int(os.getenv("VIDEO_WIDTH",  "1080"))
VIDEO_H  = int(os.getenv("VIDEO_HEIGHT", "1920"))
VIDEO_FPS = int(os.getenv("VIDEO_FPS",  "30"))

FONT_PATH     = os.getenv("FONT_PATH",
                           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
MUSIC_VOL     = float(os.getenv("MUSIC_VOLUME", "0.15"))
VOICE_VOL     = float(os.getenv("VOICE_VOLUME", "1.0"))

VOICE_PRIMARY  = os.getenv("VOICE_PRIMARY",  "fr-FR-DeniseNeural")
VOICE_FALLBACK = os.getenv("VOICE_FALLBACK", "fr")
WHISPER_MODEL  = os.getenv("WHISPER_MODEL",  "base")

PEXELS_KEY  = os.getenv("PEXELS_API_KEY",  "")
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")


# ── Logging ───────────────────────────────────────────────────────────
def setup_logging() -> None:
    log_file = BASE / "logs" / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    log_file.parent.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[fh, ch])
    for lib in ["httpx", "httpcore", "urllib3"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    logging.info(f"Log → {log_file}")


logger = logging.getLogger(__name__)


# ── Résultat d'une exécution ──────────────────────────────────────────
@dataclass
class RunResult:
    theme:      str
    success:    bool
    output:     Optional[Path] = None
    error:      Optional[str]  = None
    duration_s: float          = 0.0


# ── Pipeline principal ────────────────────────────────────────────────
class TikTokChretienPipeline:
    def __init__(self, whisper_model: str = WHISPER_MODEL):
        from modules.content         import get_content_by_theme, PEXELS_QUERIES, PIXABAY_QUERIES
        from modules.media_downloader import MediaDownloader
        from modules.voice_generator  import VoiceGenerator
        from modules.subtitle_engine  import SubtitleEngine
        from modules.audio_mixer      import AudioMixer
        from modules.video_composer   import VideoComposer

        self._get_content     = get_content_by_theme
        self._pexels_queries  = PEXELS_QUERIES
        self._pixabay_queries = PIXABAY_QUERIES

        self.downloader = MediaDownloader(
            videos_dir=VIDEOS_DIR,
            music_dir=MUSIC_DIR,
            pexels_key=PEXELS_KEY,
            pixabay_key=PIXABAY_KEY,
        )
        self.voice = VoiceGenerator(
            voice_primary=VOICE_PRIMARY,
            voice_fallback=VOICE_FALLBACK,
        )
        self.subtitles = SubtitleEngine(
            whisper_model=whisper_model,
            font_path=FONT_PATH,
            font_size=int(os.getenv("SUBTITLE_FONT_SIZE", "64")),
            color=os.getenv("SUBTITLE_COLOR", "white"),
            stroke_color=os.getenv("SUBTITLE_STROKE_COLOR", "black"),
            stroke_width=int(os.getenv("SUBTITLE_STROKE_WIDTH", "3")),
            video_width=VIDEO_W,
            y_position=float(os.getenv("SUBTITLE_POSITION", "0.74")),
        )
        self.mixer    = AudioMixer(voice_volume=VOICE_VOL, music_volume=MUSIC_VOL)
        self.composer = VideoComposer(width=VIDEO_W, height=VIDEO_H, fps=VIDEO_FPS)

    def run(self, theme: str) -> RunResult:
        t0     = time.time()
        result = RunResult(theme=theme, success=False)
        logger.info(f"\n{'='*60}")
        logger.info(f"VIDÉO — thème : '{theme}'")
        logger.info(f"{'='*60}")

        try:
            # ── 1. Contenu ─────────────────────────────────────────────
            content = self._get_content(theme)
            titre   = content.titre_interne
            logger.info(f"[1/5] Contenu : {titre} | {content.verset}")

            # ── 2. Médias ──────────────────────────────────────────────
            logger.info(f"[2/5] Sélection médias ({content.categorie_visuelle}/{content.ambiance})")
            queries     = self._pexels_queries.get(content.categorie_visuelle, ["nature peaceful"])
            video_path  = self.downloader.get_background_video(content.categorie_visuelle, queries)
            music_path  = self.downloader.get_music(content.ambiance)

            # ── 3. Voix off ────────────────────────────────────────────
            logger.info("[3/5] Génération voix off")
            voice_path  = self.voice.generate(
                text=content.script,
                output_path=TEMP_DIR / f"{titre}_voix",
            )

            # ── 4. Sous-titres (Whisper) ───────────────────────────────
            logger.info("[4/5] Transcription Whisper + sous-titres")
            try:
                segments = self.subtitles.transcribe(voice_path)
            except Exception as e:
                logger.warning(f"Whisper échoué ({e}) — fallback proportionnel")
                segments = self.subtitles.transcribe_fallback(
                    content.script,
                    self._audio_duration(voice_path),
                )

            from moviepy import AudioFileClip
            duration       = AudioFileClip(str(voice_path)).duration
            subtitle_clips = self.subtitles.build_clips(segments)
            verset_clip    = self.subtitles.build_verset_clip(
                content.verset, duration,
                font_size=int(os.getenv("VERSET_FONT_SIZE", "42")),
                color=os.getenv("VERSET_COLOR", "#FFD700"),
            )

            # ── 5. Montage & export ────────────────────────────────────
            logger.info("[5/5] Montage vidéo final")
            audio_track = self.mixer.mix(voice_path, music_path)
            output_path = OUTPUT_DIR / f"{titre}.mp4"

            self.composer.compose(
                video_path=video_path,
                audio_track=audio_track,
                subtitle_clips=subtitle_clips,
                verset_clip=verset_clip,
                output_path=output_path,
                temp_dir=TEMP_DIR,
            )

            result.success = True
            result.output  = output_path

        except FileNotFoundError as e:
            result.error = str(e)
            logger.error(f"\n[ERREUR MÉDIAS]\n{e}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"[ERREUR] {e}", exc_info=True)

        result.duration_s = round(time.time() - t0, 1)
        self._log_result(result)
        return result

    @staticmethod
    def _audio_duration(path: Path) -> float:
        from moviepy import AudioFileClip
        a = AudioFileClip(str(path))
        d = a.duration
        a.close()
        return d

    def _log_result(self, r: RunResult) -> None:
        status = "OK ✓" if r.success else "ÉCHEC ✗"
        logger.info(f"{'─'*60}")
        logger.info(f"[{status}] '{r.theme}' — {r.duration_s}s")
        if r.output:
            logger.info(f"  Vidéo → {r.output}")
        if r.error:
            logger.error(f"  Erreur : {r.error}")
        logger.info(f"{'─'*60}")


# ── Batch ─────────────────────────────────────────────────────────────
def run_batch(
    themes: list[str],
    pipeline: TikTokChretienPipeline,
) -> list[RunResult]:
    logger.info(f"\nBATCH — {len(themes)} thème(s)")
    results = []
    for i, theme in enumerate(themes, 1):
        logger.info(f"\n[{i}/{len(themes)}]")
        results.append(pipeline.run(theme))

    success = sum(1 for r in results if r.success)
    logger.info(f"\n{'='*60}")
    logger.info(f"BATCH TERMINÉ : {success}/{len(results)} vidéos créées")
    for r in results:
        icon = "✓" if r.success else "✗"
        logger.info(f"  {icon} {r.theme}")
        if r.output:
            logger.info(f"      → {r.output}")
    logger.info(f"{'='*60}")
    return results


# ── CLI ───────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    from modules.content import list_themes
    parser = argparse.ArgumentParser(
        description="Génération de vidéos chrétiennes TikTok",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--theme",  type=str, default="la confiance en Dieu")
    parser.add_argument("--batch",  action="store_true",
                        help="Générer toutes les vidéos du catalogue")
    parser.add_argument("--whisper", type=str, default=WHISPER_MODEL,
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Modèle Whisper (défaut: base)")
    parser.add_argument("--list-themes", action="store_true",
                        help="Afficher les thèmes disponibles et quitter")
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()

    if args.list_themes:
        from modules.content import list_themes
        print("\nThèmes disponibles dans le catalogue :\n")
        for t in list_themes():
            print(f"  • {t}")
        print(f"\nUsage : python main.py --theme \"<thème>\"\n")
        return 0

    pipeline = TikTokChretienPipeline(whisper_model=args.whisper)

    if args.batch:
        from modules.content import list_themes
        results = run_batch(list_themes(), pipeline)
        failed  = [r for r in results if not r.success]
        if failed:
            logger.error(f"{len(failed)} erreur(s) :")
            for r in failed:
                logger.error(f"  • {r.theme} : {r.error}")
        return 1 if failed else 0
    else:
        result = pipeline.run(args.theme)
        return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
