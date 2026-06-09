import { Ionicons } from '@expo/vector-icons';

// ─── User & Auth ─────────────────────────────────────────────
export type UserRole = 'DEO' | 'MEO' | 'HM' | 'TEACHER' | 'STUDENT' | 'PARENT';

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  school_id: number | null;
  district_id: number | null;
  mandal_id: number | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

// ─── Student ──────────────────────────────────────────────────
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Gender = 'MALE' | 'FEMALE' | 'OTHER';

export interface Student {
  id: number;
  admission_no: string;
  first_name: string;
  last_name: string;
  full_name: string;
  date_of_birth: string | null;
  gender: Gender;
  category: string | null;
  parent_name: string | null;
  parent_phone: string | null;
  current_class: number;
  section: string | null;
  academic_year: string;
  school_id: number;
  dropout_risk_score: number | null;
  risk_level: RiskLevel;
  is_active: boolean;
  enrollment_date: string | null;
}

// ─── Attendance ───────────────────────────────────────────────
export type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'LATE' | 'HALF_DAY' | 'HOLIDAY' | 'LEAVE';

export interface AttendanceRecord {
  id: number;
  reference_type: 'STUDENT' | 'TEACHER';
  reference_id: number;
  date: string;
  status: AttendanceStatus;
  session: string;
  is_geo_verified: boolean;
  remarks: string | null;
}

export interface AttendanceSummary {
  total_days: number;
  present_days: number;
  absent_days: number;
  late_days: number;
  half_days: number;
  attendance_percentage: number;
  consecutive_absences: number;
  last_absent_date: string | null;
}

// ─── Assessment ───────────────────────────────────────────────
export interface Assessment {
  id: number;
  title: string;
  assessment_type: string;
  subject: string;
  class_grade: number;
  max_marks: number;
  is_published: boolean;
}

export interface AssessmentResult {
  id: number;
  assessment_id: number;
  student_id: number;
  marks_obtained: number | null;
  grade: string | null;
  percentage: number | null;
  is_absent: boolean;
}

// ─── AI Insights ──────────────────────────────────────────────
export interface AIInsight {
  id: number;
  type: string;
  risk_score: number | null;
  confidence: number | null;
  summary: string;
  recommendations: string | null;
  is_actioned: boolean;
  created_at: string;
}

export interface DropoutRiskResult {
  student_id: number;
  student_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  risk_factors: string[];
  recommendations: string[];
}

// ─── School ───────────────────────────────────────────────────
export interface School {
  id: number;
  dise_code: string;
  name: string;
  school_type: string;
  address: string | null;
  total_students: number;
  total_teachers: number;
  health_score: number | null;
  mandal_id: number;
  district_id: number;
}

// ─── Analytics ───────────────────────────────────────────────
export interface DistrictOverview {
  district_id: number;
  total_schools: number;
  total_students: number;
  high_risk_students: number;
  attendance_rate_this_month: number;
  dropout_risk_rate: number;
}

export interface SchoolHealthSummary {
  school_id: number;
  school_name: string;
  health_score: number;
  breakdown: Record<string, { value: string; weight: number; weighted_score: number }>;
  grade: string;
}

export interface SchoolHealthAnalyzerBreakdown {
  school_id: number;
  school_name: string;
  dise_code: string;
  health_score: number;
  attendance_rate: number;
  dropout_risk_count: number;
  total_students: number;
  total_teachers: number;
  teacher_student_ratio: number;
  infrastructure_score: number;
  mandal_name: string;
}

export interface SchoolHealthAnalyzerResponse {
  mandal_id: number;
  mandal_name: string;
  selected_school_count: number;
  cluster_insights: string;
  strengths: string[];
  concerns: string[];
  recommendations: string[];
  action_plan: string[];
  top_school: string;
  most_at_risk_school: string;
  school_breakdown: SchoolHealthAnalyzerBreakdown[];
}

// ─── Notifications ────────────────────────────────────────────
export interface AppNotification {
  id: number;
  title: string;
  body: string;
  channel: string;
  status: string;
  is_read: boolean;
  notification_type: string | null;
  created_at: string;
}

// ─── Career Recommender ───────────────────────────────────────
export interface CareerSurveyQuestion {
  question_id: string;
  question_text: string;
  options: string[];
}

export interface CareerSurveyResponse {
  question_id: string;
  answer: string;
}

export interface CareerStreamRecommendation {
  stream: string;
  match_percent: number;
  why: string;
}

