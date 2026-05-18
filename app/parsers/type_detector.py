"""
app/parsers/type_detector.py

Heuristically detects the project type from its file/dir structure
without making any LLM calls — fast and deterministic.
"""

from __future__ import annotations

from app.models.project import ParsedStructure, ProjectType
from app.utils.logger import get_logger

log = get_logger(__name__)

# Each rule: (ProjectType, set_of_signals)
# Signals are lowercase file names or directory names.
_RULES: list[tuple[ProjectType, set[str]]] = [
    (ProjectType.NEXTJS,    {"next.config.js", "next.config.ts", "pages", "_app.tsx", "_app.jsx"}),
    (ProjectType.REACT,     {"app.jsx", "app.tsx", "vite.config.js", "vite.config.ts", "package.json", "components"}),
    (ProjectType.VUE,       {"app.vue", "nuxt.config.js", "vue.config.js"}),
    (ProjectType.FASTAPI,   {"main.py", "routers", "schemas", "uvicorn"}),
    (ProjectType.DJANGO,    {"manage.py", "settings.py", "urls.py", "wsgi.py"}),
    (ProjectType.FLASK,     {"app.py", "routes.py", "templates", "flask"}),
    (ProjectType.NODEJS,    {"index.js", "server.js", "app.js", "package.json", "node_modules"}),
    (ProjectType.AI_PROJECT, {"agent.py", "chains", "prompts", "embeddings", "vectorstore", "langchain"}),
    (ProjectType.CLI,       {"cli.py", "__main__.py", "typer", "click", "argparse"}),
]


class TypeDetector:
    """Detect project type from a ParsedStructure."""

    def detect(self, structure: ParsedStructure) -> ProjectType:
        # Build a flat set of all names (lowercase) present in the tree
        names: set[str] = set()
        for f in structure.files:
            names.add(f.name.lower())
        for d in structure.directories:
            names.add(d.name.lower())

        scores: dict[ProjectType, int] = {}
        for project_type, signals in _RULES:
            hit = len(signals & names)
            if hit:
                scores[project_type] = hit

        if not scores:
            log.info("No signals matched — defaulting to GENERIC project type")
            return ProjectType.GENERIC

        best = max(scores, key=lambda k: scores[k])

        # React + FastAPI → fullstack
        has_react = scores.get(ProjectType.REACT, 0) > 0 or scores.get(ProjectType.NEXTJS, 0) > 0
        has_backend = (
            scores.get(ProjectType.FASTAPI, 0) > 0
            or scores.get(ProjectType.DJANGO, 0) > 0
            or scores.get(ProjectType.FLASK, 0) > 0
        )
        if has_react and has_backend:
            log.info("Detected FULLSTACK project")
            return ProjectType.FULLSTACK

        log.info(f"Detected project type: {best.value} (score={scores[best]})")
        return best