"""
app/utils/file_helpers.py
Pure utility functions — no side-effects, no I/O.
"""

from __future__ import annotations

import os
from pathlib import Path

# Maps extension → language label used in prompts
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "React JSX",
    ".ts": "TypeScript",
    ".tsx": "React TSX",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".json": "JSON",
    ".md": "Markdown",
    ".env": "dotenv",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".sh": "Bash",
    ".dockerfile": "Dockerfile",
    "dockerfile": "Dockerfile",
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
}


def get_language(filename: str) -> str:
    """Return the human-readable language label for a filename."""
    name = filename.lower()
    ext = Path(name).suffix
    if ext in EXTENSION_LANGUAGE_MAP:
        return EXTENSION_LANGUAGE_MAP[ext]
    # Handle bare names like 'Dockerfile'
    return EXTENSION_LANGUAGE_MAP.get(name, "text")


def safe_path(base: str, *parts: str) -> Path:
    """Join and resolve a path, ensuring it stays inside *base*."""
    root = Path(base).resolve()
    target = (root / Path(*parts)).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError(f"Path traversal detected: {target}")
    return target


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_binary_extension(ext: str) -> bool:
    binary = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".ttf", ".eot"}
    return ext in binary