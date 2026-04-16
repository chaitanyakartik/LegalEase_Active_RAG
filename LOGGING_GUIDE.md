# LegalEase RAG Logging Guide

This guide explains how to view and understand the logging output from the LegalEase RAG system.

## Overview

Comprehensive logging has been added throughout the RAG pipeline to track:
- **File Ingestion**: What files are being processed, extracted, chunked, and stored
- **RAG Pipeline**: Each step of the question-answering flow
- **Vector Store Operations**: What documents are being retrieved and how they're being processed

## Log Output

Logs are written to two places simultaneously:

1. **Console Output**: Visible in your terminal/Streamlit interface
2. **Log Files**: Saved in `logs/` directory with timestamp

### Log File Location
```
logs/rag_YYYYMMDD_HHMMSS.log
```

Each time you run the application, a new log file is created.

## Understanding the Output

### File Ingestion Flow

When you upload a document, you'll see output like:

```
================================================================================
📥 STARTING FILE INGESTION
================================================================================
File: contract.pdf
Case ID: case_123
Source path: /path/to/contract.pdf
✓ File copied to: /path/to/uploads/case_123/contract.pdf
✓ Document registered with ID: doc_abc123
--------------------------------------------------------------------------------
📄 EXTRACTION: Extracting text and images...
✓ Text extracted: 45320 characters
✓ Images extracted: 3
--------------------------------------------------------------------------------
✂️  CHUNKING & SUMMARIZING: Processing extracted content...
✓ Text chunks: 12
✓ Image descriptions: 3
--------------------------------------------------------------------------------
🗂️  STORING: Adding to vector databases...
   Storing in collection: case_123
   ✓ Stored 12 text chunks (with embeddings)
   ✓ Stored 3 image descriptions (with embeddings)
   Storing in collection: all_cases
   ✓ Stored 12 text chunks (with embeddings)
   ✓ Stored 3 image descriptions (with embeddings)
================================================================================
✅ FILE INGESTION COMPLETE
================================================================================
```

### RAG Pipeline Flow

When you ask a question, you'll see:

```
================================================================================
🚀 STARTING RAG PIPELINE
================================================================================
Question: What are the key terms of the contract?
Category: Contract Law
Case ID: case_123
--------------------------------------------------------------------------------
🔀 QUESTION ROUTER: Analyzing question from category 'Contract Law'
   Question: What are the key terms of the contract?...
   ✓ Route Decision: LEGAL

🔍 MULTI-QUERY: Generating query variants for retrieval
   Generated 3 query variants:
   1. key terms contract definition...
   2. essential contract clauses...
   3. main provisions agreement...

📚 RETRIEVE: Fetching documents from case-specific vector store
   Query: 'key terms contract definition' → Found 4 similar documents
   Query: 'essential contract clauses' → Found 3 similar documents
   Query: 'main provisions agreement' → Found 2 similar documents
   ✓ Total unique documents retrieved: 5

⭐ GRADE DOCUMENTS: Evaluating relevance of 5 documents
   Doc 1: ✓ RELEVANT | Definitions section paragraph 1: In this agreement...
   Doc 2: ✗ NOT RELEVANT | General disclaimer text...
   Doc 3: ✓ RELEVANT | Key Terms section...
   Doc 4: ✓ RELEVANT | Scope and obligations...
   Doc 5: ✗ NOT RELEVANT | Footer and page numbers...
   ✓ Total relevant documents: 3/5

✍️  GENERATE: Creating response from graded documents
   Context sources: 3 docs + 0 web results
   Context length: 2847 characters
   ✓ Response generated: The key terms of the contract include...

🔐 HALLUCINATION CHECK: Verifying response is grounded in sources
   ✓ GROUNDED (retry count: 1)

--------------------------------------------------------------------------------
✅ RAG PIPELINE COMPLETE
Final response: The key terms of the contract include the definitions of core parties...
================================================================================
```

## Log Levels

The system uses these log levels:

- **INFO** (default): Normal operation messages, showing the flow of data
- **WARNING**: Issues that don't stop execution (e.g., failed web search, missing fields)
- **ERROR**: Serious problems that affect results

## Emoji Guide

The logs use emojis to make different stages easy to identify:

| Emoji | Stage | Meaning |
|-------|-------|---------|
| 📥 | Ingestion | File upload started |
| 📄 | Extraction | Text/image extraction |
| ✂️ | Chunking | Text segmentation |
| 🗂️ | Storage | Vector DB operations |
| ✅ | Complete | Process finished successfully |
| 🚀 | Start | RAG pipeline started |
| 🔀 | Router | Question classification |
| 💬 | Direct | Non-legal question (no RAG) |
| 🔍 | MultiQuery | Query variant generation |
| 📚 | Retrieve | Document retrieval |
| ⭐ | Grade | Document relevance checking |
| 🌐 | Web Search | Internet search for fallback |
| ✍️ | Generate | Response generation |
| 🔐 | Hallucination | Grounding verification |

## Viewing Logs

### View latest log in terminal
```bash
tail -f logs/rag_*.log  # Watch logs in real-time
```

### View all logs
```bash
ls -lt logs/  # List logs by date
cat logs/rag_YYYYMMDD_HHMMSS.log  # View a specific log
```

### Search logs
```bash
grep "RETRIEVE" logs/rag_*.log  # Find retrieval operations
grep "ERROR" logs/rag_*.log     # Find errors
```

## What to Look For

### When Documents Aren't Being Retrieved
Check the `RETRIEVE` section:
- Are query variants being generated?
- How many documents are found per query?
- Does `Total unique documents` match your expectations?

### When Responses Are Poor Quality
Check the `GRADE DOCUMENTS` section:
- Are relevant documents being marked as relevant?
- Are too many irrelevant documents included?
- Check `Total relevant documents` ratio

### When Responses Seem Made Up (Hallucinations)
Check the `HALLUCINATION CHECK` section:
- Is it marked as GROUNDED or not?
- Does `retry_count` indicate multiple retries?

### When Ingestion Fails
Check the `EXTRACTION` and `CHUNKING` sections:
- Did the file extract correctly?
- How many chunks were created?
- Were images found and described?

## Performance Insights

From the logs you can observe:

1. **Processing time**: Time between log messages indicates where delays occur
2. **Data volume**: Number of chunks, documents, images shows processing scope
3. **Relevance**: Ratio of relevant to total documents shows document quality
4. **Retrieval coverage**: Number of query variants and results shows search effectiveness

## Troubleshooting

If you're seeing unexpected behavior, the logs will help you identify where:

- **Documents aren't stored**: Check `STORING` section
- **Documents aren't found**: Check `RETRIEVE` section and vector store count
- **Wrong documents selected**: Check `GRADE DOCUMENTS` relevance decisions
- **Poor responses**: Check context used in `GENERATE` section
- **Hallucinations**: Check `HALLUCINATION CHECK` results

## Tips

1. **Keep recent logs**: The logs directory can grow; periodically archive old logs
2. **Search for issues**: Use `grep` to find specific problems across all logs
3. **Compare runs**: Compare logs from successful vs. failed queries to identify patterns
4. **Monitor in real-time**: Use `tail -f` when testing to watch the flow in real-time
