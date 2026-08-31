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

---

## Testing & Quality

Run the test suite:

```bash
# Baseline smoke tests + Unit & Integration tests
pytest tests/baseline/ tests/unit/ -v
```

---

## API Endpoints Overview

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register Candidate or Recruiter |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain Access + Refresh Tokens |
| `POST` | `/api/v1/auth/refresh` | Rotate access token |
| `GET` | `/api/v1/jobs` | Browse active job listings |
| `POST` | `/api/v1/jobs` | Post new job (Recruiter RBAC) |
| `POST` | `/api/v1/applications/<id>/stage` | Update Kanban pipeline stage |
| `POST` | `/api/v1/matching/evaluate` | Multidimensional resume-to-JD match score |
| `POST` | `/api/v1/chat` | RAG Career Assistant AI chat |
| `GET` | `/api/v1/analytics/recruiter` | Hiring funnels and score distributions |
| `GET` | `/api/v1/system/health` | Service healthcheck ping |
