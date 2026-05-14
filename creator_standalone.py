#!/usr/bin/env python3
"""
Créateur autonome de vidéos chrétiennes — aucune clé API requise.
Compatible MoviePy 2.x, edge-tts, Pillow.
"""

import logging
import sys
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageSequenceClip,
    TextClip,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
TEMP = BASE / "temp"
OUTPUT = BASE / "output"
TEMP.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

W, H = 1080, 1920
FPS = 24
VOICE = "roa/fr"  # voix française espeak-ng (hors ligne)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_GOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ─────────────────────────────────────────────────────
# TEXTES BIBLIQUES D'ENCOURAGEMENT (5 vidéos)
# ─────────────────────────────────────────────────────
MESSAGES = [
    {
        "titre": "ne_crains_pas",
        "verset": "Ésaïe 41:10",
        "script": (
            "Ne crains pas, car je suis avec toi. "
            "Ne te décourage pas, car je suis ton Dieu. "
            "Je te fortifie, oui, je t'aide. "
            "Je te soutiens de ma main droite victorieuse. "
            "Quelles que soient les tempêtes de ta vie aujourd'hui, "
            "rappelle-toi que le Seigneur marche à tes côtés. "
            "Tu n'es jamais seul. Sa présence est ta force. "
            "Laisse cette vérité entrer dans ton cœur."
        ),
        "couleur_haut": (8, 8, 45),
        "couleur_bas": (25, 0, 75),
        "couleur_halo": (100, 80, 255),
    },
    {
        "titre": "force_en_lui",
        "verset": "Philippiens 4:13",
        "script": (
            "Je puis tout par celui qui me fortifie. "
            "Cette parole n'est pas un slogan. C'est une promesse vivante. "
            "Tu traverses peut-être une période difficile, "
            "un moment où tes forces semblent épuisées. "
            "Mais Dieu te dit : ma grâce te suffit. "
            "Ma puissance s'accomplit dans la faiblesse. "
            "Lève-toi aujourd'hui avec foi. Il est ta force."
        ),
        "couleur_haut": (5, 20, 55),
        "couleur_bas": (0, 45, 100),
        "couleur_halo": (80, 160, 255),
    },
    {
        "titre": "esperance_avenir",
        "verset": "Jérémie 29:11",
        "script": (
            "Car je connais les projets que j'ai formés sur vous, "
            "déclare l'Éternel. "
            "Des projets de paix et non de malheur, "
            "afin de vous donner un avenir et de l'espérance. "
            "Dieu n'a pas oublié ton histoire. "
            "Chaque douleur, chaque larme, il les voit. "
            "Et au-delà de ce que tu traverses, "
            "il prépare quelque chose de beau pour ta vie."
        ),
        "couleur_haut": (45, 15, 0),
        "couleur_bas": (90, 35, 0),
        "couleur_halo": (255, 160, 60),
    },
    {
        "titre": "paix_de_dieu",
        "verset": "Jean 14:27",
        "script": (
            "Je vous laisse la paix, je vous donne ma paix. "
            "Je ne vous donne pas comme le monde donne. "
            "Que votre cœur ne se trouble pas et ne se décourage pas. "
            "Dans un monde agité, Jésus t'offre une paix différente. "
            "Une paix qui ne dépend pas des circonstances. "
            "Accueille-la maintenant. Pose ton fardeau devant lui. "
            "Il est le Prince de la paix."
        ),
        "couleur_haut": (0, 30, 55),
        "couleur_bas": (0, 65, 85),
        "couleur_halo": (100, 220, 255),
    },
    {
        "titre": "confiance_seigneur",
        "verset": "Proverbes 3:5-6",
        "script": (
            "Confie-toi en l'Éternel de tout ton cœur "
            "et ne t'appuie pas sur ta propre intelligence. "
            "Reconnais-le dans toutes tes voies, "
            "et il aplanira tes sentiers. "
            "Tu ne comprends peut-être pas tout ce qui se passe. "
            "C'est normal. La foi ce n'est pas tout comprendre. "
            "C'est faire confiance à Celui qui voit tout. "
            "Laisse-le guider chacun de tes pas."
        ),
        "couleur_haut": (5, 35, 10),
        "couleur_bas": (0, 65, 25),
        "couleur_halo": (100, 255, 140),
    },
]


