export interface Skill {
  id: string;
  name: string;
  proficiency: string | null;
  source: string;
}

export interface Project {
  id: string;
  title: string;
  description: string | null;
  tech_stack: string[] | null;
  url: string | null;
}

export interface Experience {
  id: string;
  company_name: string;
  role: string | null;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
}

export interface Profile {
  id: string;
  full_name: string | null;
  phone: string | null;
  location: string | null;
  college: string | null;
  degree: string | null;
  graduation_year: number | null;
  cgpa: number | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  cover_letter_default: string | null;
  preferred_roles: string[] | null;
  preferred_locations: string[] | null;
  preferred_job_type: string | null;
  preferred_stipend_min: number | null;
  work_from_home_only: boolean;
  fresher_only: boolean;
  active_resume_id: string | null;
  skills: Skill[];
  projects: Project[];
  experiences: Experience[];
}

export interface Resume {
  id: string;
  file_name: string;
  parse_status: "pending" | "processing" | "completed" | "failed";
  parse_error: string | null;
  parsed_data: Record<string, any> | null;
  is_generated: boolean;
  created_at: string;
}

export interface Company {
  id: string;
  name: string;
  website: string | null;
  logo_url: string | null;
}

export interface Job {
  id: string;
  title: string;
  description: string | null;
  job_type: string;
  location: string | null;
  is_remote: boolean;
  stipend_min: number | null;
  stipend_max: number | null;
  stipend_currency: string;
  skills_required: string[] | null;
  min_cgpa: number | null;
  eligible_grad_years: number[] | null;
  freshers_only: boolean;
  source: string;
  external_url: string;
  allows_auto_submit: boolean;
  is_active: boolean;
  created_at: string;
  company: Company | null;
  match_score?: number | null;
  match_breakdown?: Record<string, number> | null;
}

export type ApplicationStatus =
  | "matched"
  | "queued_for_review"
  | "saved"
  | "skipped"
  | "ready_to_submit"
  | "submitted"
  | "failed"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn";

export interface Application {
  id: string;
  job_id: string;
  status: ApplicationStatus;
  match_score: number | null;
  match_breakdown: Record<string, number> | null;
  cover_letter_text: string | null;
  autofill_payload: Record<string, any> | null;
  requires_manual_submission: boolean;
  submitted_at: string | null;
  created_at: string;
  job: Job | null;
}

export interface DashboardStats {
  total_jobs_found: number;
  applications_prepared: number;
  applications_submitted: number;
  pending_review: number;
  response_rate: number;
  interviews: number;
  rejections: number;
  offers: number;
}

export interface TimeSeriesPoint {
  period: string;
  applications: number;
  interviews: number;
  offers: number;
  rejections: number;
}

export interface AnalyticsOverview {
  daily: TimeSeriesPoint[];
  weekly: TimeSeriesPoint[];
  monthly: TimeSeriesPoint[];
  top_companies: { name: string; count: number }[];
  top_skills: { name: string; count: number }[];
  response_rate: number;
  interview_rate: number;
  offer_rate: number;
}
