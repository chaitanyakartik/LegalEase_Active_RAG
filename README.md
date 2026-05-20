# LegalEase — Advanced AI Legal Assistant

An enterprise-grade AI-powered legal assistant with cutting-edge RAG capabilities for comprehensive legal analysis, precedent research, and document drafting.

## Advanced RAG Pipeline with Multiple Enhancements

### Multi-Stage Intelligent Retrieval (Hyde + Raptor + Query Expansion)
Question → **Question Analysis** (legal/general routing) → **Enhanced MultiQuery** (legal expansion + jurisdiction) → **Hyde Retrieval** (hypothetical answers) + **Raptor Retrieval** (hierarchical clustering) → **Multi-Modal Enhancement** → **Grade Documents**
- **Hyde**: Generates hypothetical legal answers to find semantically similar documents
- **Raptor**: Hierarchical clustering for organized, context-aware retrieval
- **Query Expansion**: Adds legal concepts, terminology, and jurisdiction context
- **Multi-Modal**: Enhanced image-text integration for visual legal evidence
- **Confidence Scoring**: Rates response reliability (1-10 scale)
- Docs relevant → **Generate** → **Hallucination Check** → if grounded → Answer / if not → Web Search → Regenerate
- Docs not relevant → **Web Search** (DuckDuckGo) → **Generate** → **Hallucination Check**

### Novel Enterprise Features
- **Intelligent Legal Matching**: Finds precedents by legal principle, not keywords
- **Jurisdiction Awareness**: Context-aware analysis for India, USA, UK, and international law
- **Multi-Modal Evidence**: Integrates visual documents (contracts, charts) with text analysis
- **Confidence Indicators**: Users see reliability scores for each response
- **Query Enhancement**: Automatically expands queries with legal terminology and concepts
- **Hierarchical Organization**: Documents clustered by legal themes for better context
- **Quota-Free Operation**: Uses Groq/Ollama with local embeddings
- **Hallucination Prevention**: Multi-layer validation ensures grounded responses

### Advanced Analysis Suite
- **Citation Network Analysis**: Maps citation relationships between legal documents and identifies landmark cases
- **Counterfactual Legal Analysis**: Explores "what if" scenarios and their legal implications
- **Automated Research Reports**: Generates professional legal research memoranda
- **Case Brief Generator**: Creates structured, professional case briefs
- **Legal Risk Assessment**: Evaluates case strength and identifies vulnerabilities

Data storage uses local embeddings: text and images are chunked, processed via custom Raptor tree, and indexed in ChromaDB. Retrieval combines multi-query variants with Hyde hypothetical embeddings and jurisdiction context.

## Features

- **AI Legal Analysis** — Issue summary, potential violations, missing facts, next steps, risk factors
- **Precedent Search** — Find similar judgments and relevant case law
- **Document Summarization** — Key clauses, obligations, deadlines, and red flags from uploaded docs
- **Drafting Assistant** — Generate legal notices, complaints, response letters, and more
- **Case Timeline** — Track hearings, filings, deadlines, and AI-suggested milestones
- **Cross-case Search** — Ask questions across all uploaded documents
- **Confidence Scoring** — Color-coded reliability indicators (1-10 scale)
- **Jurisdiction Awareness** — Automatic detection and context for different legal systems
- **Multi-Modal Analysis** — Enhanced processing of images, charts, and visual evidence
- **Citation Network Analysis** — Map citation relationships and identify landmark cases
- **Counterfactual Analysis** — Explore "what if" scenarios and legal implications
- **Automated Research Reports** — Generate professional legal research memoranda
- **Case Brief Generator** — Create structured, professional case briefs

## Stack

- **LLM**: Groq (compound-mini, free tier) + Ollama (Mistral, local)
- **Embeddings**: Custom local embeddings (quota-free)
- **Vector Store**: ChromaDB (persistent)
- **Retrieval**: Custom Raptor (hierarchical) + Hyde (hypothetical) + Query Expansion
- **Enhancements**: Confidence Scoring, Jurisdiction Awareness, Multi-Modal Analysis
- **Orchestration**: LangGraph
- **Web Search**: DuckDuckGo (no API key needed)
- **UI**: Streamlit with confidence indicators
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

![WORK](https://github.com/user-attachments/assets/b36480f1-84db-4167-b625-49f39803c6d6)

# --- Advanced Analyses ---

def save_advanced_analysis(case_id: str, analysis_type: str, title: str, content: str) -> str:
    analysis_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO advanced_analyses (id, case_id, analysis_type, title, content) VALUES (?, ?, ?, ?, ?)",
            (analysis_id, case_id, analysis_type, title, content)
        )
    return analysis_id

def get_advanced_analyses(case_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM advanced_analyses WHERE case_id = ? ORDER BY created_at DESC", (case_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def delete_advanced_analysis(analysis_id: str):
    with _conn() as conn:
        conn.execute("DELETE FROM advanced_analyses WHERE id = ?", (analysis_id,))

CREATE TABLE IF NOT EXISTS advanced_analyses (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,  -- e.g., 'citation', 'counterfactual', 'memo', 'brief'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);
