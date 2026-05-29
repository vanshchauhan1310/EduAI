import api from './api';
import { DistrictOverview, SchoolHealthSummary } from '../types';

export const analyticsService = {
  getDistrictOverview: async (districtId: number): Promise<DistrictOverview> => {
    const { data } = await api.get(`/analytics/district/${districtId}/overview`);
    return data;
  },

  getMandalOverview: async (mandalId: number) => {
    const { data } = await api.get(`/analytics/mandal/${mandalId}/overview`);
    return data;
  },

  getSchoolPerformance: async (schoolId: number, academicYear: string) => {
    const { data } = await api.get(`/analytics/school/${schoolId}/performance`, {
      params: { academic_year: academicYear },
    });
    return data;
  },

  getSchoolHealthScore: async (schoolId: number): Promise<SchoolHealthSummary> => {
    const { data } = await api.get(`/ai/school/${schoolId}/health-score`);
    return data;
  },

  getStudentRisk: async (studentId: number) => {
    const { data } = await api.get(`/ai/student/${studentId}/risk`);
    return data;
  },

  runSchoolRiskScan: async (schoolId: number) => {
    const { data } = await api.post(`/ai/school/${schoolId}/run-risk-scan`);
    return data;
  },

  getStudentRecommendations: async (studentId: number) => {
    const { data } = await api.get(`/ai/student/${studentId}/recommendations`);
    return data;
  },

  getInsights: async (scope: string, referenceId: number) => {
    const { data } = await api.get(`/ai/insights/${scope}/${referenceId}`);
    return data;
  },
};
