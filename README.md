### AI Video To Knowledge (ai_video_to_knowledge)
A production-grade Python application that parses YouTube URLs, extracts transcripts, processes them using OpenAI's LLMs with structured Pydantic outputs to generate comprehensive summaries and lesson plans, and exports knowledge outputs.

--------------------------------------------------------------------------------

##### 🏗️ Project Architecture
```text
AI_VideoToKnowledge/
├── src/
│   └── ai_video_to_knowledge/       # Core application package
│       ├── __init__.py
│       ├── exceptions.py             # Custom domain exception hierarchy
│       ├── video_id_extractor.py     # Regex YouTube URL parser & validator
│       ├── transcript.py             # YouTube transcript fetcher & formatter
│       ├── schemas.py                # Pydantic structured output models & to_markdown()
│       └── process_ai.py             # OpenAI LLM integration & prompt engineering
├── tests/                            # Unit and integration test suite
│   ├── __init__.py
│   ├── test_video_id_extractor.py   # Unit tests for URL parser
│   ├── test_transcript.py           # Unit tests for transcript fetcher (pytest-mock)
│   ├── test_process_ai.py           # Unit tests for OpenAI AI summarizer
│   └── test_main.py                 # Integration and CLI tests (pytest-mock)
├── .env                              # Local environment secrets (Git ignored)
├── .env.example                      # Environment variable template
├── .gitignore                        # Git exclusion rules
├── pyproject.toml                    # Pyproject package configuration & CLI entrypoint
├── main.py                           # Production CLI entry point & path resolver
├── README.md                         # Central project documentation & architecture log
└── requirements.txt                  # Direct project dependencies
```

--------------------------------------------------------------------------------

##### 🏛️ Engineering Decisions
During the architecture and implementation of this project, key engineering decisions were established to guarantee production-grade quality, strict testability, enterprise maintainability, and resource optimization:

###### 1. Custom Exception Hierarchy & API Decoupling (VideoToKnowledgeError)
*   **Decision:** Designed a custom domain exception hierarchy in `src/ai_video_to_knowledge/exceptions.py`. A base exception `VideoToKnowledgeError` serves as the root, with specific subclasses like `ExtractorError`, `TranscriptError`, and `SummarizerError`.
*   **Rationale & Benefits:**
    *   **Decoupling Application Logic:** Upstream application code (CLI, Web UI, API) should never directly catch third-party vendor library exceptions (e.g., `youtube_transcript_api._errors.VideoUnavailable` or `openai.AuthenticationError`).
    *   **Single Point of Translation:** All third-party library exceptions are intercepted at module boundaries and wrapped into clean domain-specific exceptions.
    *   **Clean Error Boundaries:** Prevents generic system errors (like `ValueError` or `KeyError`) from masking domain failures.

###### 2. Preventing Exception Re-wrapping (except SummarizerError: raise)
*   **Decision:** Placed an explicit `except SummarizerError: raise` block immediately before the generic `except Exception as e:` catch-all block in `process_ai.py`.
*   **Rationale & Benefits:**
    *   **Eliminating Double-Wrapping:** Custom domain exceptions raised deliberately inside a `try:` block inherit from `Exception`. Without an explicit re-raise block, they get caught by the generic catch-all and re-wrapped into misleading "Unexpected error..." messages.
    *   **Preserving Original Context:** Guarantees that precise domain validation errors propagate unchanged to the CLI layer.

###### 3. Structured Outputs & Encapsulated Formatting (EducationalContent)
*   **Decision:** Utilized OpenAI Structured Outputs (`beta.chat.completions.parse`) mapped strictly to Pydantic models in `schemas.py`, with an encapsulated `to_markdown()` instance method on `EducationalContent`.
*   **Rationale & Benefits:**
    *   **Eliminating Fragile Parsing:** Avoids unreliable Markdown or raw text scraping from LLM completions.
    *   **Domain Encapsulation:** The Pydantic model itself knows how to format its structured fields into a clean Markdown body, making it 100% reusable across CLI, Web APIs (FastAPI), and PDF generators.

