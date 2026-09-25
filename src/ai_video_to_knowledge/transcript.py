"""Transcript fetcher and formatter module."""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable)
from ai_video_to_knowledge.exceptions import TranscriptNotAvailableError


def _format_transcript(raw_transcript: list[dict]) -> str:
    """Combines raw transcript dictionary items into a single continuous string."""
    return " ".join(item.text.strip() for item in raw_transcript if item.text).strip()


def fetch_transcript(video_id: str) -> str:
    """Fetches and formats a YouTube transcript for a given 11-character video ID.
    Args:
        video_id: The 11-character YouTube video ID.
    Returns:
        A cleaned, continuous transcript string ready for LLM consumption.
    Raises:
        TranscriptNotAvailableError: If captions are disabled, unavailable, or missing.
    """
    try:
        api = YouTubeTranscriptApi()
        raw_transcript = api.fetch(video_id)
        return _format_transcript(raw_transcript)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        raise TranscriptNotAvailableError(
            f"Could not retrieve transcript for video ID '{video_id}'"
        ) from e
