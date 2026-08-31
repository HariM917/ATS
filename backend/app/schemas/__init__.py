"""
TalentFlow AI — Pydantic Validation Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# Common
class StandardResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None


# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    role: Optional[str] = "candidate"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str = Field(min_length=2)
    role: str = "candidate"
    company_name: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    status: str = "success"
    token: str
    refresh_token: Optional[str] = None
    role: str
    user: str
    email: str


# Job
class JobCreateSchema(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    required_skills: Optional[str] = None
    experience_required: int = Field(default=0, ge=0)
    location: str = "Remote"
    job_type: str = "Full-time"
    salary: Optional[str] = ""
    department: Optional[str] = None
    company_name: Optional[str] = None
    scoring_config: Optional[Dict[str, float]] = None


class JobUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[str] = None
    experience_required: Optional[int] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary: Optional[str] = None
    status: Optional[str] = None
    scoring_config: Optional[Dict[str, float]] = None


# Application
class ApplicationCreateSchema(BaseModel):
    job_id: str
    resume_path: Optional[str] = None


class StageUpdateSchema(BaseModel):
    stage: str
    status: Optional[str] = None
    notes: Optional[str] = None


# Chat
class ChatRequestSchema(BaseModel):
    query: str = Field(min_length=1)
    session_id: Optional[str] = None


# Resume Health
class ResumeHealthSchema(BaseModel):
    ats_score: float
    feedback: List[str]
    missing_sections: List[str]
    strong_skills: List[str]
