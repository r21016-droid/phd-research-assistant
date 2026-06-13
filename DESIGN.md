# Research Assistant — Design Document

**A multi-tab AI toolkit for the PhD research lifecycle**
Author: Skumar · Built with Streamlit, LangChain, OpenAI (`gpt-4o-mini`), and Pydantic

---

## 1. The problem

A PhD researcher does five recurring jobs, and each has its own friction:

1. **Reading papers** — the reading list is always longer than the time available, and deciding what deserves a deep read is slow.
2. **Scouting literature** — entering an unfamiliar subfield means hours of searching, skimming abstracts, and piecing together what the open questions are.
3. **Planning the thesis** — turning a vague topic into a concrete chapter structure and timeline is daunting and easy to procrastinate on.
4. **Stress-testing ideas** — getting honest, structured feedback on a half-formed idea usually means waiting for an advisor meeting.
5. **Cross-referencing what you've already read** — once you've collected 50+ papers in Zotero, finding "what did the three papers I read on construct X say about its measurement?" takes hours of grep-by-memory.

These tasks share a lot of plumbing but are normally scattered across different tools, notebooks, and browser tabs.

## 2. The solution

**One app, five tabs, one shared library.** The Research Assistant gives a researcher an AI companion for each of the five jobs:

| Tab | Input | Output |
|---|---|---|
| 📄 **Paper Digest** | A paper PDF (+ optional thesis topic) | Structured triage: research questions, methodology, findings, theoretical contributions, acknowledged **and** unacknowledged limitations, thesis fit, follow-up questions, APA citation |
| 🔭 **Literature Explorer** | A research topic | 8–10 *real* papers from Semantic Scholar with summarized abstracts, plus a synthesis of dominant themes, methodological trends, and 3 open gaps |
| 🧭 **Thesis Outline Coach** | Topic + field + methodology + timeline | Chapter-by-chapter outline, per-chapter research questions and methods, a milestone timeline, and seed citations |
| 🧪 **Research Idea Critic** | A research idea or abstract | Novelty score (1–10) with reasoning, related work, methodological concerns, concrete improvements, and sharpening questions |
| 📚 **Zotero Chat** *(Week 2 RAG)* | A Zotero collection | Pinecone-backed RAG: pick a collection, sync its PDFs (chunk + embed), then ask cross-paper questions and get cited answers via a LangGraph 2-node graph (retrieve → generate) |

Every output can be saved to a single local library, browsable from the sidebar and tagged by tab and timestamp. It is a personal companion that travels with the researcher through the whole PhD.

## 3. Architecture

