import json
import logging
import time
from pathlib import Path
from typing import Optional

import httpx

import config

logger = logging.getLogger(__name__)

SESSION_FILE = config.SESSIONS_DIR / "tiktok_session.json"
TIKTOK_UPLOAD_API = "https://open.tiktokapis.com/v2/post/publish/video/init/"


class TikTokPublisher:
    def __init__(self):
        self.mode = config.TIKTOK_MODE
        self.access_token = config.TIKTOK_ACCESS_TOKEN

    def publish(self, video_path: Path, content: dict) -> bool:
        """Point d'entrée : publie selon le mode configuré."""
        caption = self._build_caption(content)
        logger.info(f"Publication TikTok en mode '{self.mode}' : {video_path.name}")

        if self.mode == "api":
            return self._publish_api(video_path, caption)
        elif self.mode == "playwright":
            return self._publish_playwright(video_path, caption, content)
        else:
            raise ValueError(f"Mode TikTok inconnu : {self.mode}")

    def _build_caption(self, content: dict) -> str:
        hashtags_str = " ".join(
            f"#{tag.lstrip('#')}" for tag in content.get("hashtags", [])
        )
        cta = content.get("call_to_action", "")
        desc = content.get("description_tiktok", "")
        return f"{desc}\n\n{cta}\n\n{hashtags_str}"

    # ─────────────────────────────────────────────
    # Mode 1 : API officielle TikTok Content Posting
    # ─────────────────────────────────────────────
    def _publish_api(self, video_path: Path, caption: str) -> bool:
        if not self.access_token:
            raise ValueError("TIKTOK_ACCESS_TOKEN manquant pour le mode API")

        file_size = video_path.stat().st_size
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        # Étape 1 : initialiser l'upload
        init_payload = {
            "post_info": {
                "title": caption[:2200],
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
            resp = client.post(TIKTOK_UPLOAD_API, headers=headers, json=init_payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("error", {}).get("code") != "ok":
            logger.error(f"Erreur API TikTok init : {data}")
            return False

        upload_url = data["data"]["upload_url"]
        publish_id = data["data"]["publish_id"]

        # Étape 2 : uploader le fichier
        video_bytes = video_path.read_bytes()
        upload_headers = {
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            "Content-Length": str(file_size),
        }
        with httpx.Client(timeout=120) as client:
            up_resp = client.put(upload_url, content=video_bytes, headers=upload_headers)
            up_resp.raise_for_status()

        logger.info(f"Vidéo uploadée. publish_id={publish_id}")
        return True

    # ─────────────────────────────────────────────
    # Mode 2 : Playwright (session persistante)
    # ─────────────────────────────────────────────
    def _publish_playwright(self, video_path: Path, caption: str, content: dict) -> bool:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError("Playwright non installé. Lancez : pip install playwright && playwright install chromium")

        with sync_playwright() as p:
            context = self._load_or_create_context(p)
            page = context.new_page()

            try:
                success = self._do_upload_playwright(page, video_path, caption)
            finally:
                self._save_session(context)
                context.close()

        return success

    def _load_or_create_context(self, playwright):
        """Charge la session sauvegardée ou crée un nouveau contexte."""
        browser = playwright.chromium.launch(headless=False)

        if SESSION_FILE.exists():
            logger.info("Session TikTok existante chargée")
            storage = json.loads(SESSION_FILE.read_text())
            context = browser.new_context(storage_state=storage)
        else:
            logger.info("Aucune session TikTok — nouvelle session (connexion manuelle requise)")
            context = browser.new_context()

        return context

    def _save_session(self, context) -> None:
        storage = context.storage_state()
        SESSION_FILE.write_text(json.dumps(storage))
        logger.info(f"Session TikTok sauvegardée : {SESSION_FILE}")

    def _do_upload_playwright(self, page, video_path: Path, caption: str) -> bool:
        page.goto("https://www.tiktok.com/upload", wait_until="networkidle")

        # Vérifier si connecté
        if "login" in page.url or page.locator("text=Log in").is_visible():
            logger.warning("Non connecté à TikTok — connexion manuelle requise")
            logger.warning("Connectez-vous dans le navigateur, puis appuyez sur Entrée...")
            input(">>> Appuyez sur Entrée après connexion manuelle <<<")
            page.goto("https://www.tiktok.com/upload", wait_until="networkidle")

        # Upload du fichier
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(video_path))
        logger.info("Fichier vidéo sélectionné, attente du traitement...")
        page.wait_for_timeout(8000)

        # Saisie de la légende
        caption_box = page.locator('[data-contents="true"]').first
        caption_box.click()
        caption_box.fill("")
        page.keyboard.type(caption[:2200], delay=20)
        page.wait_for_timeout(1000)

        # Publier
        post_button = page.locator('button:has-text("Post"), button:has-text("Publier")').first
        post_button.click()

        # Attendre confirmation
        try:
            page.wait_for_selector("text=successfully", timeout=30000)
            logger.info("Vidéo publiée avec succès sur TikTok")
            return True
        except Exception:
            logger.warning("Confirmation non détectée — vérifiez manuellement sur TikTok")
            return False
