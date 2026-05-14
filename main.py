#!/usr/bin/env python3
"""
Point d'entrée du pipeline de génération de vidéos chrétiennes pour TikTok.

Usage :
  python main.py                          # thème par défaut
  python main.py --theme "la paix"        # thème unique
  python main.py --batch themes.txt       # batch depuis un fichier
  python main.py --theme "espoir" --publish   # avec publication TikTok
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import config
from modules.pipeline import Pipeline


def setup_logging() -> None:
    log_file = config.LOGS_DIR / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
    )

    # Réduire le bruit des bibliothèques tierces
    for noisy in ["httpx", "httpcore", "urllib3", "asyncio", "moviepy"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.info(f"Logs écrits dans : {log_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline de génération de vidéos chrétiennes pour TikTok"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--theme",
        type=str,
        default="la confiance en Dieu",
        help="Thème pour générer une seule vidéo (défaut : 'la confiance en Dieu')",
    )
    group.add_argument(
        "--batch",
        type=Path,
        metavar="FICHIER",
        help="Fichier texte avec un thème par ligne pour le mode batch",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        default=False,
        help="Publier la vidéo sur TikTok après création",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        default=False,
        help="Génère uniquement le texte et l'audio (sans rendu vidéo)",
    )
    return parser.parse_args()


def load_batch_themes(filepath: Path) -> list[str]:
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier batch introuvable : {filepath}")
    themes = [
        line.strip()
        for line in filepath.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not themes:
        raise ValueError(f"Aucun thème trouvé dans {filepath}")
    return themes


def main() -> int:
    setup_logging()
    args = parse_args()

    logging.info("Démarrage du pipeline vidéo chrétien TikTok")
    logging.info(f"Config : voice={config.VOICE_NAME}, model={config.CLAUDE_MODEL}")

    pipeline = Pipeline(publish=args.publish)

    if args.batch:
        themes = load_batch_themes(args.batch)
        logging.info(f"Mode batch : {len(themes)} thème(s) depuis {args.batch}")
        results = pipeline.run_batch(themes)
        failed = [r for r in results if not r.success]
        return 1 if failed else 0
    else:
        result = pipeline.run_single(args.theme)
        return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
