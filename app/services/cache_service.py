"""
app/services/cache_service.py

In-memory LRU cache for generated file content.
Keyed by (project_type, file_path) so identical files across projects
are never regenerated unnecessarily.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.utils.logger import get_logger

log = get_logger(__name__)


class TemplateCache:
    """Simple dict-backed cache with hit/miss telemetry."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._hits = 0
        self._misses = 0

    def _key(self, project_type: str, file_path: str) -> str:
        return f"{project_type}::{file_path}"

    def get(self, project_type: str, file_path: str) -> Optional[str]:
        key = self._key(project_type, file_path)
        value = self._store.get(key)
        if value is not None:
            self._hits += 1
            log.debug(f"Cache HIT  → {file_path}")
        else:
            self._misses += 1
        return value

    def set(self, project_type: str, file_path: str, content: str) -> None:
        key = self._key(project_type, file_path)
        self._store[key] = content

    @property
    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses, "size": len(self._store)}


@lru_cache(maxsize=1)
def get_cache() -> TemplateCache:
    """Singleton cache instance."""
    return TemplateCache()