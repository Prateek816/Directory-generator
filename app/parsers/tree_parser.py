"""
app/parsers/tree_parser.py

Converts a raw ASCII-tree layout string into a nested dict and
flat lists of FileNode / DirectoryNode objects.

Handles both tree-style (├──, └──, │) and indented layouts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.models.project import DirectoryNode, FileNode, ParsedStructure
from app.utils.file_helpers import get_extension, is_binary_extension
from app.utils.logger import get_logger

log = get_logger(__name__)

# Strip common box-drawing and tree characters
_TREE_CHARS = re.compile(r"[│├└─\s]+")
# Detect indentation level (spaces or tabs before a name)
_INDENT_RE = re.compile(r"^(\s*)")


def _strip_tree_chars(line: str) -> str:
    """Remove box-drawing characters, return the clean name."""
    # Remove tree characters but preserve leading whitespace for indent calc
    cleaned = re.sub(r"[├└│─]+", "", line)
    return cleaned.strip()


def _calc_depth(line: str) -> int:
    """
    Estimate nesting depth from a raw line.
    Each 4-space (or 1-tab) indent block = 1 level.
    Tree characters like │   also count as indent markers.
    """
    # Count leading whitespace + tree chars
    prefix = re.match(r"^([\s│]*)", line)
    raw = prefix.group(1) if prefix else ""
    # Replace tabs with 4 spaces
    raw = raw.replace("\t", "    ")
    # Each │ represents one indent level
    raw = raw.replace("│", "    ")
    return len(raw) // 4


class TreeParser:
    """Stateless parser: call parse() and get a ParsedStructure back."""

    def parse(self, raw_text: str) -> ParsedStructure:
        lines = [l for l in raw_text.splitlines() if l.strip()]
        log.debug(f"Parsing {len(lines)} non-empty lines")

        tree: dict[str, Any] = {}
        files: list[FileNode] = []
        dirs: list[DirectoryNode] = []

        # Stack tracks (depth, current_dict) to build the nested tree
        stack: list[tuple[int, dict[str, Any]]] = [(-1, tree)]

        for raw_line in lines:
            depth = _calc_depth(raw_line)
            name = _strip_tree_chars(raw_line)

            if not name:
                continue

            is_dir = name.endswith("/")
            name = name.rstrip("/")

            # Pop stack until we find the right parent
            while len(stack) > 1 and stack[-1][0] >= depth:
                stack.pop()

            parent_dict = stack[-1][1]

            if is_dir:
                node: dict[str, Any] = {}
                parent_dict[name] = node
                stack.append((depth, node))
            else:
                parent_dict[name] = "file"

        # Build flat lists from the nested tree
        self._walk(tree, "", files, dirs)

        log.info(
            f"Parsed: {len(dirs)} directories, {len(files)} files"
        )
        return ParsedStructure(raw_tree=tree, files=files, directories=dirs)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _walk(
        self,
        node: dict[str, Any],
        current_path: str,
        files: list[FileNode],
        dirs: list[DirectoryNode],
    ) -> None:
        for name, value in node.items():
            path = f"{current_path}/{name}" if current_path else name

            if value == "file":
                ext = get_extension(name)
                if not is_binary_extension(ext):
                    files.append(
                        FileNode(path=path, name=name, extension=ext)
                    )
            elif isinstance(value, dict):
                dirs.append(DirectoryNode(path=path, name=name))
                self._walk(value, path, files, dirs)