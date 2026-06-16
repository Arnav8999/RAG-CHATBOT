# Design Decisions

This document explains the key architectural and engineering decisions made while building the Document Assistant system.

---

# 1. Structured PDF Extraction with Docling

## Decision

Use Docling instead of plain PDF text extraction.

## Why?

Technical manuals contain:

* Headings
* Tables
* Figures
* Captions
* Hierarchical sections

Traditional PDF extraction often loses this structure, making retrieval less accurate.

Docling preserves document semantics and produces structured markdown that is easier to index and search.

## Tradeoff

* Slightly slower processing
* Higher memory usage

In exchange, retrieval quality improves significantly.

---

# 2. Parent–Child Chunking

## Decision

Use two levels of chunking:

| Chunk Type   | Size            |
| ------------ | --------------- |
| Parent Chunk | 1500 characters |
| Child Chunk  | 300 characters  |

## Why?

Large chunks provide context.

Small chunks improve retrieval precision.

The system retrieves child chunks but expands them back to parent chunks before sending context to the LLM.

## Benefit

Balances retrieval accuracy and answer completeness.

---

# 3. Semantic Search using FAISS

## Decision

Use FAISS with BGE embeddings.

## Why?

Users often phrase questions differently than the wording used in manuals.

Example:

**User Query**

```text
What is the sound card?
```

**Manual**

```text
Audio Controller
```

Semantic embeddings allow the system to retrieve relevant content based on meaning rather than exact wording.

## Benefit

Improved retrieval for natural language questions.

---

# 4. Keyword Search using BM25

## Decision

Use BM25 alongside vector search.

## Why?

Technical manuals contain many exact identifiers:

* eDP cable
* I/O-board FPC cable
* ALC3329
* Service Tag
* Express Service Code

Keyword-based retrieval performs well for these terms.

## Benefit

Improved retrieval for highly specific technical queries.

---

# 5. Hybrid Retrieval

## Decision

Combine FAISS and BM25 retrieval results.

## Why?

Each retrieval method has different strengths:

### FAISS

* Semantic understanding
* Natural language queries

### BM25

* Exact keyword matching
* Technical identifiers

Combining both improves recall and robustness.

## Benefit

Better retrieval performance across a wider range of query types.

---

# 6. Cross-Encoder Reranking

## Decision

Use a Cross-Encoder model after retrieval.

Model:

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

## Why?

Initial retrieval can return partially relevant chunks.

The reranker evaluates:

```text
Query + Chunk
```

together and assigns a relevance score.

## Benefit

Improved precision and reduced retrieval noise.

---

# 7. Context Expansion

## Decision

Expand retrieved child chunks back to their parent documents.

## Why?

Retrieved chunks may only contain a portion of the information needed to answer a question.

Parent expansion restores surrounding context.

## Benefit

Produces more complete and coherent answers.

---

# 8. Separate Image Retrieval Pipeline

## Decision

Maintain a dedicated image indexing pipeline.

## Why?

Many technical questions require visual information.

Examples:

```text
Where is the battery located?
```

```text
Show me the system board.
```

Text retrieval alone cannot answer these effectively.

Images are extracted, captioned, embedded, and indexed separately.

## Benefit

Supports multimodal question answering.

---

# 9. Metadata-Driven Retrieval

## Decision

Store metadata alongside indexed chunks.

Metadata includes:

* Source document
* Parent ID
* Section name
* Content type
* Parser information

## Why?

Metadata enables:

* Context expansion
* Source attribution
* Debugging
* Future filtering capabilities

## Benefit

Improved maintainability and traceability.

---

# 10. Retrieval-Augmented Generation (RAG)

## Decision

Use Retrieval-Augmented Generation instead of relying solely on the LLM.

## Why?

The language model does not contain knowledge of proprietary manuals.

Relevant document context must be retrieved and supplied at runtime.

## Benefit

* Reduced hallucinations
* Document-grounded responses
* Support for new documents without retraining

---

# 11. Hallucination Prevention

## Decision

Restrict the model to retrieved context.

## Why?

Technical documentation requires factual accuracy.

The model is instructed to:

* Answer only from provided context
* Avoid assumptions
* Refuse unsupported questions

## Benefit

More trustworthy responses.

---

# 12. Persisted Indexes

## Decision

Save generated indexes to disk.

Stored artifacts include:

* FAISS index
* BM25 index
* Parent document store

## Why?

Generating embeddings is computationally expensive.

Persisting indexes avoids rebuilding them on every startup.

## Benefit

Faster application startup and lower processing costs.

---

# Future Improvements

Potential enhancements include:

* Exact page-level citations
* Table-aware retrieval
* Metadata filtering
* Query rewriting
* Evaluation dashboard
* Multimodal embeddings
* Access control and user permissions

---

# Summary

The system is designed around a simple principle:

> Retrieval quality drives answer quality.

The architecture combines structured document extraction, hybrid retrieval, reranking, context expansion, and multimodal support to provide accurate, source-grounded answers from technical documentation.
