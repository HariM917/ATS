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

### 4a. Legacy Training Artifacts (backend/) — Pending Stage B Removal

> All legacy files are training-only. `pickle.load` is never called by any runtime module.
> They are kept until Stage B confirms the new pipeline is fully operational.

| File | Size | Type | Purpose | Runtime? | Stage B Action |
|------|------|------|---------|----------|----------------|
| `backend/resume_classifier.pkl` | 444MB | Training artifact | Old centroid+boosting classifier | **NO** | Remove after new model validated |
| `backend/job_dataset.csv` | 611KB | Training data | Fallback CSV for `train_model.py` | **NO** | Remove after new pipeline verified |
| `backend/resumes.jsonl` | 263KB | Training data | Legacy resume samples | **NO** | Remove (no code references it) |
| `backend/archive (3).zip` | 65MB | Training data | Primary training corpus for old `train_model.py` | **NO** | Remove after new pipeline verified |
| `backend/train_model.py` | 6KB | Legacy script | Old training script (hardcoded paths) | **NO** | Superseded by `scripts/train_model.py` |

### 4b. New Dataset Pipeline (data/) — Stage A Infrastructure

| File | Type | Purpose | Committed? |
|------|------|---------|------------|
| `data/raw/clean_resume_data.csv` | Source data | New resume dataset (awaiting upload) | No (gitignored) |
| `data/processed/resume_train.csv` | Processed | Training split | No (gitignored) |
| `data/processed/resume_validation.csv` | Processed | Validation split | No (gitignored) |
| `data/processed/resume_test.csv` | Processed | Frozen test split | No (gitignored) |
| `data/reports/quality_report.csv` | Report | Data quality metrics | No (gitignored) |
| `data/reports/class_distribution.csv` | Report | Category distribution | No (gitignored) |
| `data/reports/duplicates.csv` | Report | Duplicate record log | No (gitignored) |
| `data/dataset_manifest.json` | Metadata | Dataset version manifest | No (gitignored) |
| `data/DATASET_CARD.md` | Documentation | Dataset provenance, schema, limitations | **Yes** |

### 4c. Runtime Source Code (always kept)

| File | Size | Type | Purpose | Runtime? |
|------|------|------|---------|----------|
| `backend/ats_skills_dataset.py` | 22KB | Source code | 800+ skill taxonomy | **YES** |

---

## 5. Dataset Migration Pipeline (Stage A → B)

### Stage A: Structure Preparation (Complete)
```
backend/app/data/
├── __init__.py       ← package definition
├── loader.py         ← safe CSV loading, schema inspection
├── cleaner.py        ← text normalization, artifact removal
├── normalizer.py     ← role label + skill normalization
├── deduplicator.py   ← exact + near-dup detection
├── taxonomy.py       ← controlled category taxonomy (stub, populated in Stage B)
├── splitter.py       ← deterministic train/val/test split with leakage prevention
├── validator.py      ← schema + quality validation
└── report.py         ← quality_report.csv, class_distribution.csv, manifest

scripts/
├── build_dataset.py  ← full pipeline orchestrator
└── train_model.py    ← migrated training script (new dataset paths)
```

### Stage B: Dataset Processing (triggers after clean_resume_data.csv upload)
```
data/raw/clean_resume_data.csv
        ↓
python scripts/build_dataset.py
        ↓ schema inspection
        ↓ validation
        ↓ text cleaning
        ↓ duplicate detection
        ↓ role normalization
        ↓ train/val/test split
        ↓
data/processed/   ← resume_train.csv, resume_validation.csv, resume_test.csv
data/reports/     ← quality_report.csv, class_distribution.csv, duplicates.csv
data/dataset_manifest.json
        ↓
python scripts/train_model.py
        ↓ MPNet embeddings (all-mpnet-base-v2, 768D)
        ↓ NearestCentroid + HistGradientBoosting
        ↓ validation evaluation
        ↓
models/resume_classifier/v2/resume_classifier.pkl
models/resume_classifier/manifest.json
```

### Production Safety Constraint
The new dataset is **training infrastructure only**.
Production ATS candidate matching always operates on:
```
uploaded resume → resume parser → skill extraction → MPNet embedding → matching engine → ranking
```
Training data is never loaded during API request handling.

---

## 6. Refactoring Constraints

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
13. **DO NOT** use TF-IDF, hash vectors, or random vectors as substitutes for MPNet in production evaluation

---

## 7. 22-Class Occupational Classification & Recruiter Safety Engine (Phase V21 / V23 Production)

### Overview & Service Architecture
The **Occupational Classifier Service** (`backend/app/services/occupational_classifier.py`) implements the finalized Phase V21/V23 champion architecture for granular, multi-domain occupational classification across **22 standardized occupational classes**:

