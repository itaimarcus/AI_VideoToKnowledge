import os
from pathlib import Path
import pytest

from ai_video_to_knowledge.exceptions import VideoToKnowledgeError
from ai_video_to_knowledge.schemas import EducationalContent
from main import (
    check_existing_file,
    main,
    resolve_api_key,
    resolve_output_dir,
)


# =============================================================================
# 1. Configuration & Resolution Rules Tests
# =============================================================================

def test_resolve_output_dir_precedence(monkeypatch):
    """Ensures CLI flag overrides env var, and env var overrides default fallback."""
    # CLI Flag Precedence
    assert resolve_output_dir("custom/cli/path") == Path("custom/cli/path")

    # Env Var Precedence
    monkeypatch.setenv("OUTPUT_DIR", "C:/Env/Path")
    assert resolve_output_dir(None) == Path("C:/Env/Path")

    # Default Fallback
    monkeypatch.delenv("OUTPUT_DIR", raising=False)
    resolved_default = resolve_output_dir(None)
    assert resolved_default == Path.home() / "Desktop" / "knowledge" or resolved_default.name == "knowledge"


def test_resolve_api_key_precedence_and_missing(monkeypatch):
    """Ensures CLI flag > Env Var > VideoToKnowledgeError raised when missing."""
    # CLI Override
    assert resolve_api_key("sk-cli-key") == "sk-cli-key"

    # Env Var Fallback
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    assert resolve_api_key(None) == "sk-env-key"

    # Missing Key Error
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(VideoToKnowledgeError, match="OpenAI API Key missing"):
        resolve_api_key(None)


# =============================================================================
# 2. Duplicate Detection Tests (check_existing_file)
# =============================================================================

def test_check_existing_file_detects_substring_and_missing(tmp_path):
    """Ensures check_existing_file detects video_id substrings and handles non-existent paths."""
    video_id = "dQw4w9WgXcQ"
    output_dir = tmp_path / "knowledge"
    output_dir.mkdir()

    # Case A: Missing file
    assert check_existing_file(output_dir, video_id) is None

    # Case B: File exists with video_id substring
    existing_file = output_dir / f"Custom_Title_{video_id}_notes.md"
    existing_file.write_text("content", encoding="utf-8")
    assert check_existing_file(output_dir, video_id) == existing_file

    # Case C: Directory does not exist
    assert check_existing_file(tmp_path / "non_existent", video_id) is None


# =============================================================================
# 3. Pipeline Integration Tests (main)
# =============================================================================

def test_main_skips_processing_when_file_exists(mocker, tmp_path):
    """Ensures main skips API calls and returns 0 if output file already exists."""
    video_id = "dQw4w9WgXcQ"
    mocker.patch("main.extract_video_id", return_value=video_id)

    # Create dummy existing file
    existing = tmp_path / f"renamed_{video_id}_summary.md"
    existing.write_text("content", encoding="utf-8")

    mock_fetch = mocker.patch("main.fetch_transcript")

    exit_code = main([
        f"https://www.youtube.com/watch?v={video_id}",
        "--output-dir", str(tmp_path)
    ])

    assert exit_code == 0
    mock_fetch.assert_not_called()


def test_main_pipeline_success(mocker, tmp_path):
    """Ensures full end-to-end pipeline completes with exit code 0."""
    video_id = "dQw4w9WgXcQ"
    mocker.patch("main.extract_video_id", return_value=video_id)
    mocker.patch("main.fetch_transcript", return_value="Raw transcript")

    mock_edu = mocker.MagicMock(spec=EducationalContent)
    mock_edu.to_markdown.return_value = "# Educational Content"
    mocker.patch("main.process_transcript_with_ai", return_value=mock_edu)

    exit_code = main([
        f"https://www.youtube.com/watch?v={video_id}",
        "--output-dir", str(tmp_path),
        "--api-key", "sk-test"
    ])

    assert exit_code == 0
    assert (tmp_path / f"{video_id}_knowledge.md").exists()


def test_main_handles_domain_errors(mocker):
    """Ensures caught VideoToKnowledgeError returns exit code 1."""
    mocker.patch("main.extract_video_id", side_effect=VideoToKnowledgeError("Invalid URL"))
    assert main(["invalid_url", "--api-key", "sk-test"]) == 1
