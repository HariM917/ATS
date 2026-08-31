# TalentFlow AI — API Inventory

All existing API endpoints as of the current codebase.

## Authentication

| Method | Endpoint | Auth | Handler | Frontend Usage |
|--------|----------|------|---------|----------------|
| POST | `/api/login` | None | `app.py:login()` | `LoginPage.tsx` |
| POST | `/api/register` | None | `app.py:register()` | `LoginPage.tsx` |
| POST | `/api/logout` | None | `app.py:logout()` | `App.tsx:handleSignOut` |

## Profile

| Method | Endpoint | Auth | Handler | Frontend Usage |
|--------|----------|------|---------|----------------|
| GET | `/api/profile` | Optional JWT | `app.py:profile()` | `SettingsPage.tsx` |
| PUT | `/api/profile` | Optional JWT | `app.py:profile()` | `SettingsPage.tsx` |

## Resume & AI

| Method | Endpoint | Auth | Handler | Frontend Usage |
|--------|----------|------|---------|----------------|
| POST | `/api/upload` | JWT | `app.py:upload_file()` | `CandidateDashboard.tsx` |
| POST | `/api/upload_and_extract` | JWT | `app.py:upload_and_extract()` | `CandidateDashboard.tsx` |
| GET | `/api/resume/skills` | JWT | `app.py:get_resume_skills()` | `CandidateDashboard.tsx` |
| POST | `/api/candidate/match` | JWT | `app.py:candidate_match()` | `CandidateDashboard.tsx` |
| POST | `/api/process_resumes` | HR JWT | `app.py:process_resumes()` | `HRDashboard.tsx` |

## Jobs (Blueprint: `job_bp`)

| Method | Endpoint | Auth | Handler | Frontend Usage |
|--------|----------|------|---------|----------------|
| GET | `/api/jobs` | HR JWT | `job_manager.py:manage_jobs()` | `JobManagement.tsx` |
| POST | `/api/jobs` | HR JWT | `job_manager.py:manage_jobs()` | `JobManagement.tsx` |
| DELETE | `/api/jobs/<id>` | HR JWT | `job_manager.py:delete_job()` | `JobManagement.tsx` |
| GET | `/api/all_jobs` | None | `job_manager.py:get_all_jobs()` | `JobBrowse.tsx` |
| POST | `/api/jobs/<id>/apply` | Candidate JWT | `job_manager.py:apply_job()` | `JobBrowse.tsx` |
| GET | `/api/jobs/<id>/applications` | HR JWT | `job_manager.py:list_applications()` | `JobManagement.tsx` |
| POST | `/api/applications/<id>/status` | HR JWT | `job_manager.py:change_status()` | `JobManagement.tsx` |

## Chat

| Method | Endpoint | Auth | Handler | Frontend Usage |
|--------|----------|------|---------|----------------|
| POST | `/api/chat` | Optional JWT | `app.py:chat()` | `ChatPage.tsx` |
| GET | `/api/chat_history` | Optional JWT | `app.py:chat_history()` | `App.tsx` |

## System

| Method | Endpoint | Auth | Handler | Frontend Usage |
|--------|----------|------|---------|----------------|
| GET | `/` | None | `app.py:home()` | Health check |
| GET | `/api/health` | None | `app.py:health_check()` | `App.tsx` keep-alive |
| GET/POST | `/api/warm` | Optional secret | `app.py:warm_endpoint()` | Render warm-up |
| POST | `/api/admin/clear_data` | HR JWT + Admin Secret | `app.py:clear_data()` | None |
| GET | `/api/test` | None | `job_manager.py:test_backend()` | None |

## Deprecated

| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/batch_match` | Returns 405, use `/api/process_resumes` |
