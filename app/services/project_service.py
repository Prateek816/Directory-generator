"""
app/services/project_service.py

The main pipeline orchestrator.
Wires together: parser → type detector → content generator → disk writer.
This is the single entry point called by main.py.
"""

from __future__ import annotations

import time

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from app.generators.dir_generator import DirectoryGenerator
from app.generators.file_generator import FileGenerator
from app.models.project import GenerationResult, ProjectContext
from app.parsers.tree_parser import TreeParser
from app.parsers.type_detector import TypeDetector
from app.services.cache_service import get_cache
from app.services.content_generator import ContentGeneratorService
from app.utils.logger import get_logger

log = get_logger(__name__)
console = Console()


class ProjectService:
    """
    Orchestrates the full project-generation pipeline:

    1. Parse raw text layout → ParsedStructure
    2. Detect project type heuristically
    3. Generate AI content for each file (async, parallel)
    4. Write directories and files to disk
    5. Return a GenerationResult summary
    """

    def __init__(self, context: ProjectContext) -> None:
        self._ctx = context
        self._parser = TreeParser()
        self._detector = TypeDetector()

    async def run(self, raw_layout: str) -> GenerationResult:
        result = GenerationResult(
            success=False,
            output_dir=self._ctx.output_dir,
            dry_run=self._ctx.dry_run,
        )

        start = time.perf_counter()

        try:
            # ── Step 1: Parse ──────────────────────────────────────────
            console.rule("[bold cyan]Step 1 — Parsing layout")
            structure = self._parser.parse(raw_layout)
            self._ctx.structure = structure

            console.print(
                f"  [green]✓[/green] Found "
                f"[bold]{len(structure.directories)}[/bold] dirs, "
                f"[bold]{len(structure.files)}[/bold] files"
            )

            # ── Step 2: Detect project type ────────────────────────────
            console.rule("[bold cyan]Step 2 — Detecting project type")
            self._ctx.project_type = self._detector.detect(structure)
            console.print(
                f"  [green]✓[/green] Project type: [bold magenta]{self._ctx.project_type.value}[/bold magenta]"
            )

            # ── Step 3: Generate file content ──────────────────────────
            console.rule("[bold cyan]Step 3 — Generating file content")

            gen_service = ContentGeneratorService(self._ctx)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    "Generating...", total=len(structure.files)
                )

                # Wrap gather so we can tick progress per file
                import asyncio

                semaphore = asyncio.Semaphore(5)  # max 5 concurrent LLM calls

                async def _generate_one(file):
                    async with semaphore:
                        result_file = await gen_service._process_file(file)
                        progress.advance(task)
                        return result_file

                populated_files = await asyncio.gather(
                    *[_generate_one(f) for f in structure.files]
                )

            console.print(
                f"  [green]✓[/green] Content ready for {len(populated_files)} files "
                f"(cache stats: {get_cache().stats})"
            )

            # ── Step 4: Write directories ──────────────────────────────
            console.rule("[bold cyan]Step 4 — Creating directories")
            dir_gen = DirectoryGenerator(self._ctx)
            dir_gen.generate(structure.directories, result)
            console.print(f"  [green]✓[/green] {len(result.dirs_created)} directories created")

            # ── Step 5: Write files ────────────────────────────────────
            console.rule("[bold cyan]Step 5 — Writing files to disk")
            file_gen = FileGenerator(self._ctx)
            await file_gen.generate_all(list(populated_files), result)
            console.print(f"  [green]✓[/green] {len(result.files_created)} files written")

            # ── Done ───────────────────────────────────────────────────
            elapsed = time.perf_counter() - start
            result.success = not bool(result.errors)
            result.total_tokens_used = self._ctx.total_tokens

            console.rule("[bold green]Complete")
            console.print(
                f"  Output: [bold]{self._ctx.output_dir}[/bold]\n"
                f"  Time  : [bold]{elapsed:.1f}s[/bold]\n"
                f"  Tokens: [bold]{result.total_tokens_used}[/bold]\n"
                f"  Errors: [bold red]{len(result.errors)}[/bold red]"
            )

            if result.errors:
                for err in result.errors:
                    console.print(f"    [red]✗[/red] {err}")

        except Exception as exc:
            log.exception(f"Pipeline failed: {exc}")
            result.errors.append(str(exc))
            result.success = False

        return result