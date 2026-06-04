"""Tab 3 — Thesis Outline Coach.

Give a thesis topic, field, intended methodology, and timeline; get a
chapter-by-chapter outline with research questions per chapter, suggested
methods, a milestone timeline, and seed citations the LLM knows about.
Pure prompting + structured output — no external APIs.
"""

from __future__ import annotations

import streamlit as st

from schemas import ThesisOutline
from utils import run_structured

TITLE = "🧭 Thesis Outline Coach"
TITLE_KEY = "Thesis Outline Coach"
DESCRIPTION = (
    "Turn a vague thesis topic into an actionable plan: a chapter-by-chapter "
    "outline with per-chapter research questions, suggested methods, a milestone "
    "timeline matched to your months, and seed citations to chase down."
)

_RESULT_KEY = "thesis_coach::result"
_METHODS = ["Qualitative", "Quantitative", "Mixed methods", "Conceptual / Not sure"]


def _bullets(items: list[str]) -> str:
    items = [i for i in (items or []) if str(i).strip()]
    if not items:
        return "_None._"
    return "\n".join(f"- {i}" for i in items)


def _render_outline(d: dict) -> None:
    st.markdown(f"**Overview** — {d.get('overview', '')}")

    st.markdown("#### Chapters")
    for ch in d.get("chapters", []):
        header = f"Chapter {ch.get('number', '?')}: {ch.get('title', '')}"
        with st.expander(header, expanded=False):
            if ch.get("purpose"):
                st.caption(ch["purpose"])
            st.markdown("**Research questions**")
            st.markdown(_bullets(ch.get("research_questions", [])))
            st.markdown("**Suggested methods**")
            st.markdown(_bullets(ch.get("suggested_methods", [])))
            st.markdown("**Key points**")
            st.markdown(_bullets(ch.get("key_points", [])))

    st.markdown("#### Milestone timeline")
    milestones = sorted(
        d.get("milestones", []), key=lambda m: m.get("month", 0)
    )
    if milestones:
        for m in milestones:
            st.markdown(f"- **Month {m.get('month', '?')}** — {m.get('deliverable', '')}")
    else:
        st.markdown("_None._")

    st.markdown("#### Seed citations")
    st.caption("⚠️ Model-generated — verify each reference before citing.")
    st.markdown(_bullets(d.get("seed_citations", [])))


def render(ctx) -> None:
    st.subheader(TITLE)
    st.caption(DESCRIPTION)

    topic = st.text_input(
        "Thesis topic",
        placeholder="e.g., How psychological safety shapes knowledge sharing in remote teams",
    )
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        field = st.text_input("Field", value=ctx["field"])
    with col2:
        methodology = st.selectbox("Intended methodology", _METHODS)
    with col3:
        timeline = st.number_input(
            "Timeline (months)", min_value=3, max_value=72, value=24, step=1
        )

    if st.button("Generate outline", type="primary", disabled=not topic.strip()):
        user_content = (
            f"THESIS TOPIC: {topic.strip()}\n"
            f"FIELD: {field.strip() or ctx['field']}\n"
            f"INTENDED METHODOLOGY: {methodology}\n"
            f"TIMELINE: {int(timeline)} months"
        )
        with st.spinner("Drafting your outline…"):
            try:
                outline = run_structured(
                    ThesisOutline, ctx["get_prompt"](TITLE_KEY), user_content
                )
            except RuntimeError as e:  # missing API key
                st.error(str(e))
                return
            except Exception:
                st.error(
                    "Something went wrong while drafting the outline. Please try "
                    "again in a moment."
                )
                return
        result = outline.model_dump()
        result["_topic"] = topic.strip()  # for the library title
        st.session_state[_RESULT_KEY] = result

    result = st.session_state.get(_RESULT_KEY)
    if result:
        st.divider()
        _render_outline(result)
        if st.button("💾 Save to library", key="thesis_coach::save"):
            ctx["save_to_library"](
                "Thesis Outline", result.get("_topic", "Thesis outline"),
                result, ctx["field"],
            )
            st.success("Saved to library.")
            st.rerun()
