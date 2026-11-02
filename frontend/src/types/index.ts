/**
 * TalentFlow AI — Core TypeScript Domain Types
 */

export type UserRole = 'candidate' | 'hr' | 'recruiter' | 'admin' | 'org_admin' | 'super_admin';

export const isRecruiter = (user?: { role?: string } | null): boolean => {
  if (!user || !user.role) return false;
  const r = String(user.role).trim().toLowerCase();
  return r === 'hr' || r === 'recruiter' || r === 'admin' || r === 'org_admin' || r === 'super_admin';
};

export interface QualityIssue {
  severity: 'high' | 'medium' | 'low' | 'critical' | 'warning' | 'info';
  category?: string;
  message?: string;
  problem?: string;
  evidence?: string;
  why_it_matters?: string;
  recommendation?: string;
}

export interface JobSuggestion {
  role: string;
  score: number;
  matching_skills: string[];
  experience_level?: string;
  raw_score?: number;
}

export interface JobMatchDetails {
  overall: number | null;
  job_match_score?: number | null;
  has_sufficient_jd: boolean;
  reason?: string | null;
  message?: string | null;
  semantic: number | null;
  skills: number | null;
  experience: number | null;
  education: number | null;
  responsibility: number | null;
  matched_skills: string[];
  missing_skills: string[];
  has_explicit_skills?: boolean;
  years_detected?: number;
  years_required?: number;
  applicable_dimensions?: string[];
  unavailable_dimensions?: string[];
  extracted_jd_skills?: string[];
}

export interface ResumeQualityAnalysis {
  resume_text_available?: boolean;
  error?: string;
  overall?: number;
  formatting_score: number;
  grade: string;
  is_ats_friendly: boolean;
  document_type: string;
  page_count: number;
  word_count: number;
  character_count: number;
  subscores: {
    ats_readability: number;
    formatting_layout?: number;
    section_structure?: number;
    bullet_quality?: number;
    grammar_spelling?: number;
    consistency?: number;
    contact_information?: number;
    structure?: number;
    layout?: number;
    typography?: number;
    section_organization?: number;
    document_integrity?: number;
    [key: string]: number | undefined;
  };
  detected_sections: string[];
  missing_sections: string[];
  issues: QualityIssue[];
  good_practices: string[];
  recommendations: string[];
  metrics?: Record<string, any>;
}

export interface User {
  id: string;
  email: string;
  role: UserRole;
  user?: string;
  name?: string;
  username?: string;
  candidate_id?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
}

export interface AuthResponse {
  status: 'success' | 'error';
  token?: string;
  refresh_token?: string;
  role?: UserRole;
  user?: string;
  email?: string;
  message?: string;
  error_code?: string;
}

export interface CandidateProfile {
  user_id: string;
  candidate_id?: string;
  name: string;
  email: string;
  username?: string;
  headline?: string;
  branch?: string;
  graduation_year?: number | null;
  location?: string;
  bio?: string;
  phone?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  role?: string;
  avatar_url?: string;
  skills?: string[];
  education?: string | any[];
  experience?: string | any[];
  certifications?: string[] | any[];
  preferred_role?: string;
  preferred_location?: string;
}

export interface OccupationalClassification {
  predicted_role: string;
  confidence: number;
  runner_up_role: string;
  runner_up_confidence: number;
  margin: number;
  review_required: boolean;
  review_reasons: string[];
  model_version: string;
  taxonomy_version: string;
  occupational_domain?: string;
  specific_role?: string;
  specific_role_confidence?: number;
}

export interface Resume {
  id: string;
  candidate_id: string;
  version: number;
  is_current: boolean;
  file_path: string;
  original_filename: string;
  file_size_bytes?: number;
  mime_type?: string;
  raw_text?: string;
  extracted_skills: string[];
  categorized_skills: Record<string, string[]>;
  predicted_role?: string;
  ats_score?: number;
  health_analysis?: {
    ats_score?: number;
    breakdown?: Record<string, number>;
    suggestions?: string[];
    occupational_classification?: OccupationalClassification;
    quality_analysis?: ResumeQualityAnalysis;
    formatting_score?: number;
    is_ats_friendly?: boolean;
  };
  parser_status?: string;
  created_at?: string;
  updated_at?: string;
  occupational_classification?: OccupationalClassification;
  quality_analysis?: ResumeQualityAnalysis;
}

export interface ResumeUploadResponse {
  status: 'success' | 'error';
  data?: Resume;
  resume?: Resume;
  message?: string;
  error_code?: string;
}

export interface MatchResult {
  final_score: number;
  overall_score?: number;
  job_match_score?: number | null;
  formula_breakdown?: string;
  has_sufficient_jd?: boolean;
  resume_text_available?: boolean;
  error?: string;
  job_suggestions?: JobSuggestion[];
  job_match?: JobMatchDetails;
  resume_suggestions?: string[];
  match_percentage: number;
  semantic_score: number;
  skill_score: number;
  semantic?: number | null;
  skills?: number | null;
  experience?: number | null;
  education?: number | null;
  responsibility?: number | null;
  no_skills_specified?: boolean;
  experience_score?: number;
  education_score?: number;
  responsibility_score?: number;
  matched_skills: string[];
  missing_skills: string[];
  extracted_skills?: string[];
  required_skills?: string[];
  explanation?: any;
  recommendations?: string[];
  occupational_classification?: OccupationalClassification;
  resume_quality?: ResumeQualityAnalysis;
  target_role?: any;
  specific_role_target?: string;
  domain_target?: string;
  is_inferred?: boolean;
  review_required?: boolean;
  review_message?: string;
}

export interface Job {
  id: string;
  title: string;
  company_name: string;
  department?: string;
  description: string;
  required_skills?: string;
  experience_required: number;
  location: string;
  job_type: string;
  salary?: string;
  status?: string;
  created_at?: string;
  recruiter_id?: string;
  organization_id?: string;
  occupational_class?: string;
  specific_role?: string;
}

export interface Application {
  id: string;
  job_id: string;
  candidate_id: string;
  resume_id?: string | null;
  status: string;
  stage: string;
  score: number;
  notes?: string | null;
  created_at?: string;
  candidate_name?: string;
  email?: string;
  branch?: string;
  graduation_year?: number | null;
  job_title?: string;
  company_name?: string;
  location?: string;
}

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'ai';
  text: string;
  timestamp?: number;
  sources?: Array<{
    id?: string;
    category?: string;
    question?: string;
    content?: string;
    similarity?: number;
  }>;
}

export interface ApiError {
  status: 'error';
  error_code: string;
  message: string;
  details?: any;
}
