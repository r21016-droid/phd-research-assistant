# Week 2 Submission Pack

Everything you need to submit the Week 2 RAG project. Three artifacts to prepare, one Google Form to fill.

---

## Artifact 1 — Google Doc (1–2 pages)

Copy the structure below into a fresh Google Doc at https://docs.new. Replace the **<placeholders>** with your own words, then share with "Anyone with the link can view."

---

### **PhD Research Assistant — Zotero Chat (Week 2 RAG)**

**Cohort member:** Sonal Kumar (XLRI)
**Track:** Code-heavy (LangChain + LangGraph + Pinecone)
**GitHub:** <paste your repo URL here>
**Video walkthrough:** <paste your Loom/YouTube URL here>

---

#### 1. The problem

PhD researchers in management/business build large Zotero libraries (often hundreds of PDFs) but can't quickly answer cross-paper questions like *"how did the three papers I read on construct X measure it?"* Linear reading and grep-by-memory don't scale past 50 papers. This is the exact problem RAG was invented for.

#### 2. The solution

Tab 5 of my Research Assistant lets me:
1. Pick a Zotero collection (e.g., "Psychological Safety Literature")
2. Click sync — the app downloads every PDF, chunks it, embeds it with OpenAI's `text-embedding-3-small`, and stores the vectors in Pinecone under a namespace named after the collection
3. Ask cross-paper questions and get cited answers via a LangGraph 2-node pipeline

The retrieved chunks are displayed alongside the answer so I can verify grounding in real time.

#### 3. Decision framework

| Decision | Choice | Why |
|---|---|---|
| **Corpus source** | Zotero Web API via `pyzotero` | The researcher's actual reading list; no re-upload friction |
| **Chunking** | RecursiveCharacterTextSplitter, chunk_size=700, overlap=100 | Industry default; respects paragraph/sentence boundaries; balances precision (small chunk) and context (overlap) |
| **Embedding model** | OpenAI `text-embedding-3-small` (1536 dims) | Top of MTEB English at this size; free credits cover usage; matches cohort default |
| **Vector store** | Pinecone serverless (AWS us-east-1, cosine) | Cohort default; free tier sufficient; serverless = no infra to manage |
| **Storage isolation** | One Pinecone namespace per Zotero collection (slugified name) | Perfect isolation between subject areas; one query never mixes domains |
| **Retrieval** | Cosine similarity, top-K (default 5, slider 1–10 in UI) | Standard baseline; tunable for experimentation |
| **Re-ranking** | None in V1 | Deferred to V2; would be a new LangGraph node |
| **LLM** | OpenAI `gpt-4o-mini`, temperature=0 | Cheapest reliable model; deterministic citations |
| **System prompt** | "Answer ONLY from context, cite inline as [source p.X], say I don't know if context is insufficient" | Forces grounding; kills most hallucinations |
| **Orchestration** | LangGraph 2-node state graph (retrieve → generate) | Minimal today; extensible to grader/rewriter nodes in Week 3 without rewriting |
| **Evaluation** | 10-question manual eval set with known-correct citations | See `EVAL_QUESTIONS.md` in the repo |

#### 4. Architecture diagram

```
SYNC pipeline (one-time per collection):
  Zotero collection → pyzotero.collection_items()
    → PDF attachments → pyzotero.file(key) → bytes
    → pypdf extract → per-page text (with source + page metadata)
    → RecursiveCharacterTextSplitter(700, 100) → chunks
    → OpenAI text-embedding-3-small (1536 dims)
    → Pinecone upsert into namespace = slugified collection name

QUERY pipeline (every question, LangGraph):
  START → retrieve  (Pinecone similarity_search top-K)
        → generate (gpt-4o-mini with cite-only-from-context prompt)
        → END
```

#### 5. Evaluation

I built a 10-question manual eval set (see `EVAL_QUESTIONS.md` in the repo). For each question I knew the correct paper + section from my own reading. I scored:

- **Citation accuracy** — did the answer cite the right paper(s)?
- **Faithfulness** — was every claim in the answer supported by the retrieved chunks?
- **Coverage** — did the answer surface all relevant papers, or did it miss one?

Out of 10 questions: **<X> citation-accurate, <Y> faithful, <Z> full-coverage.** The biggest failure mode was <describe what you observed — e.g. "construct-name queries where my Zotero PDFs use the construct in passing missed the most relevant paper because their abstract emphasized a different framing." Tuning chunk_size up to 1000 helped.>

#### 6. Prompts used to build it

I built this with Claude Code on Opus in three checkpointed prompts:

1. **Architecture brainstorm** — described the 5th tab + shared sidebar + Zotero/Pinecone/LangGraph constraint, asked for file structure, the LangGraph state schema, and a build order *before any code was written*.
2. **Incremental build** — "Build it step by step: rag.py first, then zotero_lib.py, then the tab. Stop after each so I can test."
3. **Setup doc** — "Write a Pinecone + Zotero setup guide that even a non-coder can follow."

#### 7. What's next

