import api from './api';
import {
  TutorLanguage,
  TutorGenerateResponse,
  QuizGradeResponse,
  TutorQuizItem,
  ChatMessage,
  ChatSource,
  ConceptImage,
  SuggestedVideo,
  ConceptMastery,
  KnowledgeBaseSource,
  IngestResult,
  RagSource,
} from '../types';

// NVIDIA NIM lesson+quiz generation runs multiple LLM calls (core → quiz → translations).
// With parallel translation the wall-clock is ~45-60 s, but allow 180 s for slow batches.
const GENERATION_TIMEOUT = 180000;
const INGEST_TIMEOUT = 180000; // OCR runs ~seconds/page — give large chapters room.

export interface GenerateLessonParams {
  subject: string;
  chapter: string;
  concept: string;
  mastery: number;
  language: TutorLanguage;
  num_questions: number;
  question_types: string[];
}

export interface GradeQuizParams {
  subject: string;
  chapter: string;
  concept: string;
  mastery: number;
  quiz: TutorQuizItem[];
  answers: Record<number, string>;
}

export interface ChatParams {
  question: string;
  language: TutorLanguage;
  history: { role: 'user' | 'assistant'; content: string }[];
}

export const aiTutorService = {
  // ── Adaptive lesson + quiz generation (learning_system.AdaptiveTutor.generate) ──
  generateLesson: async (params: GenerateLessonParams): Promise<TutorGenerateResponse> => {
    const { data } = await api.post('/tutor/generate', params, { timeout: GENERATION_TIMEOUT });
    return data;
  },

  // ── Score quiz answers, update mastery, return the score-gated decision ──
  gradeQuiz: async (params: GradeQuizParams): Promise<QuizGradeResponse> => {
    const { data } = await api.post('/tutor/quiz/grade', params, { timeout: GENERATION_TIMEOUT });
    return data;
  },

  // ── Current mastery for a concept (falls back to 0 server-side if unseen) ──
  getMastery: async (subject: string, concept: string): Promise<ConceptMastery> => {
    const { data } = await api.get('/tutor/mastery', { params: { subject, concept } });
    return data;
  },

  getRecentConcepts: async (limit = 5): Promise<ConceptMastery[]> => {
    const { data } = await api.get('/tutor/mastery/recent', { params: { limit } });
    return data;
  },

  // ── RAG-grounded doubt-solving chat (chat_engine.TutorChat.reply) ──
  chat: async (params: ChatParams): Promise<{ answer: string; detected_topic: string; sources: ChatSource[]; images: ConceptImage[]; videos: SuggestedVideo[] }> => {
    const { data } = await api.post('/tutor/chat', params, { timeout: GENERATION_TIMEOUT });
    return data;
  },

  // ── "My Study Material" — PDF upload with optional OCR (pdf_ingest.ingest_pdf) ──
  ingestPdf: async (
    fileUri: string,
    fileName: string,
    opts: { subject: string; chapter: string; useOcr: boolean; pageStart?: number; pageEnd?: number },
    onUploadProgress?: (fraction: number) => void,
  ): Promise<IngestResult> => {
    const form = new FormData();
    form.append('file', { uri: fileUri, name: fileName, type: 'application/pdf' } as any);
    form.append('subject', opts.subject);
    form.append('chapter', opts.chapter);
    form.append('use_ocr', String(opts.useOcr));
    if (opts.useOcr) {
      form.append('page_start', String(opts.pageStart ?? 1));
      form.append('page_end', String(opts.pageEnd ?? 20));
    }
    const { data } = await api.post('/tutor/knowledge-base/ingest', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: INGEST_TIMEOUT,
      onUploadProgress: (evt) => {
        if (onUploadProgress && evt.total) onUploadProgress(evt.loaded / evt.total);
      },
    });
    return data;
  },

  getKnowledgeBaseSources: async (): Promise<KnowledgeBaseSource[]> => {
    const { data } = await api.get('/tutor/knowledge-base/sources');
    return data;
  },

  searchKnowledgeBase: async (query: string): Promise<RagSource[]> => {
    const { data } = await api.get('/tutor/knowledge-base/search', { params: { q: query } });
    return data;
  },
};

export function newMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function emptyChatGreeting(): ChatMessage {
  return {
    id: newMessageId(),
    role: 'assistant',
    text: "Hi! I'm your AI tutor 📚 Ask me anything from your syllabus — Physics, "
      + 'Chemistry or Maths — and I\'ll explain it in plain English (or తెలుగు), '
      + 'grounded in your textbook.',
  };
}
