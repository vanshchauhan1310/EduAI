import { UserRole } from '../types';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

function getDevApiBaseUrl() {
  const configured = process.env.EXPO_PUBLIC_API_BASE_URL || Constants.expoConfig?.extra?.API_BASE_URL;
  if (configured) return configured;

  const hostUri =
    Constants.expoConfig?.hostUri ??
    Constants.manifest2?.extra?.expoGo?.debuggerHost ??
    Constants.manifest?.debuggerHost;
  const host = hostUri?.split(':')[0];
  if (host) return `http://${host}:8000/api/v1`;

  if (Platform.OS === 'android') return 'http://10.0.2.2:8000/api/v1';
  return 'http://localhost:8000/api/v1';
}

export const API_BASE_URL = getDevApiBaseUrl();

export const ROLE_LABELS: Record<UserRole, string> = {
  DEO: 'District Education Officer',
  MEO: 'Mandal Education Officer',
  HM: 'Headmaster / Principal',
  TEACHER: 'Teacher',
  STUDENT: 'Student',
  PARENT: 'Parent',
};

export const RISK_COLORS = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
} as const;

export const RISK_LABELS = {
  LOW: 'Low Risk',
  MEDIUM: 'Medium Risk',
  HIGH: 'High Risk',
  CRITICAL: 'Critical Risk',
} as const;

export const ATTENDANCE_STATUS_COLORS = {
  PRESENT: '#22c55e',
  ABSENT: '#ef4444',
  LATE: '#f59e0b',
  HALF_DAY: '#8b5cf6',
  HOLIDAY: '#6b7280',
  LEAVE: '#3b82f6',
} as const;

export const GRADE_COLORS: Record<string, string> = {
  'A+': '#22c55e',
  A:   '#4ade80',
  'B+': '#86efac',
  B:   '#fbbf24',
  C:   '#f97316',
  D:   '#fb923c',
  F:   '#ef4444',
};

export const CLASS_GRADES = Array.from({ length: 12 }, (_, i) => ({
  label: `Class ${i + 1}`,
  value: i + 1,
}));

export const ACADEMIC_YEARS = ['2023-24', '2024-25', '2025-26'];

export const SUBJECTS = [
  'Mathematics', 'Science', 'Social Studies', 'English',
  'Telugu', 'Hindi', 'Computer Science', 'Physical Education',
];

export const TOKEN_KEY = 'eduai_access_token';
export const REFRESH_TOKEN_KEY = 'eduai_refresh_token';
export const USER_KEY = 'eduai_user';

export const QUERY_KEYS = {
  ME: ['me'],
  STUDENTS: 'students',
  ATTENDANCE: 'attendance',
  ASSESSMENTS: 'assessments',
  ANALYTICS: 'analytics',
  NOTIFICATIONS: 'notifications',
  AI_INSIGHTS: 'ai_insights',
  SCHOOL_HEALTH: 'school_health',
  DISTRICT_OVERVIEW: 'district_overview',
  DROPOUT_HIGH_RISK: 'dropout-high-risk',
  DROPOUT_SCHOOL: 'dropout-school',
  DROPOUT_MANDAL: 'dropout-mandal',
  DROPOUT_DISTRICT: 'dropout-district',
  CAREER: 'career',
} as const;
