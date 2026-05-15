#!/usr/bin/env python3
"""
Demo run — generates a real MP4 for the theme 'Le pardon'
without any API keys or network calls.

Uses:
  - Hardcoded script (replaces Anthropic call)
  - FFmpeg colour-bar clips (replaces Pexels download)
  - FFmpeg sine-tone audio (replaces gTTS)
  - Real video_assembler (identical FFmpeg pipeline as production)
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.video_assembler import assemble_video

BASE = Path(__file__).parent
TEMP = BASE / "temp"
OUTPUT = BASE / "output"
TEMP.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

FFMPEG = "ffmpeg"
W, H, FPS = 1080, 1920, 30

# ── Hardcoded script: Le pardon ────────────────────────────────────────────────
SCRIPT = {
    "theme": "Le pardon",
    "title": "Libéré par la grâce du pardon",
    "scripture": {
        "reference": "Éphésiens 4:32",
        "text": (
            "Soyez bons et compatissants les uns envers les autres, "
            "vous pardonnant mutuellement, comme Dieu vous a pardonné "
            "en Christ."
        ),
    },
    "narration_segments": [
        {
            "segment_id": 1,
            "duration_seconds": 15,
            "text": (
                "Le pardon est l'un des plus grands cadeaux que Dieu nous a offerts. "
                "Pardonner, c'est choisir de libérer son cœur du poids de la rancœur. "
                "C'est marcher dans la liberté que Christ nous a donnée."
            ),
            "visual_keyword": "peaceful forest light",
            "mood": "peaceful",
        },
        {
            "segment_id": 2,
            "duration_seconds": 15,
            "text": (
                "Dieu lui-même nous a donné l'exemple parfait du pardon. "
                "Alors que nous étions encore pécheurs, Christ est mort pour nous. "
                "Son amour dépasse toute faute, toute erreur, tout manquement."
            ),
            "visual_keyword": "sunrise mountain hope",
            "mood": "hopeful",
        },
        {
            "segment_id": 3,
            "duration_seconds": 15,
            "text": (
                "Pardonner ne signifie pas oublier, ni approuver ce qui a été fait. "
                "Cela signifie remettre la justice entre les mains de Dieu "
                "et choisir la paix plutôt que l'amertume."
            ),
            "visual_keyword": "calm river water",
            "mood": "reflective",
        },
        {
            "segment_id": 4,
            "duration_seconds": 15,
            "text": (
                "Quand nous pardonnons, nous nous libérons nous-mêmes. "
                "La rancœur est une prison dont la clé est entre nos mains. "
                "Aujourd'hui, Dieu t'invite à ouvrir cette porte et à marcher libre."
            ),
            "visual_keyword": "open field flowers joy",
            "mood": "joyful",
        },
        {
            "segment_id": 5,
            "duration_seconds": 15,
            "text": (
                "Seigneur, aide-nous à pardonner comme tu nous as pardonné. "
                "Que ta grâce coule à travers nous vers ceux qui nous ont blessés. "
                "Que le pardon soit notre témoignage de ton amour dans ce monde."
            ),
            "visual_keyword": "golden sunset sky peace",
            "mood": "peaceful",
        },
    ],
    "background_music_mood": "reflective",
    "call_to_action": "Choisis aujourd'hui de pardonner et de marcher dans la liberté de Christ.",
}

# Colour palette: one warm colour per segment for visual variety
COLOURS = ["#2C5F8A", "#3D7A5E", "#8A5C2C", "#6B4A8A", "#8A7A2C"]

def make_clip(seg_id: int, duration: int) -> Path:
    dest = TEMP / f"clip_{seg_id}.mp4"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    colour = COLOURS[(seg_id - 1) % len(COLOURS)]
    # Gradient-like look: colour bar + light overlay text
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"color=c={colour}:size={W}x{H}:rate={FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  [demo] clip_{seg_id}.mp4 generated ({duration}s, colour {colour})")
    return dest


def make_tts(seg_id: int, duration: int) -> Path:
    """Generate a soft sine tone as stand-in for TTS."""
    dest = TEMP / f"tts_{seg_id}.mp3"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    freq = 220 + seg_id * 40  # different tone per segment
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency={freq}:duration={duration}",
        "-c:a", "libmp3lame", "-q:a", "4",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  [demo] tts_{seg_id}.mp3 generated ({duration}s, {freq}Hz tone)")
    return dest


def main():
    print()
    print("✝  DEMO — Vidéo chrétienne : Le Pardon")
    print("=" * 52)
    print("  (Clips synthétiques FFmpeg — aucune API requise)")
    print()

    segments = SCRIPT["narration_segments"]

    print("[1/4] Génération des clips vidéo synthétiques…")
    for seg in segments:
        clip = make_clip(seg["segment_id"], seg["duration_seconds"])
        seg["clip_path"] = clip

    print()
    print("[2/4] Génération des pistes audio de test…")
    for seg in segments:
        tts = make_tts(seg["segment_id"], seg["duration_seconds"])
        seg["tts_path"] = tts

    print()
    print("[3/4] Assemblage FFmpeg (pipeline de production réel)…")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT / f"video_le_pardon_{ts}.mp4"

    assemble_video(
        segments=segments,
        title=SCRIPT["title"],
        scripture=SCRIPT["scripture"],
        output_path=output_path,
        music_path=None,
        debug=True,
        dry_run=False,
    )

    size_kb = output_path.stat().st_size / 1024
    total_dur = sum(s["duration_seconds"] for s in segments)

    print()
    print("[4/4] Nettoyage du dossier temp…")
    for f in TEMP.iterdir():
        if f.is_file():
            f.unlink()
    print("  temp/ vidé.")

    print()
    print("=" * 52)
    print("✅  DEMO terminée avec succès !")
    print(f"   Fichier  : {output_path}")
    print(f"   Durée    : {total_dur}s")
    print(f"   Taille   : {size_kb:.0f} KB")
    print(f"   Thème    : {SCRIPT['title']}")
    print(f"   Verset   : {SCRIPT['scripture']['reference']}")
    print()
    print("  Pour un vrai run avec Anthropic + Pexels + gTTS :")
    print("  → Copie .env.example → .env")
    print("  → Renseigne PEXELS_API_KEY et ANTHROPIC_API_KEY")
    print("  → Lance : python main.py --theme \"Le pardon\"")
    print("=" * 52)
    print()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n[ERREUR FFmpeg] {e}")
        print(e.stderr.decode() if e.stderr else "")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        sys.exit(1)
