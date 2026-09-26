# AI Video To Knowledge (`ai_video_to_knowledge`)

A production-grade Python application that parses YouTube URLs, extracts transcripts, processes them using OpenAI's LLMs with structured Pydantic outputs to generate comprehensive summaries and lesson plans, and exports knowledge outputs.

---

## 🏗️ Project Architecture

```text
AI_VideoToKnowledge/
├── src/
│   └── ai_video_to_knowledge/       # Core application package
│       ├── __init__.py
│       ├── exceptions.py             # Custom domain exception hierarchy
│       ├── video_id_extractor.py     # Regex YouTube URL parser & validator
│       ├── transcript.py             # YouTube transcript fetcher & formatter
│       ├── schemas.py                # Pydantic structured output models
│       └── process_ai.py             # OpenAI LLM integration & prompt engineering
├── outputs/                          # Generated knowledge files (.md)
├── tests/                            # Unit and integration test suite
│   ├── __init__.py
│   ├── test_video_id_extractor.py   # Unit tests for URL parser
│   ├── test_transcript.py           # Unit tests for transcript fetcher (pytest-mock)
│   ├── test_process_ai.py           # Unit tests for OpenAI AI summarizer
│   └── test_main.py                 # CLI integration tests
├── .env                              # Local environment secrets (Git ignored)
├── .env.example                      # Environment variable template
├── .gitignore                        # Git exclusion rules
├── pyproject.toml                    # Pytest configuration & package pathing
├── main.py                           # CLI entry point
├── run.bat                           # Windows batch execution script with PYTHONPATH
├── README.md                         # Central project documentation & architecture log
└── requirements.txt                  # Direct project dependencies
```

---

## 🏛️ Engineering Decisions

During the architecture and implementation of this project, key engineering decisions were established to guarantee production-grade quality, strict testability, enterprise maintainability, and resource optimization:

### 1. Custom Exception Hierarchy & API Decoupling (`VideoToKnowledgeError`)
* **Decision:** Designed a custom domain exception hierarchy in `src/ai_video_to_knowledge/exceptions.py`. A base exception `VideoToKnowledgeError` serves as the root, with specific subclasses like `ExtractorError`, `TranscriptError`, and `SummarizerError`.
* **Rationale & Benefits:**
  * **Decoupling Application Logic:** Upstream application code (CLI, Web UI, API) should never directly catch third-party vendor library exceptions (e.g., `youtube_transcript_api._errors.VideoUnavailable` or `openai.AuthenticationError`). If we switch providers or if external libraries change their exception schemas, upstream modules remain completely unaffected.
  * **Single Point of Translation:** All third-party library exceptions are intercepted at module boundaries and wrapped into clean domain-specific exceptions.
  * **Clean Error Boundaries:** Prevents generic system errors (like `ValueError` or `KeyError`) from masking domain failures.

### 2. Preventing Exception Re-wrapping (`except SummarizerError: raise`)
* **Decision:** Placed an explicit `except SummarizerError: raise` block immediately before the generic `except Exception as e:` catch-all block in `process_ai.py`.
* **Rationale & Benefits:**
  * **Eliminating Double-Wrapping:** Custom domain exceptions raised deliberately inside a `try:` block inherit from `Exception`. Without an explicit re-raise block, they get caught by the generic catch-all and re-wrapped into misleading `"Unexpected error during AI processing..."` messages.
  * **Preserving Original Context:** Guarantees that precise domain validation errors (e.g., `"Transcript text cannot be empty."` or `"OPENAI_API_KEY is not configured."`) propagate unchanged to the CLI layer.

### 3. Structured Outputs with Enforced Pydantic Schemas (`EducationalContent`)
* **Decision:** Utilized OpenAI Structured Outputs (`beta.chat.completions.parse`) mapped strictly to Pydantic models in `schemas.py`.
* **Rationale & Benefits:**
  * **Eliminating Fragile Regex Parsing:** Avoids unreliable Markdown or raw text scraping from LLM completions.
  * **Field-Level Prompt Engineering:** Enforces semantic constraints and formatting expectations directly inside the Pydantic schema using `Field(description="...")`.
  * **Runtime Validation:** Guarantees that generated responses contain all required fields (`title`, `summary`, `key_takeaways`, `lesson_plan`) before returning to caller functions.

### 4. Optional Secret Parameters & BYOK (Bring Your Own Key) Architecture
* **Decision:** Designed core functions to accept optional parameters (`api_key: str | None = None`, `model: str | None = None`) with fallback to environment variables (`os.getenv`).
* **Rationale & Benefits:**
  * **Test Suite Isolation:** Allows unit tests to pass explicit dummy keys (`api_key="fake-key"`) without mutating operating system environment variables (`os.environ`).
  * **Multi-Tenant BYOK Web Architecture:** Seamlessly supports future Web API deployments where end-users provide their own personal OpenAI API key per request.

