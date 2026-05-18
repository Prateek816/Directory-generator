"""
app/utils/logger.py
Centralised Rich-powered logger.
"""

from __future__ import annotations

import logging
import sys
from functools import lru_cache

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)


@lru_cache(maxsize=None)
def get_logger(name: str = "project_initializer") -> logging.Logger:
    """Return (and cache) a named logger backed by Rich."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    handler = RichHandler(
        console=_console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger