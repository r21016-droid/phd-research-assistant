# Setup: Pinecone + Zotero for Tab 5

The Zotero Chat tab needs **three** sets of credentials in your `.env`:

```
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk_...
ZOTERO_USER_ID=...
ZOTERO_API_KEY=...
```

This doc tells you exactly where to find each one. Total time: ~10 minutes.

---

## 1. Pinecone (~3 min)

Pinecone is the vector database. You only need to do this once — the app
auto-creates the index on first sync.

### Steps

1. Go to **https://www.pinecone.io** and click **Sign up free**.
2. Use your Google/GitHub login or an email. Free tier is fine — it gives you
   2 GB storage and ~5M reads/month, way more than this project needs.
3. After login you'll land on the **Console**. In the left sidebar click
   **API Keys** (or go to https://app.pinecone.io/-/keys).
4. You'll see a default key already created. Click the **Copy** button next
   to it.
5. Open your `.env` file and paste:

   ```
   PINECONE_API_KEY=pcsk_paste_here
   ```

### You do NOT need to manually create an index

The app creates `phd-zotero` automatically the first time you click **Sync**.
It uses:

- **Dimensions:** 1536 (matches OpenAI `text-embedding-3-small`)
- **Metric:** cosine
- **Spec:** serverless, AWS us-east-1 (free tier)

If you ever want a different name, change `Pinecone index name` in the tab UI.

### How storage is organized

| Concept | What it maps to |
|---|---|
| **Index** | One Pinecone database — `phd-zotero` by default |
| **Namespace** | One Zotero collection (slugified name like `psychological-safety`) |
| **Vector** | One chunk of a PDF page |
| **Metadata** | `source` (paper title) + `page` (1-indexed) |

So if you sync three Zotero collections, you'll have one index with three
namespaces — fully isolated, no cross-talk.

---

## 2. Zotero (~5 min)

You need your **userID** (a number) and a **personal API key**.

### Step 1 — find your userID

1. Make sure you're logged into Zotero at **https://www.zotero.org**.
2. Go to **https://www.zotero.org/settings/keys**.
3. Near the top of the page you'll see a line like:

   > *Your userID for use in API calls is **8675309***

4. Copy that number into `.env`:

   ```
   ZOTERO_USER_ID=8675309
   ```

### Step 2 — create an API key

1. Same page (`/settings/keys`), scroll down to **Create new private key**
   and click it. (Direct link: https://www.zotero.org/settings/keys/new)
2. Give it a name like *"PhD Research Assistant"*.
3. Check these permissions:
   - **Personal Library** → ✅ Allow library access (read)
   - **Personal Library** → ✅ Allow notes access (optional but useful)
   - **Default Group Permissions** → leave as "None" unless you use groups
4. Click **Save Key**.
5. The key is shown once — copy it immediately:

   ```
   ZOTERO_API_KEY=paste_long_string_here
   ```

### Step 3 — verify your PDFs are syncable

The app only ingests **PDF attachments**. Make sure your papers have actual
PDF attachments in Zotero (not just metadata records). Check by opening any
paper in the Zotero desktop app — if you see a paperclip icon with a
filename, it's a PDF and will sync.

**Tip:** if you use Zotero's free 300 MB tier, attached PDFs may live on
your local computer only. For this app to download them, you need them in
Zotero's cloud storage — either by upgrading to paid storage, or by storing
PDFs in a linked folder + using Zotero File Sync.

---

## 3. Wire it together

Once your `.env` has all four keys filled in:

```powershell
cd "C:\Users\sonal\OneDrive\Desktop\Learning AI by Ash\PhD Research Assistant"
uv sync          # picks up the new langgraph + pinecone + pyzotero deps
.venv\Scripts\activate
streamlit run app.py
```

Open the **📚 Zotero Chat** tab (the 5th one). Then:

1. Click **🔄 List my Zotero collections** — confirms the credentials work
2. Pick a small collection (start with 3–5 PDFs to test)
3. Click **📥 Sync this collection** — takes ~10 sec per PDF
4. Ask a question — first answer takes ~5 sec

---

## Troubleshooting

| Error | Likely cause | Fix |
|---|---|---|
| `PINECONE_API_KEY is not set` | `.env` not loaded or key missing | Restart Streamlit after editing `.env` |
| `Forbidden` from Zotero | API key lacks library read permission | Recreate key with library access enabled |
| `No PDFs found in this collection` | Items have no PDF attachments | Add PDFs in Zotero, then re-sync |
| `Could not extract text from PDF` | Scanned-image PDF | Run OCR via ABBYY/Adobe first, or skip |
| `Index creation timeout` | Pinecone free tier provisioning | Wait 30s and retry the sync |

---

## What the app actually does (for the writeup)

```
Zotero collection
   ↓  pyzotero.collection_items()
PDF attachments (titles + keys)
   ↓  pyzotero.file(key)  →  bytes
PDF bytes
   ↓  pypdf  →  per-page text
Page documents
   ↓  RecursiveCharacterTextSplitter (700/100)
Chunks  ←  metadata: {source: paper_title, page: 1-indexed}
   ↓  OpenAI text-embedding-3-small (1536-dim)
Vectors
   ↓  Pinecone upsert into namespace = slugified collection name
Pinecone (serverless, AWS us-east-1)

QUERY TIME — LangGraph 2-node pipeline:

   START
     ↓
   retrieve  →  Pinecone similarity_search(question, k=5)
     ↓
   generate  →  GPT-4o-mini with system prompt:
                  "answer only from context, cite inline as [source p.X],
                   say I don't know if context is insufficient"
     ↓
    END
```

Every box maps to a concept Aishwarya covered in Session 1: chunking
strategy, embedding model choice, vector database, retrieval, prompted
generation with grounding. The LangGraph wrapper is what makes it
"agent-ready" for Week 3 — you can later add nodes for re-ranking,
query rewriting, or self-grading without rewriting the rest.
