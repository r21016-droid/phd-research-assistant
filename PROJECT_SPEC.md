# PhD Research Assistant — All-in-One Toolkit

A multi-tab Streamlit app that gives a PhD researcher four AI-powered companions for the most common parts of the research lifecycle: reading papers, scouting literature, planning the thesis, and stress-testing ideas.

## Why one app, four tabs

Each of the four features shares 80% of its infrastructure: same UI shell, same LLM client, same env loading, same local "library" for saving outputs. The only things that differ per tab are the **input**, the **system prompt**, and the **output schema**. Architecting it this way means adding features 2, 3, 4 takes ~30 minutes each after the first one is done.

## The four tabs

### Tab 1 — Paper Digest
- **Input:** Upload a research paper PDF + (optional) "my thesis topic" text field
- **Output:** Structured digest with TL;DR, research question, methodology, findings, limitations (acknowledged + unacknowledged), thesis fit, follow-up questions, APA citation
- **LLM features used:** PDF text extraction, structured output (Pydantic)
- **Use case:** Triage papers in your reading list before committing to a deep read

### Tab 2 — Literature Explorer
- **Input:** A research topic (e.g., "psychological safety in remote teams")
- **Output:** List of 8–10 recent papers (title, authors, year, abstract summary), plus a synthesis: dominant themes, methodological trends, and 3 open gaps
- **LLM features used:** Tool calling (arXiv or Semantic Scholar API), structured output
- **Use case:** First-pass landscape scan of an unfamiliar topic

### Tab 3 — Thesis Outline Coach
- **Input:** Thesis topic + field + intended methodology + timeline
- **Output:** Chapter-by-chapter outline, research questions per chapter, suggested methods, milestones for the timeline, list of seed citations the LLM knows about
- **LLM features used:** Pure prompt engineering + structured output, no tools
- **Use case:** Break a vague thesis topic into an actionable plan

### Tab 4 — Research Idea Critic
- **Input:** A research idea/abstract (free text)
- **Output:** Novelty score (1–10) with reasoning, related work the LLM knows, methodological concerns, suggested improvements, follow-up questions to sharpen the idea
- **LLM features used:** Structured output with mixed types (int + lists + strings)
- **Use case:** Stress-test an idea before pitching it to your advisor

### Shared "Library" sidebar
Every tab's output can be saved to a single local JSON library, browsable from the sidebar. Each entry knows which tab created it (digest / exploration / outline / critique) and is timestamped.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit (multi-tab via `st.tabs`) | Same as Arvind's demo |
| LLM | OpenAI GPT-4o-mini via LangChain | Cheap, fast, you have credits |
| PDF parsing | pypdf | Built-in, no setup |
| Lit search | `arxiv` Python library OR Semantic Scholar API | Free, no key needed |
| Storage | Local JSON file | Zero-config |
| Env | UV (pyproject.toml) | Matches cohort repo pattern |

## File structure (target)

```
PhD Research Assistant/
├── app.py                # Streamlit entry, defines the 4 tabs
├── tabs/
│   ├── paper_digest.py
│   ├── lit_explorer.py
│   ├── thesis_coach.py
│   └── idea_critic.py
├── prompts.py            # All system prompts in one editable file
├── schemas.py            # All Pydantic output models
├── utils.py              # Shared: LLM client, PDF parser, library save/load
├── data/
│   └── library.json      # Saved outputs across all tabs
├── pyproject.toml
├── uv.lock
├── .env.example
└── README.md
```

## Field tuning (management / business research)

The system prompts in `prompts.py` should be tuned for management/business research conventions:
- APA citation style by default
- Awareness of journals like AMJ, AMR, ASQ, Org Science, JAP, JIBS
- Familiarity with qual/quant/mixed methods and constructs vs variables
- Tone: rigorous but accessible

Tunable from the sidebar so you can swap to a different field later.

## Out of scope (save for later weeks)

- Multi-document Q&A across the library (Week 2 — RAG)
- Automatic literature cross-referencing (Week 3 — agents with memory)
- Browser automation for full-text retrieval (Week 4 — tools)
- Annotation/highlighting on PDFs (Week 5)

## Success criteria for submission

- [ ] `streamlit run app.py` boots a four-tab app
- [ ] Each tab produces a structured output without errors on at least one real input
- [ ] Library save/load works across tabs
- [ ] System prompts editable from the sidebar
- [ ] README has setup + screenshot
- [ ] Code pushed to GitHub
- [ ] 1–2 page Google Doc explaining the design
- [ ] ≤5 minute screen recording walkthrough

## Build order (recommended)

Build tabs in this order — earlier ones unblock later ones:

1. **Skeleton** — app.py with empty tabs, shared utils, .env loading, library JSON
2. **Tab 1 (Paper Digest)** — proves PDF + structured output pattern works
3. **Tab 3 (Thesis Outline Coach)** — simplest, no external APIs
4. **Tab 4 (Research Idea Critic)** — same pattern as Tab 3
5. **Tab 2 (Literature Explorer)** — last because it has the extra API dependency
6. **Polish** — error handling, sidebar tweaks, README, screenshots

If time runs out, ship with whatever's done. Three solid tabs beats four flaky ones.
