# Productive Failure Maths Tutor (Class 10)

CSC530 group project. Local RAG tutor for NCERT Class 10 Mathematics.


## Group Members

Jash Agicha :- AU2320253
Nidhi Mehta :- AU2440019
Aangi Shah :- AU2300055

The tutor uses Manu Kapur's Productive Failure idea: student tries first (exploration), then we explain the proper method (consolidation). It should not dump the formula on the first message.

Prompt details are in `docs/RTAO.md` and `docs/TOCD.md`. Pedagogy notes used in the index are in `data/pedagogy_pf.md`.

## Stack

- LLM: Qwen 3 1.7B through Ollama (`qwen3:1.7b`)
- Embeddings: HuggingFace `all-MiniLM-L6-v2`
- Vector DB: ChromaDB (saved in `chroma_db/`)
- RAG: LangChain
- UI: Streamlit

## Folder structure

```
pf-rag-tutor/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── jemh101.pdf ... jemh114.pdf   # NCERT chapters (not in git)
│   ├── pedagogy_pf.md
│   ├── misconceptions.json
│   └── worked_examples.json
├── docs/
│   ├── RTAO.md
│   └── TOCD.md
└── chroma_db/                        # created on first run
```

## Setup

Need Python 3.10+, Ollama installed, and the model:

```
ollama pull qwen3:1.7b
```

Then:

```
cd pf-rag-tutor
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Put the Class 10 NCERT maths PDFs in `data/`. We used the chapter-wise files (`jemh101.pdf` to `jemh114.pdf`). Any `*.pdf` in that folder gets loaded.

If you add or replace PDFs later, delete `chroma_db/` and start the app again so the index is rebuilt.

## Run

```
streamlit run app.py
```

Opens at http://localhost:8501

## Quick test

1. Ask: How do I find the area of a parallelogram?
2. In exploration it should ask you to try, not give the formula.
3. Example attempt: parallelogram base 8 cm, sloping side 5 cm, I think area is 8 x 5 = 40.
4. Click **Move to Consolidation** in the sidebar.
5. It should explain base x perpendicular height and give another problem.
6. Open **Retrieved Knowledge Used** to see the chunks that were pulled.

## Sidebar

- **New Session** - clears chat and goes back to exploration
- **Move to Consolidation** - we switch phase manually for now

## What we did not finish

- auto switch from exploration to consolidation
- scoring how good the attempt was
- detecting misconceptions from the student message
- measuring frustration

## If something breaks

- Ollama error: run `ollama serve` and check `qwen3:1.7b` is pulled
- First start is slow because embeddings download and chroma builds once
- After changing files in `data/`, delete `chroma_db/` and restart
- If a PDF is not showing up in retrieval, same thing: delete `chroma_db/` and restart
- `No module named 'torchvision'` in the terminal is from Streamlit watching torch files. We turned the file watcher off in `.streamlit/config.toml`
