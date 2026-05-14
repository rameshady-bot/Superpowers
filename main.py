"""
TikTok Christian Video Generator — Orchestrator
Usage: python main.py --theme "anxiété" --verse "Phil 4:6"
"""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from modules.audio_generator import AudioGenerator
from modules.caption_burner import CaptionBurner
from modules.content_calendar import ContentCalendar
from modules.metadata_builder import MetadataBuilder
from modules.script_generator import ScriptGenerator
from modules.video_generator import VideoGenerator

load_dotenv()

console = Console()


def make_output_dir(target_date: str) -> Path:
    output_dir = Path("output") / target_date
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


async def run_pipeline(theme: str, verse: str, dry_run: bool, target_date: str, avatar_id: str | None) -> None:
    console.print(Panel(
        f"[bold cyan]TikTok Christian Video Generator[/bold cyan]\n"
        f"Theme: [yellow]{theme}[/yellow]  |  Verse: [yellow]{verse}[/yellow]\n"
        f"Date: {target_date}  |  Dry-run: {dry_run}",
        expand=False,
    ))

    output_dir = make_output_dir(target_date)
    calendar = ContentCalendar()

    # ── 1. Duplicate check ──────────────────────────────────────────────────
    console.print("\n[bold]Step 1/6:[/bold] Checking content calendar for duplicates…")
    duplicate_warning = calendar.check_duplicates(theme=theme, verse=verse, days=14)
    if duplicate_warning:
        console.print(f"[bold yellow]⚠  WARNING:[/bold yellow] {duplicate_warning}")
        if not Confirm.ask("Continue anyway?", default=False):
            console.print("[red]Aborted.[/red]")
            sys.exit(0)

    # ── 2. Script generation ────────────────────────────────────────────────
    console.print("\n[bold]Step 2/6:[/bold] Generating script…")
    console.print("[yellow]⚠  This will call the Anthropic API (~$0.003).[/yellow]")
    if not Confirm.ask("Proceed with script generation?", default=True):
        console.print("[red]Aborted.[/red]")
        sys.exit(0)

    generator = ScriptGenerator()
    script = await generator.generate(theme=theme, verse=verse)
    script_path = output_dir / "script.txt"
    script_path.write_text(script, encoding="utf-8")
    console.print(f"[green]✓[/green] Script saved → {script_path}")
    console.print(Panel(script, title="Generated Script", expand=False))

    if dry_run:
        console.print("[yellow]--dry-run active: skipping audio and video generation.[/yellow]")
        calendar.record(date=target_date, theme=theme, verse=verse)
        console.print("[green]✓[/green] Entry recorded in content calendar (dry run).")
        return

    # ── 3. Audio generation ─────────────────────────────────────────────────
    console.print("\n[bold]Step 3/6:[/bold] Generating voiceover…")
    console.print("[yellow]⚠  This will call the ElevenLabs API (~$0.015).[/yellow]")
    if not Confirm.ask("Proceed with audio generation?", default=True):
        console.print("[red]Aborted.[/red]")
        sys.exit(0)

    audio_gen = AudioGenerator()
    audio_path = output_dir / "audio.mp3"
    await audio_gen.generate(script=script, output_path=audio_path)
    console.print(f"[green]✓[/green] Audio saved → {audio_path}")

    # ── 4. Video generation ─────────────────────────────────────────────────
    console.print("\n[bold]Step 4/6:[/bold] Generating talking-head video…")
    console.print("[yellow]⚠  This will call HeyGen or D-ID API (~$0.50).[/yellow]")
    if not Confirm.ask("Proceed with video generation?", default=True):
        console.print("[red]Aborted.[/red]")
        sys.exit(0)

    video_gen = VideoGenerator()
    raw_video_path = output_dir / "raw_video.mp4"
    await video_gen.generate(audio_path=audio_path, output_path=raw_video_path, avatar_id=avatar_id)
    console.print(f"[green]✓[/green] Raw video saved → {raw_video_path}")

    # ── 5. Caption burning ──────────────────────────────────────────────────
    console.print("\n[bold]Step 5/6:[/bold] Burning captions…")
    burner = CaptionBurner()
    final_path = output_dir / "final_video_with_captions.mp4"
    await burner.burn(
        video_path=raw_video_path,
        audio_path=audio_path,
        verse=verse,
        output_path=final_path,
    )
    console.print(f"[green]✓[/green] Captioned video saved → {final_path}")

    # ── 6. Metadata ─────────────────────────────────────────────────────────
    console.print("\n[bold]Step 6/6:[/bold] Building metadata…")
    builder = MetadataBuilder()
    metadata = builder.build(theme=theme, verse=verse, date=target_date)
    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] Metadata saved → {metadata_path}")

    # ── Human review gate ───────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold white]HUMAN REVIEW REQUIRED[/bold white]\n\n"
        f"Video: [cyan]{final_path}[/cyan]\n"
        f"Script: [cyan]{script_path}[/cyan]\n"
        f"Metadata: [cyan]{metadata_path}[/cyan]\n\n"
        f"[yellow]Please review the final video before approving.[/yellow]",
        title="⚠  Review Gate",
        border_style="yellow",
        expand=False,
    ))

    approved = Confirm.ask("Mark this video as READY TO POST?", default=False)
    if approved:
        metadata["status"] = "approved"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        calendar.record(date=target_date, theme=theme, verse=verse)
        console.print("[bold green]✓ Video approved and recorded in content calendar.[/bold green]")
    else:
        metadata["status"] = "pending_review"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print("[yellow]Video marked as pending review. Re-run to approve later.[/yellow]")


@click.command()
@click.option("--theme", required=True, help="Topic/emotion (e.g. 'anxiété', 'espoir')")
@click.option("--verse", required=True, help="Bible verse reference (e.g. 'Phil 4:6')")
@click.option("--dry-run", is_flag=True, default=False, help="Generate script only, skip video/audio")
@click.option("--date", "target_date", default=str(date.today()), help="Output date folder (YYYY-MM-DD)")
@click.option("--avatar", "avatar_id", default=None, help="HeyGen avatar ID override")
def cli(theme: str, verse: str, dry_run: bool, target_date: str, avatar_id: str | None) -> None:
    """TikTok Christian video generator for French-speaking believers."""
    asyncio.run(run_pipeline(theme, verse, dry_run, target_date, avatar_id))


if __name__ == "__main__":
    cli()
