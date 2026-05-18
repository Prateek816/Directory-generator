"""
app/models/project.py
Domain models — the shared language of the entire system.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    NODEJS = "nodejs"
    FULLSTACK = "fullstack"
    CLI = "cli"
    AI_PROJECT = "ai_project"
    GENERIC = "generic"


class FileNode(BaseModel):
    """A single file within the project tree."""

    path: str
    name: str
    extension: str
    content: str = ""
    is_generated: bool = False


class DirectoryNode(BaseModel):
    """A directory within the project tree."""

    path: str
    name: str


class ParsedStructure(BaseModel):
    """Result of parsing the raw text layout."""

    raw_tree: dict[str, Any] = Field(default_factory=dict)
    files: list[FileNode] = Field(default_factory=list)
    directories: list[DirectoryNode] = Field(default_factory=list)


class ProjectContext(BaseModel):
    """Full context passed through the generation pipeline."""

    project_type: ProjectType = ProjectType.GENERIC
    structure: ParsedStructure = Field(default_factory=ParsedStructure)
    output_dir: str = "./generated_project"
    dry_run: bool = False
    overwrite: bool = False
    ai_generate_content: bool = True

    # Token usage tracking
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    def track_tokens(self, prompt: int, completion: int) -> None:
        self.total_prompt_tokens += prompt
        self.total_completion_tokens += completion

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens


class GenerationResult(BaseModel):
    """Final output summary returned to the CLI."""

    success: bool
    output_dir: str
    files_created: list[str] = Field(default_factory=list)
    dirs_created: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_tokens_used: int = 0
    dry_run: bool = False