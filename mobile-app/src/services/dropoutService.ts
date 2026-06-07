/**
 * Dropout Prediction Service — Frontend API client.
 */

import api from './api';

// ─── Types ────────────────────────────────────────────────────

export interface RunPredictionsResponse {
  message: string;
  batch_id: string;
  total_students: number;
  high_risk_count: number;
  critical_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  started_at: string;
}

export interface HighRiskStudent {
  prediction_id: number;
  student_id: number;
  student_name: string;
  admission_no: string;
  school_id: number;
  school_name: string;
  current_class: number;
  dropout_probability: number;
  risk_level: string;
  recommendation: string;
  predicted_at: string;
}

export interface HighRiskListResponse {
  total: number;
  students: HighRiskStudent[];
}

export interface StudentPredictionDetail {
  prediction_id: number;
  student_id: number;
  student_name: string;
  admission_no: string;
  school_id: number;
  school_name: string;
  current_class: number;
  section: string | null;
  academic_year: string;
  dropout_probability: number;
  risk_level: string;
  recommendation: string;
  predicted_at: string;
}

export interface SchoolDropoutSummary {
  school_id: number;
  school_name: string;
  total_students: number;
  total_predictions: number;
  high_risk_count: number;
  critical_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  average_risk_score: number;
  last_prediction_at: string | null;
}

export interface SchoolDropoutStudent {
  student_id: number;
  student_name: string;
  admission_no: string;
  current_class: number;
  dropout_probability: number;
  risk_level: string;
  recommendation: string;
}

export interface SchoolDropoutDetailResponse {
  summary: SchoolDropoutSummary;
  students: SchoolDropoutStudent[];
}

// ─── Class-Wise Prediction Types ─────────────────────────

export interface ClassPredictionStudent {
  student_id: number;
  student_name: string;
  admission_no: string;
  current_class: number;
  section: string | null;
  gender: string;
  age: number;
  attendance_pct: number;
  avg_marks: number;
  previous_failures: number;
  dropout_probability: number;
  risk_level: string;
  recommendation: string;
}

export interface PredictByClassResponse {
  batch_id: string;
  school_id: number;
  class_level: number;
  total_students: number;
  high_risk_count: number;
  critical_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  students: ClassPredictionStudent[];
  message: string;
}

// ─── API Calls ────────────────────────────────────────────────

export const dropoutService = {
  async runPredictions(schoolId?: number, academicYear?: string): Promise<RunPredictionsResponse> {
    const { data } = await api.post('/dropout/run-predictions', {
      school_id: schoolId,
      academic_year: academicYear,
    });
    return data;
  },

  async runPredictionsSync(schoolId?: number, academicYear?: string) {
    const { data } = await api.post('/dropout/run-predictions/sync', {
      school_id: schoolId,
      academic_year: academicYear,
    });
    return data;
  },

  async getHighRiskStudents(schoolId?: number, limit = 100, offset = 0): Promise<HighRiskListResponse> {
    const params: Record<string, any> = { limit, offset };
    if (schoolId) params.school_id = schoolId;
    const { data } = await api.get('/dropout/high-risk', { params });
    return data;
  },

  async getStudentPrediction(studentId: number): Promise<StudentPredictionDetail> {
    const { data } = await api.get(`/dropout/student/${studentId}`);
    return data;
  },

  async getSchoolAnalysis(schoolId: number): Promise<SchoolDropoutDetailResponse> {
    const { data } = await api.get(`/dropout/school/${schoolId}`);
    return data;
  },

  async getMandalAnalysis(mandalId: number) {
    const { data } = await api.get(`/dropout/mandal/${mandalId}`);
    return data;
  },

  async getDistrictAnalysis(districtId: number) {
    const { data } = await api.get(`/dropout/district/${districtId}`);
    return data;
  },

  async downloadTemplate(): Promise<Blob | null> {
    try {
      const response = await api.get('/dropout/template', { responseType: 'blob' });
      return response.data as Blob;
    } catch {
      const baseUrl = api.defaults?.baseURL || 'http://localhost:8000/api/v1';
      window.open(`${baseUrl}/dropout/template`, '_blank');
      return null;
    }
  },

  async uploadAndPredict(file: File): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/dropout/upload-predict', formData, {
      responseType: 'blob',
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data as Blob;
  },

  async uploadJson(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/dropout/upload-json', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  async uploadAndPredictJson(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/dropout/upload-predict-json', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  /** Run predictions for a class. school_id is derived from auth token on backend. */
  async predictByClass(classLevel: number): Promise<PredictByClassResponse> {
    const { data } = await api.post('/dropout/predict-by-class', {
      class_level: classLevel,
    });
    return data;
  },

  async reloadModel(): Promise<{ message: string }> {
    const { data } = await api.post('/dropout/model/reload');
    return data;
  },
};