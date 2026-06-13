"""Zotero helpers: list collections, fetch PDFs, chunk them.

Uses the official `pyzotero` package. All API calls go through the
authenticated client built from env vars set in `.env`.
"""

from __future__ import annotations

import io
import os
from typing import List, Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader
from pyzotero import zotero


def _client() -> zotero.Zotero:
    user_id = os.getenv("ZOTERO_USER_ID")
    api_key = os.getenv("ZOTERO_API_KEY")
    if not user_id or not api_key:
        raise RuntimeError(
            "ZOTERO_USER_ID or ZOTERO_API_KEY missing. See ZOTERO_PINECONE_SETUP.md."
        )
    return zotero.Zotero(user_id, "user", api_key)


def list_collections() -> List[Tuple[str, str]]:
    """Return [(collection_name, collection_key), ...] across the whole library."""
    z = _client()
    cols = z.everything(z.collections())
    return sorted((c["data"]["name"], c["key"]) for c in cols)


def get_pdf_attachments(collection_key: str) -> List[Tuple[str, str]]:
    """Return [(paper_title, attachment_key), ...] for every PDF in the collection.

    Walks both standalone PDF attachments and child attachments of parent items
    (which is how Zotero stores them when you import via Connector).
    """
    z = _client()
    items = z.everything(z.collection_items(collection_key))
    pdfs: List[Tuple[str, str]] = []
    for item in items:
        data = item.get("data", {})
        itype = data.get("itemType")
        if itype == "attachment" and data.get("contentType") == "application/pdf":
            title = data.get("title") or data.get("filename") or "Untitled"
            pdfs.append((title, item["key"]))
        elif itype not in ("attachment", "note"):
            parent_title = data.get("title", "Untitled")
            for child in z.children(item["key"]):
                cd = child.get("data", {})
                if cd.get("contentType") == "application/pdf":
                    pdfs.append((parent_title, child["key"]))
    return pdfs


def download_pdf_bytes(attachment_key: str) -> bytes:
    """Download the raw PDF bytes for one attachment."""
    return _client().file(attachment_key)


def chunk_pdf(
    pdf_bytes: bytes,
    source: str,
    chunk_size: int = 700,
    chunk_overlap: int = 100,
) -> List[Document]:
    """Read a PDF and return LangChain Documents with page metadata.

    One page -> raw text -> recursive character split into chunks. Every chunk
    keeps `source` (the paper title) and `page` (1-indexed) in its metadata.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    page_docs: List[Document] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            page_docs.append(
                Document(page_content=text, metadata={"source": source, "page": i + 1})
            )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(page_docs)
