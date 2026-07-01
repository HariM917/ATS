export interface UserData {
  user: string;
  email: string;
  role: 'hr' | 'candidate';
  token?: string;
}

export interface Job {
  id: number;
  title: string;
  description: string;
  company_name?: string;
  company?: string;
  branch?: string;
  location?: string;
  job_type: string;
  required_skills?: string;
  skills?: string;
  experience_required?: number;
  salary?: string;
  hr_email?: string;
  created_at?: string;
  applications?: Application[];
}

export interface Application {
  id: number;
  candidate_name: string;
  candidate_email: string;
  resume_path: string;
  score: number;
  status: string;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  timestamp?: number;
}

export interface MatchResult {
  final_score: number;
  match_percentage?: number;
  predicted_role?: string;
  top_roles?: string[];
  experience_years?: number;
  experience?: string;
  resume_skills?: string[];
  all_skills?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  total_skills?: number;
  summary_reasoning?: string;
  candidate_name?: string;
}