###### 4. Optional Secret Parameters, .env & BYOK Architecture (12-Factor App Methodology)
*   **Decision:** Designed core functions and CLI entrypoints to accept optional parameters (`api_key: str | None = None`) with fallback to environment variables (`os.getenv`) and `.env` local configuration (`load_dotenv()`).
*   **Rationale & Benefits:**
    *   **12-Factor App Methodology:** Adheres strictly to 12-Factor App principles by separating configuration and secrets from code execution using `.env` files and environment variables.
    *   **Test Suite Isolation:** Allows unit tests to pass explicit dummy keys (`api_key="sk-test"`) or clean environment variables without mutating operating system environment variables.
    *   **Multi-Tenant BYOK Web Architecture:** Seamlessly supports future Web API deployments where end-users provide their own personal OpenAI API key per request.

###### 5. Output Stream Decoupling (stdout vs stderr) & Safe Redirection
*   **Decision:** Directed all user-facing status messages and errors in the CLI to `sys.stderr` rather than standard print (`sys.stdout`).
*   **Rationale & Benefits:**
    *   **Data Pipeline Integrity:** When users redirect CLI output to files or pipes (e.g., `yt-ai <URL> > output.txt`), status and error messages do not contaminate data files.
    *   **Real-Time Error Feedback:** Error messages remain visible on the user's terminal screen even when stdout is redirected.

###### 6. Design for Testability & Dependency Injection (parse_args(cli_args))
*   **Decision:** Implemented `parse_args(cli_args: list[str] | None = None)` in `main.py`. When `cli_args` is `None` (production execution), `argparse` automatically inspects `sys.argv`. In unit tests, explicit argument lists are injected directly.
*   **Rationale & Benefits:**
    *   **Isolated Testing:** Enables testing dozens of CLI flag combinations and syntax error states in pytest without mutating global `sys.argv` or spawning subprocesses.

###### 7. Early Guard & Cost Optimization (Duplicate Skip with Exit Code 0)
*   **Decision:** Placed an early existence check in `main.py` for the target output file before making any network calls to YouTube or OpenAI.
*   **Rationale & Benefits:**
    *   **Financial API Protection:** Immediately halts execution if the video was already processed, saving OpenAI API credit consumption.
    *   **Data Loss Prevention:** Prevents accidental overwriting of user-edited knowledge notes.
    *   **Batch Friendly:** Returns a clean Exit Code 0 with an informative stderr warning, allowing automated batch scripts to skip existing files without crashing.

###### 8. CLI Exit Code Contract & SystemExit Exception Hierarchy
*   **Decision:** Enforced a strict exit code contract in `main.py`: 0 for success/skip, 1 for caught domain errors (`VideoToKnowledgeError`), and 2 for CLI argument syntax errors (raised via `sys.exit(2)` in `argparse`).
*   **Rationale & Benefits:**
    *   **SystemExit Mechanics:** `sys.exit()` raises `SystemExit`, which inherits from `BaseException` (not `Exception`). This guarantees that generic `except Exception:` blocks do not catch CLI exit requests.
    *   **UI Decoupling:** Isolates process termination to the CLI layer (`main.py`), ensuring core domain modules in `src/` can be imported safely into Web applications without terminating web server workers.

###### 9. Enforcing spec=Class in Mocks & Eliminating "Mock Illusion"
*   **Decision:** Standardized mock creation using `mocker.MagicMock(spec=EducationalContent)` in `test_main.py`.
*   **Rationale & Benefits:**
    *   **Eliminating False Positives:** Default `MagicMock` dynamically accepts any non-existent method call, causing tests to pass even when calling methods that do not exist on the real class. Specifying `spec=Class` restricts the mock strictly to attributes defined on the target class, catching interface mismatches instantly during test runs.

###### 10. Cross-Platform UTF-8 File I/O (encoding="utf-8")
*   **Decision:** Mandated explicit `encoding="utf-8"` parameters across all `Path.read_text()` and `Path.write_text()` calls in application and test code.
*   **Rationale & Benefits:**
    *   **Windows Code Page Compatibility:** Prevents `UnicodeDecodeError` and character corruption when running on Windows operating systems that default to legacy code pages (e.g., CP1252 / Windows-1255).

