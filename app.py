"""
CSC530 Project - Productive Failure Maths Tutor (Class 10 NCERT)

Streamlit RAG app. Uses Qwen (Ollama) + ChromaDB.
Tutor follows Manu Kapur's Productive Failure: exploration first, then consolidation.
"""

import json
from pathlib import Path

import streamlit as st
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

LLM_MODEL = "qwen3:1.7b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 80
RETRIEVAL_K = 5

PEDAGOGY_PATH = DATA_DIR / "pedagogy_pf.md"
MISCONCEPTIONS_PATH = DATA_DIR / "misconceptions.json"
WORKED_EXAMPLES_PATH = DATA_DIR / "worked_examples.json"


def load_all_documents() -> list[Document]:
    documents: list[Document] = []

    # all pdfs in data/ (we used separate ncert chapter files)
    pdf_paths = sorted(DATA_DIR.glob("*.pdf"))
    if pdf_paths:
        loaded_count = 0
        for pdf_path in pdf_paths:
            try:
                pdf_loader = PyPDFLoader(str(pdf_path))
                pdf_docs = pdf_loader.load()
                for doc in pdf_docs:
                    doc.metadata["source_type"] = "ncert_pdf"
                    doc.metadata["source_file"] = pdf_path.name
                documents.extend(pdf_docs)
                loaded_count += 1
            except Exception as e:
                st.warning(f"Could not load `{pdf_path.name}`: {e}")
        if loaded_count:
            st.caption(f"Loaded {loaded_count} NCERT chapter PDF(s) from `data/`.")
    else:
        st.info(
            "No PDFs found in `data/`. Add NCERT chapter PDFs there. "
            "Pedagogy notes and json files will still be indexed."
        )

    if PEDAGOGY_PATH.exists():
        pedagogy_loader = TextLoader(str(PEDAGOGY_PATH), encoding="utf-8")
        pedagogy_docs = pedagogy_loader.load()
        for doc in pedagogy_docs:
            doc.metadata["source_type"] = "pedagogy"
        documents.extend(pedagogy_docs)

    # json -> langchain Document so it can go into chroma
    if MISCONCEPTIONS_PATH.exists():
        with open(MISCONCEPTIONS_PATH, encoding="utf-8") as f:
            misconceptions = json.load(f)
        for item in misconceptions:
            content = (
                f"Misconception ({item['topic']}): {item['symptom']}\n"
                f"Root cause: {item['root_cause']}\n"
                f"Diagnostic question: {item['diagnostic_question']}\n"
                f"Corrective hint: {item['corrective_hint']}"
            )
            documents.append(
                Document(page_content=content, metadata={"source_type": "misconception", "id": item["id"]})
            )

    if WORKED_EXAMPLES_PATH.exists():
        with open(WORKED_EXAMPLES_PATH, encoding="utf-8") as f:
            examples = json.load(f)
        for item in examples:
            steps = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(item["solution_steps"]))
            content = (
                f"Worked example ({item['topic']}): {item['problem']}\n"
                f"Solution steps:\n{steps}\n"
                f"Why it works: {item['why_it_works']}"
            )
            documents.append(
                Document(page_content=content, metadata={"source_type": "worked_example", "id": item["id"]})
            )

    return documents


@st.cache_resource(show_spinner="Building knowledge base (first run may take a minute)...")
def get_vector_store() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # skip re-embedding if we already built chroma_db
    if CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()):
        return Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings,
        )

    raw_docs = load_all_documents()
    if not raw_docs:
        st.error("No documents found in `data/`. Add the knowledge base files and restart.")
        st.stop()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(raw_docs)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    return vector_store


@st.cache_resource
def get_llm() -> OllamaLLM:
    return OllamaLLM(model=LLM_MODEL, temperature=0.4)


def build_phase_tocd(phase: str) -> str:
    if phase == "exploration":
        return """
Task: Elicit the student's own attempt first. Diagnose their reasoning with questions. Do NOT provide the full solution or canonical formula yet.
Output: Short, supportive reply (2–4 sentences). One diagnostic question OR one minimal hint. Encourage sketching or labeling.
Constraints: NO immediate solutions. NO step-by-step worked solution. NO final numerical answer. Minimal hints only.
Domain: NCERT Class 10 Mathematics (geometry, algebra, trigonometry).
"""
    return """
Task: Provide the canonical NCERT explanation. Compare with the student's attempt if available. Clarify misconceptions. End with a transfer problem.
Output: Brief explanation (3–6 sentences), comparison to student work, one transfer question.
Constraints: Be accurate and NCERT-aligned. Acknowledge what the student did well. Correct errors gently.
Domain: NCERT Class 10 Mathematics (geometry, algebra, trigonometry).
"""


