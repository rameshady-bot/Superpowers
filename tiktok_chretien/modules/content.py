"""
Contenu chrétien intégré + mapping thème → ambiance → médias.

Ce module est indépendant de toute API : il fonctionne hors ligne.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────
# Structure d'un message vidéo
# ─────────────────────────────────────────────────────────────────────
@dataclass
class VideoContent:
    theme: str
    titre_interne: str          # slug snake_case pour nommage fichiers
    verset: str                 # référence biblique (ex: Jean 3:16)
    script: str                 # texte lu en voix off
    description_tiktok: str     # légende TikTok (< 150 chars)
    hashtags: list[str]
    call_to_action: str
    ambiance: str = "calme"     # calme | inspirant | celebration | priere
    categorie_visuelle: str = "nature"  # nature | ciel | eau | lumiere | croix


# ─────────────────────────────────────────────────────────────────────
# Catalogue de messages bibliques
# ─────────────────────────────────────────────────────────────────────
CATALOGUE: list[VideoContent] = [
    VideoContent(
        theme="la confiance en Dieu",
        titre_interne="confiance_en_dieu",
        verset="Proverbes 3:5-6",
        ambiance="calme",
        categorie_visuelle="nature",
        script=(
            "Est-ce que tu essaies de tout contrôler seul ? "
            "Confie-toi en l'Éternel de tout ton cœur "
            "et ne t'appuie pas sur ta propre intelligence. "
            "Reconnais-le dans toutes tes voies, "
            "et il aplanira tes sentiers. "
            "Dieu ne te demande pas de tout comprendre. "
            "Il te demande simplement de lui faire confiance. "
            "Lâche prise aujourd'hui. "
            "Il connaît le chemin mieux que toi."
        ),
        description_tiktok="Dieu connaît le chemin. Tu peux lui faire confiance aujourd'hui. 🙏",
        hashtags=["#foi", "#confiance", "#dieu", "#chretien", "#encouragement",
                  "#bible", "#proverbes", "#paix", "#spiritualite", "#jesus"],
        call_to_action="Commente AMEN si tu fais confiance à Dieu aujourd'hui.",
    ),
    VideoContent(
        theme="ne crains pas",
        titre_interne="ne_crains_pas",
        verset="Ésaïe 41:10",
        ambiance="inspirant",
        categorie_visuelle="ciel",
        script=(
            "Est-ce que la peur te paralyse en ce moment ? "
            "Ne crains pas, car je suis avec toi. "
            "Ne te décourage pas, car je suis ton Dieu. "
            "Je te fortifie. Oui, je t'aide. "
            "Je te soutiens de ma main droite victorieuse. "
            "Quelles que soient les tempêtes de ta vie aujourd'hui, "
            "rappelle-toi que le Seigneur marche à tes côtés. "
            "Tu n'es jamais seul. Sa présence est ta force."
        ),
        description_tiktok="Tu n'es jamais seul. Dieu marche avec toi dans cette tempête. 💙",
        hashtags=["#ncrainspas", "#esaie", "#dieu", "#foi", "#force",
                  "#encouragement", "#chretien", "#bible", "#jesus", "#espoir"],
        call_to_action="Partage si quelqu'un a besoin d'entendre ça aujourd'hui.",
    ),
    VideoContent(
        theme="l'espérance et l'avenir",
        titre_interne="esperance_avenir",
        verset="Jérémie 29:11",
        ambiance="inspirant",
        categorie_visuelle="ciel",
        script=(
            "Est-ce que ton avenir te fait peur ? "
            "Car je connais les projets que j'ai formés sur vous, déclare l'Éternel. "
            "Des projets de paix et non de malheur, "
            "afin de vous donner un avenir et de l'espérance. "
            "Dieu n'a pas oublié ton histoire. "
            "Chaque douleur, chaque larme, il les voit. "
            "Au-delà de ce que tu traverses, "
            "il prépare quelque chose de beau pour ta vie."
        ),
        description_tiktok="Dieu a un plan pour toi. L'espérance n'est pas une illusion. ✨",
        hashtags=["#esperance", "#jeremie", "#avenir", "#foi", "#dieu",
                  "#encouragement", "#chretien", "#bible", "#espoir", "#jesus"],
        call_to_action="Dis ESPOIR en commentaire pour le recevoir à nouveau demain.",
    ),
    VideoContent(
        theme="la paix de Dieu",
        titre_interne="paix_de_dieu",
        verset="Jean 14:27",
        ambiance="calme",
        categorie_visuelle="eau",
        script=(
            "Ton cœur est agité en ce moment ? "
            "Jésus dit : je vous laisse la paix, je vous donne ma paix. "
            "Je ne vous donne pas comme le monde donne. "
            "Que votre cœur ne se trouble pas et ne se décourage pas. "
            "Dans un monde agité, Jésus t'offre une paix différente. "
            "Une paix qui ne dépend pas des circonstances. "
            "Accueille-la maintenant. Pose ton fardeau devant lui."
        ),
        description_tiktok="La paix que Jésus donne surpasse toute compréhension. 🕊️",
        hashtags=["#paix", "#jean", "#jesus", "#foi", "#dieu",
                  "#encouragement", "#chretien", "#bible", "#serenite", "#repos"],
        call_to_action="Tape PAIX si tu as besoin de cette paix aujourd'hui.",
    ),
    VideoContent(
        theme="je puis tout par Christ",
        titre_interne="force_en_christ",
        verset="Philippiens 4:13",
        ambiance="celebration",
        categorie_visuelle="lumiere",
        script=(
            "Tu te sens à bout de forces ? "
            "Je puis tout par celui qui me fortifie. "
            "Cette parole n'est pas un slogan. C'est une promesse vivante. "
            "Tu traverses peut-être une période difficile, "
            "un moment où tes forces semblent épuisées. "
            "Mais Dieu te dit : ma grâce te suffit. "
            "Ma puissance s'accomplit dans la faiblesse. "
            "Lève-toi avec foi. Il est ta force."
        ),
        description_tiktok="Philippiens 4:13 n'est pas un tatouage. C'est une promesse vivante. 💪",
        hashtags=["#force", "#philippiens", "#jesus", "#foi", "#dieu",
                  "#encouragement", "#chretien", "#bible", "#victoire", "#puissance"],
        call_to_action="Écris FORT si tu as besoin de cette force aujourd'hui.",
    ),
    VideoContent(
        theme="la prière",
        titre_interne="puissance_priere",
        verset="Matthieu 7:7",
        ambiance="priere",
        categorie_visuelle="lumiere",
        script=(
            "Est-ce que tu as prié aujourd'hui ? "
            "Demandez et l'on vous donnera. "
            "Cherchez et vous trouverez. "
            "Frappez et l'on vous ouvrira. "
            "La prière n'est pas une formalité religieuse. "
            "C'est une conversation avec le Père qui t'aime. "
            "Il entend chaque murmure de ton cœur. "
            "Ne cesse pas de prier. Il répond."
        ),
        description_tiktok="La prière change les choses. Ne cesse pas de frapper à la porte. 🙌",
        hashtags=["#priere", "#matthieu", "#jesus", "#foi", "#dieu",
                  "#encouragement", "#chretien", "#bible", "#spiritualite", "#louange"],
        call_to_action="Rejoins notre communauté de prière. Partage ta requête en commentaire.",
    ),
    VideoContent(
        theme="la grâce et le pardon",
        titre_interne="grace_pardon",
        verset="Éphésiens 2:8-9",
        ambiance="calme",
        categorie_visuelle="eau",
        script=(
            "Est-ce que tu portes la culpabilité de tes erreurs passées ? "
            "C'est par la grâce que vous êtes sauvés, par le moyen de la foi. "
            "Et cela ne vient pas de vous, c'est le don de Dieu. "
            "Tu n'as pas à gagner l'amour de Dieu. "
            "Tu l'as déjà. "
            "Sa grâce efface tout ce que tu croyais irrécupérable. "
            "Tu es pardonné. Tu es libre. Marche dans cette liberté."
        ),
        description_tiktok="Tu n'as pas à gagner l'amour de Dieu. Tu l'as déjà. 🤍",
        hashtags=["#grace", "#pardon", "#ephesiens", "#jesus", "#foi",
                  "#dieu", "#encouragement", "#chretien", "#bible", "#liberte"],
        call_to_action="Dis LIBRE si tu reçois cette grâce aujourd'hui.",
    ),
    VideoContent(
        theme="recommencer après l'échec",
        titre_interne="recommencer_apres_echec",
        verset="Lamentations 3:22-23",
        ambiance="inspirant",
        categorie_visuelle="nature",
        script=(
            "Tu as l'impression d'avoir tout raté ? "
            "Les bontés de l'Éternel ne sont pas épuisées, "
            "ses compassions ne cessent point. "
            "Elles se renouvellent chaque matin. "
            "Dieu ne compte pas tes échecs. "
            "Il voit ta repentance et il dit : relève-toi. "
            "Chaque matin est une nouvelle page. "
            "Aujourd'hui, tu peux recommencer."
        ),
        description_tiktok="Chaque matin est une nouvelle page. Dieu dit : relève-toi. 🌅",
        hashtags=["#relever", "#lamentations", "#jesus", "#foi", "#dieu",
                  "#encouragement", "#chretien", "#bible", "#recommencer", "#grace"],
        call_to_action="Écris NOUVEAU DÉPART si tu recommences aujourd'hui.",
    ),
]


# ─────────────────────────────────────────────────────────────────────
# Mapping thème → ambiance + catégorie visuelle
# ─────────────────────────────────────────────────────────────────────
_KEYWORDS_AMBIANCE: dict[str, str] = {
    # Calme
    "paix": "calme", "repos": "calme", "sérénité": "calme",
    "grâce": "calme", "pardon": "calme", "amour": "calme",
    "confiance": "calme", "consolation": "calme",
    # Inspirant
    "espoir": "inspirant", "espérance": "inspirant", "avenir": "inspirant",
    "foi": "inspirant", "force": "inspirant", "courage": "inspirant",
    "surmonter": "inspirant", "recommencer": "inspirant", "victoire": "inspirant",
    "relever": "inspirant", "croire": "inspirant",
    # Célébration
    "joie": "celebration", "louange": "celebration", "gloire": "celebration",
    "triumphant": "celebration", "alléluia": "celebration",
    # Prière
    "prière": "priere", "prier": "priere", "adoration": "priere",
    "contemplation": "priere", "méditation": "priere", "intercession": "priere",
}

_KEYWORDS_VISUEL: dict[str, str] = {
    # Nature
    "confiance": "nature", "foi": "nature", "recommencer": "nature",
    "relever": "nature", "guérison": "nature",
    # Ciel
    "espoir": "ciel", "espérance": "ciel", "avenir": "ciel",
    "gloire": "ciel", "résurrection": "ciel", "ciel": "ciel",
    # Eau
    "paix": "eau", "repos": "eau", "grâce": "eau",
    "pardon": "eau", "baptême": "eau", "purification": "eau",
    # Lumière
    "victoire": "lumiere", "force": "lumiere", "joie": "lumiere",
    "lumière": "lumiere", "prière": "lumiere", "adoration": "lumiere",
    # Croix
    "salut": "croix", "croix": "croix", "sacrifice": "croix",
    "rédemption": "croix", "passion": "croix",
}

# Mots-clés Pexels pour chaque catégorie visuelle
PEXELS_QUERIES: dict[str, list[str]] = {
    "nature":  ["peaceful forest", "green meadow nature", "autumn forest light"],
    "ciel":    ["golden sunrise sky", "clouds sunset", "blue sky heaven light"],
    "eau":     ["calm ocean waves", "peaceful lake reflection", "waterfall nature"],
    "lumiere": ["golden light rays", "sunbeams forest", "candlelight warm"],
    "croix":   ["church architecture", "cross silhouette sunset", "cathedral light"],
    "default": ["peaceful nature", "calm landscape", "serene scenery"],
}

PIXABAY_QUERIES: dict[str, list[str]] = {
    "nature":  ["nature peaceful", "forest calm", "green meadow"],
    "ciel":    ["sunrise sky", "sunset clouds", "blue sky"],
    "eau":     ["ocean waves", "lake calm", "waterfall"],
    "lumiere": ["light rays", "golden light", "sunbeams"],
    "croix":   ["church", "cross sunset", "cathedral"],
    "default": ["nature calm", "peaceful landscape"],
}


def get_content_by_theme(theme: str) -> VideoContent:
    """
    Retourne le VideoContent le plus proche du thème donné.
    Cherche d'abord dans le catalogue, puis construit un contenu générique.
    """
    t = theme.lower()
    for item in CATALOGUE:
        if t in item.theme.lower() or item.theme.lower() in t:
            return item
        if t in item.titre_interne.replace("_", " "):
            return item

    # Fallback : trouver l'ambiance et le visuel via mots-clés
    ambiance = "calme"
    visuel = "nature"
    for kw, val in _KEYWORDS_AMBIANCE.items():
        if kw in t:
            ambiance = val
            break
    for kw, val in _KEYWORDS_VISUEL.items():
        if kw in t:
            visuel = val
            break

    # Retourner le premier message du catalogue comme base
    base = CATALOGUE[0]
    return VideoContent(
        theme=theme,
        titre_interne=theme.lower().replace(" ", "_").replace("'", "")[:30],
        verset=base.verset,
        ambiance=ambiance,
        categorie_visuelle=visuel,
        script=base.script,
        description_tiktok=base.description_tiktok,
        hashtags=base.hashtags,
        call_to_action=base.call_to_action,
    )


def list_themes() -> list[str]:
    return [c.theme for c in CATALOGUE]
