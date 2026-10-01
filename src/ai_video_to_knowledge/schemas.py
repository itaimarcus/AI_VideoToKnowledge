"""Pydantic schemas for structured educational content extraction."""

from pydantic import BaseModel, Field


class Concept(BaseModel):
    """Represents a core technical or theoretical concept within a module."""

    concept_name: str = Field(description="Name of the concept.")
    detailed_explanation: str = Field(description="In-depth explanation of the concept.")
    code_or_formulas: list[str] = Field(
        default_factory=list,
        description="Relevant code snippets, math formulas, or equations if applicable.",
    )
    examples_or_case_studies: list[str] = Field(
        default_factory=list,
        description="Real-world examples or case studies demonstrating the concept.",
    )


class Module(BaseModel):
    """Represents a major thematic section or module in the lecture."""

    module_title: str = Field(description="Title of the module.")
    summary_of_section: str = Field(description="Summary overview of this section.")
    concepts: list[Concept] = Field(description="Key concepts covered in this module.")


class GlossaryItem(BaseModel):
    """Represents a term and its definition in the lecture glossary."""

    term: str = Field(description="Technical term or acronym.")
    definition: str = Field(description="Clear definition of the term.")


class EducationalContent(BaseModel):
    """Root Pydantic schema representing full structured educational notes extracted from a transcript."""

    lecture_title: str = Field(description="Overall title of the lecture or video.")
    target_audience_and_prerequisites: str = Field(
        description="Target audience and recommended prerequisites for this content."
    )
    executive_overview: str = Field(
        description="Executive summary of the key takeaways and core subject matter."
    )
    modules: list[Module] = Field(description="Ordered list of lecture modules.")
    glossary: list[GlossaryItem] = Field(
        default_factory=list, description="Glossary of key terms."
    )
    study_and_review_questions: list[str] = Field(
        default_factory=list,
        description="Self-study and review questions to test comprehension.",
    )

    def to_markdown(self) -> str:
        """Converts structured educational content into formatted Markdown body."""
        lines = [
            f"# {self.lecture_title}",
            "",
            "## Target Audience & Prerequisites",
            self.target_audience_and_prerequisites,
            "",
            "## Executive Overview",
            self.executive_overview,
            "",
            "## Lecture Modules",
        ]
        for module in self.modules:
            lines.append(f"### {module.module_title}")
            lines.append(module.summary_of_section)
            for concept in module.concepts:
                lines.append(f"#### {concept.concept_name}")
                lines.append(concept.detailed_explanation)
                if concept.code_or_formulas:
                    for item in concept.code_or_formulas:
                        lines.append(f"```\n{item}\n```")
                if concept.examples_or_case_studies:
                    for example in concept.examples_or_case_studies:
                        lines.append(f"*Example:* {example}")
            lines.append("")

        if self.glossary:
            lines.append("## Glossary")
            for g in self.glossary:
                lines.append(f"* **{g.term}**: {g.definition}")
            lines.append("")

        if self.study_and_review_questions:
            lines.append("## Study & Review Questions")
            for i, q in enumerate(self.study_and_review_questions, 1):
                lines.append(f"{i}. {q}")
            lines.append("")

        return "\n".join(lines)
