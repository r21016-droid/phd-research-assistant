"""Tab 2 — Literature Explorer.

Type a research topic and get 8-10 recent papers (title, authors, year,
abstract summary) pulled from Semantic Scholar, plus an LLM synthesis:
dominant themes, methodological trends, and 3 open gaps.

The papers are *real* (fetched from Semantic Scholar); the LLM only summarizes
the abstracts and synthesizes across the set — it never invents references.
"""

from __future__ import annotations

import streamlit as st

from schemas import LiteratureReview
from utils import run_structured, search_semantic_scholar

TITLE = "🔭 Literature Explorer"
# Key used to look up this tab's prompt in prompts.py (no emoji).
TITLE_KEY = "Literature Explorer"
DESCRIPTION = (
    "Enter a topic and get a first-pass landscape scan: 8-10 recent papers with "
    "summarized abstracts (via Semantic Scholar), then a synthesis of dominant "
    "themes, methodological trends, and 3 open gaps to target."
)

_RESULT_KEY = "lit_explorer::result"


def _bullets(items: list[str]) -> str:
    items = [i for i in (items or []) if str(i).strip()]
    if not items:
        return "_None._"
    return "\n".join(f"- {i}" for i in items)


def _build_user_content(topic: str, papers: list[dict]) -> str:
    """Pack the fetched papers into the user message for the LLM."""
    lines = [f"RESEARCH TOPIC: {topic}", "", "RETRIEVED PAPERS:"]
    for i, p in enumerate(papers, 1):
        meta = " · ".join(x for x in [p.get("venue", ""), p.get("year", "")] if x)
        lines.append(f"\n[{i}] {p.get('title', '')}")
        lines.append(f"    Authors: {p.get('authors', '')}")
        if meta:
            lines.append(f"    {meta}")
        lines.append(f"    Abstract: {p.get('abstract', '')}")
    return "\n".join(lines)


def _render_review(d: dict, sources: list[dict] | None = None) -> None:
    """Pretty markdown rendering of a LiteratureReview dict."""
    # Map title -> source paper so we can link out where we have a URL.
    by_title = {(s.get("title") or "").strip().lower(): s for s in (sources or [])}

    st.markdown("#### Papers")
    papers = d.get("papers", [])
    if not papers:
        st.markdown("_No papers._")
    for p in papers:
        title = p.get("title", "(untitled)")
        meta = " · ".join(
            x for x in [p.get("authors", ""), str(p.get("year", ""))] if x
        )
        src = by_title.get(title.strip().lower())
        url = src.get("url") if src else ""
        heading = f"**[{title}]({url})**" if url else f"**{title}**"
        st.markdown(heading)
        if meta:
            st.caption(meta)
        st.markdown(p.get("abstract_summary", ""))

    st.divider()
    st.markdown("#### Dominant themes")
    st.markdown(_bullets(d.get("dominant_themes", [])))

    st.markdown("#### Methodological trends")
    st.markdown(_bullets(d.get("methodological_trends", [])))

    st.markdown("#### Open gaps to target")
    st.markdown(_bullets(d.get("open_gaps", [])))


def render(ctx) -> None:
    st.subheader(TITLE)
    st.caption(DESCRIPTION)

    topic = st.text_input(
        "Research topic",
        placeholder="e.g., Psychological safety in remote teams",
    )

    if st.button("Scan the literature", type="primary", disabled=not topic.strip()):
        # 1) Fetch real papers from Semantic Scholar.
        with st.spinner("Searching Semantic Scholar…"):
            try:
                papers = search_semantic_scholar(topic.strip(), limit=10)
            except RuntimeError as e:  # network / API / rate-limit
                st.error(str(e))
                return
            except Exception:
                st.error(
                    "Something went wrong while searching for papers. Please try "
                    "again in a moment."
                )
                return

        if not papers:
            st.warning(
                "No papers with abstracts found for that topic. Try rephrasing or "
                "broadening it."
            )
            return

        # 2) Summarize + synthesize with the LLM, grounded in the fetched papers.
        user_content = _build_user_content(topic.strip(), papers)
        with st.spinner(f"Summarizing {len(papers)} papers and synthesizing…"):
            try:
                review = run_structured(
                    LiteratureReview, ctx["get_prompt"](TITLE_KEY), user_content
                )
            except RuntimeError as e:  # missing API key
                st.error(str(e))
                return
            except Exception:
                st.error(
                    "Something went wrong while synthesizing the literature. "
                    "Please try again in a moment."
                )
                return

        result = review.model_dump()
        result["_topic"] = topic.strip()  # for the library title
        result["_sources"] = papers       # keep URLs/metadata for linking
        st.session_state[_RESULT_KEY] = result

    # 3) Render the most recent result (persists across reruns, e.g. after save).
    result = st.session_state.get(_RESULT_KEY)
    if result:
        st.divider()
        st.caption(f"Topic: **{result.get('_topic', '')}**")
        _render_review(result, result.get("_sources"))
        if st.button("💾 Save to library", key="lit_explorer::save"):
            ctx["save_to_library"](
                "Literature Explorer",
                result.get("_topic", "Literature scan"),
                result,
                ctx["field"],
            )
            st.success("Saved to library.")
            st.rerun()
