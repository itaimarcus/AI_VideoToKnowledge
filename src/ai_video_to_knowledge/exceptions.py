"""Custom domain exceptions for ai_video_to_knowledge."""

class VideoToKnowledgeError(Exception):
    """Base exception for all errors in the ai_video_to_knowledge application."""
    pass


class ExtractorError(VideoToKnowledgeError):
    """Raised when a YouTube URL cannot be parsed or is invalid."""
    pass


class TranscriptNotAvailableError(VideoToKnowledgeError):
    """Raised when a transcript cannot be retrieved for a video."""
    pass
