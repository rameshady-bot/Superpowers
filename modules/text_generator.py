"""
Génération du contenu textuel via l'API Claude.
Retourne un JSON structuré exploitable par le reste du pipeline.
"""

import json
import logging
import re

import anthropic

import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un créateur de contenu chrétien spécialisé pour TikTok.
Tu génères des scripts d'encouragement chrétien courts, percutants, authentiques et adaptés à un public francophone.
Tes vidéos durent entre 45 et 75 secondes. Le script voix-off doit être naturel, chaleureux, et spirituellement riche.
Tu réponds UNIQUEMENT avec du JSON valide, sans aucun texte avant ou après."""

JSON_SCHEMA = """{
  "theme": "string — thème principal en 2-4 mots",
  "titre_interne": "string — slug snake_case sans accents ni espaces",
  "verset": "string — référence biblique courte ex: Jean 3:16",
  "script_voix_off": "string — script complet 120-180 mots, naturel, avec pauses",
  "description_tiktok": "string — accroche max 150 caractères",
  "hashtags": ["liste", "de", "10", "à", "15", "hashtags"],
  "call_to_action": "string — phrase finale max 15 mots"
}"""

USER_PROMPT = """Génère du contenu TikTok chrétien d'encouragement sur le thème : "{theme}"

Le script doit :
- Commencer par une phrase d'accroche forte (question ou affirmation percutante)
- Intégrer naturellement un verset ou une histoire biblique
- Apporter un encouragement concret et applicable aujourd'hui
- Se terminer par le call_to_action

JSON attendu :
{schema}"""


class TextGenerator:
    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY manquante.\n"
                "Ajoutez-la dans votre fichier .env : ANTHROPIC_API_KEY=sk-ant-..."
            )
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def generate(self, theme: str) -> dict:
        logger.info(f"Génération Claude — thème : '{theme}'")

        message = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": USER_PROMPT.format(theme=theme, schema=JSON_SCHEMA),
            }],
        )

        raw = message.content[0].text.strip()
        content = self._parse_json(raw)
        self._validate(content)
        logger.info(f"Contenu généré : {content['titre_interne']}")
        return content

    def _parse_json(self, text: str) -> dict:
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"La réponse Claude n'est pas un JSON valide : {e}\n"
                f"Réponse brute :\n{text[:500]}"
            ) from e

    def _validate(self, content: dict) -> None:
        required = [
            "theme", "titre_interne", "verset", "script_voix_off",
            "description_tiktok", "hashtags", "call_to_action",
        ]
        missing = [k for k in required if k not in content]
        if missing:
            raise ValueError(f"Champs manquants dans le JSON Claude : {missing}")
        if not isinstance(content["hashtags"], list):
            raise ValueError("'hashtags' doit être une liste JSON.")
