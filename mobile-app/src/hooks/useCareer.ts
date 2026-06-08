import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { careerService } from '../services/careerService';
import { QUERY_KEYS } from '../constants';
import { CareerSurveyResponse } from '../types';

export function useCareerSurvey() {
  return useQuery({
    queryKey: [QUERY_KEYS.CAREER, 'survey'],
    queryFn: () => careerService.getSurvey(),
    staleTime: Infinity,
  });
}

export function useMyCareerRecommendations() {
  return useQuery({
    queryKey: [QUERY_KEYS.CAREER, 'me'],
    queryFn: () => careerService.getMyRecommendations(),
  });
}

export function useSubmitCareerSurvey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (responses: CareerSurveyResponse[]) => careerService.submitSurvey(responses),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CAREER] });
    },
  });
}

export function useGenerateCareerRecommendations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => careerService.generateRecommendations(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.CAREER] });
    },
  });
}
