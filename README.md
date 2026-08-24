# Superpowers

Marketplace de plugins Claude Code personnel. Ajoutez ce dépôt **une fois** comme marketplace, puis installez les plugins voulus dans chacun de vos projets (ou globalement) — plus besoin de copier des skills projet par projet.

## Installation

Dans Claude Code (CLI ou `/plugin` UI), depuis n'importe quel projet :

```
/plugin marketplace add rameshady-bot/superpowers
/plugin install prompt-master@superpowers
/plugin install watermarks-remover@superpowers
```

Pour mettre à jour plus tard :

```
/plugin marketplace update superpowers
```

## Plugins disponibles

### [`prompt-master`](plugins/prompt-master/)

Génère des prompts optimisés pour n'importe quel outil IA (Claude, ChatGPT, Cursor, Midjourney, outils image/vidéo, agents de code, ...). Voir [plugins/prompt-master/README.md](plugins/prompt-master/README.md).

### [`watermarks-remover`](plugins/watermarks-remover/)

Retire les marques de provenance IA multi-fournisseurs (Unicode invisible, watermarks statistiques de texte, métadonnées C2PA/EXIF/XMP) sur du contenu **que vous possédez** — hygiène et confidentialité. Fournit les skills `remove-ai-marks` (nécessite le service HTTP local du plugin) et `clean-user-facing-text` (autonome, texte uniquement). Voir [plugins/watermarks-remover/README.md](plugins/watermarks-remover/README.md) pour le détail (service, hook automatique, Docker).

## Structure du dépôt

```
.claude-plugin/marketplace.json   # déclare les plugins ci-dessous
plugins/
  prompt-master/
    .claude-plugin/plugin.json
    skills/prompt-master/
  watermarks-remover/
    .claude-plugin/plugin.json
    skills/remove-ai-marks/
    skills/clean-user-facing-text/
    service/                      # backend HTTP stdlib requis par remove-ai-marks
    hooks/                        # hook PostToolUse optionnel
```

Chaque plugin garde sa propre licence (`plugins/<nom>/LICENSE`) et son propre README.
