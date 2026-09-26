"""Pydantic schemas for structuring YouTube educational lecture transcript outputs."""

from pydantic import BaseModel, Field


class ConceptDetail(BaseModel):
    concept_name: str = Field(
        ...,
        description="The name of the concept, algorithm, theory, or tool being taught.",
    )
    detailed_explanation: str = Field(
        ...,
        description=(
            "A comprehensive, step-by-step explanation of the concept as taught in the video. "
            "Retain all core technical details, nuances, and logical steps. Do not generalize or skip substance."
        ),
    )
    code_or_formulas: list[str] | None = Field(
        None,
        description=(
            "Exact code blocks, CLI commands, mathematical formulas, or syntax rules introduced for this concept, if applicable."
        ),
    )
    examples_or_case_studies: list[str] = Field(
        default_factory=list,
        description=(
            "Real-world examples, analogies, or practical demonstrations used by the instructor to illustrate this concept."
        ),
    )


class LectureModule(BaseModel):
    module_title: str = Field(
        ...,
        description="Title of this specific topic/chapter within the lecture.",
    )
    summary_of_section: str = Field(
        ...,
        description="Brief context on what this section covers and why it matters.",
    )
    concepts: list[ConceptDetail] = Field(
        ...,
        description="All specific concepts, techniques, or instructions taught in this section in chronological order.",
    )


class GlossaryItem(BaseModel):
    term: str = Field(
        ..., description="Key term, keyword, or acronym introduced in the video."
    )
    definition: str = Field(
        ..., description="Clear definition based on the context of the lecture."
    )


class EducationalContent(BaseModel):
    lecture_title: str = Field(
        ...,
        description="An accurate, professional title for the overall tutorial/lecture.",
    )
    target_audience_and_prerequisites: str = Field(
        ...,
        description="Estimated difficulty level, target audience, and any prerequisite knowledge mentioned or implied.",
    )
    executive_overview: str = Field(
        ...,
        description=(
            "A high-level orientation (2-3 paragraphs) summarizing the overarching goals and scope of the entire lecture."
        ),
    )
    modules: list[LectureModule] = Field(
        ...,
        description=(
            "Chronological breakdown of the core educational modules. Skip tangents, intros, and sponsorships, "
            "but preserve 100% of the actual teaching."
        ),
    )
    glossary: list[GlossaryItem] = Field(
        default_factory=list,
        description="A list of essential terms and definitions defined throughout the lecture.",
    )
    study_and_review_questions: list[str] = Field(
        default_factory=list,
        description=(
            "3 to 5 self-assessment questions or practical exercises based strictly on the material taught, "
            "to help the learner verify their understanding."
        ),
    )
