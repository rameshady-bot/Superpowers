#!/usr/bin/env python3
"""
Demo run — génère un vrai MP4 pour le thème 'Le pardon'
sans clé API ni réseau.

  Vidéo : fonds dégradés animés via FFmpeg (pas de blocs unis)
  Audio : voix de synthèse via espeak-ng OU ton sinusoïdal fort
  Texte : titres et verset brûlés via le pipeline de production réel
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.video_assembler import assemble_video

BASE   = Path(__file__).parent
TEMP   = BASE / "temp"
OUTPUT = BASE / "output"
TEMP.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)

FFMPEG = "ffmpeg"
W, H, FPS = 1080, 1920, 30

# ── Script figé : Le pardon ────────────────────────────────────────────────────
SCRIPT = {
    "theme": "Le pardon",
    "title": "Libere par la grace du pardon",
    "scripture": {
        "reference": "Ephesiens 4:32",
        "text": (
            "Soyez bons et compatissants les uns envers les autres, "
            "vous pardonnant mutuellement, comme Dieu vous a pardonne en Christ."
        ),
    },
    "narration_segments": [
        {
            "segment_id": 1, "duration_seconds": 15,
            "text": "Le pardon est l'un des plus grands cadeaux que Dieu nous a offerts.",
            "visual_keyword": "peaceful forest light", "mood": "peaceful",
        },
        {
            "segment_id": 2, "duration_seconds": 15,
            "text": "Dieu lui-meme nous a donne l'exemple parfait du pardon en Christ.",
            "visual_keyword": "sunrise mountain hope", "mood": "hopeful",
        },
        {
            "segment_id": 3, "duration_seconds": 15,
            "text": "Pardonner signifie remettre la justice entre les mains de Dieu.",
            "visual_keyword": "calm river water", "mood": "reflective",
        },
        {
            "segment_id": 4, "duration_seconds": 15,
            "text": "Quand nous pardonnons, nous nous liberons nous-memes.",
            "visual_keyword": "open field flowers joy", "mood": "joyful",
        },
        {
            "segment_id": 5, "duration_seconds": 15,
            "text": "Seigneur, aide-nous a pardonner comme tu nous as pardonne.",
            "visual_keyword": "golden sunset sky peace", "mood": "peaceful",
        },
    ],
}

# Dégradés animés par segment — couleurs chaudes/naturelles
GRADIENTS = [
    ("0x1a3a5c", "0x2d7a4f"),   # bleu nuit → vert forêt
    ("0x7a4a1a", "0xc87941"),   # brun → or (lever de soleil)
    ("0x1a4a6b", "0x3d8fb5"),   # bleu profond → bleu ciel
    ("0x2d6b2d", "0x8fb53d"),   # vert sombre → vert prairie
    ("0x8b3a1a", "0xe8923a"),   # rouge sombre → orange coucher
]


def _espeak_available() -> bool:
    r = subprocess.run(["which", "espeak-ng"], capture_output=True)
    return r.returncode == 0


def make_clip(seg_id: int, duration: int) -> Path:
    """Dégradé animé simulant une scène naturelle (blend de deux couleurs)."""
    dest = TEMP / f"clip_{seg_id}.mp4"
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    c1, c2 = GRADIENTS[(seg_id - 1) % len(GRADIENTS)]
    # Blend from c1 to c2 over the full duration using FFmpeg blend filter
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c={c1}:size={W}x{H}:rate={FPS}",
        "-f", "lavfi", "-i", f"color=c={c2}:size={W}x{H}:rate={FPS}",
        "-t", str(duration),
        "-filter_complex", f"[0][1]blend=all_expr='A*(1-T/{duration})+B*(T/{duration})'",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  [demo] clip_{seg_id}.mp4 : dégradé animé {c1}→{c2} ({duration}s)")
    return dest


def make_audio(text: str, seg_id: int, duration: int) -> Path:
    """
    Tente espeak-ng pour une vraie voix de synthèse.
    Si indisponible, génère un signal audio fort et audible.
    """
    dest = TEMP / f"tts_{seg_id}.mp3"
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    if _espeak_available():
        # Vraie voix de synthèse (approximation du français)
        wav = TEMP / f"tts_{seg_id}.wav"
        r = subprocess.run(
            ["espeak-ng", "-v", "fr", "-s", "140", "-a", "200",
             "-w", str(wav), text],
            capture_output=True
        )
        if r.returncode == 0 and wav.exists():
            # Convert WAV → MP3 and pad/trim to duration
            cmd = [
                FFMPEG, "-y", "-i", str(wav),
                "-af", f"apad=pad_dur={duration},atrim=end={duration}",
                "-c:a", "libmp3lame", "-q:a", "3",
                str(dest),
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            wav.unlink(missing_ok=True)
            print(f"  [demo] tts_{seg_id}.mp3 : voix espeak-ng")
            return dest

    # Fallback : signal modulé audible (ressemble à une parole rythmée)
    freq = 160 + seg_id * 15
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", (
            f"aevalsrc="
            f"'0.6*sin(2*PI*{freq}*t)*sin(2*PI*3*t)+"
            f"0.3*sin(2*PI*{freq*2}*t)*sin(2*PI*5*t)'"
            f":s=44100:c=stereo"
        ),
        "-t", str(duration),
        "-af", "volume=2.0",
        "-c:a", "libmp3lame", "-q:a", "3",
        str(dest),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  [demo] tts_{seg_id}.mp3 : signal audio ({freq}Hz, {duration}s)")
    return dest


def main():
    print()
    print("✝  DEMO — Vidéo chrétienne : Le Pardon")
    print("=" * 52)
    print("  Clips  : dégradés animés FFmpeg (pas de Pexels)")
    print("  Audio  : espeak-ng ou signal modulé (pas de gTTS)")
    print("  Texte  : pipeline de production réel (drawtext)")
    print()

    segments = SCRIPT["narration_segments"]

    print("[1/4] Génération des clips vidéo animés…")
    for seg in segments:
        seg["clip_path"] = make_clip(seg["segment_id"], seg["duration_seconds"])

    print()
    print("[2/4] Génération de l'audio…")
    for seg in segments:
        seg["tts_path"] = make_audio(
            seg["text"], seg["segment_id"], seg["duration_seconds"]
        )

    print()
    print("[3/4] Assemblage FFmpeg (pipeline complet)…")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT / f"video_le_pardon_{ts}.mp4"

    assemble_video(
        segments=segments,
        title=SCRIPT["title"],
        scripture=SCRIPT["scripture"],
        output_path=output_path,
        music_path=None,
        debug=False,
        dry_run=False,
    )

    print()
    print("[4/4] Nettoyage temp…")
    for f in TEMP.iterdir():
        if f.is_file():
            f.unlink()

    size_kb = output_path.stat().st_size / 1024
    total_dur = sum(s["duration_seconds"] for s in segments)

    print()
    print("=" * 52)
    print("✅  Vidéo générée avec succès !")
    print(f"   Fichier  : {output_path.name}")
    print(f"   Durée    : {total_dur}s")
    print(f"   Taille   : {size_kb:.0f} KB")
    print(f"   Titre    : {SCRIPT['title']}")
    print(f"   Verset   : {SCRIPT['scripture']['reference']}")
    print()
    print("  → Pour vraies images + vraie voix française :")
    print("    Ajoute PEXELS_API_KEY + ANTHROPIC_API_KEY dans .env")
    print("    Puis : python main.py --theme 'Le pardon'")
    print("=" * 52)
    print()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n[ERREUR FFmpeg]\n{e.stderr.decode() if e.stderr else e}")
        sys.exit(1)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"\n[ERREUR] {e}")
        sys.exit(1)
