# TalentFlow AI — Database Inventory

## Authoritative Database

**`hiring_system.db`** (140 KB) — Schema v3, actively used by the application.

### Tables

| Table | Rows | Description |
|-------|------|-------------|
| `users` | 11 | Unified user table (email, password_hash, role) |
| `candidates` | 7 | Candidate profiles (user_id FK → users) |
| `recruiters` | 4 | Recruiter profiles (user_id FK → users) |
| `jobs` | 5 | Job postings (recruiter_id FK → recruiters) |
| `applications` | 3 | Job applications (job_id FK, candidate_id FK) |
| `chat_history` | 3 | AI chat messages (user_id FK → users) |
| `user_profiles` | 6 | Extended profile data (user_id FK → users) |
| `notifications` | 0 | Notification queue (user_id FK → users) |
| `hr_users` | 2 | Legacy HR auth table (kept for backward compat) |
| `schema_version` | 1 | Migration tracking (currently v3) |

### Key Relationships
```
users (11)
  ├── candidates (7) via user_id
  ├── recruiters (4) via user_id
  ├── user_profiles (6) via user_id
  ├── chat_history (3) via user_id
  └── notifications (0) via user_id

recruiters (4)
  └── jobs (5) via recruiter_id

jobs (5)
  └── applications (3) via job_id

candidates (7)
  └── applications (3) via candidate_id
```

### Data Quality Notes
- Several candidates have `extracted_skills = NULL` (never uploaded resume)
- Some jobs have `company_name = NULL`, `required_skills = NULL`
- `hr_users` table is legacy (2 rows) — data duplicated in `users` + `recruiters`
- User IDs range 1-11, candidate IDs 1-7, recruiter IDs 1-4, job IDs 3-7

---

## Legacy Databases (NOT Authoritative)

### `ai_hiring.db` (12 KB) — Legacy v1

| Table | Rows | Description |
|-------|------|-------------|
| `users` | 4 | Old flat user table (username, password, email, role) |

**Status**: Obsolete. Contains old user records that were migrated to `hiring_system.db` during schema v2→v3 migration. No other tables.

### `ats_database.db` (16 KB) — Legacy v0

| Table | Rows | Description |
|-------|------|-------------|
| `jobs` | 3 | Old job postings with different schema |
| `candidates` | 0 | Empty candidate table |

**Status**: Obsolete. Different schema (no foreign keys, different column names). Sample jobs are test data.

### `flowats.db` (0 bytes) — Empty

**Status**: Empty placeholder file. Never used.

---

## Migration Recommendations

1. **Source**: `hiring_system.db` is the only authoritative database
2. **Legacy DBs**: `ai_hiring.db`, `ats_database.db`, `flowats.db` can be archived but NOT auto-deleted
3. **Data to migrate**: All 11 users, 7 candidates, 4 recruiters, 5 jobs, 3 applications, 3 chat messages, 6 profiles
4. **Data quality**: Fix NULL company_names, clean up test data during migration
5. **IDs**: Use UUID in PostgreSQL, maintain a mapping table for old integer IDs if needed
