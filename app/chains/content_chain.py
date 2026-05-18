"""
Public API
----------
chain = ContentChain()
content: str = await chain.agenerate(
    project_type="react",
    file_path="src/components/Navbar.jsx",
    language="jsx",
)
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSerializable
from langchain_groq import ChatGroq

from app.config.settings import get_settings
from app.prompts.templates import build_content_prompt
from app.utils.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Retry / throttle knobs
# ---------------------------------------------------------------------------
_MAX_RETRIES: int = 3
_RETRY_DELAY: float = 1.5   # seconds — backs off exponentially


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _build_llm() -> ChatGroq:
    """Construct (and cache) a ChatGroq instance from env settings."""
    settings = get_settings()
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.model_name,
        temperature=0.3,          # low temp → deterministic boilerplate
        max_tokens=settings.max_tokens,
        streaming=False,
    )


def _build_chain() -> RunnableSerializable:
    """Assemble the LCEL chain: prompt | llm | output_parser."""
    prompt = build_content_prompt()   # ChatPromptTemplate
    llm = _build_llm()
    parser = StrOutputParser()
    return prompt | llm | parser


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class ContentChain:
    """
    Thin wrapper around a LangChain LCEL chain that generates file
    boilerplate via the Groq LLM.

    The chain is built once (lazy) and reused for all calls, which
    avoids repeated object construction overhead in async gather loops.
    """

    def __init__(self) -> None:
        self._chain: Optional[RunnableSerializable] = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def agenerate(
        self,
        *,
        project_type: str,
        file_path: str,
        language: str,
    ) -> str:
        """
        Asynchronously generate boilerplate content for a single file.

        Parameters
        ----------
        project_type : str
            Detected project type, e.g. ``"react"``, ``"fastapi"``.
        file_path : str
            Relative path of the file inside the project, e.g.
            ``"src/components/Navbar.jsx"``.
        language : str
            Human-readable language/format identifier, e.g. ``"jsx"``,
            ``"python"``, ``"markdown"``.

        Returns
        -------
        str
            Generated file content (raw source code / text).

        Raises
        ------
        RuntimeError
            Propagated after all retries are exhausted.
        """
        chain = self._get_chain()
        inputs = {
            "project_type": project_type,
            "file_path": file_path,
            "language": language,
        }

        last_exc: Optional[Exception] = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                log.debug(
                    "ContentChain.agenerate attempt=%d  path=%s",
                    attempt,
                    file_path,
                )
                result: str = await chain.ainvoke(inputs)
                return _clean_output(result)

            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                log.warning(
                    "ContentChain error (attempt %d/%d) for %s: %s",
                    attempt,
                    _MAX_RETRIES,
                    file_path,
                    exc,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_RETRY_DELAY * attempt)

        raise RuntimeError(
            f"ContentChain failed after {_MAX_RETRIES} retries for "
            f"'{file_path}': {last_exc}"
        ) from last_exc

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_chain(self) -> RunnableSerializable:
        """Lazy-initialise the LCEL chain on first call."""
        if self._chain is None:
            self._chain = _build_chain()
        return self._chain


# ---------------------------------------------------------------------------
# Output cleaner
# ---------------------------------------------------------------------------

def _clean_output(raw: str) -> str:
    """
    Strip markdown code-fence wrappers that the LLM sometimes adds.

    Example input::

        ```python
        print("hello")
        ```

    Example output::

        print("hello")
    """
    text = raw.strip()

    # Remove leading fence line  (```python  /  ```jsx  /  ``` etc.)
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]

    # Remove trailing fence
    if text.endswith("```"):
        text = text[: text.rfind("```")].rstrip()

    return text