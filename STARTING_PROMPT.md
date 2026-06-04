# Starting prompts for Claude Code / Codex — Full Toolkit

## How to use

1. Open VS Code in the `PhD Research Assistant` folder
2. Open Claude Code (or Codex) panel
3. **Switch to "Ask before edits" mode** — NOT auto mode
4. Switch the model to **Claude Opus** (Claude Code) or **GPT-5** (Codex) — best for first pass
5. Paste prompts in order. Wait for output between each. Don't skip the brainstorm.

---

## Prompt 1 — Brainstorm the architecture (paste first)

```
I want to build a multi-tab Streamlit app called "PhD Research Assistant" using Streamlit + LangChain + OpenAI. It is the deliverable for Week 1 of an AI agents course. The submission has to demo well in under 5 minutes.

The app has 4 tabs, all sharing the same OpenAI client, .env loading, and local JSON library:

TAB 1 — Paper Digest
- Input: upload a research paper PDF + optional "my thesis topic" text field
- Output: structured digest with TL;DR, research question(s), methodology (qual/quant/mixed + sample), top 3-5 findings, theoretical contributions, limitations the authors acknowledge, limitations they did NOT acknowledge (LLM critique), how it fits the user's thesis topic, follow-up questions, APA citation
- Uses: pypdf for text extraction, structured output via Pydantic

TAB 2 — Literature Explorer
- Input: a research topic string
- Output: 8-10 recent papers (title, authors, year, abstract summary) + a synthesis section with dominant themes, methodological trends, and 3 open gaps
- Uses: arxiv Python library OR Semantic Scholar API (whichever needs less setup), then LLM summarization + structured synthesis

TAB 3 — Thesis Outline Coach
- Input: thesis topic + field + intended methodology + timeline in months
- Output: chapter-by-chapter outline with research questions per chapter, suggested methods, milestone timeline, seed citations the LLM knows
- Uses: pure prompting + structured output, no APIs

TAB 4 — Research Idea Critic
- Input: a research idea or abstract (free text)
- Output: novelty score 1-10 with reasoning, related work the LLM knows, methodological concerns, suggested improvements, follow-up questions to sharpen the idea
- Uses: structured output (mixed int + lists + strings)

SHARED — Library sidebar
- Every tab's output can be "saved to library" → appended to data/library.json with timestamp + tab name + title
- Sidebar lists saved entries; clicking one shows the saved output

TUNING — Field
- The default system prompts should be tuned for management/business research (APA citations; awareness of AMJ, AMR, ASQ, JAP, JIBS, Org Science; constructs vs variables; qual/quant/mixed methods vocabulary)
- A sidebar expander lets the user switch the "field" (Management / STEM / Social Sciences / Other) which swaps which prompt variant is loaded

TECH REQUIREMENTS
- UV project (pyproject.toml + uv.lock)
- streamlit, langchain, langchain-openai, pypdf, pydantic, python-dotenv, arxiv (or semanticscholar)
- OPENAI_API_KEY loaded from .env via python-dotenv
- Pydantic schemas for ALL structured outputs (one per tab)
- Clean file structure:
  - app.py (main entry, sets up tabs and library sidebar)
  - tabs/ (one file per tab)
  - prompts.py (all system prompts)
  - schemas.py (all Pydantic models)
  - utils.py (LLM client factory, PDF parsing, library save/load)
  - data/library.json

BEFORE WRITING CODE, please respond with:
1. Confirmation of the file structure
2. The 4 Pydantic schemas you'd define (just field names + types)
3. Which lit search library you recommend (arxiv vs semanticscholar) and why
4. Any assumptions or open questions
5. A suggested build order so I can stop at any checkpoint and still have something working

DO NOT WRITE CODE YET. Wait for my green light.
```

---

## Prompt 2 — After you approve the plan

