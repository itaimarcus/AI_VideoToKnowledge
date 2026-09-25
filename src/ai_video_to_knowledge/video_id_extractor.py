"""YouTube Video ID Extractor module."""
import re
from ai_video_to_knowledge.exceptions import ExtractorError

YOUTUBE_URL_REGEX = re.compile(
    r'(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/|shorts/)|youtu\.be/)([\w-]{11})'
)

def extract_video_id(url: str) -> str:
    """Extracts YouTube 11-character video ID from a URL.
    Args:
        url: The YouTube URL string to parse.
    Returns:
        The 11-character YouTube video ID.
    Raises:
        TypeError: If input is not a string.
        ExtractorError: If input string is empty or contains an invalid YouTube URL.
    """
    if not isinstance(url, str):
        raise TypeError(f"Expected string for URL, got {type(url).__name__}")
        
    cleaned_url = url.strip()
    if not cleaned_url:
        raise ExtractorError("URL string cannot be empty or whitespace only.")

    match = YOUTUBE_URL_REGEX.search(cleaned_url)
    if not match:
        raise ExtractorError(f"Could not extract YouTube Video ID from invalid URL: '{url}'")
        
    return match.group(1)