```
Resume Text / PDF Document
            │
            ▼
Occupational Classifier Service (v21-v23-final)
  ├── Lexical TF-IDF Sublinear Vectorizer (5,000 features)
  ├── 768-Dimensional MPNet Semantic Embeddings
  └── Calibrated Hybrid Model (CalibratedClassifierCV / Sigmoid)
            │
            ▼
Probability Simplex Over 22 Occupational Classes (Sum = 1.0)
  ├── Top-1 Prediction: Role & Confidence (P1)
  ├── Top-2 Runner-Up: Role & Confidence (P2)
  └── Top-2 Margin: ΔP = P1 - P2
            │
            ▼
Recruiter Safety Review Guard (Phase V23 Policy)
  ├── Low Confidence Rule: P1 < 0.40
  └── Thin Margin Rule: ΔP < 0.15
            │
            ▼
Structured JSON Response Contract
```

### The 22 Canonical Occupational Classes
The 22 verified occupational classes exclude the legacy non-occupational industry tags (`AUTOMOBILE` and `BPO`), which the Phase V20 census established possess zero genuine occupational practitioners:
1. `ACCOUNTANT`
2. `ADVOCATE`
3. `AGRICULTURE`
4. `APPAREL`
5. `ARTS`
6. `AVIATION`
7. `BANKING`
8. `BUSINESS-DEVELOPMENT`
9. `CHEF`
10. `CONSTRUCTION`
11. `CONSULTANT`
12. `DESIGNER`
13. `DIGITAL-MEDIA`
14. `ENGINEERING`
15. `FINANCE`
16. `FITNESS`
17. `HEALTHCARE`
18. `HR`
19. `INFORMATION-TECHNOLOGY`
20. `PUBLIC-RELATIONS`
21. `SALES`
22. `TEACHER`

### Production Response Contract
All endpoints integrating the service (`/api/v1/resumes/upload`, `/api/v1/matching/evaluate`, and `/api/v1/resumes/<id>/analysis`) adhere to the standard schema:

```json
{
  "predicted_role": "INFORMATION-TECHNOLOGY",
  "confidence": 0.6186,
  "runner_up_role": "ENGINEERING",
  "runner_up_confidence": 0.0670,
  "margin": 0.5516,
  "review_required": false,
  "review_reasons": [],
  "model_version": "v21-v23-final",
  "taxonomy_version": "22-class-occupational-v1"
}
```

### Recruiter Safety Rules (Phase V23 Policy)
To prevent automated rejection of candidates with interdisciplinary backgrounds or boundary careers (e.g. `TEACHER` with strong `ARTS` experience, or `ADVOCATE` in labor relations), the service executes the recruiter review guard:

```python
review_reasons = []
if confidence < 0.40:
    review_reasons.append(f"Low prediction confidence ({confidence:.2f} < 0.40)")
if margin < 0.15:
    review_reasons.append(f"Thin top-2 probability margin ({margin:.2f} < 0.15) between '{predicted_role}' and runner-up '{runner_up_role}'")

review_required = len(review_reasons) > 0
```
- **Operational Principle**: Candidates flagged with `review_required: true` are routed to human recruiter review queues instead of automated triage.
- **Empirical Grounding**: The Phase V23 error autopsy proved that 52.4% (11/21) of clean test errors exhibited thin margins ($\Delta P < 0.15$), and in 42.9% (9/21) of errors, the true role was the runner-up.

### Official Benchmarks & Generalization Registry

| Benchmark Track | Model Architecture | Evaluated Split | Evaluation Basis | Accuracy | Macro-Precision | Macro-Recall | Macro-F1 | Weighted-F1 |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Track 1: Legacy Benchmark** | Phase V19 Champion | Validation (`n=248`) | Original 24-Class | 90.32% | 84.44% | 85.31% | 84.46% | 89.62% |
| **Track 1: Legacy Benchmark** | Phase V19 Champion | **Test (`n=248`)** | **Original 24-Class** | **85.89%** | **83.62%** | **79.99%** | **79.77%** | **84.84%** |
| **Track 2: Primary Benchmark**| Phase V21 22-Class | Validation (`n=248`) | Clean 22-Class | **91.53%** | **90.56%** | **92.05%** | **90.12%** | **91.86%** |
| **Track 2: Primary Benchmark**| Phase V21 22-Class | **Test (`n=242`)** | **Original 22-Class** | **87.60%** | **88.52%** | **86.13%** | **86.05%** | **87.18%** |
| **Clean Test Stratum** | Phase V21 22-Class | **Test Clean (`n=200`)** | **Verified Clean** | **89.50%** | — | — | — | — |
| *Audited Sensitivity View* | Phase V21 22-Class | Test Audited (`n=248`) | Heuristic Audit | 76.61% | 77.78% | 78.18% | 75.89% | 76.38% |

*Note: The Five-Gate $\ge 90.0\%$ target was achieved on the validation set in Phase V21; the official unseen test benchmark generalizes at 87.60% Accuracy / 86.05% Macro-F1, with 89.50% accuracy on verified clean resumes (93.50% forensic adjusted occupational accuracy).*

