"""
Metadata builder — generates title, hashtags, optimal posting slots, and video metadata.
Optimal slots are based on TikTok engagement patterns for French Christian audiences.
"""

import logging
from datetime import datetime, date as date_type
from typing import Any

logger = logging.getLogger(__name__)

# TikTok optimal posting windows for FR Christian content (CET/CEST)
OPTIMAL_SLOTS = [
    {
        "day": "Dimanche",
        "time_cet": "09:00–10:00",
        "rationale": "Dévotion matinale / avant l'église — fort engagement spirituel",
    },
    {
        "day": "Mercredi",
        "time_cet": "12:00–13:00",
        "rationale": "Encouragement de mi-semaine — pic d'ouverture TikTok sur pause déjeuner",
    },
    {
        "day": "Vendredi",
        "time_cet": "18:30–19:30",
        "rationale": "Fin de semaine — contenu inspirant partagé avant le week-end",
    },
]

# Hashtag pools by theme category
HASHTAG_POOLS: dict[str, list[str]] = {
    "anxiété": [
        "#anxiété", "#paixintérieure", "#philippiens46", "#confiance",
        "#foichretienne", "#videchrétien",
    ],
    "espoir": [
        "#espoir", "#foi", "#esperance", "#dieu", "#chrétientiktok",
        "#encouragement",
    ],
    "solitude": [
        "#solitude", "#dieuavectoi", "#paix", "#foi", "#chretientiktok",
        "#versetdujour",
    ],
    "purpose": [
        "#vocation", "#foi", "#voiededieu", "#chretientiktok",
        "#identitéchretienne",
    ],
    "_default": [
        "#foi", "#chrétientiktok", "#encouragement", "#versetdujour",
        "#dieu", "#france", "#francophone", "#chretientiktok",
        "#motivationchrétienne", "#bibletiktok",
    ],
}

UNIVERSAL_HASHTAGS = [
    "#foi", "#chrétientiktok", "#versetdujour", "#dieu",
    "#encouragement", "#bibletiktok",
]


def _pick_hashtags(theme: str, verse: str) -> list[str]:
    theme_lower = theme.lower()
    pool = HASHTAG_POOLS.get(theme_lower, HASHTAG_POOLS["_default"])
    combined = list(dict.fromkeys(pool + UNIVERSAL_HASHTAGS))  # deduplicate, preserve order
    return combined[:12]


def _build_title(theme: str, verse: str) -> str:
    titles = [
        f"Tu traverses {theme} ? Ce verset va tout changer 🙏",
        f"Pour tous ceux qui luttent avec {theme} — {verse}",
        f"Dieu a quelque chose à te dire sur {theme}",
        f"Si tu ressens {theme}, regarde jusqu'au bout 💛",
    ]
    import hashlib
    idx = int(hashlib.md5(f"{theme}{verse}".encode()).hexdigest(), 16) % len(titles)
    return titles[idx]


class MetadataBuilder:
    def build(self, theme: str, verse: str, date: str) -> dict[str, Any]:
        title = _build_title(theme, verse)
        hashtags = _pick_hashtags(theme, verse)

        metadata = {
            "date": date,
            "theme": theme,
            "verse": verse,
            "title": title,
            "hashtags": hashtags,
            "hashtag_string": " ".join(hashtags),
            "optimal_post_times": OPTIMAL_SLOTS,
            "status": "pending_review",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "platform": "TikTok",
            "target_audience": "Croyants francophones, 18–35 ans",
            "language": "fr",
            "content_warnings": [],
            "denomination_neutral": True,
        }

        logger.info("Metadata built for theme='%s' verse='%s'", theme, verse)
        return metadata
