"""Unit tests for ai_video_to_knowledge.transcript using pytest-mock."""

import types
import pytest
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from ai_video_to_knowledge.exceptions import TranscriptNotAvailableError
from ai_video_to_knowledge.transcript import fetch_transcript


@pytest.mark.parametrize(
    "raw_input, expected_output",
    [
        (
            [
                types.SimpleNamespace(text="Hello world"),
                types.SimpleNamespace(text="welcome"),
            ],
            "Hello world welcome",
        ),
        (
            [
                types.SimpleNamespace(text="   Hello \n\n "),
                types.SimpleNamespace(text=" World\n   "),
            ],
            "Hello World",
        ),
    ],
)
def test_fetch_transcript_success(mocker, raw_input, expected_output):
    """Ensures raw transcript items are formatted into a clean continuous string."""
    mock_youtube_api_get_transcript = mocker.patch(
        "ai_video_to_knowledge.transcript.YouTubeTranscriptApi.fetch"
    )
    mock_youtube_api_get_transcript.return_value = raw_input

    result = fetch_transcript("dQw4w9WgXcQ")

    assert result == expected_output
    mock_youtube_api_get_transcript.assert_called_once_with("dQw4w9WgXcQ")


@pytest.mark.parametrize(
    "api_error_instance",
    [
        TranscriptsDisabled(video_id="dQw4w9WgXcQ"),
        NoTranscriptFound(
            video_id="dQw4w9WgXcQ",
            requested_language_codes=["en"],
            transcript_data={},
        ),
        VideoUnavailable(video_id="dQw4w9WgXcQ"),
    ],
)
def test_fetch_transcript_api_errors(mocker, api_error_instance):
    """Ensures all YouTube API failures are translated to TranscriptNotAvailableError."""
    mock_youtube_api_get_transcript = mocker.patch(
        "ai_video_to_knowledge.transcript.YouTubeTranscriptApi.fetch"
    )
    mock_youtube_api_get_transcript.side_effect = api_error_instance

    with pytest.raises(TranscriptNotAvailableError) as exc_info:
        fetch_transcript("dQw4w9WgXcQ")

    assert "Could not retrieve transcript for video ID 'dQw4w9WgXcQ'" in str(
        exc_info.value
    )
    mock_youtube_api_get_transcript.assert_called_once_with("dQw4w9WgXcQ")
