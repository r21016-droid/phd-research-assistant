"""Minimal RAG pipeline: Pinecone + OpenAI embeddings + LangGraph.

Graph (two nodes, the simplest possible useful agent):

    START -> retrieve -> generate -> END

Used by tabs/zotero_chat.py. Kept tiny on purpose — every component the
cohort teaches (embed, vector store, retriever, prompt, LLM, graph) is
visible in <100 lines.
"""

from __future__ import annotations

import os
from typing import List, TypedDict

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import END, START, StateGraph
from pinecone import Pinecone, ServerlessSpec

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIMS = 1536
LLM_MODEL = "gpt-4o-mini"


# --- Pinecone helpers ------------------------------------------------------

def _pc() -> Pinecone:
    key = os.getenv("PINECONE_API_KEY")
    if not key:
        raise RuntimeError("PINECONE_API_KEY is not set. See ZOTERO_PINECONE_SETUP.md.")
    return Pinecone(api_key=key)


def ensure_index(name: str) -> None:
    """Create the Pinecone index on first use. Idempotent."""
    pc = _pc()
    existing = [i["name"] for i in pc.list_indexes()]
    if name not in existing:
        pc.create_index(
            name=name,
            dimension=EMBED_DIMS,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )


def get_vectorstore(index_name: str, namespace: str) -> PineconeVectorStore:
    """Return a vector store handle scoped to one (index, namespace)."""
    return PineconeVectorStore(
        index_name=index_name,
        embedding=OpenAIEmbeddings(model=EMBED_MODEL),
        namespace=namespace,
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    )


def upsert_documents(docs: List[Document], index_name: str, namespace: str) -> None:
    """Embed and push chunks into Pinecone under one namespace (one collection)."""
    ensure_index(index_name)
    get_vectorstore(index_name, namespace).add_documents(docs)


# --- LangGraph RAG ---------------------------------------------------------

class RAGState(TypedDict):
    question: str
    documents: List[Document]
    answer: str


def build_graph(index_name: str, namespace: str, system_prompt: str, top_k: int = 5):
    """Compile the 2-node RAG graph for one Zotero collection."""
    vs = get_vectorstore(index_name, namespace)
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    def retrieve(state: RAGState) -> dict:
        return {"documents": vs.similarity_search(state["question"], k=top_k)}

    def generate(state: RAGState) -> dict:
        context = "\n\n---\n\n".join(
            f"[{d.metadata.get('source', '?')} p.{d.metadata.get('page', '?')}]\n"
            f"{d.page_content}"
            for d in state["documents"]
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "Retrieved context:\n{context}\n\nQuestion: {question}"),
            ]
        )
        result = (prompt | llm).invoke(
            {"context": context, "question": state["question"]}
        )
        return {"answer": result.content}

    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
