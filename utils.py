"""Shared infrastructure for all tabs.

Holds the three things every tab needs:
  - get_llm()         -> a configured LangChain ChatOpenAI client
  - save_to_library() -> append one output to data/library.json
  - load_library()    -> read all saved entries back

Everything here is import-safe: loading this module never makes a network
call. The OpenAI key is only required the moment you actually call get_llm().
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env once, on import, so every tab sees OPENAI_API_KEY.
load_dotenv()

# --- Constants -------------------------------------------------------------

# One place to change the model for the whole app.
MODEL_NAME = "gpt-4o-mini"

# Paths are resolved relative to this file so the app works no matter what
# directory Streamlit is launched from.
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
LIBRARY_PATH = DATA_DIR / "library.json"

# Roughly cap how much paper text we send to the LLM (~12k tokens ≈ 48k chars).
# Keeps cost/latency sane on long PDFs without chunking (Week 1 scope).
MAX_PAPER_CHARS = 48_000


# --- LLM factory -----------------------------------------------------------

def get_llm(temperature: float = 0.2):
    """Return a configured ChatOpenAI client.

    Imported lazily so the rest of the app (and the test boot in Step A) does
    not depend on langchain being importable or the API key being present.
    Raises a clear, user-facing error if the key is missing.
    """
    import os

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=MODEL_NAME, temperature=temperature)


def run_structured(schema, system_prompt: str, user_content: str,
                   temperature: float = 0.2):
    """Call the LLM and return an instance of `schema` (a Pydantic model).

    Shared by every tab that produces structured output. Raises RuntimeError
    (from get_llm) if the API key is missing; tabs catch and show a friendly
    message.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(temperature)
    structured = llm.with_structured_output(schema)
    return structured.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    )


# --- PDF parsing -----------------------------------------------------------

def extract_pdf_text(file, max_chars: int = MAX_PAPER_CHARS) -> str:
    """Extract text from an uploaded PDF (a Streamlit UploadedFile or path).

    Returns the concatenated page text, truncated to `max_chars`. Returns ''
    when the PDF has no extractable text (e.g. a scanned/image-only PDF) — the
    caller decides how to message that. Raises only on genuinely unreadable
    files, which the caller turns into a friendly error.
    """
    from pypdf import PdfReader

    reader = PdfReader(file)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    text = "\n".join(parts).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... text truncated for length ...]"
    return text


# --- Literature search (Semantic Scholar) ----------------------------------

# Semantic Scholar Graph API — free, no key required for light use.
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_S2_FIELDS = "title,abstract,year,authors,venue,citationCount,url"


def _format_authors(authors: list[dict]) -> str:
    """Turn Semantic Scholar's author objects into one display string."""
    names = [a.get("name", "").strip() for a in (authors or []) if a.get("name")]
    if not names:
        return "Unknown authors"
    if len(names) > 3:
        return f"{names[0]}, et al."
    return ", ".join(names)


def search_semantic_scholar(topic: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Semantic Scholar for recent papers on `topic`.

    Returns a list of normalized dicts (title, authors, year, abstract, venue,
    citations, url). Only papers that actually have an abstract are returned,
    since the LLM needs one to summarize. Raises RuntimeError with a friendly
    message on network/API failure so the tab can surface it cleanly.
    """
    import requests

    params = {
        "query": topic.strip(),
        # Over-fetch so we can drop abstract-less papers and still hit `limit`.
        "limit": min(max(limit * 3, limit), 100),
        "fields": _S2_FIELDS,
    }
    try:
        resp = requests.get(SEMANTIC_SCHOLAR_URL, params=params, timeout=20)
    except requests.RequestException as e:
        raise RuntimeError(
            "Could not reach Semantic Scholar. Check your connection and try again."
        ) from e

    if resp.status_code == 429:
        raise RuntimeError(
            "Semantic Scholar is rate-limiting requests right now. "
            "Wait a moment and try again."
        )
    if not resp.ok:
        raise RuntimeError(
            "Semantic Scholar returned an error. Try a different topic or retry."
        )

    data = resp.json().get("data", []) or []
    papers: list[dict[str, Any]] = []
    for item in data:
        abstract = (item.get("abstract") or "").strip()
        if not abstract:
            continue  # nothing for the LLM to summarize
        papers.append(
            {
                "title": (item.get("title") or "Untitled").strip(),
                "authors": _format_authors(item.get("authors", [])),
                "year": str(item.get("year") or "n.d."),
                "abstract": abstract,
                "venue": (item.get("venue") or "").strip(),
                "citation_count": item.get("citationCount") or 0,
                "url": item.get("url") or "",
            }
        )
        if len(papers) >= limit:
            break
    return papers


# --- Library storage -------------------------------------------------------

def _ensure_library_file() -> None:
    """Make sure data/library.json exists and holds a JSON list."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LIBRARY_PATH.exists():
        LIBRARY_PATH.write_text("[]", encoding="utf-8")


def load_library() -> list[dict[str, Any]]:
    """Return all saved entries, newest first. Never raises on a fresh repo."""
    _ensure_library_file()
    try:
        data = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    # Newest first for the sidebar.
    return list(reversed(data))


def save_to_library(tab: str, title: str, payload: dict[str, Any],
                    field: str = "Management") -> dict[str, Any]:
    """Append one output to the library and return the stored entry.

    Args:
        tab:     which tab produced this (e.g. "Paper Digest").
        title:   short human-readable label for the sidebar.
        payload: the structured output, already a plain dict (model_dump()).
        field:   the research field active when this was generated.
    """
    _ensure_library_file()
    try:
        existing = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            existing = []
    except (json.JSONDecodeError, OSError):
        existing = []

    entry = {
        "id": f"{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tab": tab,
        "title": title or "(untitled)",
        "field": field,
        "payload": payload,
    }
    existing.append(entry)
    LIBRARY_PATH.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return entry