def build_system_prompt(phase: str, context: str, attempt_count: int) -> str:
    tocd = build_phase_tocd(phase)
    return f"""You are a Productive Failure maths tutor for Class 10 NCERT students (Manu Kapur pedagogy).

## RTAO
Role: Supportive Productive Failure tutor aligned with NCERT Class 10 Mathematics.
Task: Elicit attempts before teaching (Exploration), then consolidate formal knowledge (Consolidation).
Audience: Indian high school Class 10 students. Use clear, encouraging language.
Output: Short, Socratic tutoring turns—questions and hints in Exploration; explanations and transfer problems in Consolidation.

## TOCD (Current Phase: {phase.upper()})
{tocd}

## Session Info
- Current phase: {phase}
- Student attempts so far: {attempt_count}

## PF Rules (always enforce)
1. NO immediate solutions during Exploration.
2. Ask diagnostic questions to surface reasoning.
3. Give minimal hints only—never the full method on first contact.
4. In Consolidation, explain after attempts and give a transfer problem.

## Retrieved Knowledge Context
Use the following excerpts from NCERT, pedagogy notes, misconceptions, and worked examples when relevant:

{context}

Respond as the tutor. Stay in the {phase} phase behavior described above."""


def format_retrieved_docs(docs: list[Document]) -> tuple[str, list[str]]:
    snippets: list[str] = []
    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source_type", doc.metadata.get("source", "unknown"))
        snippet = doc.page_content[:400].strip()
        if len(doc.page_content) > 400:
            snippet += "..."
        snippets.append(f"[{source}] {snippet}")
        parts.append(f"--- Chunk {i} ({source}) ---\n{doc.page_content}")
    return "\n\n".join(parts), snippets


def run_rag_chain(
    question: str,
    chat_history: list,
    phase: str,
    attempt_count: int,
    vector_store: Chroma,
    llm: OllamaLLM,
) -> tuple[str, list[str]]:
    retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})
    retrieved_docs = retriever.invoke(question)
    context, snippets = format_retrieved_docs(retrieved_docs)
    system_prompt = build_system_prompt(phase, context, attempt_count)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ]
    )

    # last user msg is {question}, so don't put it in history again
    history_messages = []
    for msg in chat_history[:-1]:
        if msg["role"] == "user":
            history_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history_messages.append(AIMessage(content=msg["content"]))

    chain = prompt | llm
    response = chain.invoke({"history": history_messages, "question": question})
    return str(response), snippets


def init_session_state() -> None:
    defaults = {
        "messages": [],
        "attempts": [],
        "phase": "exploration",
        "last_snippets": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session() -> None:
    st.session_state.messages = []
    st.session_state.attempts = []
    st.session_state.phase = "exploration"
    st.session_state.last_snippets = []


def main() -> None:
    st.set_page_config(
        page_title="PF Maths Tutor",
        page_icon="🧠",
        layout="wide",
    )

    init_session_state()

    st.title("🧠 Productive Failure Maths Tutor (Class 10)")
    st.caption("RAG tutor for NCERT Class 10 maths (Productive Failure)")

    with st.sidebar:
        st.header("Session Controls")
        if st.button("New Session", use_container_width=True):
            reset_session()
            st.rerun()

        if st.button("Move to Consolidation", use_container_width=True):
            st.session_state.phase = "consolidation"
            st.rerun()

        st.divider()
        st.metric("Current Phase", st.session_state.phase.title())
        st.metric("Attempts", len(st.session_state.attempts))
        st.caption(f"LLM: `{LLM_MODEL}` | Embeddings: `{EMBEDDING_MODEL}`")

    try:
        vector_store = get_vector_store()
        llm = get_llm()
    except Exception as e:
        st.error(
            f"Could not start the knowledge base or LLM. "
            f"Make sure Ollama is running (`ollama serve`) and the model is pulled "
            f"(`ollama pull {LLM_MODEL}`).\n\nDetails: {e}"
        )
        st.stop()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.last_snippets:
        with st.expander("Retrieved Knowledge Used", expanded=False):
            for i, snippet in enumerate(st.session_state.last_snippets, start=1):
                st.markdown(f"**Snippet {i}**")
                st.text(snippet)

    if prompt := st.chat_input("Ask a Class 10 maths question or share your attempt..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.attempts.append(prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response, snippets = run_rag_chain(
                        question=prompt,
                        chat_history=st.session_state.messages,
                        phase=st.session_state.phase,
                        attempt_count=len(st.session_state.attempts),
                        vector_store=vector_store,
                        llm=llm,
                    )
                    st.session_state.last_snippets = snippets
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = (
                        "Could not generate a response. Check that Ollama is running and try again."
                    )
                    st.error(f"{error_msg}\n\n`{e}`")
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()
