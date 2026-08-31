# TalentFlow AI — Migration Plan

## Phase 0: Repository Audit + Baseline (THIS PHASE)

### Deliverables
- [x] `docs/API_INVENTORY.md` — All 22 endpoints documented
- [x] `docs/DATABASE_INVENTORY.md` — All 4 SQLite databases analyzed
- [x] `docs/AI_PIPELINE.md` — Full AI architecture documented
- [x] `docs/ARCHITECTURE.md` — Current system architecture
- [x] `docs/MIGRATION_PLAN.md` — This document
- [x] `tests/baseline/test_smoke.py` — Baseline smoke tests
- [ ] Run baseline tests and record results
- [ ] Verify frontend builds

### Findings

#### resume_classifier.pkl (444MB)
**Result**: NOT used at runtime. Only produced by `train_model.py`, never loaded by `app.py`, `ai_engine.py`, or any runtime module. `pickle.load` is never called. The current AI engine uses HuggingFace Inference API exclusively.

**Action**: Remove from normal git tracking. Keep local file. Document as historical training artifact.

#### SQLite Databases
| Database | Status | Rows | Action |
|----------|--------|------|--------|
| `hiring_system.db` | **AUTHORITATIVE** | 47 | Migrate to PostgreSQL |
| `ai_hiring.db` | Legacy, obsolete | 4 | Archive, do not migrate |
| `ats_database.db` | Legacy, obsolete | 3 | Archive, do not migrate |
| `flowats.db` | Empty (0 bytes) | 0 | Remove from git |

#### Data Files
| File | Purpose | Runtime? | Action |
|------|---------|----------|--------|
| `job_dataset.csv` | Training data for `train_model.py` | NO | Keep, add to `.gitignore` data section |
| `resumes.jsonl` | Resume samples for training | NO | Keep, add to `.gitignore` data section |
| `archive (3).zip` | Training corpus | NO | Remove from git, keep local |
| `ats_skills_dataset.py` | 800+ skill taxonomy | YES | Keep as source code |

---

## Phase 1: Security + Configuration + Git Cleanup

### 1.1 Centralized Configuration
- Create `backend/app/core/config.py` with Pydantic BaseSettings
- Nested settings groups: Database, Auth, AI, Storage, Email, Redis
- Fail-fast validation for production

### 1.2 Security Hardening
- Remove `"dev-secret-change-in-production"` JWT fallback
- Remove `password = "changeme"` default
- Add security headers (CSP, X-Frame-Options, HSTS, etc.)
- Remove `X-Powered-By` header
- Add rate limiting (Flask-Limiter)
- Add file upload MIME validation

### 1.3 Git Cleanup
- Remove `.db`, `.log`, `.zip` files from git tracking
- Update `.gitignore` comprehensively
- Remove orphaned HTML files from git
- Create root `.env.example`

### 1.4 Refresh Token Support
- Short-lived access tokens (15 min)
- Refresh tokens (7 days)
- Token revocation (Redis-backed when Redis is available, in-memory fallback)

---

## Phase 2: PostgreSQL + SQLAlchemy + Alembic

### 2.1 SQLAlchemy Models
- Create models matching current schema + new fields (UUID PKs, org_id, timestamps)
- Add `organizations` table
- Add `resumes` table (versioned)
- Add `match_results` table
- Add `audit_logs` table

### 2.2 Alembic Setup
- Initial migration generating full schema
- `alembic upgrade head` creates clean PostgreSQL database

### 2.3 Migration Script
- `scripts/migrate_sqlite_to_postgres.py`
- Reads from `hiring_system.db`
- Inserts into PostgreSQL with ID mapping
- Validates record counts after migration
- Does NOT delete SQLite files

### 2.4 Docker Compose
- PostgreSQL 16
- Redis 7
- Backend
- Frontend dev server

---

## Phase 3: Modular Backend

### 3.1 Flask App Factory
- `app/__init__.py` with `create_app(config_name)`
- Blueprint registration
- Middleware setup

### 3.2 API v1 Blueprints
- Route handlers become thin (validate → delegate → respond)
- Pydantic request/response schemas
- API versioning `/api/v1/`
- Backward-compatible aliases at `/api/` during transition

### 3.3 Service Layer
- Business logic extracted from route handlers
- Service functions are the single source of truth for operations

### 3.4 Repository Layer
- SQLAlchemy queries encapsulated in repository classes
- No raw SQL in services or routes

---

## Phase 4: AI Refactor + Async Workers

### 4.1 AI Module Separation
- `ai/resume_parser.py`, `ai/skill_extractor.py`, `ai/embeddings.py`, etc.
- Each module has a clean interface
- All existing logic preserved, just reorganized

### 4.2 Configurable Scoring
- Scoring weights stored in job config (JSONB)
- Every match result records the config version used

### 4.3 Explainability Service
- Detailed match explanations
- Strong/partial/missing skill breakdown

### 4.4 Async Processing (Celery + Redis)
- Resume processing queued
- Batch screening queued
- Email notifications queued

---

## Phase 5: Frontend Migration

### 5.1 Architecture Update
- features/ directory structure
- TanStack Query for server state
- Zustand for client state

### 5.2 New Pages
- Recruiter Dashboard (charts, metrics)
- Application Pipeline (Kanban)
- Candidate Profile (recruiter view)
- Resume Health Analyzer
- Job Recommendations

### 5.3 Design System
- Consistent Tailwind design tokens
- Reusable component library

---

## Phase 6: Testing + CI/CD + Docker

### 6.1 Test Suite
- Unit tests for AI modules
- Integration tests for API endpoints
- AI regression tests with evaluation dataset

### 6.2 CI/CD
- GitHub Actions for lint, test, build
- Security scanning (bandit, pip-audit, npm audit)

### 6.3 Docker
- Multi-stage Dockerfiles
- docker-compose for full stack

---

## Phase 7: Product Features + Polish

### 7.1 Notifications
- In-app notification center
- Email templates

### 7.2 Audit Logging
- All CRUD logged
- Activity timeline

### 7.3 Natural Language Search
- Intent-based search for candidates/jobs

### 7.4 Documentation
- Updated README
- CONTRIBUTING.md
- OpenAPI docs
