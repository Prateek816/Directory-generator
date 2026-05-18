"""
app/generators/file_generator.py

Writes generated file content to disk.
Uses aiofiles for non-blocking I/O and respects dry-run + overwrite flags.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiofiles

from app.models.project import FileNode, GenerationResult, ProjectContext
from app.utils.file_helpers import safe_path
from app.utils.logger import get_logger

log = get_logger(__name__)


class FileGenerator:
    """Async file writer — one coroutine per file, gathered in parallel."""

    def __init__(self, context: ProjectContext) -> None:
        self._ctx = context

    async def generate_all(
        self,
        files: list[FileNode],
        result: GenerationResult,
    ) -> None:
        """Write all files concurrently. Mutates *result* in place."""
        tasks = [self._write_file(f, result) for f in files]
        await asyncio.gather(*tasks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _write_file(
        self,
        file: FileNode,
        result: GenerationResult,
    ) -> None:
        base = Path(self._ctx.output_dir)
        try:
            target = safe_path(str(base), file.path)

            if self._ctx.dry_run:
                log.info(f"[DRY-RUN] Would write file → {target}")
                result.files_created.append(str(target))
                return

            # Overwrite protection
            if target.exists() and not self._ctx.overwrite:
                log.warning(f"Skipped (already exists, use --overwrite): {target}")
                return

            # Ensure parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(target, "w", encoding="utf-8") as fh:
                await fh.write(file.content)

            tag = "[AI]" if file.is_generated else "[empty]"
            log.debug(f"Written {tag} → {target}")
            result.files_created.append(str(target))

        except Exception as exc:
            msg = f"Failed to write file '{file.path}': {exc}"
            log.error(msg)
            result.errors.append(msg)