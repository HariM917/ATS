# TalentFlow AI — AI Pipeline Documentation

## Overview

The AI engine uses **HuggingFace Inference API** (not local models) for all embedding and LLM operations. The pipeline has two main branches:

1. **ATS Matching Engine** — Resume-to-JD scoring
2. **RAG Career Coach** — AI-powered chatbot

---

## 1. ATS Matching Pipeline

### Architecture
```
Resume File (PDF/DOCX/TXT)
       ↓
Multi-Layer Parser
  ├── PyMuPDF (Layer 1)
  ├── pdfplumber (Layer 2)
  ├── pdfminer (Layer 3)
  └── OCR/Tesseract (Layer 4)
       ↓
Raw Text (validated: min 200 chars, 30 words)
       ↓
┌──────┴──────┐
│  Section    │  Full Text
│  Extraction │  Analysis
│  (skills,   │
│  experience,│
│  projects,  │
│  education) │
└──────┬──────┘
       ↓
Triple-Layer Skill Extraction
  ├── Regex matching (800+ taxonomy)
  ├── Synonym expansion (50+ abbreviations)
  └── Fuzzy matching (RapidFuzz, cutoff 88%)
       ↓
Semantic Role Prediction
  (15 roles × embedding similarity)
       ↓
Experience Extraction
  (regex patterns + date range analysis)
       ↓
HF Embedding Generation
  (all-mpnet-base-v2, 768D, with cache)
       ↓
Scoring Engine (weighted sum)
  ├── Semantic similarity: 25%
  ├── Skill match: 40%
  ├── Projects relevance: 15%
  ├── Experience alignment: 10%
  └── Education relevance: 10%
       ↓
Sigmoid Calibration
  (1 / (1 + exp(-8*(raw - 0.35))))
       ↓
Validated Result (0-95% range)
```

### Key Functions (ai_engine.py)
| Function | Lines | Purpose |
|----------|-------|---------|
| `extract_text()` | 449-489 | Multi-layer PDF/DOCX/TXT parser |
| `extract_sections()` | 496-525 | Regex-based section splitting |
| `extract_skills()` | 539-585 | Triple-layer skill extraction |
| `get_semantic_matches()` | 588-613 | Embedding-based skill matching |
| `fuzzy_match_skills()` | 616-636 | Combined fuzzy + semantic skill matching |
| `extract_years_of_experience()` | 643-681 | Experience year detection |
| `detect_role_from_resume()` | 706-736 | Semantic role prediction (top-3) |
| `batch_compute_match_score()` | 840-996 | Main scoring pipeline |
| `compute_match_score()` | 999-1006 | Single resume wrapper |
| `validate_ats_result()` | 1013-1078 | NaN/null production guard |
| `extract_resume_data()` | 1181-1256 | Full extraction for upload |
| `categorize_skills()` | 1149-1174 | Skill → category mapping |
| `get_embeddings_safe()` | 275-347 | HF API embedding with retry |

### Models & Configuration
- **Embedding Model**: `sentence-transformers/all-mpnet-base-v2` (768D)
- **Embedding API**: HuggingFace Inference API (remote, not local)
- **Embedding Cache**: In-memory dict, max 500 entries
- **Skill Taxonomy**: 800+ skills across 15+ categories
- **Role Taxonomy**: 15 role definitions with descriptions
- **Scoring Weights**: Hard-coded in `batch_compute_match_score()`
- **Calibration**: Sigmoid stretch with center at 0.35

### resume_classifier.pkl (444MB)
- **Created by**: `train_model.py` using SentenceTransformer local model + HistGradientBoosting
- **Loaded at runtime**: NO — `pickle.load` is never called in any runtime module
- **Status**: Training artifact only. Not used by the current AI engine.
- **Contents**: Centroid classifier + Boosting classifier + BERTVectorizer (local model)
- **History**: Was the original approach; replaced by HF Inference API for production

---

## 2. RAG Chatbot Pipeline

### Architecture
```
User Query
     ↓
Query Preprocessing
  (normalize, expand abbreviations, clean)
     ↓
Fast Path Check
  (greeting/help → instant response)
     ↓
Cache Lookup (FastCache)
  ├── Exact match (O(1))
  └── Fuzzy match (RapidFuzz, threshold 90%)
     ↓
Intent & Domain Detection
  (keyword-based scoring across 7 domains + 5 intents)
     ↓
FAISS Index Rebuild (if stale, every 10 min)
     ↓
Hybrid Retrieval
  ├── Semantic: FAISS cosine search (threshold 0.35)
  └── Lexical: BM25-style keyword scoring
     ↓
RRF Merge (Reciprocal Rank Fusion)
     ↓
Reranking (tag bonus + keyword overlap)
     ↓
MMR Diversity (deduplicate near-identical chunks)
     ↓
LLM Generation (Mistral-7B-Instruct-v0.2)
  ├── System prompt with grounding rules
  ├── Last 3 conversation turns
  └── Retrieved context injection
     ↓
Fallback (if LLM fails)
  (synthesize from retrieved chunks or knowledge base)
     ↓
Persist to DB + Cache
     ↓
Observability Log
```

### Key Functions (chatbot_rag.py)
| Function | Lines | Purpose |
|----------|-------|---------|
| `preprocess_query()` | 298-317 | Abbreviation expansion, normalization |
| `FastCache.get()` | 336-356 | Zero-latency exact + fuzzy cache |
| `check_fast_path()` | 390-398 | Instant greeting/help responses |
| `detect_intent_and_domain()` | 422-452 | Keyword-based classification |
| `RAGManager.rebuild_index()` | 489-599 | FAISS index from KB + DB data |
| `RAGManager.search()` | 624-703 | Hybrid semantic + lexical retrieval |
| `get_llm_generation()` | 745-780 | Mistral-7B chat completion |
| `fallback_response()` | 786-847 | Context synthesis without LLM |
| `get_response()` | 875-1014 | Main pipeline orchestrator |
| `warm_rag_index()` | 863-872 | Pre-build index at startup |

### Knowledge Base
- 65+ curated knowledge items across 13 categories
- Categories: resume (structure, content, mistakes), interview (behavioral, technical, remote), data science, ML, backend, frontend, devops, soft skills, salary, LinkedIn, cover letter, career transition, freelancing
- Dynamic data: live jobs + application scores from database

### Models & Configuration
- **Embedding Model**: Same as ATS engine (`all-mpnet-base-v2`)
- **LLM**: `mistralai/Mistral-7B-Instruct-v0.2` via HuggingFace Inference API
- **FAISS Index**: `IndexFlatIP` (inner product on normalized vectors = cosine similarity)
- **Relevance Threshold**: 0.35 minimum similarity
- **Cache**: In-memory FastCache (max 200 entries, fuzzy threshold 90%)
- **Refresh Interval**: 10 minutes for FAISS index rebuild
- **LLM Config**: max_tokens=600, temperature=0.4

---

## 3. Embedding Architecture

Both ATS and RAG share the same embedding infrastructure:
- **Provider**: HuggingFace Inference API (cloud)
- **Model**: `sentence-transformers/all-mpnet-base-v2`
- **Dimension**: 768
- **Cache**: In-memory dict (shared within `ai_engine.py`, separate in `chatbot_rag.py`)
- **Retry**: 3 attempts with exponential backoff
- **Fallback**: Zero vectors on failure (graceful degradation)
- **Token**: `HF_TOKEN` environment variable

---

## 4. Data Files

| File | Size | Type | Purpose | Runtime? |
|------|------|------|---------|----------|
| `resume_classifier.pkl` | 444MB | Training artifact | Old centroid+boosting classifier | NO |
| `job_dataset.csv` | 611KB | Training data | Resume text corpus for `train_model.py` | NO |
| `resumes.jsonl` | 263KB | Training data | Resume samples | NO |
| `archive (3).zip` | 65MB | Training data | Compressed resume corpus | NO |
| `ats_skills_dataset.py` | 22KB | Source code | 800+ skill taxonomy | YES |

---

## 5. Refactoring Constraints

When refactoring the AI pipeline:

1. **PRESERVE** the multi-layer parsing (PyMuPDF → pdfplumber → pdfminer → OCR)
2. **PRESERVE** the 800+ skill taxonomy and triple-layer extraction
3. **PRESERVE** the HuggingFace API integration (not replace with local models)
4. **PRESERVE** the embedding caching mechanism
5. **PRESERVE** the RAG pipeline with FAISS + hybrid retrieval
6. **PRESERVE** the retry/fallback patterns
7. **IMPROVE** by making scoring weights configurable (not hard-coded)
8. **IMPROVE** by adding model versioning to results
9. **IMPROVE** by adding explainability service
10. **IMPROVE** by separating RAG and ATS FAISS indexes
11. **DO NOT** remove the knowledge base content
12. **DO NOT** change the embedding model without regression testing
