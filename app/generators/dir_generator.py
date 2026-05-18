"""
app/generators/dir_generator.py

Responsible for creating all project directories on disk.
Dry-run aware — prints what would be created without touching the filesystem.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.models.project import DirectoryNode, GenerationResult, ProjectContext
from app.utils.logger import get_logger
from app.utils.file_helpers import safe_path

log = get_logger(__name__)


class DirectoryGenerator:
    """Creates all directories for the project tree."""

    def __init__(self, context: ProjectContext) -> None:
        self._ctx = context

    def generate(
        self,
        directories: list[DirectoryNode],
        result: GenerationResult,
    ) -> None:
        """
        Create every directory in *directories* under context.output_dir.
        Mutates *result* in place — appends created paths and any errors.
        """
        base = Path(self._ctx.output_dir)

        # Always ensure the root output dir exists (unless dry-run)
        if not self._ctx.dry_run:
            base.mkdir(parents=True, exist_ok=True)

        for node in directories:
            try:
                target = safe_path(str(base), node.path)

                if self._ctx.dry_run:
                    log.info(f"[DRY-RUN] Would create dir  → {target}")
                    result.dirs_created.append(str(target))
                    continue

                target.mkdir(parents=True, exist_ok=True)
                log.debug(f"Created dir  → {target}")
                result.dirs_created.append(str(target))

            except Exception as exc:
                msg = f"Failed to create directory '{node.path}': {exc}"
                log.error(msg)
                result.errors.append(msg)