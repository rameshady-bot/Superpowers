import json
import logging
import re
from typing import Optional

import anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un créateur de contenu chrétien spécialisé pour TikTok.
Tu génères des scripts d'encouragement chrétien courts, percutants, authentiques et adaptés à un public francophone.
Tes vidéos durent entre 45 et 75 secondes. Le script voix-off doit être naturel, chaleureux, et spirituellement riche.
Tu réponds UNIQUEMENT avec du JSON valide, sans aucun texte avant ou après."""

JSON_TEMPLATE = """
{
  "theme": "string - le thème principal en 2-4 mots",
  "titre_interne": "string - titre de fichier court sans espaces ni accents (snake_case)",
  "script_voix_off": "string - script complet à lire, naturel, entre 120 et 180 mots, avec pauses naturelles",
  "description_tiktok": "string - description engageante max 150 caractères",
  "hashtags": ["liste", "de", "10", "a", "15", "hashtags", "pertinents"],
  "call_to_action": "string - phrase d'appel à l'action en fin de vidéo, max 15 mots"
}
"""

USER_PROMPT_TEMPLATE = """Génère du contenu TikTok chrétien d'encouragement sur le thème : "{theme}"

Le script doit :
- Commencer par une phrase d'accroche forte (question ou affirmation)
- Inclure une référence biblique intégrée naturellement (verset ou histoire)
- Apporter un encouragement concret et applicable aujourd'hui
- Se terminer par le call to action

Réponds avec ce JSON exact :
{template}"""


class TextGenerator:
    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY manquante dans le fichier .env")
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def generate(self, theme: str) -> dict:
        logger.info(f"Génération du texte pour le thème : '{theme}'")

        prompt = USER_PROMPT_TEMPLATE.format(theme=theme, template=JSON_TEMPLATE)

        message = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        content = self._extract_json(raw)

        self._validate(content)
        logger.info(f"Texte généré avec succès : {content['titre_interne']}")
        return content

    def _extract_json(self, text: str) -> dict:
        # Supprime les blocs markdown si Claude les ajoute
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide reçu :\n{text}")
            raise ValueError(f"La réponse Claude n'est pas un JSON valide : {e}") from e

    def _validate(self, content: dict) -> None:
        required = ["theme", "titre_interne", "script_voix_off",
                    "description_tiktok", "hashtags", "call_to_action"]
        missing = [k for k in required if k not in content]
        if missing:
            raise ValueError(f"Champs manquants dans le JSON généré : {missing}")
        if not isinstance(content["hashtags"], list):
            raise ValueError("Le champ 'hashtags' doit être une liste")
