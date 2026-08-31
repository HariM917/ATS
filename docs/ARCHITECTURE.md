# TalentFlow AI — Architecture (Current State)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                          │
│                                                                 │
│  React 18 + TypeScript + Tailwind CSS v4 + Vite               │
│                                                                 │
│  Pages:                                                         │
│  ├── LoginPage          (auth)                                  │
│  ├── CandidateDashboard (resume upload, skills, matching)       │
│  ├── HRDashboard        (batch screening, rankings)             │
│  ├── JobManagement      (job CRUD, applications)                │
│  ├── JobBrowse          (job feed, apply)                       │
│  ├── ChatPage           (RAG AI assistant)                      │
│  ├── SettingsPage       (profile management)                    │
│  ├── TechQuiz           (quiz game)                             │
│  └── PuzzleGame         (puzzle game)                           │
│                                                                 │
│  State: localStorage (auth), useState (all data)               │
│  API: centralized fetch client (services/api.ts)               │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS + JWT Bearer Token
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Render)                           │
│                                                                 │
│  Flask + Gunicorn + Python 3.11                                │
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐            │
│  │ app.py   │  │ job_manager  │  │ auth_utils.py │            │
│  │ (routes) │  │ (blueprint)  │  │ (JWT/RBAC)    │            │
│  └────┬─────┘  └──────┬───────┘  └───────────────┘            │
│       │               │                                        │
│  ┌────┴───────────────┴────┐                                   │
│  │     db_manager.py       │                                   │
│  │  (SQLite + migrations)  │                                   │
│  └─────────────────────────┘                                   │
│                                                                 │
│  ┌──────────────────────────────────────────────┐              │
│  │              AI Layer                         │              │
│  │                                               │              │
│  │  ai_engine.py          chatbot_rag.py        │              │
│  │  ├── Resume Parser     ├── Knowledge Base     │              │
│  │  ├── Skill Extractor   ├── FAISS Index        │              │
│  │  ├── Role Predictor    ├── RAG Manager        │              │
│  │  ├── Scoring Engine    ├── LLM (Mistral-7B)   │              │
│  │  └── Embeddings (HF)   └── FastCache          │              │
│  └──────────────────────────────────────────────┘              │
│                                                                 │
│  External APIs:                                                 │
│  ├── HuggingFace (embeddings + LLM)                            │
│  └── Gmail SMTP (notifications)                                │
│                                                                 │
│  Storage:                                                       │
│  ├── SQLite (hiring_system.db)                                 │
│  └── Local filesystem (uploads/)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
app.py
  ├── db_manager        (database CRUD)
  ├── ai_engine         (matching, extraction)
  ├── chatbot_rag       (RAG chatbot)
  ├── auth_utils        (JWT, decorators)
  └── job_manager       (Blueprint)
        ├── db_manager
        ├── ai_engine
        └── auth_utils

ai_engine
  ├── ats_skills_dataset (skill taxonomy)
  ├── huggingface_hub   (embeddings API)
  ├── rapidfuzz         (fuzzy matching)
  └── scikit-learn      (TF-IDF, cosine)

chatbot_rag
  ├── db_manager        (chat history, jobs, apps)
  ├── huggingface_hub   (embeddings + LLM)
  ├── faiss             (vector search)
  └── rapidfuzz         (fuzzy cache)

db_manager
  ├── sqlite3           (database)
  └── werkzeug.security (password hashing)
```

## Roles & Permissions

| Role | Capabilities |
|------|-------------|
| `candidate` | Register, login, upload resume, view skills, match against JD, browse jobs, apply, chat, view profile |
| `hr` | Register, login, create/delete jobs, view applications, change status, batch screen, chat |
| `admin` | Same as `hr` + clear_data (with admin secret) |

## Deployment

| Component | Platform | URL |
|-----------|----------|-----|
| Frontend | Vercel | `https://ats917.vercel.app` |
| Backend | Render | `https://ats-ibwo.onrender.com` |
| Keep-alive | Render Cron | Every 10 minutes |
