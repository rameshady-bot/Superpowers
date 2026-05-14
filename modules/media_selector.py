"""
Sélection automatique des médias (vidéo de fond + musique) selon le thème.

Arborescence attendue :
  assets/videos/
    nature/     ← forêt, pluie, rivière
    ciel/       ← coucher de soleil, nuages, étoiles
    eau/        ← océan, lac, cascade
    lumiere/    ← lumière dorée, rayons, bougies
    croix/      ← croix, église, vitrail
    default/    ← fallback générique

  assets/music/
    calme/      ← piano doux, ambient
    inspirant/  ← orchestre montant
    celebration/← joyeux, louange
    priere/     ← choral, contemplatif
    default/    ← fallback générique
"""

import logging
import random
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)

# ── Mapping thème → catégorie visuelle ───────────────────────────────
THEME_TO_VISUAL: dict[str, list[str]] = {
    # Foi / confiance
    "confiance":    ["nature", "lumiere"],
    "foi":          ["ciel", "lumiere"],
    "croire":       ["ciel", "lumiere"],
    "dieu":         ["lumiere", "ciel"],
    "seigneur":     ["lumiere", "ciel"],

    # Paix / repos
    "paix":         ["eau", "nature"],
    "repos":        ["eau", "nature"],
    "calme":        ["eau", "nature"],
    "sérénité":     ["eau", "nature"],

    # Espoir / avenir
    "espoir":       ["ciel", "lumiere"],
    "espérance":    ["ciel", "lumiere"],
    "avenir":       ["ciel", "nature"],
    "futur":        ["ciel", "nature"],

    # Force / victoire
    "force":        ["nature", "ciel"],
    "victoire":     ["ciel", "lumiere"],
    "courage":      ["nature", "ciel"],
    "surmonter":    ["nature", "ciel"],
    "persévérer":   ["nature", "ciel"],

    # Prière / spiritualité
    "prière":       ["lumiere", "croix"],
    "prier":        ["lumiere", "croix"],
    "adoration":    ["croix", "lumiere"],
    "louange":      ["ciel", "lumiere"],
    "saint":        ["croix", "lumiere"],

    # Amour / grâce
    "amour":        ["lumiere", "nature"],
    "grâce":        ["lumiere", "eau"],
    "pardon":       ["eau", "lumiere"],
    "miséricorde":  ["eau", "lumiere"],

    # Épreuve / résilience
    "épreuve":      ["nature", "eau"],
    "souffrance":   ["eau", "nature"],
    "guérison":     ["lumiere", "eau"],
    "recommencer":  ["ciel", "nature"],
}

# ── Mapping thème → ambiance musicale ────────────────────────────────
THEME_TO_MUSIC: dict[str, str] = {
    "confiance":    "calme",
    "foi":          "inspirant",
    "croire":       "inspirant",
    "dieu":         "priere",
    "seigneur":     "priere",
    "paix":         "calme",
    "repos":        "calme",
    "calme":        "calme",
    "sérénité":     "calme",
    "espoir":       "inspirant",
    "espérance":    "inspirant",
    "avenir":       "inspirant",
    "futur":        "inspirant",
    "force":        "inspirant",
    "victoire":     "celebration",
    "courage":      "inspirant",
    "surmonter":    "inspirant",
    "persévérer":   "inspirant",
    "prière":       "priere",
    "prier":        "priere",
    "adoration":    "priere",
    "louange":      "celebration",
    "saint":        "priere",
    "amour":        "calme",
    "grâce":        "calme",
    "pardon":       "calme",
    "miséricorde":  "calme",
    "épreuve":      "calme",
    "souffrance":   "calme",
    "guérison":     "inspirant",
    "recommencer":  "inspirant",
}


def _match_theme(theme: str) -> tuple[list[str], str]:
    """Retourne (catégories_visuelles, catégorie_musicale) pour un thème."""
    theme_lower = theme.lower()
    visuals, music = None, None

    for keyword in THEME_TO_VISUAL:
        if keyword in theme_lower:
            visuals = THEME_TO_VISUAL[keyword]
            break

    for keyword in THEME_TO_MUSIC:
        if keyword in theme_lower:
            music = THEME_TO_MUSIC[keyword]
            break

    return (visuals or ["default"]), (music or "default")


def _pick_file(base_dir: Path, categories: list[str],
               extensions: set[str]) -> Optional[Path]:
    """
    Cherche un fichier dans les catégories données (ordre de priorité).
    Retourne un fichier aléatoire, ou None si rien n'est trouvé.
    """
    candidates: list[Path] = []

    for cat in categories:
        folder = base_dir / cat
        if folder.is_dir():
            found = [f for f in folder.iterdir()
                     if f.suffix.lower() in extensions and f.stat().st_size > 0]
            candidates.extend(found)
        if candidates:
            break  # priorité à la première catégorie qui a des fichiers

    # Fallback global dans tout base_dir (hors sous-dossiers nommés)
    if not candidates:
        for f in base_dir.rglob("*"):
            if f.suffix.lower() in extensions and f.stat().st_size > 0:
                candidates.append(f)

    return random.choice(candidates) if candidates else None


def select_video(theme: str) -> Path:
    """
    Sélectionne une vidéo de fond dans assets/videos/ selon le thème.
    Lève FileNotFoundError si aucune vidéo n'est disponible.
    """
    visuals, _ = _match_theme(theme)
    logger.info(f"Thème '{theme}' → catégories visuelles : {visuals}")

    video = _pick_file(config.VIDEOS_DIR, visuals, config.VIDEO_EXTENSIONS)
    if video is None:
        raise FileNotFoundError(
            f"Aucune vidéo trouvée dans {config.VIDEOS_DIR}.\n"
            f"Ajoutez des fichiers .mp4/.mov dans : "
            f"{config.VIDEOS_DIR}/nature/, /ciel/, /eau/, /lumiere/, /croix/, /default/"
        )

    logger.info(f"Vidéo sélectionnée : {video.relative_to(config.BASE_DIR)}")
    return video


def select_music(theme: str) -> Optional[Path]:
    """
    Sélectionne une musique de fond dans assets/music/ selon l'ambiance.
    Retourne None (sans erreur) si aucune musique n'est disponible.
    """
    _, music_cat = _match_theme(theme)
    logger.info(f"Thème '{theme}' → ambiance musicale : {music_cat}")

    music = _pick_file(config.MUSIC_DIR, [music_cat], config.AUDIO_EXTENSIONS)
    if music is None:
        logger.warning(
            f"Aucune musique trouvée dans {config.MUSIC_DIR}.\n"
            f"Ajoutez des fichiers .mp3/.wav dans : "
            f"{config.MUSIC_DIR}/calme/, /inspirant/, /celebration/, /priere/, /default/\n"
            f"La vidéo sera générée sans musique de fond."
        )
        return None

    logger.info(f"Musique sélectionnée : {music.relative_to(config.BASE_DIR)}")
    return music
