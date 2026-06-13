# Evaluation Set — Zotero Chat (Tab 5)

A small, honest manual eval. Run each question against a real synced collection from your Zotero library, then score the answer on three dimensions:

| Dimension | Question to ask yourself |
|---|---|
| **Citation accuracy** | Did the answer cite the right paper(s)? |
| **Faithfulness** | Is every claim in the answer actually supported by the retrieved chunks? |
| **Coverage** | Did it surface all relevant papers, or miss obvious ones? |

Use this template — fill in column "✓" with a 0 (fail), 0.5 (partial), or 1 (pass) for each dimension.

---

## Test questions

Pick a Zotero collection you know well (e.g., 5–15 papers on one topic). For each row below, substitute the **<placeholders>** with terms from your own collection.

| # | Question | Expected behavior | Citation ✓ | Faithful ✓ | Coverage ✓ |
|---|---|---|---|---|---|
| 1 | What is the dominant operationalization of **<construct X>** across these papers? | Should name 2–3 specific measures with paper citations | | | |
| 2 | Which papers use **<methodology Y>** (e.g., longitudinal, experimental, ethnographic)? | Should list the papers that use this method and cite each | | | |
| 3 | What gaps in the literature are explicitly mentioned by these authors? | Should pull "limitations" or "future work" sections and cite | | | |
| 4 | How is **<construct X>** distinguished from **<construct Z>**? | Tests construct discrimination across papers | | | |
| 5 | What sample sizes did these studies use? | Numeric retrieval; tests precision | | | |
| 6 | Which papers cite **<author surname>**? | Citation graph retrieval (often hard for RAG) | | | |
| 7 | What theoretical frameworks ground these papers? | Should name frameworks with citations | | | |
| 8 | Summarize the findings of the most recent paper in this collection. | Tests if the model can identify "most recent" from metadata | | | |
| 9 | A question whose answer is **not** in the collection — e.g., a date-specific or off-topic question | Model must say "I don't know" or "the provided context does not contain this" | | | |
| 10 | A jargon-heavy query using a domain-specific acronym from your field | Tests embedding model handling of niche vocabulary | | | |

---

## How to score the eval

After running all 10 questions:

```
Total per dimension = sum of column / 10
Total overall        = average across the three columns
```

For the writeup (`WEEK2_SUBMISSION.md`), report:

- *"Out of 10 questions: **X citation-accurate, Y faithful, Z full-coverage**."*
- One short paragraph on the **biggest failure mode** you saw + what you'd change.

Common failure modes to watch for:

1. **Construct-name queries miss the most relevant paper** — fix by increasing `chunk_size` or adding hybrid (BM25) retrieval
2. **Acronym/jargon queries fail** — domain-tuned embedder helps; otherwise prefix the query
3. **"Most recent" / date queries fail** — pure semantic search doesn't reason about time; add metadata filtering
4. **Citation graph queries fail** — vector embeddings don't capture citation links; this is a known RAG limitation
5. **Out-of-corpus queries get fabricated answers** — your system prompt should prevent this; if it doesn't, tighten the prompt

---

## Future automation

For a production-grade eval (Week 5 of the cohort covers this):

- **RAGAS** — automated metrics for context_precision, context_recall, faithfulness, answer_relevancy
- **LangSmith** — trace + score every query; track regression over prompt/model changes
- **Synthetic golden set** — use GPT-4o to generate question/answer pairs from your corpus, then test against them

For now, this 10-question manual eval is honest and sufficient for a Week 2 submission.
