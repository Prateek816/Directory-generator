"""
app/prompts/templates.py

All LangChain PromptTemplate definitions in one place.
Import the constants; never hardcode prompt text elsewhere.
"""

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# ---------------------------------------------------------------------------
# File content generation prompt
# ---------------------------------------------------------------------------

FILE_CONTENT_SYSTEM = """You are an elite software engineer generating production-quality starter code.

Rules:
- Output ONLY the file content — no markdown fences, no explanations, no commentary.
- The first character of your response must be the first character of the file.
- Match the conventions of a senior {language} developer.
- Add a brief module-level docstring / comment at the top of each code file.
- For config files (JSON, YAML, TOML) output valid, minimal configs.
- For Markdown, output a useful README section with proper headings.
- For .env files, output example keys with placeholder values and comments.
- Keep the code concise but complete — not a toy snippet, not over-engineered."""

FILE_CONTENT_HUMAN = """Project type: {project_type}
File path: {file_path}
Language/format: {language}

Generate the starter content for this file."""

FILE_CONTENT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(FILE_CONTENT_SYSTEM),
    HumanMessagePromptTemplate.from_template(FILE_CONTENT_HUMAN),
])

# ---------------------------------------------------------------------------
# Project type detection (LLM-based fallback)
# ---------------------------------------------------------------------------

PROJECT_TYPE_SYSTEM = """You are a senior software architect.
Given a project file structure, identify the project type.
Reply with EXACTLY one of these labels and nothing else:
react | nextjs | vue | fastapi | flask | django | nodejs | fullstack | cli | ai_project | generic"""

PROJECT_TYPE_HUMAN = """File structure:
{structure_summary}"""

PROJECT_TYPE_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(PROJECT_TYPE_SYSTEM),
    HumanMessagePromptTemplate.from_template(PROJECT_TYPE_HUMAN),
])

build_content_prompt = FILE_CONTENT_PROMPT