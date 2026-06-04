"""Pydantic output schemas for every tab.

One model per tab drives the LLM's structured output (via
ChatOpenAI.with_structured_output). Filled in as each tab is built:
  - Step B: PaperDigest      ✅
  - Step C: ThesisOutline    ✅
  - Step D: IdeaCritique      ✅
  - Step E: LiteratureReview  ✅
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PaperDigest(BaseModel):
    """Structured digest of a single research paper (Tab 1)."""

    title: str = Field(description="The paper's title, verbatim if findable.")
    authors: str = Field(
        description="Authors as a single string, e.g. 'Smith, J., & Lee, K.'"
    )
    year: str = Field(description="Publication year, or 'n.d.' if unknown.")
    research_questions: list[str] = Field(
        description="The explicit research question(s) the paper addresses."
    )
    methodology_type: Literal[
        "qualitative", "quantitative", "mixed", "conceptual"
    ] = Field(description="Overall methodological approach.")
    sample_description: str = Field(
        description="Sample/data: who/what, size, context. '' if conceptual."
    )
    key_findings: list[str] = Field(
        description="The 3-5 most important findings."
    )
    theoretical_contributions: list[str] = Field(
        description="What this adds to theory (constructs, mechanisms, models)."
    )
    limitations_acknowledged: list[str] = Field(
        description="Limitations the authors themselves acknowledge."
    )
    limitations_unacknowledged: list[str] = Field(
        description="Limitations the authors did NOT acknowledge — your critique."
    )
    fit_with_thesis: str = Field(
        description="How this connects to the user's thesis topic. "
        "'' if no thesis topic was provided."
    )
    follow_up_questions: list[str] = Field(
        description="Questions a researcher should ask after reading this."
    )
    apa_citation: str = Field(description="Full APA 7th-edition reference.")


class Chapter(BaseModel):
    """One chapter in a thesis outline (Tab 3)."""

    number: int = Field(description="Chapter number, starting at 1.")
    title: str = Field(description="Chapter title.")
    purpose: str = Field(description="One sentence: what this chapter does.")
    research_questions: list[str] = Field(
        description="Research question(s) addressed in this chapter."
    )
    suggested_methods: list[str] = Field(
        description="Methods/analyses appropriate for this chapter."
    )
    key_points: list[str] = Field(
        description="Key points, sections, or arguments to cover."
    )


class Milestone(BaseModel):
    """A timeline milestone (Tab 3)."""

    month: int = Field(description="Month offset within the timeline (1-based).")
    deliverable: str = Field(description="What should be done by this month.")


class ThesisOutline(BaseModel):
    """Chapter-by-chapter thesis plan (Tab 3)."""

    overview: str = Field(description="2-3 sentence framing of the thesis.")
    chapters: list[Chapter] = Field(description="Ordered chapters (typically 5-7).")
    milestones: list[Milestone] = Field(
        description="Milestones spread across the given timeline, month <= timeline."
    )
    seed_citations: list[str] = Field(
        description="APA references the model believes are relevant starting "
        "points. May include inaccuracies — must be verified by the user."
    )


class IdeaCritique(BaseModel):
    """Structured critique of a research idea (Tab 4)."""

    novelty_score: int = Field(
        ge=1,
        le=10,
        description="Novelty score from 1-10, where 10 is highly novel and valuable."
    )
    novelty_reasoning: str = Field(description="Why the idea received that score.")
    related_work: list[str] = Field(
        description="Representative related studies, theories, or approaches."
    )
    methodological_concerns: list[str] = Field(
        description="Risks or design concerns the idea should address."
    )
    suggested_improvements: list[str] = Field(
        description="Concrete improvements to strengthen the idea."
    )
    sharpening_questions: list[str] = Field(
        description="Questions to help clarify or sharpen the idea."
    )


class PaperSummary(BaseModel):
    """One paper in the literature scan (Tab 2)."""

    title: str = Field(description="The paper's title.")
    authors: str = Field(
        description="Authors as a single string, e.g. 'Smith, J., & Lee, K.' "
        "Use 'et al.' for long author lists."
    )
    year: str = Field(description="Publication year, or 'n.d.' if unknown.")
    abstract_summary: str = Field(
        description="A crisp 1-2 sentence summary of the paper's abstract, "
        "focused on its contribution and method."
    )


class LiteratureReview(BaseModel):
    """First-pass landscape scan of a research topic (Tab 2)."""

    papers: list[PaperSummary] = Field(
        description="The 8-10 papers provided, each with a summarized abstract. "
        "Use only the papers supplied; do not invent new ones."
    )
    dominant_themes: list[str] = Field(
        description="The recurring themes/topics across the papers."
    )
    methodological_trends: list[str] = Field(
        description="Methodological patterns (designs, data, analyses) seen."
    )
    open_gaps: list[str] = Field(
        description="Exactly 3 open gaps worth targeting in future research."
    )
