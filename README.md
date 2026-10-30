# TalentFlow AI — Enterprise SaaS Applicant Tracking System

[![CI Pipeline](https://github.com/HariM917/ATS/actions/workflows/ci.yml/badge.svg)](https://github.com/HariM917/ATS/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)](https://redis.io)

**TalentFlow AI** is a production-grade, multi-tenant SaaS Applicant Tracking System powered by advanced NLP, 768-dimensional MPNet sentence embeddings, calibrated ATS match scoring, and a RAG (Retrieval-Augmented Generation) career coach.

---

## Key Features

- **22-Class Occupational Engine & Recruiter Safety Guard**: Phase V21/V23 production architecture classifying resumes across 22 canonical occupational categories with probability calibration, runner-up role detection, and human-in-the-loop review routing (`confidence < 0.40` or `margin < 0.15`).
- **Multi-Tenant Architecture**: Organization-level isolation, RBAC (Candidates, Recruiters, Admins), and audit logging.
- **Enterprise Security**: Short-lived JWT access tokens, rotating refresh tokens, token revocation list, rate limiting, and strict security headers.
- **Explainable AI Matching**: Multidimensional scoring (Semantic Relevance, Skill Coverage, Experience, Education, Projects) with actionable strengths & improvement feedback.
- **Multi-Layer Resume Parser**: PyMuPDF, pdfplumber, pdfminer, OCR fallback, and structured section extraction.
- **8-Stage Kanban Pipeline**: `applied` → `screening` → `shortlisted` → `interview` → `technical` → `final` → `offer` → `hired`.
- **RAG Career Coach**: FAISS cosine vector search + BM25 hybrid retrieval grounded with Mistral-7B LLM synthesis.
- **Async Workers**: Redis & Celery for offloading document processing, batch AI screening, and email notifications.

---

## System Architecture

```
React 18 + TypeScript + Tailwind CSS (Vercel)
               │ (HTTPS + Bearer Token + Request ID)
               ▼
   Flask REST API Factory (/api/v1/)
 ┌─────────────┼─────────────┐
 ▼             ▼             ▼
PostgreSQL   Redis     Celery Workers
 (Data)     (Broker)   (Async Parsing)
                             │
                      AI Engine & RAG
                  (MPNet 768D + FAISS)
```

---

## Quick Start (Docker Compose)

The easiest way to run the complete ecosystem locally:

```bash
docker-compose up -d --build
```

- **Frontend**: `http://localhost:80`
- **Backend API**: `http://localhost:5000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## Local Development Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

pip install -r requirements.txt
pip install pydantic-settings flask-limiter

# Initialize and migrate SQLite / PostgreSQL schema
python -m alembic upgrade head
python scripts/migrate_sqlite_to_postgres.py

# Run development server
python run.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

## 22-Class Occupational Engine & Benchmark Registry

TalentFlow AI integrates an audited **22-Class Occupational Classifier** (`backend/app/services/occupational_classifier.py`) replacing legacy heuristic keyword matchers. The engine categorizes candidates across 22 canonical occupational domains (excluding legacy non-occupational industry tags: `AUTOMOBILE` and `BPO`), producing calibrated class probabilities, runner-up role detection, and human-in-the-loop review routing.

### Official Project Benchmark Registry

> *"The final 22-class occupational resume classification system achieved **87.60% accuracy, 88.52% macro-precision, 86.13% macro-recall, 86.05% macro-F1, and 87.18% weighted-F1** on the unseen test set. On 200 independently verified clean test resumes, it achieved **89.50% accuracy**. Forensic analysis identified eight additional previously undetected dataset-label conflicts, yielding an **adjusted occupational accuracy of 93.50%** on the clean subset."*

| Benchmark Track | Model Architecture | Evaluated Split | Evaluation Basis | Accuracy | Macro-Precision | Macro-Recall | Macro-F1 | Weighted-F1 |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Track 1: Legacy Benchmark** | Phase V19 Champion | Validation (`n=248`) | Original 24-Class | 90.32% | 84.44% | 85.31% | 84.46% | 89.62% |
| **Track 1: Legacy Benchmark** | Phase V19 Champion | **Test (`n=248`)** | **Original 24-Class** | **85.89%** | **83.62%** | **79.99%** | **79.77%** | **84.84%** |
| **Track 2: Primary Benchmark**| Phase V21 22-Class | Validation (`n=248`) | Clean 22-Class | **91.53%** | **90.56%** | **92.05%** | **90.12%** | **91.86%** |
| **Track 2: Primary Benchmark**| Phase V21 22-Class | **Test (`n=242`)** | **Original 22-Class** | **87.60%** | **88.52%** | **86.13%** | **86.05%** | **87.18%** |
| **Clean Test Stratum** | Phase V21 22-Class | **Test Clean (`n=200`)** | **Verified Clean** | **89.50%** | — | — | — | — |
| *Audited Sensitivity View* | Phase V21 22-Class | Test Audited (`n=248`) | Heuristic Audit | 76.61% | 77.78% | 78.18% | 75.89% | 76.38% |

### Recruiter Review Safety Policy
To protect non-traditional, multi-disciplinary candidates from automated exclusion, the engine routes uncertain profiles directly to human recruiter review:
- **Trigger Rule**: `review_required = (confidence < 0.40) OR (margin < 0.15)`
- **Behavior**: Flagged resumes are surfaced with runner-up competencies and confidence margins for human recruiter decision, ensuring zero arbitrary disqualification.

---

## Testing & Quality

Run the test suite:

```bash
# Unit, Service, and Occupational Classifier Tests
python -m pytest tests/unit/ -v
```

---

## API Endpoints Overview

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register Candidate or Recruiter |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain Access + Refresh Tokens |
| `POST` | `/api/v1/auth/refresh` | Rotate access token |
| `POST` | `/api/v1/resumes/upload` | Upload & parse resume with 22-class occupational classification |
| `GET` | `/api/v1/resumes/my-resumes` | Retrieve authenticated candidate's versioned resumes |
| `GET` | `/api/v1/resumes/<id>/analysis` | Get skills, sections, ATS health, and occupational classification |
| `GET` | `/api/v1/jobs` | Browse active job listings |
| `POST` | `/api/v1/jobs` | Post new job (Recruiter RBAC) |
| `POST` | `/api/v1/applications/<id>/stage` | Update Kanban pipeline stage |
| `POST` | `/api/v1/matching/evaluate` | Multidimensional resume-to-JD match with occupational prediction |
| `POST` | `/api/v1/chat` | RAG Career Assistant AI chat |
| `GET` | `/api/v1/analytics/recruiter` | Hiring funnels and score distributions |
| `GET` | `/api/v1/system/health` | Service healthcheck ping |

