import api from './api';
import {
  CareerSurveyQuestion,
  CareerSurveyResponse,
  CareerRecommendation,
  CareerRecommendationStatus,
} from '../types';

export const careerService = {
  getSurvey: async (): Promise<{ questions: CareerSurveyQuestion[] }> => {
    const { data } = await api.get('/career/survey');
    return data;
  },

  submitSurvey: async (responses: CareerSurveyResponse[]): Promise<{ status: string; responses_count: number }> => {
    const { data } = await api.post('/career/survey', { responses });
    return data;
  },

  generateRecommendations: async (): Promise<CareerRecommendation> => {
    // AI generation (NVIDIA NIM) can take well over the default 15s timeout — match the
    // other AI-generation calls in copilotService.ts that use a 90s allowance.
    const { data } = await api.post('/career/recommendations/generate', undefined, { timeout: 90000 });
    return data;
  },

  getMyRecommendations: async (): Promise<CareerRecommendationStatus> => {
    const { data } = await api.get('/career/recommendations/me');
    return data;
  },
};
