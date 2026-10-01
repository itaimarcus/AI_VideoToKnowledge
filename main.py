import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from ai_video_to_knowledge.exceptions import VideoToKnowledgeError
from ai_video_to_knowledge.process_ai import process_transcript_with_ai
from ai_video_to_knowledge.schemas import EducationalContent
from ai_video_to_knowledge.transcript import fetch_transcript
from ai_video_to_knowledge.video_id_extractor import extract_video_id

# Load environment variables from local .env file
load_dotenv()


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert YouTube video transcript into structured educational Markdown notes."
    )
    parser.add_argument(
        "url",
        type=str,
        help="YouTube video URL (e.g., https://www.youtube.com/watch?v=...)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Target directory for saving Markdown files (overrides OUTPUT_DIR env var and Desktop default)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key (overrides OPENAI_API_KEY environment variable)",
    )
    return parser.parse_args(args)


def get_desktop_path() -> Path:
    """Finds the real active Desktop folder, accounting for Windows OneDrive redirection and Hebrew/localized folder names."""
    home = Path.home()

    # 1. Check OneDrive environment variables
    onedrive_env = os.getenv("OneDrive") or os.getenv("OneDriveConsumer") or os.getenv("OneDriveCommercial")
    if onedrive_env:
        base_path = Path(onedrive_env)
        for desktop_name in ["שולחן העבודה", "Desktop"]:
            candidate = base_path / desktop_name
            if candidate.exists():
                return candidate

    # 2. Check standard home directory candidates for Hebrew & English names under OneDrive and Home
    for parent in [home / "OneDrive", home]:
        for desktop_name in ["שולחן העבודה", "Desktop"]:
            candidate = parent / desktop_name
            if candidate.exists():
                return candidate

    # 3. Fallback
    return home / "Desktop"


def resolve_output_dir(cli_output_dir: str | None) -> Path:
    """
    Resolves output directory with precedence:
    1. CLI Argument (--output-dir)
    2. Environment Variable (OUTPUT_DIR)
    3. Universal Active Desktop/knowledge Fallback
    """
    if cli_output_dir:
        return Path(cli_output_dir)

    env_dir = os.getenv("OUTPUT_DIR")
    if env_dir:
        return Path(env_dir)

    return get_desktop_path() / "knowledge"


def resolve_api_key(cli_api_key: str | None) -> str:
    """Resolves OpenAI API key with precedence: CLI argument > OPENAI_API_KEY env var."""
    if cli_api_key:
        return cli_api_key
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    raise VideoToKnowledgeError(
        "OpenAI API Key missing. Provide --api-key or set OPENAI_API_KEY env var."
    )


def check_existing_file(output_dir: Path, video_id: str) -> Path | None:
    """Checks if any file in output_dir contains video_id as a substring in its filename."""
    if not output_dir.exists():
        return None
    for file_path in output_dir.iterdir():
        if file_path.is_file() and video_id in file_path.name:
            return file_path
    return None


def format_to_markdown(
    content: EducationalContent,
    url: str,
    video_id: str,
) -> str:
    """Prepends CLI contextual metadata header to EducationalContent Markdown representation."""
    header = [
        "# Educational Knowledge Notes",
        f"**Source URL:** {url}",
        f"**Video ID:** `{video_id}`",
        "",
    ]
    return "\n".join(header) + content.to_markdown()


def save_markdown_to_disk(content: str, video_id: str, output_dir: Path) -> Path:
    """Ensures target directory exists and saves Markdown file in UTF-8 encoding."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target_file = output_dir / f"{video_id}_knowledge.md"
    target_file.write_text(content, encoding="utf-8")
    return target_file


def main(cli_args: list[str] | None = None) -> int:
    """Main execution pipeline."""
    try:
        args = parse_args(cli_args)

        # 0. Resolve Output Directory
        output_dir = resolve_output_dir(args.output_dir)

        # 1. Extract Video ID
        print(f"[*] Extracting Video ID from URL: {args.url}...", file=sys.stderr)
        video_id = extract_video_id(args.url)

        # 2. Early Guard: Check if output file already exists in target output_dir
        print(f"[*] Checking for existing output file in: {output_dir}...", file=sys.stderr)
        existing_file = check_existing_file(output_dir, video_id)
        if existing_file:
            print(
                f"[!] Knowledge document already exists: {existing_file}\n"
                f"[!] Skipping API processing. Delete or rename file to regenerate.",
                file=sys.stderr,
            )
            return 0

        # 3. Resolve API Key & fetch transcript
        print("[*] Resolving OpenAI API Key...", file=sys.stderr)
        api_key = resolve_api_key(args.api_key)

        print(f"[*] Fetching transcript for Video ID: {video_id}...", file=sys.stderr)
        transcript = fetch_transcript(video_id)

        # 4. Process with OpenAI
        print(
            "[*] Processing transcript and generating Educational Content with OpenAI...",
            file=sys.stderr,
        )
        educational_content = process_transcript_with_ai(transcript, api_key=api_key)

        # 5. Format & Save
        print("[*] Formatting Educational Content to Markdown...", file=sys.stderr)
        formatted_md = format_to_markdown(educational_content, args.url, video_id)
        saved_file = save_markdown_to_disk(formatted_md, video_id, output_dir)

        print(f"[+] Knowledge saved successfully: {saved_file}", file=sys.stderr)
        return 0

    except VideoToKnowledgeError as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
