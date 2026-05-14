import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import config
from modules.text_generator import TextGenerator
from modules.audio_processor import AudioProcessor
from modules.video_editor import VideoEditor
from modules.tiktok_publisher import TikTokPublisher

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    theme: str
    success: bool
    titre: Optional[str] = None
    video_path: Optional[Path] = None
    published: bool = False
    error: Optional[str] = None
    duration_s: float = 0.0


class Pipeline:
    def __init__(self, publish: bool = False):
        """
        Args:
            publish: Si True, publie la vidéo sur TikTok après rendu.
        """
        self.publish = publish
        self.text_gen = TextGenerator()
        self.audio_proc = AudioProcessor()
        self.video_editor = VideoEditor()
        self.publisher = TikTokPublisher() if publish else None

    def run_single(self, theme: str) -> PipelineResult:
        """Exécute le pipeline complet pour un thème unique."""
        start = time.time()
        result = PipelineResult(theme=theme, success=False)
        logger.info(f"{'='*60}")
        logger.info(f"PIPELINE START — thème : '{theme}'")
        logger.info(f"{'='*60}")

        try:
            # 1. Génération texte
            logger.info("[1/4] Génération du texte...")
            content = self.text_gen.generate(theme)
            titre = content["titre_interne"]
            result.titre = titre

            content_path = config.TEMP_DIR / f"{titre}_content.json"
            content_path.write_text(json.dumps(content, ensure_ascii=False, indent=2))
            logger.info(f"      Contenu sauvegardé : {content_path.name}")

            # 2. Génération audio
            logger.info("[2/4] Synthèse audio...")
            audio_path, timings = self.audio_proc.process(content["script_voix_off"], titre)
            logger.info(f"      Audio : {audio_path.name} | {len(timings)} segments")

            # 3. Création vidéo
            logger.info("[3/4] Rendu vidéo...")
            video_path = self.video_editor.render(titre, audio_path, timings)
            result.video_path = video_path
            logger.info(f"      Vidéo : {video_path}")

            # 4. Publication (optionnelle)
            if self.publish and self.publisher:
                logger.info("[4/4] Publication TikTok...")
                try:
                    published = self.publisher.publish(video_path, content)
                    result.published = published
                    status = "OK" if published else "ECHEC"
                    logger.info(f"      Publication : {status}")
                except Exception as e:
                    logger.error(f"      Erreur publication : {e}")
                    result.published = False
            else:
                logger.info("[4/4] Publication ignorée (publish=False)")

            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"PIPELINE ERREUR sur '{theme}' : {e}", exc_info=True)

        result.duration_s = round(time.time() - start, 1)
        self._log_result(result)
        return result

    def run_batch(self, themes: list[str]) -> list[PipelineResult]:
        """Exécute le pipeline sur une liste de thèmes."""
        logger.info(f"BATCH START — {len(themes)} thème(s)")
        results = []
        for i, theme in enumerate(themes, 1):
            logger.info(f"\n[Batch {i}/{len(themes)}]")
            result = self.run_single(theme)
            results.append(result)

        self._log_batch_summary(results)
        return results

    def _log_result(self, result: PipelineResult) -> None:
        status = "OK" if result.success else "ECHEC"
        logger.info(f"{'─'*60}")
        logger.info(f"RÉSULTAT [{status}] thème='{result.theme}' durée={result.duration_s}s")
        if result.video_path:
            logger.info(f"  Vidéo  : {result.video_path}")
        if result.error:
            logger.info(f"  Erreur : {result.error}")
        logger.info(f"{'─'*60}")

    def _log_batch_summary(self, results: list[PipelineResult]) -> None:
        success = sum(1 for r in results if r.success)
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH TERMINÉ : {success}/{len(results)} succès")
        for r in results:
            icon = "✓" if r.success else "✗"
            logger.info(f"  {icon} {r.theme}")
            if r.video_path:
                logger.info(f"    → {r.video_path}")
        logger.info(f"{'='*60}")
