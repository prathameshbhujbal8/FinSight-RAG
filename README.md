# FinSight RAG

AI-powered financial research assistant. Upload annual reports / financial
PDFs, ask questions in natural language, get cited answers grounded in the
source documents — plus side-by-side company comparisons and PDF report export.

Built to explore retrieval-augmented generation (RAG) on multi-document
financial corpora, with an emphasis on **source-grounded answers** and
**avoiding hallucination when relevant data isn't present** in the uploaded
documents.

## Features

- **PDF ingestion** — upload financial PDFs, automatically chunked and embedded
- **Semantic retrieval** — ChromaDB vector search with distance-based
  relevance filtering (irrelevant matches are rejected, not just ranked low)
- **Source-cited answers** — every answer is grounded in retrieved chunks,
  with page-level source citations shown alongside the response
- **Company comparison** — ask a question across two ingested documents and
  get a structured side-by-side comparison, with per-company source citations
- **PDF export** — download a formatted report of any Q&A answer or
  comparison result, including citations
- **Query analytics** — running log of all questions asked, most-queried
  documents, and query history

## Architecture

```
PDF Upload
   │
   ▼
PDF Parser ──▶ Text Chunker ──▶ Sentence-Transformer Embeddings
                                          │
                                          ▼
                                    ChromaDB (vector store)
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                                           ▼
            Single-document Q&A                      Company Comparison
         (Retriever → Groq LLM)                  (Retriever ×2 → Groq LLM)
                    │                                           │
                    └─────────────────────┬─────────────────────┘
                                          ▼
                                  Streamlit UI
                                          │
                                          ▼
                                  PDF Report Export
```

**Stack:** Python, Streamlit, ChromaDB, Sentence-Transformers, Groq
(Llama 3.1), ReportLab

## How Hallucination Is Handled

Two specific design choices reduce hallucination risk rather than just
trusting the prompt:

1. **Distance threshold filtering at retrieval time.** ChromaDB always
   returns `top_k` results regardless of relevance. This project filters out
   chunks above a distance threshold before they ever reach the LLM, so an
   off-topic question returns *no context* rather than the "closest available
   but irrelevant" chunks.
2. **Explicit empty-context handling.** If retrieval returns nothing (for a
   single question or for either side of a comparison), the system returns a
   clear "not found in the provided documents" message instead of sending a
   blank context block to the LLM and letting it guess.

## Known Limitations

- **No multi-user document isolation.** All uploaded documents share a single
  ChromaDB collection. Suitable for solo/demo use; not suitable for a public
  multi-tenant deployment without adding session-scoped filtering.
- **Distance threshold (1.5) was set empirically**, not validated against a
  labeled relevance dataset. It works well on the test PDFs used during
  development but may need adjustment for very different document types.
- **No persistence guarantee on Streamlit Cloud.** ChromaDB's storage is
  ephemeral on most free hosting — uploaded documents may need to be
  re-ingested after the app restarts/sleeps.
- **Single embedding model path is not yet unified** — see `Embedder` usage
  in `Retriever` vs ingestion (tracked as a fix, not yet resolved at time of
  writing this README).

## Running Locally

```bash
git clone <repo-url>
cd finsight-rag
pip install -r requirements.txt

# create a .env file with:
# GROQ_API_KEY=your_key_here

streamlit run streamlit_app.py
```

## Project Structure

```
src/
├── ingestion/        PDF parsing
├── chunking/          Text splitting
├── embeddings/        Sentence-transformer embedding generation
├── vectordb/           ChromaDB storage layer
├── retrieval/           Query embedding + similarity search + filtering
├── llm/                  Groq LLM call + prompt construction
├── comparison/          Two-document comparison logic
├── export/               PDF report generation
├── analytics/            Query logging
└── pipeline/              Orchestration layer tying everything together
streamlit_app.py          UI entrypoint
```

## Screenshots

### Financial Q&A:What is Infosys AI strategy?
<img width="852" height="392" alt="image" src="https://github.com/user-attachments/assets/37c73957-ac4e-4cb0-8801-1eb9752c193f" />                                                                      Source Verification Example

The answer regarding Infosys' AI strategy was retrieved from the annual report and traced back to the original PDF source.<img width="831" height="657" alt="image" src="https://github.com/user-attachments/assets/23925c01-1779-4853-8c0d-80e23b5577f2" />




### Company Comparison:Compare AI strategy
<img width="467" height="781" alt="image" src="https://github.com/user-attachments/assets/846e6c01-9448-4585-af03-25d84a86d2b3" />


### Hallucination Prevention:What is Infosys plan to build electric vehicles by 2030?
Answer:
Information not found in the provided documents.
Sources:📄 infosys_annual_report_2025.pdf
Page: 66  (This screenshot is actually a perfect example of why your hallucination test is valuable.

The question was:

What is Infosys plan to build electric vehicles by 2030?

And the page you showed is about:

Energy conservation
Renewable energy
Green buildings
Water management
Waste management
Carbon offset

There is nothing about electric vehicles.FinSight applies retrieval filtering and empty-context handling to avoid generating unsupported answers when information is not present in the source documents.)<img width="756" height="910" alt="image" src="https://github.com/user-attachments/assets/af8e15ac-7315-402b-8c82-1118a0a86fdf" />

### Analytics Dashboard
<img width="1858" height="851" alt="image" src="https://github.com/user-attachments/assets/281fb170-8419-49c5-889a-5b73e4980215" />


## What I'd Build Next

- Session-scoped document isolation for multi-user deployment
- Evaluation harness with a labeled question set to properly tune the
  relevance threshold instead of empirical guessing
- Streaming responses instead of waiting for the full Groq completion
