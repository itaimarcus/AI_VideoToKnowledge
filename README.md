# AI Video To Knowledge (`ai_video_to_knowledge`)

A production-grade Python application that parses YouTube URLs, extracts transcripts, processes them using OpenAI's LLMs to generate structured summaries and lesson plans, and exports knowledge outputs.

---

## Project Architecture

```text
AI_VideoToKnowledge/
├── src/
│   └── ai_video_to_knowledge/       # Core application package
│       ├── __init__.py
│       ├── exceptions.py             # Custom domain exception hierarchy
│       ├── video_id_extractor.py     # Regex YouTube URL parser & validator
│       └── transcript.py             # YouTube transcript fetcher & formatter
├── tests/                            # Unit and integration test suite
│   ├── __init__.py
│   ├── test_video_id_extractor.py   # Unit tests for URL parser
│   └── test_transcript.py           # Unit tests for transcript fetcher (pytest-mock)
├── .env                              # Local environment secrets (Git ignored)
├── .env.example                      # Environment variable template
├── .gitignore                        # Git exclusion rules
├── pyproject.toml                    # Pytest configuration & package pathing
├── README.md                          # Project documentation
└── requirements.txt                  # Direct project dependencies
```

---

## Engineering Decisions

During the architecture and implementation of this project, key engineering decisions were made to ensure production-grade quality, strict testability, maintainability, and resource optimization.

### 1. Custom Exception Hierarchy & API Decoupling (`VideoToKnowledgeError`)
- **Decision:** Designed a custom domain exception hierarchy in `src/ai_video_to_knowledge/exceptions.py`. A base exception `VideoToKnowledgeError` serves as the root, with specific subclasses like `ExtractorError` and `TranscriptNotAvailableError`.
- **Rationale & Benefits:**
  - **Decoupling Application Logic:** Upstream application code should never directly catch third-party library exceptions (e.g., `youtube_transcript_api._errors.VideoUnavailable`). If we switch to a different transcript provider in the future (e.g., AssemblyAI, Whisper, or a custom scraper) or if the current library changes its error definitions, upstream modules will remain completely unaffected.
  - **Single Point of Translation:** All third-party library exceptions are intercepted at the module boundary (`transcript.py`) and wrapped into domain-specific exceptions.
  - **Clean Error Boundaries:** Prevents generic Python system errors (like `ValueError` or `KeyError`) from masking domain failures, allowing callers to handle application errors predictably.

### 2. Defensive Input Validation & Fail-Fast Principle
- **Decision:** Implemented early explicit input validation (`isinstance`, `.strip()`, empty-string checks) before executing complex operations like regular expressions or network calls.
- **Rationale & Benefits:**
  - **Fail-Fast Mechanics:** In LLM pipelines, attempting to process invalid inputs (e.g., non-string URLs, empty strings, or non-YouTube links) through downstream modules leads to cascading failures, unnecessary API calls, and wasted OpenAI credit costs.
  - **Clear Error Attribution:** Validating input type and format at the function entry point raises immediate, descriptive errors (`TypeError` or `ExtractorError`) before any heavy computation occurs.

### 3. Clean Error Messaging & Traceback Isolation
- **Decision:** Removed raw stringified exception payloads (`{e}`) from user-facing error messages in `transcript.py`, relying instead on clean domain strings combined with exception chaining (`raise CustomError(...) from e`).
- **Rationale & Benefits:**
  - **Noise Reduction:** Third-party libraries like `youtube-transcript-api` often append long troubleshooting paragraphs, issue tracker URLs, and verbose stack information inside their exception strings.
  - **Clean API Contract:** Intercepting the error and returning a concise single-line message (e.g., `Could not retrieve transcript for video ID 'dQw4w9WgXc'`) provides a professional interface for downstream callers.
  - **Debugging Preservation:** Using Python's `from e` syntax preserves the full underlying stack trace for developers without polluting the primary exception string.

