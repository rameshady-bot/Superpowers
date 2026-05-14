"""
Orchestrateur du pipeline de création vidéo chrétienne.
Enchaîne : sélection médias → texte → audio → vidéo → publication.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import config
from modules.media_selector   import select_video, select_music
from modules.audio_processor  import AudioProcessor
from modules.video_editor     import VideoEditor
from modules.tiktok_publisher import TikTokPublisher

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    theme:      str
    success:    bool
    titre:      Optional[str]  = None
    video_path: Optional[Path] = None
    published:  bool           = False
    error:      Optional[str]  = None
    duration_s: float          = 0.0


class Pipeline:
    def __init__(
        self,
        publish: bool = False,
        use_claude: bool = False,
    ):
        """
        Args:
            publish:    Publier sur TikTok après rendu.
            use_claude: Générer le texte via Claude API (nécessite ANTHROPIC_API_KEY).
                        Si False, utilise les textes bibliques intégrés dans le projet.
        """
        self.publish    = publish
        self.use_claude = use_claude

        self.audio  = AudioProcessor()
        self.editor = VideoEditor()
        self.publisher = TikTokPublisher() if publish else None

        if use_claude:
            from modules.text_generator import TextGenerator
            self.text_gen = TextGenerator()

    # ── Pipeline unique ────────────────────────────────────────────────
    def run_single(self, theme: str, content: Optional[dict] = None) -> PipelineResult:
        start  = time.time()
        result = PipelineResult(theme=theme, success=False)

        logger.info(f"{'='*60}")
        logger.info(f"PIPELINE — thème : '{theme}'")
        logger.info(f"{'='*60}")

        try:
            # 1. Contenu textuel
            if content is None:
                if self.use_claude:
                    logger.info("[1/4] Génération texte via Claude…")
                    content = self.text_gen.generate(theme)
                else:
                    raise ValueError(
                        "Aucun contenu fourni et use_claude=False.\n"
                        "Passez un dict 'content' ou activez use_claude=True."
                    )
            titre  = content["titre_interne"]
            verset = content.get("verset", "")
            script = content["script_voix_off"]
            result.titre = titre

            content_path = config.TEMP_DIR / f"{titre}_content.json"
            content_path.write_text(
                json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info(f"[1/4] Contenu OK — {titre}")

            # 2. Sélection des médias
            logger.info("[2/4] Sélection des médias…")
            video_path = select_video(theme)
            music_path = select_music(theme)

            # 3. Audio
            logger.info("[3/4] Synthèse audio…")
            voiceover_path, segments = self.audio.process(script, titre)

            # 4. Rendu vidéo
            logger.info("[4/4] Rendu vidéo…")
            output_path = self.editor.render(
                titre=titre,
                video_path=video_path,
                voiceover_path=voiceover_path,
                music_path=music_path,
                segments=segments,
                verset=verset,
            )
            result.video_path = output_path
            result.success    = True

            # 5. Publication (optionnelle)
            if self.publish and self.publisher:
                logger.info("[5/4] Publication TikTok…")
                try:
                    result.published = self.publisher.publish(output_path, content)
                    logger.info(f"Publication : {'OK' if result.published else 'ÉCHEC'}")
                except Exception as e:
                    logger.error(f"Erreur publication : {e}")

        except FileNotFoundError as e:
            result.error = str(e)
            logger.error(f"\n[ERREUR MÉDIAS]\n{e}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"[ERREUR PIPELINE] {e}", exc_info=True)

        result.duration_s = round(time.time() - start, 1)
        self._log_result(result)
        return result

    # ── Batch ──────────────────────────────────────────────────────────
    def run_batch(self, items: list[dict]) -> list[PipelineResult]:
        """
        items : liste de dict avec clé obligatoire 'theme'
                et optionnellement 'content' (dict texte pré-généré).
        """
        logger.info(f"BATCH — {len(items)} vidéo(s) à créer")
        results = []
        for i, item in enumerate(items, 1):
            logger.info(f"\n[Batch {i}/{len(items)}]")
            theme   = item["theme"]
            content = item.get("content")
            results.append(self.run_single(theme, content=content))

        self._log_batch_summary(results)
        return results

    # ── Logs ───────────────────────────────────────────────────────────
    def _log_result(self, r: PipelineResult) -> None:
        status = "OK" if r.success else "ÉCHEC"
        logger.info(f"{'─'*60}")
        logger.info(f"RÉSULTAT [{status}] | thème='{r.theme}' | {r.duration_s}s")
        if r.video_path:
            logger.info(f"  → {r.video_path}")
        if r.error:
            logger.error(f"  Erreur : {r.error}")
        logger.info(f"{'─'*60}")

    def _log_batch_summary(self, results: list[PipelineResult]) -> None:
        success = sum(1 for r in results if r.success)
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH TERMINÉ : {success}/{len(results)} succès")
        for r in results:
            icon = "✓" if r.success else "✗"
            line = f"  {icon} {r.theme}"
            if r.video_path:
                line += f"\n      → {r.video_path}"
            logger.info(line)
        logger.info(f"{'='*60}")
