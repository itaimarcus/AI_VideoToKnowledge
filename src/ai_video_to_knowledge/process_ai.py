import os
from openai import (
    APIConnectionError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from ai_video_to_knowledge.exceptions import SummarizerError
from ai_video_to_knowledge.schemas import EducationalContent

SYSTEM_PROMPT = """You are an expert Educational Curriculum Designer and Technical Analyst.

Transform the provided YouTube transcript into a structured educational knowledge format.

Rules:
1. Preserve the instructional content with maximum fidelity. Capture all educational teaching, technical details, step-by-step reasoning, code snippets, CLI commands, mathematical formulas, explanations, and real-world examples presented by the instructor.
2. Remove non-educational content, including introductions, greetings, calls to action (e.g. "like and subscribe"), sponsorships, personal anecdotes, administrative remarks, and off-topic tangents.
3. Preserve the chronological order in which concepts and topics were taught.
4. Base the output exclusively on the transcript. Do not introduce external knowledge, interpretations, assumptions, corrections, or information that was not explicitly taught.
5. Do not omit technical depth merely to make the material shorter or simpler. When the instructor explains how or why something works, preserve that explanation.
6. Distinguish clearly between factual instruction, examples, demonstrations, and exercises when the transcript supports such distinctions.
7. When information is unclear, incomplete, or ambiguous in the transcript, preserve the uncertainty rather than guessing or filling in missing information.
8. The output must conform exactly to the provided Pydantic/Structured Output schema.
"""


def process_transcript_with_ai(
    transcript: str,
    model: str | None = None,
    api_key: str | None = None,
) -> EducationalContent:
    """Processes a raw YouTube transcript and returns structured educational content using OpenAI."""
    cleaned_transcript = transcript.strip() if transcript else ""
    if not cleaned_transcript:
        raise SummarizerError("Transcript text cannot be empty.")

    OPENAI_API_KEY = api_key or os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise SummarizerError("OPENAI_API_KEY is not configured.")

    OPENAI_MODEL = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.beta.chat.completions.parse(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Video Transcript:\n\n{cleaned_transcript}"},
            ],
            response_format=EducationalContent,
        )

        if not response.choices:
            raise SummarizerError("OpenAI returned an empty structured response.")

        parsed_content = response.choices[0].message.parsed

        if parsed_content is None:
            raise SummarizerError("OpenAI returned an empty structured response.")

        return parsed_content

    except SummarizerError:
        raise
    except AuthenticationError as e:
        raise SummarizerError("OpenAI API authentication failed. Check your OPENAI_API_KEY.") from e
    except RateLimitError as e:
        raise SummarizerError("OpenAI API rate limit or quota exceeded.") from e
    except APIConnectionError as e:
        raise SummarizerError("Failed to connect to OpenAI API servers.") from e
    except OpenAIError as e:
        raise SummarizerError(f"OpenAI API call failed: {str(e)}") from e
    except Exception as e:
        raise SummarizerError(f"Unexpected error during AI processing: {str(e)}") from e