The core insight is that all five tabs share ~80% of their infrastructure. Each tab differs in only three things: the **input widget**, the **system prompt**, and the **output schema** (or the RAG pipeline, in Tab 5's case). Everything else — the LLM client, `.env` loading, structured-output plumbing, and the save/load library — is shared.

```
app.py            Streamlit entry: builds the 5 tabs + sidebar (field switch + library)
tabs/             One file per tab; each exposes TITLE, DESCRIPTION, render(ctx)
  zotero_chat.py  Tab 5 — Zotero collection picker + sync + chat UI
rag.py            LangGraph 2-node RAG (retrieve → generate) + Pinecone helpers
zotero_lib.py     Zotero API wrapper (pyzotero) + PDF chunking with metadata
prompts.py        All system prompts, with a {field_guidance} slot
schemas.py        All Pydantic output models (one per Tab 1-4)
utils.py          Shared: LLM factory, PDF parsing, Semantic Scholar search, library I/O
data/library.json Saved outputs across all tabs
```

**Tabs 1–4 flow:** collect input → compose the system prompt for the active field → call the shared LLM client with a Pydantic schema (`with_structured_output`) → render the validated result as clean markdown → offer a one-click **Save to library**. The Literature Explorer adds one extra step before the LLM call: a live Semantic Scholar lookup, so the model *summarizes real papers* instead of inventing references.

**Tab 5 flow:**

```
SYNC (one-time per collection):
  pyzotero.collection_items() → [PDF attachments]
  pyzotero.file(key) → bytes
  pypdf extract → per-page text (with metadata)
  RecursiveCharacterTextSplitter(700, 100) → chunks
  OpenAI text-embedding-3-small (1536 dims)
  Pinecone serverless (AWS us-east-1, cosine) upsert
    namespace = slugified collection name (isolates collections)

QUERY (every question, LangGraph):
  START → retrieve (Pinecone similarity_search top-K)
        → generate (gpt-4o-mini + cite-only-from-context prompt)
        → END
```

A `build_ctx()` helper bundles the shared dependencies (LLM factory, prompt resolver, library functions, active field) into a single `ctx` dict that every tab's `render(ctx)` receives — so tabs stay decoupled from how those dependencies are wired.

## 4. Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit (`st.tabs`) | Fast to build, multi-tab out of the box |
| LLM | OpenAI `gpt-4o-mini` via LangChain | Cheap, fast, deterministic at temperature 0 |
| Agent orchestration (Tab 5) | LangGraph (2-node state graph) | Minimal today, extensible to grading / re-rewriting in Week 3 |
| Embeddings (Tab 5) | OpenAI `text-embedding-3-small` (1536 dims) | Top of MTEB English at this size; OpenAI credits cover it |
| Vector DB (Tab 5) | Pinecone serverless (AWS us-east-1, cosine) | Cohort default; free tier; one namespace per collection isolates data |
| Chunking (Tab 5) | `RecursiveCharacterTextSplitter` (700 chars, 100 overlap) | Industry default; respects paragraph/sentence boundaries |
| Reference manager (Tab 5) | Zotero Web API via `pyzotero` | Zero-cost integration with researcher's actual reading list |
| Structured output (Tabs 1-4) | Pydantic models | Reliable, typed output that downstream UI code can trust |
| PDF parsing | pypdf | Zero-setup text extraction |
| Literature search | Semantic Scholar Graph API | Free, no key required, real paper metadata |
| Storage | Local JSON file (Tabs 1-4) + Pinecone (Tab 5) | Right tool for each scale |
| Packaging | UV (`pyproject.toml` + `uv.lock`) | Reproducible environment |

## 5. Field tuning

The system prompts default to **management / business research** conventions — APA 7th citations, awareness of journals like AMJ, AMR, ASQ, Organization Science, JAP, and JIBS, and careful distinctions between constructs and variables and between qualitative / quantitative / mixed methods. A sidebar **Field** switch (Management / STEM / Social Sciences / Other) swaps a `field_guidance` paragraph that is injected into every prompt, so the same app retunes itself for a different discipline without code changes. Prompts can also be overridden per session from the sidebar.

## 6. Key design choices

- **One app vs. five** — sharing infrastructure means each new tab costs ~30 minutes after the first, and a single library unifies everything the researcher produces.
- **Structured output (Tabs 1-4)** — Pydantic schemas instead of free text make rendering reliable and set the app up for downstream automation.
- **Real papers in the Literature Explorer** — calling Semantic Scholar first, then summarizing, directly addresses LLM hallucination of citations.
- **Zotero as the corpus, not local uploads** — for Tab 5, pulling from the researcher's actual reference manager means the corpus is *their reading list*, not a generic dataset. Zero re-curation needed.
- **One Pinecone namespace per collection** — perfect isolation between subject areas (e.g., "psychological safety" vs "thesis methods"), so a query never accidentally retrieves out-of-scope chunks.
- **LangGraph for orchestration, not LangChain chains** — a 2-node graph today (retrieve → generate) becomes a 4-node graph in Week 3 (retrieve → grade → maybe rewrite → generate) without rewriting the rest.
- **Cite-only-from-context system prompt** — the Tab 5 LLM is explicitly forbidden to answer from training data. If retrieved context doesn't contain the answer, it must say "I don't know." This single instruction kills most hallucinations.
- **Graceful failure** — missing API keys, unreadable PDFs, scanned (image-only) PDFs, Semantic Scholar rate limits, and Zotero permission errors all produce friendly messages instead of stack traces.

## 7. Prompts used to build it

The app was built incrementally with Claude Code, in checkpoints (skeleton → one tab at a time → polish), so each step could be tested before moving on. The three most useful prompts:

1. **Architecture brainstorm** — described the four tabs and the shared-infrastructure constraint, and asked for a file structure, the four Pydantic schemas, a literature-API recommendation, and a build order *before any code was written*.
2. **Incremental build** — "build it tab by tab, stopping for me to test between each," which kept each piece verifiable.
3. **Polish pass** — field switcher, friendly error messages, markdown rendering, and a `.gitignore` that excludes secrets and the local library.

## 8. What's next

- **Hybrid retrieval in Tab 5** — BM25 + vector + reciprocal rank fusion (RRF). Helps with jargon queries that pure-semantic search misses (e.g., construct names, author names).
- **Re-ranking** with Cohere Rerank or a cross-encoder, slotted in as a new node in the LangGraph.
- **Metadata filtering** — filter by year, journal, or author before retrieval; would benefit from auto-extracting metadata from the PDF in addition to Zotero's structured fields.
- **RAGAS / LangSmith eval harness** — automate the manual eval set in `EVAL_QUESTIONS.md`.
- **Multi-collection queries** — let one question span multiple synced collections (a multi-namespace retrieval).
- **Automatic cross-referencing** between Tab 5 answers and Tabs 1–4 saved outputs.
- **Scheduled imports** from arXiv / Semantic Scholar on a topic watchlist.

## 9. Reflections

The biggest surprise was how much leverage the *shared-infrastructure* decision created: once the first tab worked end-to-end, the remaining tabs were mostly a new schema, a new prompt, and a thin render function. The second lesson was that **grounding beats generation** — having the Literature Explorer fetch real papers before summarizing made it dramatically more trustworthy than asking the model to recall references from memory. Structured output via Pydantic was the quiet hero across Tabs 1-4.

Adding Tab 5 (Week 2 RAG) reinforced the same lesson at a different scale: grounding *every* answer in retrieved chunks, with mandatory inline citations and an explicit "say I don't know" instruction, was what made the chatbot trustworthy. The choice of **LangGraph over a plain LangChain chain** felt over-engineered for a 2-node graph today, but is already paying off when planning Week 3's agentic extensions — adding a grading node or a query-rewriter node is a one-line graph edit, not a refactor.

The third lesson was about **the corpus choice**. Pulling PDFs from Zotero rather than asking the user to re-upload them turned out to be the single highest-leverage UX decision in Tab 5 — the corpus *is* the researcher's actual reading list, which means every demo is also a real-use moment.
