"""Tab 5 — Chat with my Zotero library.

UX flow:
  1. Connect: app reads ZOTERO_USER_ID / ZOTERO_API_KEY from .env
  2. List collections -> dropdown
  3. Sync collection -> downloads PDFs, chunks, embeds, upserts into Pinecone
     under a namespace named after the collection
  4. Ask: question -> LangGraph (retrieve top-K from Pinecone, then generate)
  5. Save the Q&A pair into the shared library JSON via ctx['save_to_library']
"""

from __future__ import annotations

import os

import streamlit as st

from rag import build_graph, ensure_index, upsert_documents
from zotero_lib import (
    chunk_pdf,
    download_pdf_bytes,
    get_pdf_attachments,
    list_collections,
)

TITLE = "📚 Zotero Chat"
DESCRIPTION = "Chat with a Zotero collection using RAG (Pinecone + LangGraph)."

DEFAULT_INDEX = "phd-zotero"

SYSTEM_PROMPT = (
    "You are a careful research assistant for a PhD student in management/business "
    "research. Answer the question using ONLY the retrieved context below. Cite "
    "every claim inline as [source p.X]. If the context does not contain the "
    "answer, say so explicitly — do not guess. Prefer construct-aware academic tone."
)


def _slug(name: str) -> str:
    """Make a Pinecone-safe namespace from a collection name."""
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")[:40]


def _check_env() -> bool:
    missing = []
    if not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    if not os.getenv("PINECONE_API_KEY"):
        missing.append("PINECONE_API_KEY")
    if not os.getenv("ZOTERO_USER_ID"):
        missing.append("ZOTERO_USER_ID")
    if not os.getenv("ZOTERO_API_KEY"):
        missing.append("ZOTERO_API_KEY")
    if missing:
        st.error(
            "Missing env vars: " + ", ".join(f"`{m}`" for m in missing)
            + ". See `ZOTERO_PINECONE_SETUP.md`."
        )
        return False
    return True


def render(ctx: dict) -> None:
    st.subheader(TITLE)
    st.caption(DESCRIPTION)

    if not _check_env():
        return

    # --- 1. Sync section -------------------------------------------------
    with st.expander("⚙️ Sync a Zotero collection to Pinecone", expanded=True):
        index_name = st.text_input("Pinecone index name", value=DEFAULT_INDEX)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 List my Zotero collections"):
                try:
                    with st.spinner("Fetching collections from Zotero..."):
                        st.session_state.zotero_collections = list_collections()
                except Exception as exc:
                    st.error(f"Zotero connection failed: {exc}")

        collections = st.session_state.get("zotero_collections", [])
        if not collections:
            st.info("Click the button above to pull your Zotero collection list.")
            return

        col_map = {f"{name}  ({key[:6]}…)": key for name, key in collections}
        with col2:
            label = st.selectbox("Collection", list(col_map.keys()))
        chosen_key = col_map[label]
        chosen_name = label.split("  (")[0]
        namespace = _slug(chosen_name)
        st.caption(f"Will sync into namespace: `{namespace}`")

        if st.button("📥 Sync this collection", type="primary"):
            _sync_collection(index_name, chosen_key, chosen_name, namespace)

    # --- 2. Chat section -------------------------------------------------
    st.divider()
    st.subheader("Ask a question")

    if "rag_namespace" not in st.session_state:
        st.info("Sync a collection above before asking questions.")
        return

    namespace = st.session_state["rag_namespace"]
    index_name = st.session_state["rag_index"]
    st.caption(f"Querying `{index_name}` / namespace `{namespace}`")

    top_k = st.slider("Top-K retrieved chunks", 1, 10, 5)
    question = st.text_input(
        "Your question",
        placeholder="What methods did these papers use to study X?",
    )
    if not question:
        return

    try:
        with st.spinner("Retrieving and generating..."):
            graph = build_graph(index_name, namespace, SYSTEM_PROMPT, top_k=top_k)
            result = graph.invoke(
                {"question": question, "documents": [], "answer": ""}
            )
    except Exception as exc:
        st.error(f"Query failed: {exc}")
        return

    st.markdown("### Answer")
    st.write(result["answer"])

    with st.expander(f"Retrieved chunks ({len(result['documents'])})", expanded=False):
        for i, doc in enumerate(result["documents"], 1):
            st.markdown(
                f"**{i}. {doc.metadata.get('source', '?')}** — "
                f"page {doc.metadata.get('page', '?')}"
            )
            text = doc.page_content
            st.text(text[:400] + ("…" if len(text) > 400 else ""))

    if st.button("💾 Save Q&A to library"):
        ctx["save_to_library"](
            tab=TITLE,
            title=question[:60],
            payload={
                "question": question,
                "answer": result["answer"],
                "namespace": namespace,
                "top_k": top_k,
            },
        )
        st.success("Saved.")


def _sync_collection(
    index_name: str, collection_key: str, collection_name: str, namespace: str
) -> None:
    """Download every PDF in the collection, chunk, embed, upsert."""
    try:
        with st.spinner("Ensuring Pinecone index exists..."):
            ensure_index(index_name)
        with st.spinner("Listing PDFs in this collection..."):
            pdfs = get_pdf_attachments(collection_key)
        if not pdfs:
            st.warning("No PDF attachments found in this collection.")
            return

        st.write(f"Found **{len(pdfs)}** PDFs. Embedding...")
        progress = st.progress(0)
        all_chunks = []
        for i, (title, key) in enumerate(pdfs, 1):
            try:
                pdf_bytes = download_pdf_bytes(key)
                all_chunks.extend(chunk_pdf(pdf_bytes, source=title))
            except Exception as exc:
                st.warning(f"Skipped *{title}*: {exc}")
            progress.progress(i / len(pdfs))

        if not all_chunks:
            st.error("All PDFs failed to parse. Check that they aren't scanned images.")
            return

        with st.spinner(f"Pushing {len(all_chunks)} chunks into Pinecone..."):
            upsert_documents(all_chunks, index_name, namespace)

        st.session_state["rag_namespace"] = namespace
        st.session_state["rag_index"] = index_name
        st.success(
            f"Synced **{len(all_chunks)} chunks** from **{len(pdfs)} PDFs** "
            f"into `{index_name}` / `{namespace}`."
        )
    except Exception as exc:
        st.error(f"Sync failed: {exc}")