### 4. Isolated, Zero-Network Unit Testing (`pytest-mock` & `types.SimpleNamespace`)
- **Decision:** Standardized unit tests to run completely offline without making live HTTP requests to YouTube servers, leveraging `pytest-mock` (`mocker.patch`) and `types.SimpleNamespace`.
- **Rationale & Mechanics:**
  - **Why Avoid Live Network Calls?** Real HTTP requests to external APIs are slow, unreliable, and subject to rate limits or network dropouts. A unit test must verify internal code logic, not YouTube's external uptime.
  - **How Mocking Works (`mocker.patch`):** Intercepts calls to `YouTubeTranscriptApi().fetch` during test runs, returning pre-defined in-memory data instantly.
  - **Object Attribute Mimicking (`types.SimpleNamespace`):** Modern versions of `youtube-transcript-api` (v1.0+) return structured snippet objects with a `.text` attribute rather than raw dictionaries. We use Python's standard library `types.SimpleNamespace(text="...")` to construct lightweight mock objects that support dot-notation (`item.text`).
  - **Outcome:** The entire unit test suite executes deterministically in **less than 0.1 seconds**, completely offline.

### 5. Production `src/` Package Layout & Editable Installation (`pip install -e .`)
- **Decision:** Adopted the canonical `src/` project layout (`src/ai_video_to_knowledge/`), configured `pyproject.toml` with `pythonpath = ["src"]`, and registered the package in editable mode via `pip install -e .`.
- **Rationale & Problem Solution:**
  - **Where We Encountered the Issue:** Running test scripts from the root directory or inside PyCharm's PyDev console originally threw `ModuleNotFoundError: No module named 'ai_video_to_knowledge'` or required temporary `sys.path` hacks.
  - **Role of `src/` Layout:** Isolates core source code from root configuration scripts, preventing accidental import collisions between repository files and Python packages.
  - **Role of Editable Mode (`pip install -e .`):** Generates package metadata (`ai_video_to_knowledge.egg-info/`) in `.venv`. Python's package manager links the `src/` directory directly into the virtual environment, allowing `from ai_video_to_knowledge...` imports to resolve globally across CLI, PyCharm, and Pytest without mutating `sys.path`.
  - **Role of `pyproject.toml` (`pythonpath`):** Explicitly informs `pytest` where to resolve package paths during test execution.

### 6. Decoupled Module Architecture & REPL-Driven Sanity Testing
- **Decision:** Designed core business logic modules (`transcript.py`, `video_id_extractor.py`) as independent, pure functional components without embedded `if __name__ == "__main__":` entry points or tight coupling to CLI interfaces.
- **Rationale & Benefits:**
  - **High Reusability:** Core functions can be imported seamlessly into CLI tools, web application endpoints (e.g., FastAPI), or background workers.
  - **Interactive REPL Sanity Checks:** Allows developers to test live behavior directly inside the Python REPL console (`>>> print(fetch_transcript("..."))`) to verify real-world API output formats alongside offline unit tests.

### 7. Module-Level Pattern Pre-Compilation (`re.compile`)
- **Decision:** Compiled regular expressions at the module top-level (`YOUTUBE_URL_REGEX = re.compile(...)`) rather than inside function bodies.
- **Rationale & Performance Benefits:**
  - Compiling regular expressions inside a frequently called function forces Python to re-parse the regex string into a state machine on every function execution.
  - Pre-compiling the pattern once when the module is imported eliminates redundant parsing overhead, optimizing execution speed for high-throughput batch URL processing.

### 8. Strict Character-Level Exception Assertions in Parametrized Tests
- **Decision:** Enforced exact string equality (`assert str(exc_info.value) == expected_message`) when testing exception handling across valid and invalid URL formats using `@pytest.mark.parametrize`.
- **Rationale & Benefits:**
  - Loose assertions (such as substring checking `in`) can mask subtle formatting bugs, missing parameters, or unexpected string mutations.
  - Pairwise parametrization maps each invalid input directly to its exact expected error string, guaranteeing consistent error communication.

