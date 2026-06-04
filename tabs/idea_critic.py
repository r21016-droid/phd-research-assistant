"""Tab 4 — Research Idea Critic.

Paste a research idea or abstract and get a critique: a novelty score (1-10)
with reasoning, related work the LLM knows, methodological concerns,
suggested improvements, and follow-up questions to sharpen the idea.
"""

from __future__ import annotations

import streamlit as st

from schemas import IdeaCritique
from utils import run_structured

TITLE = "🧪 Research Idea Critic"
TITLE_KEY = "Research Idea Critic"
DESCRIPTION = (
    "Stress-test an idea before pitching it to your advisor: a novelty score "
    "(1-10) with reasoning, related work, methodological concerns, concrete "
    "improvements, and sharpening questions."
)

_RESULT_KEY = "idea_critic::result"


def _bullets(items: list[str]) -> str:
    items = [i for i in (items or []) if str(i).strip()]
    if not items:
        return "_None._"
    return "\n".join(f"- {i}" for i in items)


def _render_critique(d: dict) -> None:
    st.markdown(f"**Novelty score** — {d.get('novelty_score', '?')}/10")
    st.markdown("**Reasoning**")
    st.markdown(d.get("novelty_reasoning", ""))

    st.markdown("**Related work**")
    st.markdown(_bullets(d.get("related_work", [])))

    st.markdown("**Methodological concerns**")
    st.markdown(_bullets(d.get("methodological_concerns", [])))

    st.markdown("**Suggested improvements**")
    st.markdown(_bullets(d.get("suggested_improvements", [])))

    st.markdown("**Sharpening questions**")
    st.markdown(_bullets(d.get("sharpening_questions", [])))


def render(ctx) -> None:
    st.subheader(TITLE)
    st.caption(DESCRIPTION)

    idea = st.text_area(
        "Research idea / abstract",
        placeholder="Describe your idea or proposal in 3-8 sentences.",
        height=180,
    )

    if st.button("Evaluate idea", type="primary", disabled=not idea.strip()):
        with st.spinner("Analyzing your idea…"):
            try:
                critique = run_structured(
                    IdeaCritique,
                    ctx["get_prompt"](TITLE_KEY),
                    f"RESEARCH IDEA:\n{idea.strip()}"
                )
            except RuntimeError as e:
                st.error(str(e))
                return
            except Exception:
                st.error(
                    "Something went wrong while evaluating the idea. Please try "
                    "again in a moment."
                )
                return
        result = critique.model_dump()
        result["_idea"] = idea.strip()
        st.session_state[_RESULT_KEY] = result

    result = st.session_state.get(_RESULT_KEY)
    if result:
        st.divider()
        _render_critique(result)
        if st.button("💾 Save to library", key="idea_critic::save"):
            ctx["save_to_library"](
                "Research Idea Critic",
                result.get("_idea", "Research idea"),
                result,
                ctx["field"],
            )
            st.success("Saved to library.")
            st.rerun()
