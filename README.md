# AIVideoToFiles

A production-grade Python application that extracts transcripts from YouTube videos, processes them using OpenAI's LLMs to generate summaries and lesson plans, and exports structured results.

---

## Project Architecture

```text
AIVideoToFiles/
├── src/
│   └── ai_video_to_file/       # Core application package
│       └── __init__.py
├── tests/                      # Unit and integration tests
│   └── __init__.py
├── .env                        # Local environment secrets (Git ignored)
├── .env.example                # Environment variable template
├── .gitignore                  # Git exclusion rules
├── README.md                   # Project documentation
└── requirements.txt            # Direct dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key

### Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/AIVideoToFiles.git
cd AIVideoToFiles
```

2. Create and activate a virtual environment:

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create your local environment file.

5. Add your OpenAI API key and other required configuration to `.env`.

---

## Configuration

Keep secrets and environment-specific configuration in `.env`.

Example:

```env
OPENAI_API_KEY=your_api_key_here
```

Do not commit `.env` to version control.

---

## Usage

Run the application from the project root using the project's configured entry point.

The application is designed to:

1. Accept a YouTube video as input.
2. Extract its transcript.
3. Send the transcript to an OpenAI LLM for processing.
4. Generate a structured summary and lesson plan.
5. Export the generated content to files.
6. Save those files in NoSQL databases

---

## Testing

Run the test suite with:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

---

## Environment Variables

The `.env.example` file serves as a template for the environment variables required by the application.

Never commit real API keys or other secrets to the repository.

---

## Dependencies

Direct Python dependencies are listed in:

```text
requirements.txt
```

Install or update dependencies using your virtual environment rather than the system-wide Python installation.

---
