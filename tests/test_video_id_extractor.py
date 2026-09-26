"""Unit tests for youtube_summary.extractor using pytest."""
import pytest
from ai_video_to_knowledge.exceptions import ExtractorError
from ai_video_to_knowledge.video_id_extractor import extract_video_id

# ---------------------------------------------------------------------------
# 1. Valid URL Tests (Parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "url, expected_id",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s", "dQw4w9WgXcQ"),
        ("  https://youtu.be/dQw4w9WgXcQ  ", "dQw4w9WgXcQ"),
    ],
)
def test_valid_urls_parametrized(url: str, expected_id: str) -> None:
    """Ensures each valid YouTube URL returns the correct 11-character video ID."""
    assert extract_video_id(url) == expected_id


# ---------------------------------------------------------------------------
# 2. Invalid URL Tests (Parametrized Exception Handling)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "invalid_url, expected_message",
    [
        ("invalid_url_string", "Could not extract YouTube Video ID from invalid URL: 'invalid_url_string'"),
        ("", "URL string cannot be empty or whitespace only."),
        (" ", "URL string cannot be empty or whitespace only."),
        ("https://vimeo.com/123456789", "Could not extract YouTube Video ID from invalid URL: 'https://vimeo.com/123456789'"),
        ("https://youtube.com/watch?v=shortID", "Could not extract YouTube Video ID from invalid URL: 'https://youtube.com/watch?v=shortID'"),
    ],
)
def test_invalid_urls_raise_extractor_error(invalid_url: str, expected_message: str) -> None:
    """Ensures all invalid URLs raise ExtractorError with descriptive error messages."""
    with pytest.raises(ExtractorError) as exc_info:
        extract_video_id(invalid_url)
    assert str(exc_info.value) == expected_message


# ---------------------------------------------------------------------------
# 3. Invalid Type Tests (Parametrized Type Validation)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("invalid_type", [12345, None, ["https://youtu.be/dQw4w9WgXcQ"]])
def test_invalid_types_raise_type_error(invalid_type) -> None:
    """Ensures non-string inputs raise TypeError with expected message."""
    with pytest.raises(TypeError) as exc_info:
        extract_video_id(invalid_type)
    assert "Expected string for URL" in str(exc_info.value)