### 9. Strict Environment Secret Hygiene (`.env` vs `.env.example`)
- **Decision:** Enforced complete isolation of environment secrets (`.env`) from version control while maintaining a tracked `.env.example` template contract.
- **Rationale & Benefits:**
  - Hardcoding sensitive credentials (such as `OPENAI_API_KEY`) creates severe security risks.
  - Excluding `.env` and local build artifacts (`*.egg-info/`) in `.gitignore` prevents secret leaks, while `.env.example` provides a clear configuration blueprint for collaborators.

---

## New Knowledge & Concepts Learned

Throughout the engineering process, the following core Python engineering concepts, tools, and paradigms were mastered from first principles:

1. **Python Import Resolution & `sys.path` Mechanics**:
   - Learned how Python locates packages via `sys.path` when executing scripts from different working directories.
   - Discovered why `src/` layouts require explicit path configuration (via `pyproject.toml`, `sys.path`, or `pip install -e .`).
   - Mastered Editable Mode (`pip install -e .`), which registers local package metadata (`*.egg-info`) inside the virtual environment (`.venv`) for live development imports.

2. **Object-Oriented Exception Handling & Chaining**:
   - Learned how to design domain exception class hierarchies using inheritance (`class ExtractorError(VideoToKnowledgeError)`).
   - Mastered exception chaining using `raise CustomError(...) from e` to preserve underlying traceback context while surfacing clean domain errors.

3. **API Method Instantiation & Schema Debugging**:
   - Diagnosed unbound instance method errors (`TypeError: fetch() missing 1 required positional argument: 'video_id'`) caused by invoking instance methods without instantiation (`YouTubeTranscriptApi().fetch(...)`).
   - Inspected third-party object schemas (`dir()`, `type()`, `hasattr()`) to adapt to breaking library updates (transitioning from dictionary lookups `item["text"]` to object attributes `item.text`).

4. **Advanced Unit Testing with `pytest` & `pytest-mock`**:
   - Mastered `@pytest.mark.parametrize` to test multiple URL variations (standard, shorts, embed, mobile `m.youtube.com`, timestamped links) without code duplication.
   - Learned how to mock external network dependencies using `mocker.patch`.
   - Utilized `types.SimpleNamespace` from Python's standard library to construct lightweight mock objects with dot-notation (`item.text`) for unit tests.
   - Implemented exact exception assertions using `with pytest.raises(ExceptionClass) as exc_info:` and `assert str(exc_info.value) == expected`.

5. **Robust Regular Expressions for URL Parsing**:
   - Designed regex patterns with non-capturing groups `(?:...)` and explicit capture groups `([\w-]{11})` to extract 11-character YouTube video IDs across diverse URL formats (`watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`, `/v/`, `m.youtube.com`).
   - Understood performance benefits of module-level regex pre-compilation (`re.compile`).

6. **Interactive REPL Prototyping vs. Automated Unit Testing**:
   - Learned how to execute and inspect package functions directly inside the Python Interactive REPL console.
   - Established a two-tier testing protocol: **automated unit testing** (fast, deterministic, offline via `pytest-mock`) and **interactive sanity testing** (verifying live API responses in REPL).

---

## Getting Started

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

## Configuration

Secrets and environment settings are managed via `.env`.

Example `.env`:

```env
## OpenAI API Configuration
OPENAI_API_KEY=your_actual_openai_api_key
OPENAI_MODEL=gpt-4o-mini

## Application Settings
LOG_LEVEL=INFO
```

---

## Running Tests

Execute the full test suite using `pytest`:

```bash
pytest
```

For verbose output showing individual test functions:

```bash
pytest -v
```

---

## Current Status & Roadmap

- [x] **Module 1 (`video_id_extractor.py`)**: Robust YouTube URL parsing & validation.
- [x] **Module 2 (`transcript.py`)**: YouTube transcript fetching & continuous text formatting.
- [x] **Exception Hierarchy (`exceptions.py`)**: Custom domain error handling.
- [x] **Test Suite**: Comprehensive unit testing with `pytest` and `pytest-mock`.
- [ ] **Module 3 (`summarizer.py`)**: OpenAI API integration for transcript summarization.
- [ ] **Module 4 (Export Pipeline)**: Markdown / PDF generation & NoSQL storage.