```
Plan looks good. Build it incrementally, in this order, stopping for me to test between each:

STEP A: Skeleton
- UV project setup
- app.py with 4 empty tabs + a sidebar shell + .env loading
- utils.py with: get_llm() factory, save_to_library(entry), load_library() -> list
- schemas.py and prompts.py as empty placeholders
- README.md with setup steps
- Run streamlit to confirm boots

STEP B: Tab 1 (Paper Digest)
- Pydantic schema for PaperDigest
- System prompt in prompts.py
- tabs/paper_digest.py with PDF upload, "thesis topic" input, "Analyze" button, render output, "Save to library" button
- Test with any short PDF

STEP C: Tab 3 (Thesis Outline Coach)
- Simplest after Tab 1, no APIs
- Same pattern: schema, prompt, tab file, save button

STEP D: Tab 4 (Research Idea Critic)
- Same pattern again

STEP E: Tab 2 (Literature Explorer)
- The tricky one — uses arxiv or semanticscholar
- Tool calling via LangChain or direct API call, your choice
- Render the paper list nicely, then synthesis section

STEP F: Polish
- Field selector in sidebar that swaps prompt variants
- Library viewer in sidebar
- Friendly error messages
- README updates with screenshots

After each step, give me the commands to run and what to verify before moving on.
```

---

## Prompt 3 — Polish (after all tabs work)

```
All tabs work. Final pass:

1. Sidebar "Settings" expander:
   - Field selector (Management / STEM / Social Sciences / Other)
   - Live-editable system prompts (read from prompts.py, allow override per session)
   - "Clear library" button with confirmation

2. UX polish:
   - Loading spinners during LLM calls
   - Markdown rendering on all outputs (so headings and lists look clean)
   - Friendly error messages (no stack traces) — "Could not read this PDF. Try another file."
   - Each tab has a one-line "what this does" subtitle

3. README.md:
   - Project description
   - Setup steps (uv sync, .env, streamlit run)
   - Screenshots placeholder for each tab
   - Tech stack table
   - "What's next" section (RAG in Week 2, etc.)

4. Create a .gitignore that excludes .env, .venv, data/library.json, __pycache__

Do not break anything that works. Run the app and confirm all 4 tabs still produce output.
```

---

## What to record for the video (≤5 min)

| Time | Section |
|---|---|
| 0:00-0:30 | Who you are + why a PhD needs this (drowning in papers, lit reviews, planning) |
| 0:30-1:00 | Show the README and tech stack table, mention vibe coding with Claude Code |
| 1:00-2:00 | Tab 1 — upload a real paper, walk through the digest sections |
| 2:00-2:45 | Tab 2 — search a topic, show the explorer + synthesis |
| 2:45-3:30 | Tab 3 — paste a thesis topic, show the outline + timeline |
| 3:30-4:15 | Tab 4 — paste a research idea, show the critique |
| 4:15-4:45 | Library sidebar — show saved entries, mention RAG coming in Week 2 |
| 4:45-5:00 | Show 1-2 prompts you used, sign off |

**Recording tools:** Windows Game Bar (`Win + G`), Loom (loom.com), or OBS.

---

## Google Doc outline (1-2 pages)

1. **Problem** — PhDs juggle four research jobs (reading, scouting, planning, critiquing). Each has its own friction.
2. **Solution** — One app, four tabs, shared library. Personal companion that travels with you through the PhD.
3. **Architecture** — Tabs + shared LLM client + Pydantic structured output + local JSON library
4. **Tech stack** — Streamlit, LangChain, OpenAI GPT-4o-mini, Pydantic, pypdf, arxiv
5. **Field tuning** — Defaults tuned for management/business research; field selector for others
6. **Design choices** — Why one app vs four (shared infra), why no RAG yet (Week 2 scope), why structured output (reliability for downstream code)
7. **Prompts used** — Paste your top 3 prompts to Claude Code
8. **What's next** — Multi-paper RAG (Week 2), arXiv auto-import on schedule (Week 4), browser automation to fetch full-text PDFs (later)
9. **Reflections** — What surprised you about vibe coding 4 features in one weekend?