###### 11. Defensive Input Validation & Fail-Fast Principle
*   **Decision:** Implemented early explicit input validation (`isinstance`, `.strip()`, empty-string checks) at the start of functions before executing heavy operations like regex matching or network API calls.
*   **Rationale & Benefits:**
    *   **Resource Protection:** Avoids cascading failures and unnecessary network latency by throwing immediate descriptive errors (`TypeError`, `ExtractorError`, `SummarizerError`).

###### 12. Isolated, Zero-Network Unit Testing (pytest-mock)
*   **Decision:** Standardized unit tests to run 100% offline without making live HTTP requests to YouTube or OpenAI servers, leveraging `pytest-mock` (`mocker.patch`, `side_effect`, `return_value`).
*   **Rationale & Benefits:**
    *   **Sub-Second Execution:** The entire test suite executes deterministically in under 1.5 seconds.
    *   **Zero Financial Cost:** Eliminates API credit consumption during testing.

###### 13. Production src/ Package Layout & Editable Installation (pip install -e .)
*   **Decision:** Adopted the canonical `src/` layout (`src/ai_video_to_knowledge/`), configured `pyproject.toml` with `pythonpath = ["src"]`, and registered the package in editable mode via `pip install -e .`.
*   **Rationale & Benefits:**
    *   **Import Resolution:** Links `src/` directly into `.venv`, allowing `from ai_video_to_knowledge...` imports to resolve consistently across CLI, IDEs, and Pytest.

###### 14. Universal Output Directory Resolution & Cross-Platform Fallback
*   **Decision:** Implemented `resolve_output_dir()` in `main.py` with a 3-tier precedence hierarchy: CLI Argument (`--output-dir`) > Environment Variable (`OUTPUT_DIR`) > Central Desktop Fallback (`Path.home() / "Desktop"`).
*   **Rationale & Benefits:**
    *   **Global CLI UX:** Eliminates fragmented output files when running the global `yt-ai` command from arbitrary system directories (e.g., `System32` or root drives).
    *   **Permission Resilience:** Automatically routes file saving to the user's Desktop directory via `Path.home()`, preventing `PermissionError [WinError 5]` on protected system folders.
    *   **Zero-Configuration Convenience:** Out-of-the-box, every generated Markdown note lands safely on the user's Desktop regardless of OS or execution folder.

--------------------------------------------------------------------------------

##### 🧠 Core Concepts Learned
1.  **OpenAI Structured Outputs (beta.chat.completions.parse)**:
    *  Parsed responses mapped directly to Pydantic models.
    *  Correctly accessed response choice via list indexing: `response.choices[0].message.parsed`.
2.  **Design for Testability & Dependency Injection**:
    *  Decoupled CLI entry points by passing optional `cli_args` lists to allow unit testing without `sys.argv` mutation.
3.  **Mocking Precision (spec & side_effect)**:
    *  `spec=Class`: Enforces strict attribute verification on mocks to prevent false-passing tests.
    *  `side_effect`: Simulates raised exceptions (`AuthenticationError`, `RateLimitError`) for deterministic error testing.
4.  **Python Exception Hierarchy & SystemExit**:
    *  Understood that `SystemExit` inherits from `BaseException` rather than `Exception`, allowing clean CLI process exit handling.
5.  **Cross-Platform File I/O Hygiene**:
    *  Enforced explicit UTF-8 encoding to prevent Windows CP1252/Windows-1255 character encoding crashes.
6.  **12-Factor App Methodology & Config Separation**:
    *  Managed secrets via `.env` files and environment variables (`load_dotenv()`), isolating runtime configuration from code and preserving hermetic test isolation.
7.  **Global Executable Entrypoints (`project.scripts`)**:
    *  Configured `pyproject.toml` entry points (`yt-ai = "main:main"`) to generate native system executables on installation.

--------------------------------------------------------------------------------

##### 🚀 Getting Started
###### Prerequisites
*   **Python 3.10+**
*   **OpenAI API Key**

###### Setup Instructions
1.  **Clone the repository:**
```bash
git clone https://github.com/<your-username>/AIVideoToKnowledge.git
cd AIVideoToKnowledge
```

2.  **Create and activate a virtual environment:**
    *Windows (PowerShell):*
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
    *macOS / Linux:*
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3.  **Install dependencies and register package as a global CLI tool:**
```bash
pip install -r requirements.txt
pip install -e .
```

