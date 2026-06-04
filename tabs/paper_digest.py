"""Tab 1 — Paper Digest.

Upload a research paper PDF (plus an optional thesis topic) and get a
structured digest: research questions, methodology, key findings,
theoretical contributions, limitations the authors acknowledge AND ones they
don't, how it fits your thesis, follow-up questions, and an APA citation.
"""

from __future__ import annotations

import streamlit as st

from schemas import PaperDigest
from utils import extract_pdf_text, run_structured

TITLE = "📄 Paper Digest"
# Key used to look up this tab's prompt in prompts.py (no emoji).
TITLE_KEY = "Paper Digest"
DESCRIPTION = (
    "Upload a paper PDF and get a structured digest — research questions, "
    "methodology, findings, acknowledged **and** unacknowledged limitations, "
    "fit with your thesis, follow-up questions, and an APA citation. "
    "Triage your reading list before committing to a deep read."
)

# Session keys (namespaced so tabs never collide).
_RESULT_KEY = "paper_digest::result"


def _bullets(items: list[str]) -> str:
    """Render a list of strings as a markdown bullet list (or a dash if empty)."""
    items = [i for i in (items or []) if str(i).strip()]
    if not items:
        return "_None identified._"
    return "\n".join(f"- {i}" for i in items)


def _render_digest(d: dict) -> None:
    """Pretty markdown rendering of a PaperDigest dict."""
    st.markdown(f"### {d.get('title', '(untitled)')}")
    meta = " · ".join(
        x for x in [d.get("authors", ""), str(d.get("year", ""))] if x
    )
    if meta:
        st.caption(meta)

    method = d.get("methodology_type", "")
    sample = d.get("sample_description", "")
    st.markdown(f"**Methodology:** `{method}`" + (f" — {sample}" if sample else ""))

    st.markdown("**Research question(s)**")
    st.markdown(_bullets(d.get("research_questions", [])))

    st.markdown("**Key findings**")
    st.markdown(_bullets(d.get("key_findings", [])))

    st.markdown("**Theoretical contributions**")
    st.markdown(_bullets(d.get("theoretical_contributions", [])))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Limitations — acknowledged**")
        st.markdown(_bullets(d.get("limitations_acknowledged", [])))
    with col2:
        st.markdown("**Limitations — *not* acknowledged** 🔎")
        st.markdown(_bullets(d.get("limitations_unacknowledged", [])))

    fit = d.get("fit_with_thesis", "")
    if fit and fit.strip():
        st.markdown("**Fit with your thesis**")
        st.markdown(fit)

    st.markdown("**Follow-up questions**")
    st.markdown(_bullets(d.get("follow_up_questions", [])))

    st.markdown("**APA citation**")
    st.markdown(f"> {d.get('apa_citation', '')}")


def render(ctx) -> None:
    st.subheader(TITLE)
    st.caption(DESCRIPTION)

    uploaded = st.file_uploader("Research paper (PDF)", type=["pdf"])
    thesis = st.text_area(
        "My thesis topic (optional)",
        placeholder="e.g., Psychological safety in distributed software teams",
        height=80,
    )

    if st.button("Analyze paper", type="primary", disabled=uploaded is None):
        # 1) Extract text — turn any failure into a friendly message.
        try:
            text = extract_pdf_text(uploaded)
        except Exception:
            st.error("Could not read this PDF. Try another file.")
            return
        if not text.strip():
            st.error(
                "Could not extract any text from this PDF — it may be a scanned "
                "image. Try a text-based PDF."
            )
            return

        # 2) Call the LLM for a structured digest.
        user_content = (
            f"THESIS TOPIC: {thesis.strip() or '(none provided)'}\n\n"
            f"PAPER TEXT:\n{text}"
        )
        with st.spinner("Analyzing paper…"):
            try:
                digest = run_structured(
                    PaperDigest, ctx["get_prompt"](TITLE_KEY), user_content
                )
            except RuntimeError as e:  # missing API key
                st.error(str(e))
                return
            except Exception:
                st.error(
                    "Something went wrong while analyzing the paper. Please try "
                    "again in a moment."
                )
                return
        st.session_state[_RESULT_KEY] = digest.model_dump()

    # 3) Render the most recent result (persists across reruns, e.g. after save).
    result = st.session_state.get(_RESULT_KEY)
    if result:
        st.divider()
        _render_digest(result)
        if st.button("💾 Save to library", key="paper_digest::save"):
            ctx["save_to_library"](
                "Paper Digest", result.get("title", "Paper digest"),
                result, ctx["field"],
            )
            st.success("Saved to library.")
            st.rerun()
