# Research Assistant — Design Document

**A multi-tab AI toolkit for the PhD research lifecycle**
Author: Skumar · Built with Streamlit, LangChain, OpenAI (`gpt-4o-mini`), and Pydantic

---

## 1. The problem

A PhD researcher does four recurring jobs, and each has its own friction:

1. **Reading papers** — the reading list is always longer than the time available, and deciding what deserves a deep read is slow.
2. **Scouting literature** — entering an unfamiliar subfield means hours of searching, skimming abstracts, and piecing together what the open questions are.
3. **Planning the thesis** — turning a vague topic into a concrete chapter structure and timeline is daunting and easy to procrastinate on.
4. **Stress-testing ideas** — getting honest, structured feedback on a half-formed idea usually means waiting for an advisor meeting.

These tasks share a lot of plumbing but are normally scattered across different tools, notebooks, and browser tabs.

## 2. The solution

**One app, four tabs, one shared library.** The Research Assistant gives a researcher an AI companion for each of the four jobs:

| Tab | Input | Output |
|---|---|---|
| 📄 **Paper Digest** | A paper PDF (+ optional thesis topic) | Structured triage: research questions, methodology, findings, theoretical contributions, acknowledged **and** unacknowledged limitations, thesis fit, follow-up questions, APA citation |
| 🔭 **Literature Explorer** | A research topic | 8–10 *real* papers from Semantic Scholar with summarized abstracts, plus a synthesis of dominant themes, methodological trends, and 3 open gaps |
| 🧭 **Thesis Outline Coach** | Topic + field + methodology + timeline | Chapter-by-chapter outline, per-chapter research questions and methods, a milestone timeline, and seed citations |
| 🧪 **Research Idea Critic** | A research idea or abstract | Novelty score (1–10) with reasoning, related work, methodological concerns, concrete improvements, and sharpening questions |

Every output can be saved to a single local library, browsable from the sidebar and tagged by tab and timestamp. It is a personal companion that travels with the researcher through the whole PhD.

## 3. Architecture

The core insight is that all four tabs share ~80% of their infrastructure. Each tab differs in only three things: the **input widget**, the **system prompt**, and the **output schema**. Everything else — the LLM client, `.env` loading, structured-output plumbing, and the save/load library — is shared.

```
app.py            Streamlit entry: builds the 4 tabs + sidebar (field switch + library)
tabs/             One file per tab; each exposes TITLE, DESCRIPTION, render(ctx)
prompts.py        All system prompts, with a {field_guidance} slot
schemas.py        All Pydantic output models (one per tab)
utils.py          Shared: LLM factory, PDF parsing, Semantic Scholar search, library I/O
data/library.json Saved outputs across all tabs
```

**Request flow for a tab:** collect input → compose the system prompt for the active field → call the shared LLM client with a Pydantic schema (`with_structured_output`) → render the validated result as clean markdown → offer a one-click **Save to library**. The Literature Explorer adds one extra step before the LLM call: a live Semantic Scholar lookup, so the model *summarizes real papers* instead of inventing references.

A `build_ctx()` helper bundles the shared dependencies (LLM factory, prompt resolver, library functions, active field) into a single `ctx` dict that every tab's `render(ctx)` receives — so tabs stay decoupled from how those dependencies are wired.

## 4. Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit (`st.tabs`) | Fast to build, multi-tab out of the box |
| LLM | OpenAI `gpt-4o-mini` via LangChain | Cheap, fast, good enough for structured triage |
| Structured output | Pydantic models | Reliable, typed output that downstream UI code can trust |
| PDF parsing | pypdf | Zero-setup text extraction |
| Literature search | Semantic Scholar Graph API | Free, no key required, real paper metadata |
| Storage | Local JSON file | Zero-config persistence |
| Packaging | UV (`pyproject.toml` + `uv.lock`) | Reproducible environment |

## 5. Field tuning

The system prompts default to **management / business research** conventions — APA 7th citations, awareness of journals like AMJ, AMR, ASQ, Organization Science, JAP, and JIBS, and careful distinctions between constructs and variables and between qualitative / quantitative / mixed methods. A sidebar **Field** switch (Management / STEM / Social Sciences / Other) swaps a `field_guidance` paragraph that is injected into every prompt, so the same app retunes itself for a different discipline without code changes. Prompts can also be overridden per session from the sidebar.

## 6. Key design choices

- **One app vs. four** — sharing infrastructure means each new tab costs ~30 minutes after the first, and a single library unifies everything the researcher produces.
- **Structured output everywhere** — using Pydantic schemas instead of free text makes rendering reliable and sets the app up for downstream automation (search, RAG, export).
- **Real papers in the Literature Explorer** — calling Semantic Scholar first, then summarizing, directly addresses LLM hallucination of citations, which is the single biggest risk for a literature tool.
- **No RAG yet** — multi-document Q&A is deliberately out of scope for this first version; the local JSON library is the foundation it will build on.
- **Graceful failure** — missing API keys, unreadable PDFs, scanned (image-only) PDFs, and Semantic Scholar rate limits all produce friendly messages instead of stack traces.

## 7. Prompts used to build it

The app was built incrementally with Claude Code, in checkpoints (skeleton → one tab at a time → polish), so each step could be tested before moving on. The three most useful prompts:

1. **Architecture brainstorm** — described the four tabs and the shared-infrastructure constraint, and asked for a file structure, the four Pydantic schemas, a literature-API recommendation, and a build order *before any code was written*.
2. **Incremental build** — "build it tab by tab, stopping for me to test between each," which kept each piece verifiable.
3. **Polish pass** — field switcher, friendly error messages, markdown rendering, and a `.gitignore` that excludes secrets and the local library.

## 8. What's next

- **Multi-paper Q&A across the library** (RAG) — ask questions spanning everything saved.
- **Automatic cross-referencing** between saved entries.
- **Scheduled imports** from arXiv / Semantic Scholar on a topic watchlist.
- **Full-text PDF retrieval** for papers surfaced by the Literature Explorer.

## 9. Reflections

The biggest surprise was how much leverage the *shared-infrastructure* decision created: once the first tab worked end-to-end, the remaining three were mostly a new schema, a new prompt, and a thin render function. The second lesson was that **grounding beats generation** — having the Literature Explorer fetch real papers before summarizing made it dramatically more trustworthy than asking the model to recall references from memory. Structured output via Pydantic was the quiet hero throughout: it turned "hope the model formats this nicely" into typed data the UI could render with confidence.
