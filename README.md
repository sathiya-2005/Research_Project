# ResearchPilot — Agentic Research & Report Generator

ResearchPilot is a small local web application that takes a research question, asks an LLM to decompose it into sub-questions, uses a document-search tool, and generates a structured report with source-filename citations.

## Features

- Streamlit browser interface
- LangChain/LangGraph agent loop with a callable document-search tool
- Built-in sample reference notes plus user-uploaded `.txt` and `.md` documents
- Evidence-based report headings and explicit evidence-gap section
- Downloadable Markdown report
- No database or cloud deployment required

## Requirements

- Python 3.10 or newer (Python 3.11 is a sensible choice)
- An OpenAI API key and internet access for model calls
- Windows, macOS, or Linux

The application runs locally, but the question and retrieved excerpts are sent to the selected model API. Do not upload confidential material.

## Run on Windows

Open Command Prompt in this project folder and run:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If `py` is not recognized, try `python` instead. Your browser should open the local app. Enter your API key in the sidebar, enter a research question, and click **Plan and generate report**.

## Run on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Try it

Example question:
> What are the main challenges in managing heat in electric-vehicle battery packs?

The bundled sample files are illustrative learning notes, not a complete or authoritative literature review. Upload your own `.txt` or `.md` reference documents to research a different topic.

## Project structure

```text
researchpilot_agent/
├── app.py
├── requirements.txt
├── README.md
├── schema.md
├── .gitignore
└── knowledge_base/
    ├── ev_battery_thermal_management.txt
    └── research_methods.txt
```

## Agent workflow

See [`schema.md`](schema.md) for the flowchart and machine-readable workflow schema.

## Important limitations

- Document retrieval uses keyword overlap, not embeddings or a semantic search index.
- The agent can make mistakes. Check every claim and citation against the original document.
- Citations refer to filenames and do not automatically provide page numbers or external URLs.
- The sample notes are starter material; replace or supplement them with reliable sources.
- This is an educational prototype, not a replacement for a proper literature review.

## Attribution and development note

The project uses the open-source Streamlit interface framework and LangChain/LangGraph agent framework. The app-specific prompt, document loading, keyword retrieval, workflow configuration, report interface, and assignment schema are assembled for this project. If you modify this project for assessment, document the changes you actually make and understand the key functions before presenting it.
