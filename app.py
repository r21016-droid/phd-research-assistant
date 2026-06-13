"""Research Assistant — a multi-tab Streamlit toolkit for PhD researchers.

Five AI companions over the research lifecycle, sharing one LLM client, one
.env, and one local JSON library:

  1. Paper Digest        — structured digest of an uploaded paper PDF
  2. Literature Explorer — landscape scan of a topic (Semantic Scholar + LLM)
  3. Thesis Outline Coach— chapter-by-chapter thesis plan
  4. Research Idea Critic— novelty + rigor critique of an idea
  5. Zotero Chat         — RAG over a Zotero collection (Pinecone + LangGraph)

Run with:  uv run streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from prompts import get_system_prompt
from tabs import idea_critic, lit_explorer, paper_digest, thesis_coach, zotero_chat
from utils import MODEL_NAME, get_llm, load_library, save_to_library

# Order here = tab order in the UI. Tabs 1-4 are the Week 1 toolkit;
# Tab 5 is the Week 2 RAG tab (Zotero + Pinecone + LangGraph).
TAB_MODULES = [paper_digest, lit_explorer, thesis_coach, idea_critic, zotero_chat]

# Field variants the sidebar can switch between (prompt tuning lands in Step F).
FIELDS = ["Management", "STEM", "Social Sciences", "Other"]


def build_ctx() -> dict:
    """Bundle the shared dependencies handed to every tab's render()."""
    field = st.session_state.get("field", FIELDS[0])

    def get_prompt(tab_name: str) -> str:
        """Effective system prompt: per-session override if set, else the
        field-tuned default from prompts.py."""
        override = st.session_state.get(f"prompt_override::{tab_name}")
        if override and override.strip():
            return override
        return get_system_prompt(tab_name, field)

    return {
        "get_llm": get_llm,
        "field": field,
        "save_to_library": save_to_library,
        "load_library": load_library,
        "get_prompt": get_prompt,
    }


def render_sidebar() -> None:
    """The shared shell: field selector + saved-library viewer."""
    with st.sidebar:
        st.title("🎓 Research Assistant")
        st.caption(f"Model: `{MODEL_NAME}`")

        with st.expander("⚙️ Research field", expanded=False):
            st.selectbox(
                "Tune prompts for…",
                FIELDS,
                key="field",
                help="Swaps the system-prompt variant used across all tabs "
                     "(wired up in Step F).",
            )

        st.divider()
        st.subheader("📚 Library")
        entries = load_library()
        if not entries:
            st.caption("No saved outputs yet. Generate something and hit "
                       "**Save to library**.")
        else:
            st.caption(f"{len(entries)} saved")
            for entry in entries:
                label = f"{entry.get('tab', '?')} · {entry.get('title', '(untitled)')}"
                with st.expander(label, expanded=False):
                    st.caption(entry.get("timestamp", ""))
                    st.json(entry.get("payload", {}), expanded=False)


def main() -> None:
    st.set_page_config(page_title="Research Assistant", page_icon="🎓",
                       layout="wide")
    render_sidebar()

    st.title("🎓 Research Assistant")
    st.caption("Five AI companions for reading papers, scouting literature, "
               "planning your thesis, stress-testing ideas, and chatting "
               "with your Zotero library.")

    ctx = build_ctx()
    tab_objs = st.tabs([m.TITLE for m in TAB_MODULES])
    for tab_obj, module in zip(tab_objs, TAB_MODULES):
        with tab_obj:
            module.render(ctx)


if __name__ == "__main__":
    main()
