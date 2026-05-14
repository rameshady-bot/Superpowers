"""
Script generator — uses Claude to produce 150–200 word French TikTok scripts
for a Christian encouragement channel.
"""

import logging
import os
import time
from pathlib import Path

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un créateur de contenu TikTok chrétien francophone.
Tu écris des scripts courts (150–200 mots) pour des vidéos de 15–60 secondes.
Ton ton est chaleureux, direct et non dogmatique — comme un ami de confiance, pas un prédicateur.
Tu ne représentes aucune dénomination spécifique ni position politique.

Structure OBLIGATOIRE de chaque script :
1. ACCROCHE (3 premières secondes) — une question, une affirmation forte, ou un point de douleur relatable
2. MESSAGE — un verset biblique ou encouragement ancré dans la vie chrétienne quotidienne
3. APPEL À L'ACTION — ex: "Commente AMEN si tu ressens ça", "Sauvegarde pour y revenir", "Tague quelqu'un qui a besoin de lire ça"

Contraintes :
- 150–200 mots maximum
- Rythme : 130–145 mots par minute (adapté TikTok)
- Langue : français naturel, pas formel
- Jamais de musique de fond suggérée
- Le verset doit être cité précisément avec sa référence
- NE PAS inclure de didascalies ou instructions de mise en scène"""

USER_PROMPT_TEMPLATE = """Écris un script TikTok sur le thème : {theme}
Verset de référence : {verse}

Réponds uniquement avec le texte du script, sans titres ni formatage."""

COST_LOG = Path("logs/costs.log")


def _log_cost(model: str, input_tokens: int, output_tokens: int) -> None:
    COST_LOG.parent.mkdir(exist_ok=True)
    # Pricing: claude-3-5-haiku input $0.80/M, output $4.00/M
    cost = (input_tokens * 0.0000008) + (output_tokens * 0.000004)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with COST_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} | ANTHROPIC  | script_generation  | ~${cost:.4f} | {model} | in={input_tokens} out={output_tokens}\n")
    logger.info("Anthropic cost logged: $%.4f", cost)


class ScriptGenerator:
    def __init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set in environment")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = "claude-haiku-4-5-20251001"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        reraise=True,
    )
    async def generate(self, theme: str, verse: str) -> str:
        """Generate a 150–200 word French TikTok script."""
        logger.info("Generating script for theme='%s' verse='%s'", theme, verse)

        response = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(theme=theme, verse=verse),
                }
            ],
        )

        _log_cost(
            model=self._model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        script = response.content[0].text.strip()
        word_count = len(script.split())
        logger.info("Script generated: %d words", word_count)

        if word_count > 220:
            logger.warning("Script exceeds 220 words (%d) — truncating not applied, review manually", word_count)

        return script