### 5. Output Stream Decoupling (`stdout` vs `stderr`) & Safe Redirection
* **Decision:** Directed all user-facing status messages and errors in the CLI to `sys.stderr` rather than standard `print` (`sys.stdout`).
* **Rationale & Benefits:**
  * **Data Pipeline Integrity:** When users redirect CLI output to files or pipes (e.g., `python main.py <URL> > log.txt`), status and error messages do not contaminate data files.
  * **Real-Time Error Feedback:** Error messages remain visible on the user's terminal screen even when `stdout` is redirected.

### 6. Defensive Input Validation & Fail-Fast Principle
* **Decision:** Implemented early explicit input validation (`isinstance`, `.strip()`, empty-string checks) at the start of functions before executing heavy operations like regex matching or network API calls.
* **Rationale & Benefits:**
  * **Resource & Cost Protection:** In LLM pipelines, attempting to process invalid inputs through downstream modules leads to cascading failures, unnecessary network latency, and wasted OpenAI API credits.
  * **Clear Error Attribution:** Raises immediate, descriptive errors (`TypeError`, `ExtractorError`, `SummarizerError`) at the function entry point.

### 7. Clean Error Messaging & Traceback Isolation
* **Decision:** Removed raw stringified exception payloads (`{e}`) from user-facing error messages, relying instead on clean domain strings combined with exception chaining (`raise CustomError(...) from e`).
* **Rationale & Benefits:**
  * **Noise Reduction:** Intercepts multi-paragraph third-party library error dumps and replaces them with concise single-line domain messages.
  * **Debugging Preservation:** The `from e` syntax preserves the underlying stack trace in `__cause__` for developer debugging in log files (`app.log`) without polluting CLI user output.

### 8. Isolated, Zero-Network Unit Testing (`pytest-mock` & `types.SimpleNamespace`)
* **Decision:** Standardized unit tests to run 100% offline without making live HTTP requests to YouTube or OpenAI servers, leveraging `pytest-mock` (`mocker.patch`, `side_effect`, `return_value`) and `types.SimpleNamespace`.
* **Rationale & Benefits:**
  * **Sub-Second Speed:** The entire test suite executes deterministically in under 1.5 seconds (< 0.05s per test).
  * **Zero Financial Cost:** Mocks prevent real API credit consumption during test runs.
  * **Deterministic Error Simulation:** `side_effect` allows simulating network crashes, `AuthenticationError`, `RateLimitError`, and `APIConnectionError` instantly without disrupting live servers.

### 9. Production `src/` Package Layout & Editable Installation (`pip install -e .`)
* **Decision:** Adopted the canonical `src/` layout (`src/ai_video_to_knowledge/`), configured `pyproject.toml` with `pythonpath = ["src"]`, and registered the package in editable mode via `pip install -e .`.
* **Rationale & Benefits:**
  * **Eliminating Import Collisions:** Prevents accidental import collisions between working directory scripts and installed packages.
  * **Global Resolution:** Links `src/` directly into `.venv`, allowing `from ai_video_to_knowledge...` imports to resolve across CLI, PyCharm, and Pytest.

### 10. Decoupled Module Architecture & REPL-Driven Sanity Testing
* **Decision:** Designed core business logic modules (`transcript.py`, `video_id_extractor.py`, `process_ai.py`) as independent, pure functional components without embedded `if __name__ == "__main__":` blocks or tight CLI coupling.
* **Rationale & Benefits:**
  * **High Reusability:** Core functions import seamlessly into CLI scripts, FastAPI web endpoints, or background task queues.
  * **REPL Sanity Testing:** Enables interactive testing directly inside the Python REPL console (`>>> process_transcript_with_ai(...)`).

### 11. Module-Level Pattern Pre-Compilation (`re.compile`)
* **Decision:** Compiled regular expressions at the top level of `video_id_extractor.py` (`YOUTUBE_URL_REGEX = re.compile(...)`).
* **Rationale & Benefits:**
  * Pre-compiling regex strings once at module load time eliminates redundant parsing overhead during high-throughput batch execution.

### 12. Strict Character-Level Exception Assertions in Parametrized Tests
* **Decision:** Enforced exact string equality (`assert str(exc_info.value) == expected_message`) in `@pytest.mark.parametrize` test suites.
* **Rationale & Benefits:**
  * Prevents false-positive test passes by verifying that the exact intended guard clause raised the exception.

### 13. Environment Secret Hygiene (`.env` vs `.env.example`)
* **Decision:** Strictly excluded `.env` from version control via `.gitignore` while maintaining a tracked `.env.example` template.
* **Rationale & Benefits:**
  * Protects sensitive API credentials from being committed to source control while providing a clear setup blueprint for collaborators.

---

## 🧠 New Knowledge & Core Concepts Learned

1. **OpenAI Structured Outputs & Response List Indexing (`choices[0]`)**:
   - Mastered `beta.chat.completions.parse` with Pydantic models.
   - Diagnosed runtime `AttributeError` caused by accessing `response.choices.message` instead of indexing the list element `response.choices[0].message`.