export interface CareerPath {
  title: string;
  sector: string;
  description: string;
}

export interface CareerSkillCourse {
  name: string;
  provider: string;
  duration: string;
}

export interface CareerScholarship {
  name: string;
  eligibility: string;
  how_to_apply: string;
}

export interface CareerRecommendation {
  summary: string;
  recommended_streams: CareerStreamRecommendation[];
  career_paths: CareerPath[];
  skill_courses: CareerSkillCourse[];
  scholarships: CareerScholarship[];
}

export interface CareerRecommendationStatus {
  survey_completed: boolean;
  has_recommendation: boolean;
  generated_at: string | null;
  recommendation: CareerRecommendation | null;
}

// ─── AI Tutor (adaptive learning) ────────────────────────────
export type TutorLanguage = 'english' | 'telugu' | 'both';
export type MasteryLevel = 'Beginner' | 'Intermediate' | 'Advanced';
export type QuizType = 'MCQ' | 'MSQ' | 'Short Answer' | 'Long Answer';
export type QuizDifficulty = 'Easy' | 'Medium' | 'Hard';

export interface TutorConcept {
  subject: string;
  chapter: string;
  concept: string;
  icon: keyof typeof Ionicons.glyphMap;
}

export interface ConceptMastery {
  subject: string;
  chapter: string;
  concept: string;
  mastery: number;          // 0-100
  level: MasteryLevel;
  updated_at: string | null;
}

export interface StudentAnalysis {
  level: MasteryLevel;
  strong_concepts: string[];
  weak_concepts: string[];
  misconceptions: string[];
}

export interface LearningPathItem {
  concept: string;
  priority: number;
  reason: string;
  estimated_time: string;
  activity: string;
}

export interface TutorLesson {
  concept: string;
  english_explanation: string;
  telugu_explanation: string;
  real_life_examples: string[];
  worked_examples: string[];
  common_mistakes: string[];
  revision_notes: string[];
}

export interface TutorQuizItem {
  question: string;
  type: QuizType;
  difficulty: QuizDifficulty;
  concept_tested: string;
  options: string[];
  answer: string;
  explanation: string;
}

export interface TutorRecommendations {
  next_concepts: string[];
  estimated_mastery_score: number;
  next_lesson: string;
}

export interface RagSource {
  kind: 'pdf' | 'note';
  concept: string;
  text: string;
  score: number;
  source?: string;
}

// A relevant educational diagram/photo for a concept (e.g. "Ohm's Law"),
// sourced from Wikimedia Commons — shown alongside the explanation so
// students can "see it visually" before reading the details.
export interface ConceptImage {
  title: string;
  thumbnail_url: string;
  full_url: string;
  attribution: string;
  source_url: string;
}

export interface TutorGenerateResponse {
  student_analysis: StudentAnalysis;
  learning_path: LearningPathItem[];
  lesson: TutorLesson;
  quiz: TutorQuizItem[];
  recommendations: TutorRecommendations;
  rag_sources: RagSource[];
  mastery: number;
  images: ConceptImage[];
}

export interface QuizGradeResult {
  index: number;
  question: string;
  type: QuizType;
  is_correct: boolean | null;   // null = ungraded (Short/Long answer, reviewed qualitatively)
  correct_answer: string;
  explanation: string;
}

export interface QuizGradeResponse {
  correct: number;
  scored: number;
  percentage: number;
  results: QuizGradeResult[];
  passed: boolean;
  message: string;
  next_concept: string | null;
  review_topics: string[];
  old_mastery: number;
  new_mastery: number;
}

export interface ChatSource {
  kind: 'pdf' | 'note';
  concept: string;
  text: string;
  score: number;
}

export interface SuggestedVideo {
  title: string;
  channel: string;
  url: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  detected_topic?: string;
  sources?: ChatSource[];
  images?: ConceptImage[];
  videos?: SuggestedVideo[];
}

export interface KnowledgeBaseSource {
  id: string;
  source: string;
  subject: string;
  chapter: string;
  chunks: number;
  uploaded_at: string;
}

export interface IngestProgress {
  done: number;
  total: number;
}

export interface IngestResult {
  success: boolean;
  source: string;
  pages: number;
  chunks: number;
  error?: string;
}

// ─── Pagination ───────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ─── API Response ────────────────────────────────────────────
export interface ApiError {
  detail: string;
  status_code?: number;
}
