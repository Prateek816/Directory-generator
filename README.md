# 🚀 Project Initializer Generator

An AI-powered developer tool that generates complete project folder structures and boilerplate code from a plain-text layout description — powered by **LangChain**, **Groq (llama-3.3-70b-versatile)**, and async Python.

---

## Features

| Feature | Details |
|---|---|
| **Layout Parsing** | Converts ASCII tree diagrams into a structured JSON representation |
| **Project Type Detection** | Heuristically detects React, FastAPI, Django, Node.js, fullstack, CLI, AI projects, etc. |
| **AI Content Generation** | Uses Groq LLM via LangChain to generate boilerplate tailored to each file's role |
| **Async & Parallel** | Up to 5 concurrent LLM requests; async disk I/O via `aiofiles` |
| **Template Caching** | Identical files across runs are never regenerated |
| **Dry-Run Mode** | Preview the full output without touching the filesystem |
| **Overwrite Protection** | Existing files are skipped unless `--overwrite` is passed |
| **Progress Indicator** | Rich-powered live progress bar during generation |
| **Token Tracking** | Total LLM token usage reported at the end of each run |
| **Retry Handling** | Exponential backoff on transient Groq API errors (via `tenacity`) |

---

## Architecture

```
project_initializer/
│
├── app/
│   ├── chains/           # LangChain Runnable chains (ContentChain, TypeDetectionChain)
│   ├── prompts/          # ChatPromptTemplate definitions
│   ├── parsers/          # TreeParser (text → JSON), TypeDetector (heuristic)
│   ├── generators/       # DirectoryGenerator, FileGenerator (disk I/O)
│   ├── services/         # ProjectService (orchestrator), ContentGeneratorService, TemplateCache
│   ├── utils/            # Logger, file_helpers
│   ├── models/           # Pydantic domain models
│   └── config/           # Settings (pydantic-settings + .env)
│
├── main.py               # Typer CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quickstart

### 1. Clone & install

```bash
git clone <repo-url>
cd project_initializer
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Create a layout file

```txt
# layout.txt
src/
 ├── components/
 │    ├── Navbar.jsx
 │    ├── Sidebar.jsx
 ├── pages/
 │    ├── Home.jsx
 │    ├── Login.jsx
 ├── services/
 │    ├── api.js
 ├── App.jsx
 ├── main.jsx
README.md
package.json
```

### 4. Run

```bash
# Full AI generation
python main.py --input layout.txt --output ./my_project

# Preview only (no files written)
python main.py --input layout.txt --output ./my_project --dry-run

# Skip AI content (creates empty files instantly)
python main.py --input layout.txt --output ./my_project --no-ai

# Overwrite existing files
python main.py --input layout.txt --output ./my_project --overwrite
```

---

## CLI Reference

```
Options:
  -i, --input    PATH   Layout .txt file           [required]
  -o, --output   PATH   Output directory            [default: ./generated_project]
  --ai / --no-ai        Enable AI content gen       [default: enabled]
  --dry-run             Preview without writing
  --overwrite           Overwrite existing files
  --help                Show this message and exit
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required.** Your Groq API key |
| `MODEL_NAME` | `llama-3.3-70b-versatile` | Groq model to use |
| `MAX_TOKENS` | `2048` | Max tokens per LLM response |
| `TEMPERATURE` | `0.3` | LLM sampling temperature (0–1) |
| `REQUEST_TIMEOUT` | `30` | Seconds before a request times out |
| `MAX_RETRIES` | `3` | Retry attempts on transient errors |
| `ENABLE_CACHING` | `true` | In-memory template cache |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Supported File Types

`.py` · `.js` · `.jsx` · `.ts` · `.tsx` · `.html` · `.css` · `.scss` · `.json` · `.md` · `.env` · `.yml` · `.yaml` · `.toml` · `.sh` · `Dockerfile` · `.sql` · `.graphql` · and more.

---

## License

MIT