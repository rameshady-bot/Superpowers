#!/usr/bin/env python3
"""
Pipeline de génération de vidéos chrétiennes pour TikTok.

Usage :
  # Mode intégré (textes bibliques pré-définis, aucune clé API)
  python main.py --theme "la confiance en Dieu"

  # Batch depuis un fichier
  python main.py --batch themes.txt

  # Avec génération Claude (nécessite ANTHROPIC_API_KEY dans .env)
  python main.py --theme "la paix" --use-claude

  # Avec publication TikTok
  python main.py --theme "espoir" --use-claude --publish
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import config
from modules.pipeline import Pipeline

# ── Textes bibliques intégrés (mode sans API) ─────────────────────────
BUILTIN_CONTENT = [
    {
        "theme": "la confiance en Dieu",
        "titre_interne": "confiance_en_dieu",
        "verset": "Proverbes 3:5-6",
        "script_voix_off": (
            "Est-ce que tu essaies de tout contrôler tout seul? "
            "Confie-toi en l'Éternel de tout ton cœur "
            "et ne t'appuie pas sur ta propre intelligence. "
            "Reconnais-le dans toutes tes voies, "
            "et il aplanira tes sentiers. "
            "Dieu ne te demande pas de tout comprendre. "
            "Il te demande de lui faire confiance. "
            "Lâche prise aujourd'hui. "
            "Il connaît le chemin mieux que toi."
        ),
        "description_tiktok": "Dieu connaît le chemin. Tu peux lui faire confiance aujourd'hui. 🙏",
        "hashtags": ["#foi", "#confiance", "#dieu", "#chretien", "#encouragement",
                     "#bible", "#proverbes", "#paix", "#spiritualite", "#jesus"],
        "call_to_action": "Commente AMEN si tu fais confiance à Dieu aujourd'hui.",
    },
    {
        "theme": "ne crains pas",
        "titre_interne": "ne_crains_pas",
        "verset": "Ésaïe 41:10",
        "script_voix_off": (
            "Ne crains pas, car je suis avec toi. "
            "Ne te décourage pas, car je suis ton Dieu. "
            "Je te fortifie, oui, je t'aide. "
            "Je te soutiens de ma main droite victorieuse. "
            "Quelles que soient les tempêtes de ta vie aujourd'hui, "
            "rappelle-toi que le Seigneur marche à tes côtés. "
            "Tu n'es jamais seul. "
            "Sa présence est ta force. "
            "Laisse cette vérité entrer dans ton cœur."
        ),
        "description_tiktok": "Tu n'es jamais seul. Dieu est avec toi dans cette tempête. 💙",
        "hashtags": ["#nevercrainspas", "#dieu", "#esaie", "#encouragement", "#foi",
                     "#chretien", "#bible", "#force", "#espoir", "#jesus"],
        "call_to_action": "Partage si quelqu'un a besoin d'entendre ça aujourd'hui.",
    },
    {
        "theme": "l'espérance",
        "titre_interne": "esperance_avenir",
        "verset": "Jérémie 29:11",
        "script_voix_off": (
            "Est-ce que ton avenir te fait peur? "
            "Car je connais les projets que j'ai formés sur vous, déclare l'Éternel. "
            "Des projets de paix et non de malheur, "
            "afin de vous donner un avenir et de l'espérance. "
            "Dieu n'a pas oublié ton histoire. "
            "Chaque douleur, chaque larme, il les voit. "
            "Et au-delà de ce que tu traverses, "
            "il prépare quelque chose de beau pour ta vie."
        ),
        "description_tiktok": "Dieu a un plan pour toi. L'espérance n'est pas une illusion. ✨",
        "hashtags": ["#esperance", "#jeremie", "#avenir", "#foi", "#dieu",
                     "#encouragement", "#chretien", "#bible", "#espoir", "#jesus"],
        "call_to_action": "Dis ESPOIR en commentaire pour le recevoir à nouveau demain.",
    },
    {
        "theme": "la paix de Dieu",
        "titre_interne": "paix_de_dieu",
        "verset": "Jean 14:27",
        "script_voix_off": (
            "Ton cœur est agité en ce moment? "
            "Jésus dit : je vous laisse la paix, je vous donne ma paix. "
            "Je ne vous donne pas comme le monde donne. "
            "Que votre cœur ne se trouble pas et ne se décourage pas. "
            "Dans un monde agité, Jésus t'offre une paix différente. "
            "Une paix qui ne dépend pas des circonstances. "
            "Accueille-la maintenant. "
            "Pose ton fardeau devant lui."
        ),
        "description_tiktok": "La paix que Jésus donne surpasse toute compréhension. 🕊️",
        "hashtags": ["#paix", "#jean", "#jesus", "#foi", "#dieu",
                     "#encouragement", "#chretien", "#bible", "#serenite", "#repos"],
        "call_to_action": "Tape PAIX si tu as besoin de cette paix aujourd'hui.",
    },
    {
        "theme": "je puis tout",
        "titre_interne": "force_en_lui",
        "verset": "Philippiens 4:13",
        "script_voix_off": (
            "Tu te sens à bout de forces? "
            "Je puis tout par celui qui me fortifie. "
            "Cette parole n'est pas un slogan. C'est une promesse vivante. "
            "Tu traverses peut-être une période difficile, "
            "un moment où tes forces semblent épuisées. "
            "Mais Dieu te dit : ma grâce te suffit. "
            "Ma puissance s'accomplit dans la faiblesse. "
            "Lève-toi avec foi. Il est ta force."
        ),
        "description_tiktok": "Philippiens 4:13 n'est pas un tatouage. C'est une promesse vivante. 💪",
        "hashtags": ["#force", "#philippiens", "#jesus", "#foi", "#dieu",
                     "#encouragement", "#chretien", "#bible", "#victoire", "#puissance"],
        "call_to_action": "Écris FORT si tu as besoin de cette force aujourd'hui.",
    },
]


def find_builtin_content(theme: str) -> dict:
    """Cherche un contenu intégré par thème (correspondance partielle)."""
    theme_lower = theme.lower()
    for item in BUILTIN_CONTENT:
        if (theme_lower in item["theme"].lower()
                or item["theme"].lower() in theme_lower
                or item["titre_interne"].replace("_", " ") in theme_lower):
            return item

    # Fallback sur le premier si aucune correspondance
    logger.warning(
        f"Thème '{theme}' non trouvé dans les contenus intégrés. "
        f"Utilisation du thème par défaut : '{BUILTIN_CONTENT[0]['theme']}'."
    )
    return BUILTIN_CONTENT[0]


def setup_logging() -> None:
    log_file = config.LOGS_DIR / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[fh, ch])

    for noisy in ["httpx", "httpcore", "urllib3", "asyncio"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.info(f"Logs → {log_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline de vidéos chrétiennes TikTok",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--theme", type=str, default="la confiance en Dieu",
                       help="Thème unique (défaut : 'la confiance en Dieu')")
    group.add_argument("--batch", type=Path, metavar="FICHIER",
                       help="Fichier texte avec un thème par ligne")

    parser.add_argument("--use-claude", action="store_true",
                        help="Générer les textes via Claude API (requiert ANTHROPIC_API_KEY)")
    parser.add_argument("--publish", action="store_true",
                        help="Publier la vidéo sur TikTok après création")
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()
    logging.info(f"Config : voice={config.VOICE_ID}, fps={config.VIDEO_FPS}, "
                 f"tiktok_mode={config.TIKTOK_MODE}")

    pipeline = Pipeline(publish=args.publish, use_claude=args.use_claude)

    if args.batch:
        if not args.batch.exists():
            logging.error(f"Fichier batch introuvable : {args.batch}")
            return 1
        themes = [
            l.strip() for l in args.batch.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")
        ]
        if not themes:
            logging.error(f"Aucun thème dans {args.batch}")
            return 1

        items = []
        for theme in themes:
            item: dict = {"theme": theme}
            if not args.use_claude:
                item["content"] = find_builtin_content(theme)
            items.append(item)

        results = pipeline.run_batch(items)
        return 0 if all(r.success for r in results) else 1
    else:
        content = None if args.use_claude else find_builtin_content(args.theme)
        result  = pipeline.run_single(args.theme, content=content)
        return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
