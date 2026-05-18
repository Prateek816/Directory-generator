"""
app/services/content_generator.py

High-level service that decides whether to call the LLM or return
cached/empty content for a given FileNode.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from app.chains.content_chain import ContentChain
from app.models.project import FileNode, ProjectContext
from app.services.cache_service import get_cache
from app.utils.file_helpers import get_language, is_binary_extension
from app.utils.logger import get_logger

log = get_logger(__name__)

# Extensions we deliberately skip AI generation for
_SKIP_EXTENSIONS = {".env", ".gitignore", ".dockerignore"}

# Very small files (config stubs) that don't need AI
_MINIMAL_CONTENT: dict[str, str] = {
    ".gitignore": "node_modules/\n__pycache__/\n*.pyc\n.env\ndist/\nbuild/\n.DS_Store\n",
    ".dockerignore": "node_modules\n__pycache__\n*.pyc\n.env\n.git\n",
}


class ContentGeneratorService:
    """Generates or retrieves content for every file in the project."""

    def __init__(self, context: ProjectContext) -> None:
        self._ctx = context
        self._chain = ContentChain() if context.ai_generate_content else None
        self._cache = get_cache()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_all(self, files: list[FileNode]) -> list[FileNode]:
        """Populate content for all files concurrently."""
        tasks = [self._process_file(f) for f in files]
        return await asyncio.gather(*tasks)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _process_file(self, file: FileNode) -> FileNode:
        """Decide what content a file should have and populate it."""
        ext = file.extension
        name_lower = file.name.lower()

        # Minimal stub — no LLM needed
        if name_lower in _MINIMAL_CONTENT:
            file.content = _MINIMAL_CONTENT[name_lower]
            return file

        # Binary or skip-listed → leave empty
        if is_binary_extension(ext) or ext in _SKIP_EXTENSIONS:
            file.content = ""
            return file

        # No AI mode → empty file
        if not self._ctx.ai_generate_content or self._chain is None:
            file.content = ""
            return file

        # Check cache
        pt = self._ctx.project_type.value
        cached = self._cache.get(pt, file.path)
        if cached is not None:
            file.content = cached
            file.is_generated = True
            return file

        # Call LLM
        language = get_language(file.name)
        try:
            content = await self._chain.agenerate(
                project_type=pt,
                file_path=file.path,
                language=language,
            )
            self._cache.set(pt, file.path, content)
            file.content = content
            file.is_generated = True
        except Exception as exc:
            log.error(f"Failed to generate content for {file.path}: {exc}")
            file.content = f"# TODO: add content for {file.name}\n"

        return file