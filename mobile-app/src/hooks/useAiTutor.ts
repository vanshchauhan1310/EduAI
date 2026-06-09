import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  aiTutorService, GenerateLessonParams, GradeQuizParams, ChatParams,
} from '../services/aiTutorService';
import { QUERY_KEYS } from '../constants';

export function useConceptMastery(subject: string, concept: string) {
  return useQuery({
    queryKey: [QUERY_KEYS.TUTOR, 'mastery', subject, concept],
    queryFn: () => aiTutorService.getMastery(subject, concept),
    enabled: !!subject && !!concept,
    staleTime: 60_000,
  });
}

export function useRecentConcepts(limit = 5) {
  return useQuery({
    queryKey: [QUERY_KEYS.TUTOR, 'recent', limit],
    queryFn: () => aiTutorService.getRecentConcepts(limit),
    staleTime: 30_000,
  });
}

export function useGenerateLesson() {
  return useMutation({
    mutationFn: (params: GenerateLessonParams) => aiTutorService.generateLesson(params),
  });
}

export function useGradeQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: GradeQuizParams) => aiTutorService.gradeQuiz(params),
    onSuccess: (_, variables) => {
      // Mastery has shifted — refresh the concept's score and the "recently studied" rail.
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TUTOR, 'mastery', variables.subject, variables.concept] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TUTOR, 'recent'] });
    },
  });
}

export function useTutorChat() {
  return useMutation({
    mutationFn: (params: ChatParams) => aiTutorService.chat(params),
  });
}

export function useKnowledgeBaseSources() {
  return useQuery({
    queryKey: [QUERY_KEYS.TUTOR, 'kb-sources'],
    queryFn: () => aiTutorService.getKnowledgeBaseSources(),
    staleTime: 30_000,
  });
}

export function useIngestPdf() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ fileUri, fileName, opts, onProgress }: {
      fileUri: string; fileName: string;
      opts: { subject: string; chapter: string; useOcr: boolean; pageStart?: number; pageEnd?: number };
      onProgress?: (fraction: number) => void;
    }) => aiTutorService.ingestPdf(fileUri, fileName, opts, onProgress),
    onSuccess: (result) => {
      if (result.success) {
        queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TUTOR, 'kb-sources'] });
      }
    },
  });
}

export function useSearchKnowledgeBase() {
  return useMutation({
    mutationFn: (query: string) => aiTutorService.searchKnowledgeBase(query),
  });
}
