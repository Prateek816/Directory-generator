"""
main.py

CLI entry point for the Project Initializer Generator.

Usage examples:
    python main.py --input layout.txt --output ./my_project
    python main.py --input layout.txt --output ./my_project --no-ai
    python main.py --input layout.txt --output ./my_project --dry-run
    python main.py --input layout.txt --output ./my_project --overwrite
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from app.models.project import ProjectContext
from app.services.project_service import ProjectService
from app.utils.logger import get_logger

app = typer.Typer(
    name="project-init",
    help="AI-powered project initializer — generates a full project from a layout description.",
    add_completion=False,
)
console = Console()
log = get_logger("main")


@app.command()
def main(
    input: Path = typer.Option(
        ...,
        "--input", "-i",
        help="Path to the .txt file containing the project layout tree.",
        exists=True,
        readable=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        Path("./generated_project"),
        "--output", "-o",
        help="Directory where the project will be generated.",
    ),
    ai: bool = typer.Option(
        True,
        "--ai/--no-ai",
        help="Enable or disable AI-powered file content generation.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be created without writing anything to disk.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing files in the output directory.",
    ),
) -> None:
    """Generate a complete project structure from a layout description file."""

    # ── Banner ─────────────────────────────────────────────────────────
    console.print(
        "\n[bold cyan]🚀 Project Initializer Generator[/bold cyan]\n"
        f"   Input  : [yellow]{input}[/yellow]\n"
        f"   Output : [yellow]{output}[/yellow]\n"
        f"   AI     : [yellow]{'enabled' if ai else 'disabled'}[/yellow]\n"
        f"   Dry run: [yellow]{dry_run}[/yellow]\n"
        f"   Overwrite: [yellow]{overwrite}[/yellow]\n"
    )

    # ── Read layout ────────────────────────────────────────────────────
    raw_layout = input.read_text(encoding="utf-8").strip()
    if not raw_layout:
        console.print("[red]Error:[/red] Layout file is empty.")
        raise typer.Exit(code=1)

    # ── Build context ──────────────────────────────────────────────────
    context = ProjectContext(
        output_dir=str(output),
        dry_run=dry_run,
        overwrite=overwrite,
        ai_generate_content=ai,
    )

    # ── Run pipeline ───────────────────────────────────────────────────
    service = ProjectService(context)
    result = asyncio.run(service.run(raw_layout))

    # ── Exit code ──────────────────────────────────────────────────────
    if not result.success:
        console.print(
            f"\n[bold red]Generation finished with {len(result.errors)} error(s).[/bold red]"
        )
        raise typer.Exit(code=1)

    console.print("\n[bold green]✅  Project generated successfully![/bold green]")


if __name__ == "__main__":
    app()