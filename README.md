# LegalEase — AI Legal Assistant

An AI-powered legal assistant for understanding legal issues, searching precedents, managing case progress, and generating document drafts.

## Features

- **AI Legal Analysis** — Issue summary, potential violations, missing facts, next steps, risk factors
- **Precedent Search** — Find similar judgments and relevant case law
- **Document Summarization** — Key clauses, obligations, deadlines, and red flags from uploaded docs
- **Drafting Assistant** — Generate legal notices, complaints, response letters, and more
- **Case Timeline** — Track hearings, filings, deadlines, and AI-suggested milestones
- **Cross-case Search** — Ask questions across all uploaded documents

## RAG Flow

Question → **Question Analysis** (legal or general routing) → **MultiQuery** → **Retrieval** → **Grade Documents**
- Docs relevant → **Generate** → **Hallucination Check** → if grounded → Answer / if not → Web Search → Regenerate
- Docs not relevant → **Web Search** (DuckDuckGo) → **Generate** → **Hallucination Check**

Data storage uses summary-based embeddings: text and images are chunked, summarized via Gemini, and indexed in ChromaDB. Retrieval returns original content via `MultiVectorRetriever`.

## Stack

- **LLM**: Google Gemini 1.5 Flash (routing/grading) + Pro (generation)
- **Embeddings**: Gemini `embedding-001`
- **Vector Store**: ChromaDB (persistent)
- **Orchestration**: LangGraph
- **Web Search**: DuckDuckGo (no API key needed)
- **UI**: Streamlit
- **DB**: SQLite

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```
GEMINI_API_KEY=your_key_here
```

Run:
```bash
streamlit run app.py
```

## Inspiration

Adaptive RAG: https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/