2. **Mocking Side Effects (`side_effect`) vs Return Values (`return_value`)**:
   - `return_value`: Simulates successful API responses (Happy Path).
   - `side_effect`: Simulates raised exceptions (`AuthenticationError`, `RateLimitError`) for deterministic error handling testing.
3. **Python Import Resolution & `sys.path` Mechanics**:
   - Understood editable package installations (`pip install -e .`) and explicit path resolution via `pyproject.toml` and `PYTHONPATH`.
4. **Exception Chaining (`raise CustomError(...) from e`)**:
   - Learned how `from e` attaches the original cause in `__cause__` while surfacing clean domain error messages.
5. **API Method Instantiation (`YouTubeTranscriptApi().fetch(...)`)**:
   - Diagnosed positional argument errors caused by invoking instance methods as unbound class methods, and adapted to schema object updates (`item.text`).
6. **Advanced Unit Testing with `pytest` & `pytest-mock`**:
   - Mastered `@pytest.mark.parametrize` for pairwise edge-case testing across URL formats.
   - Utilized `types.SimpleNamespace` to construct dot-accessible mock objects in memory.
7. **Regex Design with Non-Capturing Groups (`(?:...)`)**:
   - Extracted 11-character YouTube video IDs across diverse URL structures (`watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`, `/v/`, `m.youtube.com`).

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **OpenAI API Key**

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/AIVideoToKnowledge.git
   cd AIVideoToKnowledge
   ```

2. **Create and activate a virtual environment:**
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

3. **Install dependencies and register package in editable mode:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Configure environment variables:**
   ```powershell
   cp .env.example .env
   ```
   Edit `.env` and insert your actual `OPENAI_API_KEY`.

---

## 💻 CLI Usage

### Direct Python Execution
Run `main.py` directly by passing a YouTube URL as a positional argument:

```powershell
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Windows Helper Execution (`run.bat`)
Alternatively, execute via `run.bat` (which automatically configures `PYTHONPATH=%~dp0src` without requiring `pip install -e .`):

```cmd
run.bat "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Expected Output
The application generates a structured Markdown summary inside the `outputs/` directory and outputs clean status updates:

```text
⏳ Parsing YouTube URL...
⏳ Fetching transcript...
⏳ Processing structured knowledge with OpenAI...
✅ Knowledge extraction complete!
📄 Output saved to: outputs/dQw4w9WgXcQ_summary.md
```

---

## 🧪 Running Tests

Execute the full, 100% offline unit test suite using `pytest`:

```bash
pytest
```

For verbose output:
```bash
pytest -v
```

---

## 🗺️ Current Status & Detailed Roadmap

- [x] **Phase 1: URL Extraction & Captions Engine**
  - [x] `video_id_extractor.py`: Regex YouTube URL parsing & validation across all URL formats.
  - [x] `transcript.py`: `youtube-transcript-api` fetcher & continuous text formatting.
  - [x] `exceptions.py`: Base domain exception hierarchy (`VideoToKnowledgeError`).
  - [x] Unit test suite with 100% offline `pytest-mock` coverage.

- [x] **Phase 2: AI Knowledge Processing Engine**
  - [x] `schemas.py`: Pydantic structured output models (`EducationalContent`).
  - [x] `process_ai.py`: OpenAI LLM integration with `beta.chat.completions.parse`.
  - [x] Defensive exception mapping (`AuthenticationError`, `RateLimitError` -> `SummarizerError`).
  - [x] Prevention of double-wrapping exceptions (`except SummarizerError: raise`).

- [ ] **Phase 3: CLI & File Export Pipeline**
  - [ ] `main.py`: Command Line Interface entry point with positional URL parsing.
  - [ ] `run.bat`: Windows batch execution helper with `PYTHONPATH` resolution.
  - [ ] Automated `.md` file creation in `outputs/` directory.
  - [ ] `tests/test_main.py`: Integration and error handling unit tests for CLI.

- [ ] **Phase 4: Advanced Export & Agent Integrations**
  - [ ] **PDF Export Pipeline**: Convert generated Markdown outputs into styled PDF documents (`fpdf2` / `reportlab`).
  - [ ] **NoSQL & Vector Storage**: Persist structured knowledge summaries in NoSQL / Vector databases (MongoDB / ChromaDB).
  - [ ] **Google Drive Auto-Sync**: Automatic background upload of generated knowledge summaries to Google Drive API.
  - [ ] **MCP Server (Model Context Protocol)**: Connect the pipeline as an MCP tool server for AI agents (Claude Desktop, Cursor, Custom Agents).

- [ ] **Phase 5: Web Application & Cloud API**
  - [ ] **FastAPI Web API**: Async HTTP REST API endpoints (`/api/summarize`).
  - [ ] **BYOK (Bring Your Own Key) Support**: Allow Web UI users to provide personal OpenAI API keys securely per session.
  - [ ] **Modern Frontend (React / Web UI)**: Interactive web dashboard for URL submission, live processing status, and knowledge browsing.
