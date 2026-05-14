"""
Publication TikTok en deux modes :
  - "api"        : API officielle TikTok Content Posting
  - "playwright" : navigateur automatisé avec session persistante

La session Playwright est sauvegardée dans sessions/tiktok_session.json
et réutilisée à chaque lancement (pas de reconnexion manuelle répétée).
"""

import json
import logging
from pathlib import Path
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)

SESSION_FILE      = config.SESSIONS_DIR / "tiktok_session.json"
TIKTOK_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"


class TikTokPublisher:
    def __init__(self):
        self.mode         = config.TIKTOK_MODE
        self.access_token = config.TIKTOK_ACCESS_TOKEN

    # ── Entrée publique ────────────────────────────────────────────────
    def publish(self, video_path: Path, content: dict) -> bool:
        if not video_path.exists():
            raise FileNotFoundError(f"Vidéo introuvable : {video_path}")

        caption = self._build_caption(content)
        logger.info(f"Publication TikTok [{self.mode}] : {video_path.name}")

        if self.mode == "api":
            return self._publish_api(video_path, caption)
        elif self.mode == "playwright":
            return self._publish_playwright(video_path, caption)
        else:
            raise ValueError(
                f"TIKTOK_MODE invalide : '{self.mode}'. "
                f"Valeurs acceptées : 'api' ou 'playwright'."
            )

    # ── Caption ────────────────────────────────────────────────────────
    def _build_caption(self, content: dict) -> str:
        hashtags = " ".join(f"#{t.lstrip('#')}" for t in content.get("hashtags", []))
        parts = [
            content.get("description_tiktok", ""),
            content.get("call_to_action", ""),
            hashtags,
        ]
        return "\n\n".join(p for p in parts if p)[:2200]

    # ── Mode API officielle ────────────────────────────────────────────
    def _publish_api(self, video_path: Path, caption: str) -> bool:
        if not self.access_token:
            raise ValueError(
                "TIKTOK_ACCESS_TOKEN manquant dans .env pour le mode 'api'.\n"
                "Configurez TIKTOK_MODE=playwright si vous n'avez pas de token."
            )

        file_size = video_path.stat().st_size
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        init_payload = {
            "post_info": {
                "title": caption,
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            },
        }

        with httpx.Client(timeout=30) as client:
            resp = client.post(TIKTOK_UPLOAD_URL, headers=headers, json=init_payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("error", {}).get("code") != "ok":
            logger.error(f"Erreur init upload TikTok : {data}")
            return False

        upload_url = data["data"]["upload_url"]
        publish_id = data["data"]["publish_id"]

        with httpx.Client(timeout=180) as client:
            up = client.put(
                upload_url,
                content=video_path.read_bytes(),
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                    "Content-Length": str(file_size),
                },
            )
            up.raise_for_status()

        logger.info(f"Vidéo uploadée — publish_id={publish_id}")
        return True

    # ── Mode Playwright ────────────────────────────────────────────────
    def _publish_playwright(self, video_path: Path, caption: str) -> bool:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright non installé.\n"
                "Exécutez : pip install playwright && playwright install chromium"
            )

        with sync_playwright() as p:
            context = self._load_context(p)
            page    = context.new_page()
            try:
                success = self._upload_via_browser(page, video_path, caption)
            finally:
                self._save_context(context)
                context.close()

        return success

    def _load_context(self, playwright):
        browser = playwright.chromium.launch(headless=False)
        if SESSION_FILE.exists():
            logger.info(f"Session TikTok chargée : {SESSION_FILE}")
            storage = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            return browser.new_context(storage_state=storage)
        logger.info("Aucune session TikTok — nouveau contexte (connexion requise au premier lancement)")
        return browser.new_context()

    def _save_context(self, context) -> None:
        SESSION_FILE.write_text(
            json.dumps(context.storage_state(), ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Session TikTok sauvegardée : {SESSION_FILE}")

    def _upload_via_browser(self, page, video_path: Path, caption: str) -> bool:
        page.goto("https://www.tiktok.com/upload", wait_until="networkidle")

        # Connexion manuelle si nécessaire (premier lancement uniquement)
        if "login" in page.url or page.locator("text=Log in").count() > 0:
            logger.warning("Non connecté à TikTok.")
            logger.warning("Connectez-vous dans le navigateur ouvert, puis appuyez sur Entrée ici.")
            input(">>> Appuyez sur Entrée après connexion <<<")
            page.goto("https://www.tiktok.com/upload", wait_until="networkidle")

        # Sélection du fichier
        page.locator('input[type="file"]').set_input_files(str(video_path))
        logger.info("Fichier vidéo soumis, traitement en cours…")
        page.wait_for_timeout(8000)

        # Remplissage de la légende
        caption_box = page.locator('[data-contents="true"]').first
        caption_box.click()
        caption_box.fill("")
        page.keyboard.type(caption[:2200], delay=15)
        page.wait_for_timeout(1000)

        # Clic sur Publier
        post_btn = page.locator(
            'button:has-text("Post"), button:has-text("Publier")'
        ).first
        post_btn.click()

        # Attente de la confirmation
        try:
            page.wait_for_selector("text=successfully", timeout=30000)
            logger.info("Vidéo publiée avec succès sur TikTok ✓")
            return True
        except Exception:
            logger.warning(
                "Confirmation de publication non détectée. "
                "Vérifiez manuellement sur https://www.tiktok.com/creator-center"
            )
            return False
