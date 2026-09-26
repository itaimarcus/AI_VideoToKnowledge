"""Unit tests for ai_video_to_knowledge.process_ai."""

from unittest.mock import MagicMock
import pytest
from openai import (
    APIConnectionError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)

from ai_video_to_knowledge.exceptions import SummarizerError
from ai_video_to_knowledge.process_ai import process_transcript_with_ai
from ai_video_to_knowledge.schemas import EducationalContent


# Triggers: SummarizerError
# Expected Message: "Transcript text cannot be empty."
def test_empty_cleaned_transcript():
    """Tests that passing whitespace or empty transcript raises SummarizerError."""
    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("   ")
    assert str(exc_info.value) == "Transcript text cannot be empty."


# Triggers: SummarizerError
# Expected Message: "OPENAI_API_KEY is not configured."
def test_missing_api_key(monkeypatch):
    """Tests that missing OPENAI_API_KEY environment variable raises SummarizerError."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript content")
    assert str(exc_info.value) == "OPENAI_API_KEY is not configured."


# Triggers: Success (Happy Path)
# Expected Result: EducationalContent object with correct fields
def test_successful_processing(mocker):
    """Tests happy path where OpenAI parses structured content successfully."""
    mock_parsed_data = EducationalContent(
        lecture_title="Intro to Python",
        target_audience_and_prerequisites="Beginners",
        executive_overview="Overview content",
        modules=[],
        glossary=[],
        study_and_review_questions=[],
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = mock_parsed_data

    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.return_value = mock_response

    result = process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert result.lecture_title == "Intro to Python"


# Triggers: SummarizerError
# Expected Message: "OpenAI returned an empty structured response."
def test_empty_ai_response(mocker):
    """Tests behavior when OpenAI returns parsed=None."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.parsed = None

    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.return_value = mock_response

    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert str(exc_info.value) == "OpenAI returned an empty structured response."


# Triggers: AuthenticationError -> SummarizerError
# Expected Message: "OpenAI API authentication failed. Check your OPENAI_API_KEY."
def test_auth_error(mocker):
    """Tests handling of OpenAI AuthenticationError."""
    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.side_effect = AuthenticationError(
        message="Invalid Key", response=MagicMock(), body=None
    )

    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert str(exc_info.value) == "OpenAI API authentication failed. Check your OPENAI_API_KEY."


# Triggers: RateLimitError -> SummarizerError
# Expected Message: "OpenAI API rate limit or quota exceeded."
def test_rate_limit_error(mocker):
    """Tests handling of OpenAI RateLimitError."""
    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.side_effect = RateLimitError(
        message="Rate limit exceeded", response=MagicMock(), body=None
    )

    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert str(exc_info.value) == "OpenAI API rate limit or quota exceeded."


# Triggers: APIConnectionError -> SummarizerError
# Expected Message: "Failed to connect to OpenAI API servers."
def test_connection_error(mocker):
    """Tests handling of OpenAI APIConnectionError."""
    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.side_effect = APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert str(exc_info.value) == "Failed to connect to OpenAI API servers."


# Triggers: OpenAIError -> SummarizerError
# Expected Message: "OpenAI API call failed: Bad Request Parameters"
def test_generic_openai_error(mocker):
    """Tests handling of generic OpenAIError."""
    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.side_effect = OpenAIError("Bad Request Parameters")

    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert str(exc_info.value) == "OpenAI API call failed: Bad Request Parameters"


# Triggers: Exception -> SummarizerError
# Expected Message: "Unexpected error during AI processing: System memory error"
def test_unexpected_error(mocker):
    """Tests handling of unexpected non-OpenAI exceptions."""
    mock_client = mocker.patch("ai_video_to_knowledge.process_ai.OpenAI").return_value
    mock_client.beta.chat.completions.parse.side_effect = RuntimeError("System memory error")

    with pytest.raises(SummarizerError) as exc_info:
        process_transcript_with_ai("valid transcript", api_key="fake-key")
    assert str(exc_info.value) == "Unexpected error during AI processing: System memory error"
