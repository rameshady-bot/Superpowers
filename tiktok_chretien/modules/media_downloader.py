"""
Téléchargement automatique de vidéos de fond et de musiques.

Sources supportées :
  - Pexels  (vidéos)  : PEXELS_API_KEY dans .env
  - Pixabay (vidéos)  : PIXABAY_API_KEY dans .env
  - Fichiers locaux   : fallback automatique si aucune clé API

Les fichiers sont mis en cache dans assets/videos/ et assets/music/
pour éviter les re-téléchargements.
"""

import logging
import os
import random
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}

PEXELS_VIDEO_API  = "https://api.pexels.com/videos/search"
PIXABAY_VIDEO_API = "https://pixabay.com/api/videos/"


class MediaDownloader:
    def __init__(
        self,
        videos_dir: Path,
        music_dir: Path,
        pexels_key: str = "",
        pixabay_key: str = "",
    ):
        self.videos_dir  = videos_dir
        self.music_dir   = music_dir
        self.pexels_key  = pexels_key
        self.pixabay_key = pixabay_key

    # ── Vidéo de fond ────────────────────────────────────────────────
    def get_background_video(
        self,
        categorie: str,
        queries: list[str],
        force_download: bool = False,
    ) -> Path:
        """
        Retourne une vidéo de fond pour la catégorie donnée.
        1. Cherche dans assets/videos/<categorie>/  (cache local)
        2. Tente Pexels si PEXELS_API_KEY disponible
        3. Tente Pixabay si PIXABAY_API_KEY disponible
        4. Fallback sur assets/videos/default/
        Lève FileNotFoundError si aucune vidéo trouvée.
        """
        folder = self.videos_dir / categorie
        folder.mkdir(parents=True, exist_ok=True)

        if not force_download:
            cached = self._pick_local(folder)
            if cached:
                logger.info(f"Vidéo locale : {cached.name}")
                return cached

        # Tentative de téléchargement
        if self.pexels_key:
            for query in queries:
                path = self._download_from_pexels(query, folder)
                if path:
                    return path

        if self.pixabay_key:
            for query in queries:
                path = self._download_from_pixabay(query, folder)
                if path:
                    return path

        # Fallback dossier default
        default_folder = self.videos_dir / "default"
        fallback = self._pick_local(default_folder)
        if fallback:
            logger.warning(
                f"Aucune vidéo '{categorie}' — utilisation du fallback : {fallback.name}"
            )
            return fallback

        raise FileNotFoundError(
            f"Aucune vidéo de fond disponible.\n"
            f"Solutions :\n"
            f"  1. Ajoutez un fichier .mp4 dans : {folder}\n"
            f"  2. Configurez PEXELS_API_KEY dans .env\n"
            f"  3. Configurez PIXABAY_API_KEY dans .env"
        )

    def _pick_local(self, folder: Path) -> Optional[Path]:
        if not folder.is_dir():
            return None
        files = [
            f for f in folder.iterdir()
            if f.suffix.lower() in VIDEO_EXTENSIONS and f.stat().st_size > 1024
        ]
        return random.choice(files) if files else None

    def _download_from_pexels(self, query: str, dest_folder: Path) -> Optional[Path]:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    PEXELS_VIDEO_API,
                    headers={"Authorization": self.pexels_key},
                    params={"query": query, "per_page": 10, "orientation": "portrait"},
                )
                resp.raise_for_status()
                videos = resp.json().get("videos", [])

            if not videos:
                logger.warning(f"Pexels — aucun résultat pour '{query}'")
                return None

            video = random.choice(videos[:5])
            # Préfère la résolution HD (1280x720 ou moins pour éviter les gros fichiers)
            files = video.get("video_files", [])
            best = self._pick_best_resolution(files, max_height=1280)
            if not best:
                return None

            url  = best["link"]
            name = f"pexels_{video['id']}.mp4"
            return self._download_file(url, dest_folder / name)

        except httpx.HTTPError as e:
            logger.warning(f"Pexels HTTP erreur : {e}")
            return None
        except Exception as e:
            logger.warning(f"Pexels erreur : {e}")
            return None

    def _download_from_pixabay(self, query: str, dest_folder: Path) -> Optional[Path]:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    PIXABAY_VIDEO_API,
                    params={
                        "key": self.pixabay_key,
                        "q": query,
                        "video_type": "film",
                        "per_page": 10,
                    },
                )
                resp.raise_for_status()
                hits = resp.json().get("hits", [])

            if not hits:
                logger.warning(f"Pixabay — aucun résultat pour '{query}'")
                return None

            item = random.choice(hits[:5])
            videos = item.get("videos", {})
            # Préfère medium (640p) ou large (1080p)
            for quality in ("medium", "large", "small"):
                entry = videos.get(quality)
                if entry and entry.get("url"):
                    name = f"pixabay_{item['id']}_{quality}.mp4"
                    return self._download_file(entry["url"], dest_folder / name)

            return None

        except httpx.HTTPError as e:
            logger.warning(f"Pixabay HTTP erreur : {e}")
            return None
        except Exception as e:
            logger.warning(f"Pixabay erreur : {e}")
            return None

    @staticmethod
    def _pick_best_resolution(
        files: list[dict], max_height: int = 1280
    ) -> Optional[dict]:
        """Sélectionne la résolution la plus haute ≤ max_height."""
        eligible = [
            f for f in files
            if f.get("height", 0) <= max_height and f.get("link")
        ]
        if not eligible:
            return files[0] if files else None
        return max(eligible, key=lambda f: f.get("height", 0))

    def _download_file(self, url: str, dest: Path) -> Optional[Path]:
        if dest.exists() and dest.stat().st_size > 1024:
            logger.info(f"Déjà en cache : {dest.name}")
            return dest
        try:
            logger.info(f"Téléchargement : {url[:60]}…")
            with httpx.Client(timeout=120, follow_redirects=True) as client:
                with client.stream("GET", url) as r:
                    r.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in r.iter_bytes(chunk_size=65536):
                            f.write(chunk)
            size_mb = dest.stat().st_size / (1024 * 1024)
            logger.info(f"Téléchargé : {dest.name} ({size_mb:.1f} Mo)")
            return dest
        except Exception as e:
            logger.error(f"Échec téléchargement {url[:60]} : {e}")
            if dest.exists():
                dest.unlink()
            return None

    # ── Musique de fond ───────────────────────────────────────────────
    def get_music(self, ambiance: str) -> Optional[Path]:
        """
        Retourne une musique de fond depuis assets/music/<ambiance>/.
        Retourne None (sans erreur) si aucune musique n'est trouvée.
        """
        folder = self.music_dir / ambiance
        track  = self._pick_local_audio(folder)
        if track:
            logger.info(f"Musique : {track.name}")
            return track

        # Fallback default
        default = self._pick_local_audio(self.music_dir / "default")
        if default:
            logger.warning(f"Musique '{ambiance}' absente — fallback : {default.name}")
            return default

        logger.warning(
            f"Aucune musique trouvée dans {self.music_dir}.\n"
            f"Ajoutez des fichiers .mp3/.wav dans : {folder}\n"
            f"Sources gratuites : pixabay.com/music, freemusicarchive.org"
        )
        return None

    def _pick_local_audio(self, folder: Path) -> Optional[Path]:
        if not folder.is_dir():
            return None
        files = [
            f for f in folder.iterdir()
            if f.suffix.lower() in AUDIO_EXTENSIONS and f.stat().st_size > 1024
        ]
        return random.choice(files) if files else None