4.  **Configure environment variables:**
```powershell
cp .env.example .env
```
Edit `.env` and insert your actual `OPENAI_API_KEY`. You may optionally specify `OUTPUT_DIR` if you want to override the default Desktop path.

--------------------------------------------------------------------------------

##### 💻 CLI Usage

###### Global Executable Execution (`yt-ai`)
Once installed, run `yt-ai` from **any directory** in your terminal:
```powershell
yt-ai "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

###### Direct Python Execution
Alternatively, you can run `main.py` directly:
```powershell
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

###### Optional Arguments & Flags
*   `--output-dir`: Specify a custom output directory (overrides `OUTPUT_DIR` in `.env` and Desktop default).
*   `--api-key`: Pass an explicit OpenAI API key (overrides `OPENAI_API_KEY` in `.env`).

```powershell
yt-ai "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output-dir "C:\MyNotes" --api-key "sk-custom-key"
```

###### Expected Output
The application generates a structured Markdown file (by default on your Desktop) and outputs clean status logs:
```text
[*] Extracting Video ID from URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ...
[*] Checking for existing output file...
[*] Resolving OpenAI API Key...
[*] Fetching transcript for Video ID: dQw4w9WgXcQ...
[*] Processing transcript and generating Educational Content with OpenAI...
[*] Formatting Educational Content to Markdown...
[+] Knowledge saved successfully: C:\Users\itaim\Desktop\dQw4w9WgXcQ_knowledge.md
```

--------------------------------------------------------------------------------

##### 🧪 Running Tests
Execute the full, 100% offline unit test suite using `pytest`:
```bash
pytest
```
For verbose output:
```bash
pytest -v
```

--------------------------------------------------------------------------------

##### 🗺️ Current Status & Detailed Roadmap
*  [x]  **Phase 1: URL Extraction & Captions Engine**
    *  [x] `video_id_extractor.py`: Regex YouTube URL parsing & validation across all URL formats.
    *  [x] `transcript.py`: `youtube-transcript-api` fetcher & continuous text formatting.
    *  [x] `exceptions.py`: Base domain exception hierarchy (`VideoToKnowledgeError`).
    *  [x] Unit test suite with 100% offline `pytest-mock` coverage.
*  [x]  **Phase 2: AI Knowledge Processing Engine**
    *  [x] `schemas.py`: Pydantic structured output models (`EducationalContent`) with encapsulated `to_markdown()`.
    *  [x] `process_ai.py`: OpenAI LLM integration with `beta.chat.completions.parse`.
    *  [x] Defensive exception mapping (`AuthenticationError`, `RateLimitError` -> `SummarizerError`).
    *  [x] Prevention of double-wrapping exceptions (`except SummarizerError: raise`).
*  [x]  **Phase 3: Production CLI & File Export Pipeline**
    *  [x] `main.py`: Command Line Interface entry point with positional URL parsing and BYOK.
    *  [x] Global `yt-ai` executable registration in `pyproject.toml`.
    *  [x] Early Guard: Duplicate file detection & cost protection with Exit Code 0.
    *  [x] Universal path resolver (`resolve_output_dir`) targeting Desktop by default.
    *  [x] `tests/test_main.py`: Integration and CLI test suite using `pytest-mock` and `spec=EducationalContent`.
*  [ ]  **Phase 4: Advanced Export & Agent Integrations**
    *  [ ]  **PDF Export Pipeline**: Convert generated Markdown outputs into styled PDF documents (`fpdf2` / `reportlab`).
    *  [ ]  **Rich CLI UX**: Terminal progress bars and spinners using `rich`.
    *  [ ]  **Batch Processing**: Process text files containing multiple YouTube URLs (`--file urls.txt`).
    *  [ ]  **MCP Server (Model Context Protocol)**: Connect pipeline as an MCP tool server for AI agents.
*  [ ]  **Phase 5: Web Application & Cloud API**
    *  [ ]  **FastAPI Web API**: Async HTTP REST API endpoints (`/api/summarize`).
    *  [ ]  **BYOK Support**: Allow Web UI users to provide personal OpenAI API keys securely per session.
    *  [ ]  **Modern Frontend (React / Web UI)**: Interactive web dashboard for URL submission and knowledge browsing.