# ─────────────────────────────────────────────────────
# 1. AUDIO — espeak-ng CLI (100% hors ligne)
# ─────────────────────────────────────────────────────
def generate_audio(script: str, titre: str) -> Path:
    import subprocess
    path = TEMP / f"{titre}_audio.wav"
    logger.info(f"Synthèse vocale espeak-ng → {path.name}")
    # -v fr : voix française | -s 145 : débit | -p 50 : tonalité
    result = subprocess.run(
        ["espeak-ng", "-v", "fr", "-s", "145", "-p", "50", "-w", str(path), script],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"espeak-ng erreur : {result.stderr}")
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Fichier audio vide après espeak-ng")
    logger.info(f"Audio généré : {path.stat().st_size // 1024} Ko")
    return path


# ─────────────────────────────────────────────────────
# 2. FOND ANIMÉ — gradient + halo + étoiles
# ─────────────────────────────────────────────────────
def _make_frame(t: float, duration: float, c_haut, c_bas, c_halo) -> np.ndarray:
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Gradient vertical lent
    drift = (t / duration) * 0.15
    for y in range(H):
        ratio = min(y / H + drift, 1.0)
        r = int(c_haut[0] + (c_bas[0] - c_haut[0]) * ratio)
        g = int(c_haut[1] + (c_bas[1] - c_haut[1]) * ratio)
        b = int(c_haut[2] + (c_bas[2] - c_haut[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Halo pulsant
    pulse = 0.75 + 0.25 * np.sin(t * 0.9)
    cx, cy = W // 2, int(H * 0.28)
    for radius in range(int(350 * pulse), 0, -18):
        alpha = (1 - radius / (350 * pulse)) * 0.07
        bright_r = min(255, int(c_halo[0] * alpha * 3))
        bright_g = min(255, int(c_halo[1] * alpha * 3))
        bright_b = min(255, int(c_halo[2] * alpha * 3))
        overlay = Image.new("RGB", (W, H), (bright_r, bright_g, bright_b))
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse(
            [(cx - radius, cy - radius), (cx + radius, cy + radius)],
            fill=int(255 * alpha * 2.2)
        )
        img = Image.composite(overlay, img, mask)

    # Étoiles / particules montantes
    rng = random.Random(42)
    draw2 = ImageDraw.Draw(img)
    for _ in range(40):
        px = rng.randint(20, W - 20)
        py_base = rng.randint(0, H)
        py = int((py_base - t * 18) % H)
        sz = rng.randint(1, 3)
        bright = rng.randint(80, 200)
        draw2.ellipse([(px - sz, py - sz), (px + sz, py + sz)],
                      fill=(bright, bright, bright))

    return np.array(img)


def build_background_frames(duration: float, titre: str, c_haut, c_bas, c_halo) -> list:
    logger.info(f"Génération du fond ({duration:.1f}s à {FPS}fps)...")
    n = int(duration * FPS)
    # Générer 1 frame / 2 secondes puis répliquer (performance)
    keyframe_count = max(4, int(duration // 2))
    keyframes = []
    for i in range(keyframe_count):
        t = (i / keyframe_count) * duration
        keyframes.append(_make_frame(t, duration, c_haut, c_bas, c_halo))

    frames = []
    for i in range(n):
        t = (i / n) * duration
        ki = min(int((t / duration) * keyframe_count), keyframe_count - 1)
        frames.append(keyframes[ki])
    return frames


# ─────────────────────────────────────────────────────
# 3. SOUS-TITRES par segment de phrase
# ─────────────────────────────────────────────────────
def build_segments(script: str, duration: float) -> list:
    phrases = []
    for sentence in script.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|"):
        s = sentence.strip()
        if s:
            phrases.append(s)

    n = len(phrases)
    seg_dur = duration / max(n, 1)
    return [
        {"start": i * seg_dur, "end": (i + 1) * seg_dur, "text": phrase}
        for i, phrase in enumerate(phrases)
    ]


def build_subtitle_clips(segments: list) -> list:
    clips = []
    for seg in segments:
        text = seg["text"].strip()
        dur = seg["end"] - seg["start"]
        if not text or dur <= 0:
            continue
        try:
            clip = (
                TextClip(
                    font=FONT_BOLD,
                    text=text,
                    font_size=60,
                    color="white",
                    stroke_color="black",
                    stroke_width=3,
                    method="caption",
                    size=(W - 100, None),
                    text_align="center",
                    duration=dur,
                )
                .with_start(seg["start"])
                .with_position(("center", 0.72), relative=True)
            )
            clips.append(clip)
        except Exception as e:
            logger.warning(f"Sous-titre ignoré '{text[:30]}' : {e}")
    return clips


def build_verset_clip(verset: str, duration: float):
    try:
        return (
            TextClip(
                font=FONT_BOLD,
                text=verset,
                font_size=46,
                color="#FFD700",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(W - 100, None),
                text_align="center",
                duration=duration,
            )
            .with_start(0)
            .with_position(("center", 0.06), relative=True)
        )
    except Exception as e:
        logger.warning(f"Clip verset ignoré : {e}")
        return None


# ─────────────────────────────────────────────────────
# 4. ASSEMBLAGE
# ─────────────────────────────────────────────────────
def render_video(msg: dict) -> Path:
    titre = msg["titre"]
    output_path = OUTPUT / f"{titre}.mp4"

    logger.info(f"{'='*55}")
    logger.info(f"VIDÉO : {msg['verset']}")
    logger.info(f"{'='*55}")

    audio_path = generate_audio(msg["script"], titre)
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration
    logger.info(f"Durée audio : {duration:.1f}s")

    frames = build_background_frames(
        duration, titre,
        msg["couleur_haut"], msg["couleur_bas"], msg["couleur_halo"]
    )
    bg = ImageSequenceClip(frames, fps=FPS).with_audio(audio)

    segments = build_segments(msg["script"], duration)
    subtitle_clips = build_subtitle_clips(segments)
    verset_clip = build_verset_clip(msg["verset"], duration)

    layers = [bg]
    if verset_clip:
        layers.append(verset_clip)
    layers.extend(subtitle_clips)

    final = CompositeVideoClip(layers, size=(W, H))

    logger.info(f"Export → {output_path.name}")
    final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(TEMP / f"{titre}_tmp.m4a"),
        remove_temp=True,
        logger=None,
    )

    audio.close()
    final.close()

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Vidéo créée : {output_path} ({size_mb:.1f} Mo)")
    return output_path


# ─────────────────────────────────────────────────────
# 5. MAIN
# ─────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Créateur de vidéos chrétiennes sans clé API")
    parser.add_argument("--index", type=int, default=None,
                        help=f"Index 0-{len(MESSAGES)-1}. Défaut : toutes les vidéos.")
    args = parser.parse_args()

    msgs = [MESSAGES[args.index]] if args.index is not None else MESSAGES
    logger.info(f"{len(msgs)} vidéo(s) à créer")

    created, errors = [], []
    for msg in msgs:
        try:
            path = render_video(msg)
            created.append(path)
        except Exception as e:
            logger.error(f"Erreur '{msg['titre']}' : {e}", exc_info=True)
            errors.append(msg["titre"])

    logger.info(f"\n{'='*55}")
    logger.info(f"TERMINÉ — {len(created)} créée(s), {len(errors)} erreur(s)")
    for p in created:
        logger.info(f"  ✓ {p}")
    for e in errors:
        logger.info(f"  ✗ {e}")
    logger.info(f"{'='*55}")


if __name__ == "__main__":
    main()