- **Hybrid retrieval** (BM25 + vector + reciprocal rank fusion) — would help with jargon-heavy queries
- **Re-ranker** as a new LangGraph node (Cohere Rerank or a cross-encoder)
- **Metadata filtering** before retrieval (by year, journal, author)
- **RAGAS / LangSmith** for automated evals
- **Multi-collection queries** spanning multiple namespaces

#### 8. Reflection

The single most impactful design choice was **pulling PDFs from Zotero instead of asking for re-uploads**. The corpus *is* my real reading list, which means every demo is also a real-use moment. The second was **LangGraph over a plain chain** — a 2-node graph today feels over-engineered, but it makes the Week 3 agentic extensions (grader node, query rewriter) a one-line graph edit instead of a refactor.

The biggest surprise: the cite-only-from-context system prompt was more effective at killing hallucinations than I expected. The model genuinely says "I don't know" when context is missing — and "I don't know" is much more useful than a plausible-sounding wrong answer.

---

## Artifact 2 — Video walkthrough (≤5 min)

Record with **Loom** (loom.com — easiest, free), Windows Game Bar (`Win + G`), or OBS. Aim for <5 min total. Use this script:

| Time | What to show |
|---|---|
| 0:00 – 0:30 | Who you are. The problem: 50+ papers in Zotero, cross-paper questions are slow. |
| 0:30 – 1:00 | Quick tour of the 5-tab app. Click into **Tab 5 — Zotero Chat**. |
| 1:00 – 2:00 | Click **List my Zotero collections** → pick a real collection from your reading list → click **Sync**. Show the progress bar and the "Synced X chunks from Y PDFs" success message. |
| 2:00 – 3:30 | Ask a real cross-paper question you know the answer to. Show the answer + inline citations. Expand the **Retrieved chunks** panel and explain that this is the grounding evidence. |
| 3:30 – 4:15 | Ask a second question, deliberately a tricky one. Show how the model says "I don't know" when context doesn't contain the answer (or, if you're lucky, gets a good answer to a hard question). |
| 4:15 – 4:45 | Walk through the **architecture diagram** from your Google Doc. Mention LangGraph, Pinecone, OpenAI embeddings. |
| 4:45 – 5:00 | Show the GitHub repo. Sign off. |

**Upload:** Loom → Share → copy link. Or upload to YouTube as **Unlisted** → copy link. Test the link in an incognito window before submitting.

---

## Artifact 3 — GitHub repository

Push the entire `PhD Research Assistant/` folder to a new public GitHub repo. From PowerShell inside the folder:

```powershell
# If you haven't initialized git yet
git init
git branch -M main

# Add all files
git add .
git commit -m "Week 2 RAG: Zotero Chat tab with Pinecone + LangGraph"

# Connect to GitHub (create empty repo at github.com/new first — name it "phd-research-assistant", do NOT add README/gitignore)
git remote add origin https://github.com/YOUR-USERNAME/phd-research-assistant.git
git push -u origin main

# If you already have a repo from Week 1, just commit + push to the existing one
git add .
git commit -m "Week 2 RAG: add Zotero Chat tab"
git push
```

**Verify before submitting:**

- [ ] `https://github.com/<you>/phd-research-assistant` loads in an incognito window
- [ ] `.env` is **NOT** in the repo (check the file list — only `.env.example` should be there)
- [ ] `README.md` renders nicely (mentions all 5 tabs, has setup steps)
- [ ] `DESIGN.md`, `ZOTERO_PINECONE_SETUP.md`, and `WEEK2_SUBMISSION.md` are all there

---

## Submission checklist (Google Form)

1. **Find the Form link** — Maven → Week 2 → Weekly Project → project handout → form link
2. **Fill it in:**
   - Name: Sonal Kumar
   - Email: r21016@astra.xlri.ac.in
   - Project title: *PhD Research Assistant — Zotero Chat*
   - Track: Code-heavy
   - GitHub URL: your repo
   - Video URL: your Loom/YouTube
   - Google Doc URL: your shared doc
   - Brief description: *"Multi-tab AI research assistant; Week 2 adds a Zotero+Pinecone+LangGraph RAG tab that lets me chat with any of my Zotero collections."*

3. **After submitting:**
   - Post a short Discord message with screenshot + GitHub link (eligible for Builder of the Week)
   - Optional LinkedIn post — Aishwarya explicitly encouraged this

---

## Quick sanity check before you click submit

| Test | Pass? |
|---|---|
| Clone the repo into a fresh folder, run `uv sync`, copy `.env.example` to `.env`, fill keys → `streamlit run app.py` works on first try | ☐ |
| Tab 5 lists Zotero collections without error | ☐ |
| Sync a small collection (3 PDFs) succeeds; vectors visible in Pinecone console | ☐ |
| Ask one question → get cited answer | ☐ |
| Ask a question that ISN'T answerable from the corpus → model says "I don't know" | ☐ |
| Video plays without sign-in (incognito test) | ☐ |
| Google Doc opens without permission request (incognito test) | ☐ |

If anything fails, fix before submitting. The Form usually accepts edits/resubmissions until the deadline.
