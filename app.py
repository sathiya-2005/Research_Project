import os
import re
from pathlib import Path
from collections import Counter

import streamlit as st
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

APP_TITLE = "ResearchPilot"
SAMPLE_DIR = Path(__file__).parent / "knowledge_base"

st.set_page_config(page_title=APP_TITLE, page_icon="🔎", layout="wide")


def load_documents(uploaded_files):
    """Load bundled sample notes and user-uploaded TXT/MD documents."""
    docs = []
    if SAMPLE_DIR.exists():
        for path in sorted(SAMPLE_DIR.glob("*")):
            if path.suffix.lower() in {".txt", ".md"}:
                try:
                    docs.append({"name": path.name, "text": path.read_text(encoding="utf-8")})
                except OSError:
                    pass

    for file in uploaded_files or []:
        try:
            text = file.getvalue().decode("utf-8", errors="replace")
            docs.append({"name": file.name, "text": text})
        except Exception:
            continue
    return docs


def rank_passages(query, documents, max_results=5):
    """Simple transparent keyword-overlap retrieval; not a semantic search engine."""
    words = set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,}", query.lower()))
    scored = []
    for doc in documents:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", doc["text"]) if p.strip()]
        if not paragraphs:
            paragraphs = [doc["text"][:2000]]
        for paragraph in paragraphs:
            p_words = set(re.findall(r"[a-zA-Z0-9][a-zA-Z0-9-]{2,}", paragraph.lower()))
            overlap = words & p_words
            if overlap:
                score = len(overlap) / max(1, len(words))
                scored.append((score, doc["name"], paragraph, sorted(overlap)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:max_results]


def run_research(question, documents, api_key, model_name):
    # The tool is intentionally defined inside this function so it can access
    # the current session's document collection.
    @tool
    def search_research_materials(query: str) -> str:
        """Search the available reference documents for evidence relevant to a research sub-question.
        Use this tool multiple times with different sub-questions before writing the report.
        Returns excerpts with source filenames. Do not treat absent results as proof."""
        results = rank_passages(query, documents, max_results=5)
        if not results:
            return (
                "No matching passages found. Explain this evidence gap in the report. "
                "Do not invent sources or facts."
            )
        lines = []
        for score, filename, passage, overlap in results:
            excerpt = passage[:1400]
            lines.append(
                f"[SOURCE: {filename} | relevance={score:.2f} | matched_terms={', '.join(overlap)}]\n{excerpt}"
            )
        return "\n\n---\n\n".join(lines)

    system_prompt = """
You are ResearchPilot, a careful research workflow agent.
Your job is to create a useful, evidence-based research report from the supplied reference collection.

Workflow rules:
1. First identify 3-5 sub-questions needed to answer the user's research question.
2. Use the search_research_materials tool at least twice, with meaningfully different sub-questions.
3. Base factual claims on the retrieved excerpts. Cite them inline using [Source: exact_filename].
4. Never invent papers, URLs, authors, statistics, quotations, or citations.
5. If the available documents do not support a claim, label it as a gap or general context needing verification.
6. In the final answer use these headings:
   - Research question
   - Research plan
   - Executive summary
   - Key findings (with source citations)
   - Limitations and evidence gaps
   - Further research questions
7. Keep the report clear and appropriately concise. Distinguish evidence from interpretation.
8. The document search is keyword-based, so mention that limitation where relevant.
"""

    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key)
    agent = create_agent(
        model=llm,
        tools=[search_research_materials],
        system_prompt=system_prompt,
    )
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                f"Research question: {question}\n\n"
                "Create the report by planning sub-questions and searching the available documents. "
                "Use the tool more than once and cite the filenames of the evidence you actually retrieve."
            ),
        }]
    })
    messages = result.get("messages", [])
    for message in reversed(messages):
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            text_parts = [
                item.get("text", "") for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            if text_parts:
                return "\n".join(text_parts)
    return "The agent did not return a text report. Please try again."


st.title("🔎 ResearchPilot")
st.caption("An agentic research assistant that plans sub-questions, searches reference documents, and writes a cited report.")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "OpenAI API key",
        type="password",
        help="Used only for this run. Do not paste your key into source code or commit it to GitHub.",
    )
    model_name = st.text_input("Model", value="gpt-4.1-mini")
    st.divider()
    st.markdown("**Reference collection**")
    st.write("Bundled sample notes are loaded automatically. You can also upload `.txt` or `.md` files.")
    uploads = st.file_uploader(
        "Upload reference documents",
        type=["txt", "md"],
        accept_multiple_files=True,
    )
    st.caption("This version runs locally but sends the research prompt and retrieved excerpts to the selected model API.")

documents = load_documents(uploads)
left, right = st.columns([3, 2])
with left:
    question = st.text_area(
        "What would you like to research?",
        placeholder="Example: What are the main challenges in managing heat in electric-vehicle battery packs?",
        height=120,
    )
with right:
    st.markdown("### Available sources")
    st.metric("Documents loaded", len(documents))
    st.write("**Search method:** keyword-overlap ranking")
    st.write("**Output:** cited report + downloadable Markdown")

if documents:
    with st.expander("View available document names"):
        for doc in documents:
            st.write(f"• {doc['name']}")
else:
    st.warning("No reference documents found. Add TXT/MD files to the knowledge_base folder or upload them.")

if st.button("Plan and generate report", type="primary", disabled=not question.strip()):
    if not api_key.strip():
        st.error("Enter your model API key in the sidebar to run the agent.")
    elif not documents:
        st.error("Add at least one reference document before running research.")
    else:
        with st.spinner("The agent is planning, searching documents, and drafting your report..."):
            try:
                report = run_research(question.strip(), documents, api_key.strip(), model_name.strip())
                st.session_state["last_report"] = report
                st.session_state["last_question"] = question.strip()
            except Exception as exc:
                st.error(
                    "The agent could not complete the run. Check your API key, model name, internet connection, "
                    "and installed package versions. Technical message:"
                )
                st.code(str(exc))

if st.session_state.get("last_report"):
    st.divider()
    st.subheader("Research report")
    st.markdown(st.session_state["last_report"])
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", st.session_state.get("last_question", "research"))[:45]
    report_file = f"researchpilot_report_{safe_name}.md"
    st.download_button(
        "Download report (.md)",
        data=st.session_state["last_report"],
        file_name=report_file,
        mime="text/markdown",
    )

with st.expander("How is this agentic?"):
    st.markdown(
        """
        - **Planning:** the system prompt asks the model to decompose the question into sub-questions.
        - **Tool selection and execution:** the model can call the document-search tool with different queries.
        - **Multi-step loop:** the agent framework returns tool results to the model, which can decide what to search next.
        - **Synthesis:** the model produces a structured report based on retrieved evidence.
        - **Human input:** the user chooses the question and reference documents.

        This is a small educational prototype, not a fully autonomous or production-grade research platform.
        """
    )
