import api from './api';
import * as FileSystem from 'expo-file-system';
import * as SecureStore from 'expo-secure-store';
import * as Sharing from 'expo-sharing';
import { TOKEN_KEY } from '../constants';

type ExportFormat = 'pdf' | 'docx';

async function requestExport(url: string, method: 'get' | 'post' = 'get') {
  const { data, headers } = await api.request({
    url,
    method,
    responseType: 'arraybuffer',
    timeout: 90000,
  });
  return { data, contentType: headers['content-type'] };
}

function arrayBufferToBase64(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer);
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let output = '';
  let i = 0;
  for (; i + 2 < bytes.length; i += 3) {
    output += chars[bytes[i] >> 2];
    output += chars[((bytes[i] & 3) << 4) | (bytes[i + 1] >> 4)];
    output += chars[((bytes[i + 1] & 15) << 2) | (bytes[i + 2] >> 6)];
    output += chars[bytes[i + 2] & 63];
  }
  if (i < bytes.length) {
    output += chars[bytes[i] >> 2];
    if (i === bytes.length - 1) {
      output += chars[(bytes[i] & 3) << 4] + '==';
    } else {
      output += chars[((bytes[i] & 3) << 4) | (bytes[i + 1] >> 4)];
      output += chars[(bytes[i + 1] & 15) << 2] + '=';
    }
  }
  return output;
}

async function downloadLocalFile(url: string, fileName: string, mimeType: string, method: 'GET' | 'POST' = 'GET') {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  const fileUri = `${FileSystem.documentDirectory}${fileName}`;

  if (method === 'POST') {
    const { data } = await requestExport(url, 'post');
    const base64 = arrayBufferToBase64(data);
    await FileSystem.writeAsStringAsync(fileUri, base64, {
      encoding: FileSystem.EncodingType.Base64,
    });
  } else {
    await FileSystem.downloadAsync(`${api.defaults.baseURL}${url}`, fileUri, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      md5: false,
    });
  }

  return fileUri;
}

async function shareFile(fileUri: string, title: string, mimeType: string) {
  await Sharing.shareAsync(fileUri, {
    mimeType,
    dialogTitle: title,
  });
}

async function downloadExport(url: string, fileName: string, mimeType: string, method: 'GET' | 'POST' = 'GET') {
  return downloadLocalFile(url, fileName, mimeType, method);
}

async function shareExport(
  url: string,
  fileName: string,
  mimeType: string,
  method: 'GET' | 'POST' = 'GET',
  title: string
) {
  const fileUri = await downloadLocalFile(url, fileName, mimeType, method);
  await shareFile(fileUri, title, mimeType);
  return fileUri;
}

// ─── Circular Summarization ───────────────────────────────────────

export const circularService = {
  summarize: async (fileUri: string, fileName: string) => {
    const form = new FormData();
    form.append('file', { uri: fileUri, name: fileName, type: 'application/pdf' } as any);
    const { data } = await api.post('/copilot/summarize-circular', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return data;
  },

  getHistory: async (limit = 20) => {
    const { data } = await api.get('/copilot/circulars/history', { params: { limit } });
    return data;
  },

  getById: async (id: number) => {
    const { data } = await api.get(`/copilot/circulars/${id}`);
    return data;
  },

  exportPdfUrl: (id: number) => `${api.defaults.baseURL}/copilot/circulars/${id}/export/pdf`,
  exportPdf: async (id: number) => requestExport(`/copilot/circulars/${id}/export/pdf`),
  downloadPdf: async (id: number) =>
    downloadExport(`/copilot/circulars/${id}/export/pdf`, `circular_summary_${id}.pdf`, 'application/pdf'),
  sharePdf: async (id: number) =>
    shareExport(
      `/copilot/circulars/${id}/export/pdf`,
      `circular_summary_${id}.pdf`,
      'application/pdf',
      'GET',
      `Share circular summary #${id}`
    ),
};

// ─── Letter Generator ─────────────────────────────────────────────

export const letterService = {
  listTemplates: async () => {
    const { data } = await api.get('/copilot/letters/templates');
    return data;
  },

  generate: async (payload: {
    letter_type: string;
    template_fields: Record<string, any>;
    language?: string;
  }) => {
    const { data } = await api.post('/copilot/generate-letter', payload, { timeout: 60000 });
    return data;
  },

  getHistory: async (limit = 20) => {
    const { data } = await api.get('/copilot/letters/history', { params: { limit } });
    return data;
  },

  getById: async (id: number) => {
    const { data } = await api.get(`/copilot/letters/${id}`);
    return data;
  },

  exportPdfUrl: (id: number) => `${api.defaults.baseURL}/copilot/export-letter/pdf?letter_id=${id}`,
  exportDocxUrl: (id: number) => `${api.defaults.baseURL}/copilot/export-letter/docx?letter_id=${id}`,
  export: async (id: number, format: ExportFormat) =>
    requestExport(`/copilot/export-letter/${format}?letter_id=${id}`, 'post'),
  download: async (id: number, format: ExportFormat) =>
    downloadExport(
      `/copilot/export-letter/${format}?letter_id=${id}`,
      `letter_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'POST'
    ),
  share: async (id: number, format: ExportFormat) =>
    shareExport(
      `/copilot/export-letter/${format}?letter_id=${id}`,
      `letter_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'POST',
      `Share letter ${id}`
    ),
};

// ─── Report Generator ────────────────────────────────────────────

export const reportService = {
  generate: async (payload: {
    report_type: string;
    report_scope: string;
    scope_id: number;
    academic_year?: string;
  }) => {
    const { data } = await api.post('/copilot/generate-report', payload, { timeout: 90000 });
    return data;
  },

  getHistory: async (limit = 20) => {
    const { data } = await api.get('/copilot/reports/history', { params: { limit } });
    return data;
  },

  getById: async (id: number) => {
    const { data } = await api.get(`/copilot/reports/${id}`);
    return data;
  },

  exportPdfUrl: (id: number) => `${api.defaults.baseURL}/copilot/reports/${id}/export/pdf`,
  exportDocxUrl: (id: number) => `${api.defaults.baseURL}/copilot/reports/${id}/export/docx`,
  export: async (id: number, format: ExportFormat) =>
    requestExport(`/copilot/reports/${id}/export/${format}`),
  download: async (id: number, format: ExportFormat) =>
    downloadExport(
      `/copilot/reports/${id}/export/${format}`,
      `report_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (id: number, format: ExportFormat) =>
    shareExport(
      `/copilot/reports/${id}/export/${format}`,
      `report_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share report ${id}`
    ),
  analyzeSchoolHealth: async (payload: {
    mandal_id?: number;
    school_ids?: number[];
  }) => {
    const { data } = await api.post('/copilot/school-health-analyzer', payload, { timeout: 90000 });
    return data;
  },
};

export const meoAssistantService = {
  generateEarlyWarning: async (payload: { mandal_id: number; context?: string }) => {
    const { data } = await api.post('/copilot/early-warning-assistant', payload, { timeout: 90000 });
    return data;
  },

  generateTeacherVacancyAssistant: async (payload: { mandal_id: number; context?: string }) => {
    const { data } = await api.post('/copilot/teacher-vacancy-assistant', payload, { timeout: 90000 });
    return data;
  },

  generateGovernanceCommunication: async (payload: { mandal_id: number; context?: string }) => {
    const { data } = await api.post('/copilot/governance-communication-assistant', payload, { timeout: 90000 });
    return data;
  },

  generateClusterBriefing: async (payload: { mandal_id: number; context?: string }) => {
    const { data } = await api.post('/copilot/cluster-governance-briefing', payload, { timeout: 90000 });
    return data;
  },
};

// ─── MEO Template-based Report Generator ─────────────────────────

export const schoolHealthService = {
  exportPdfUrl: (id: number) => `${api.defaults.baseURL}/copilot/school-health-analyses/${id}/export/pdf`,
  exportDocxUrl: (id: number) => `${api.defaults.baseURL}/copilot/school-health-analyses/${id}/export/docx`,
  export: async (id: number, format: ExportFormat) =>
    requestExport(`/copilot/school-health-analyses/${id}/export/${format}`),
  download: async (id: number, format: ExportFormat) =>
    downloadExport(
      `/copilot/school-health-analyses/${id}/export/${format}`,
      `school_health_analysis_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (id: number, format: ExportFormat) =>
    shareExport(
      `/copilot/school-health-analyses/${id}/export/${format}`,
      `school_health_analysis_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share School Health Analysis`
    ),
};

export const meoReportService = {
  listTemplates: async () => {
    const { data } = await api.get('/copilot/meo-reports/templates');
    return data;
  },

  generate: async (payload: {
    report_type: string;
    template_fields: Record<string, any>;
    language?: string;
  }) => {
    const { data } = await api.post('/copilot/meo-reports/generate', payload, { timeout: 90000 });
    return data;
  },

  getHistory: async (limit = 20) => {
    const { data } = await api.get('/copilot/meo-reports/history', { params: { limit } });
    return data;
  },

  getById: async (id: number) => {
    const { data } = await api.get(`/copilot/meo-reports/${id}`);
    return data;
  },

  exportPdfUrl: (id: number) => `${api.defaults.baseURL}/copilot/meo-reports/${id}/export/pdf`,
  exportDocxUrl: (id: number) => `${api.defaults.baseURL}/copilot/meo-reports/${id}/export/docx`,
  export: async (id: number, format: ExportFormat) =>
    requestExport(`/copilot/meo-reports/${id}/export/${format}`),
  download: async (id: number, format: ExportFormat) =>
    downloadExport(
      `/copilot/meo-reports/${id}/export/${format}`,
      `meo_report_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (id: number, format: ExportFormat) =>
    shareExport(
      `/copilot/meo-reports/${id}/export/${format}`,
      `meo_report_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share MEO report ${id}`
    ),
};

// ─── DEO Copilot Services ──────────────────────────────────────────

export const deoIntelligenceService = {
  generateBrief: async (districtId: number) => {
    const { data } = await api.post(`/deo/intelligence-brief?district_id=${districtId}`, null, { timeout: 120000 });
    return data;
  },

  getHistory: async (districtId: number, limit = 20) => {
    const { data } = await api.get(`/deo/intelligence-history?district_id=${districtId}&limit=${limit}`);
    return data;
  },

  getById: async (briefId: number) => {
    const { data } = await api.get(`/deo/intelligence/${briefId}`);
    return data;
  },

  getMandalPerformance: async (districtId: number) => {
    const { data } = await api.get(`/deo/mandal-performance?district_id=${districtId}`);
    return data;
  },

  // Export methods
  exportPdfUrl: (briefId: number) => `${api.defaults.baseURL}/deo/intelligence-brief/${briefId}/export/pdf`,
  exportDocxUrl: (briefId: number) => `${api.defaults.baseURL}/deo/intelligence-brief/${briefId}/export/docx`,
  export: async (briefId: number, format: ExportFormat) =>
    requestExport(`/deo/intelligence-brief/${briefId}/export/${format}`),
  download: async (briefId: number, format: ExportFormat) =>
    downloadExport(
      `/deo/intelligence-brief/${briefId}/export/${format}`,
      `intelligence_brief_${briefId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (briefId: number, format: ExportFormat) =>
    shareExport(
      `/deo/intelligence-brief/${briefId}/export/${format}`,
      `intelligence_brief_${briefId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share Intelligence Brief #${briefId}`
    ),

  // Mandal performance export
  mandalPerformanceExportUrl: (districtId: number, format: ExportFormat) =>
    `${api.defaults.baseURL}/deo/mandal-performance/export/${format}?district_id=${districtId}`,
  shareMandalPerformance: async (districtId: number, format: ExportFormat) =>
    shareExport(
      `/deo/mandal-performance/export/${format}?district_id=${districtId}`,
      `mandal_performance_${districtId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share Mandal Performance Report`
    ),
};

export const deoRiskMonitorService = {
  scanRisks: async (districtId: number) => {
    const { data } = await api.post(`/deo/risk-monitor?district_id=${districtId}`, null, { timeout: 120000 });
    return data;
  },

  getHistory: async (districtId: number, limit = 20) => {
    const { data } = await api.get(`/deo/risk-history?district_id=${districtId}&limit=${limit}`);
    return data;
  },

  // Export methods
  exportPdfUrl: (scanId: number) => `${api.defaults.baseURL}/deo/risk-monitor/${scanId}/export/pdf`,
  exportDocxUrl: (scanId: number) => `${api.defaults.baseURL}/deo/risk-monitor/${scanId}/export/docx`,
  export: async (scanId: number, format: ExportFormat) =>
    requestExport(`/deo/risk-monitor/${scanId}/export/${format}`),
  download: async (scanId: number, format: ExportFormat) =>
    downloadExport(
      `/deo/risk-monitor/${scanId}/export/${format}`,
      `risk_monitor_${scanId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (scanId: number, format: ExportFormat) =>
    shareExport(
      `/deo/risk-monitor/${scanId}/export/${format}`,
      `risk_monitor_${scanId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share Risk Monitor Report #${scanId}`
    ),
};

export const deoTeacherRationalizationService = {
  analyze: async (districtId: number) => {
    const { data } = await api.get(`/deo/teacher-rationalization?district_id=${districtId}`, { timeout: 120000 });
    return data;
  },

  generatePlan: async (districtId: number, context?: string) => {
    const { data } = await api.post('/deo/generate-rationalization-plan', { district_id: districtId, context }, { timeout: 120000 });
    return data;
  },

  // Export methods
  exportPdfUrl: (planId: number) => `${api.defaults.baseURL}/deo/teacher-rationalization/${planId}/export/pdf`,
  exportDocxUrl: (planId: number) => `${api.defaults.baseURL}/deo/teacher-rationalization/${planId}/export/docx`,
  export: async (planId: number, format: ExportFormat) =>
    requestExport(`/deo/teacher-rationalization/${planId}/export/${format}`),
  download: async (planId: number, format: ExportFormat) =>
    downloadExport(
      `/deo/teacher-rationalization/${planId}/export/${format}`,
      `teacher_rationalization_${planId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (planId: number, format: ExportFormat) =>
    shareExport(
      `/deo/teacher-rationalization/${planId}/export/${format}`,
      `teacher_rationalization_${planId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share Teacher Rationalization Report #${planId}`
    ),
};

export const deoCommunicationService = {
  listTemplates: async () => {
    const { data } = await api.get('/deo/communication-templates');
    return data;
  },

  generate: async (payload: {
    communication_type: string;
    template_fields: Record<string, any>;
    language?: string;
  }) => {
    const { data } = await api.post('/deo/generate-communication', payload, { timeout: 120000 });
    return data;
  },

  getHistory: async (limit = 20) => {
    const { data } = await api.get(`/deo/communication-history?limit=${limit}`);
    return data;
  },

  // Export methods
  exportPdfUrl: (commId: number) => `${api.defaults.baseURL}/deo/communication/${commId}/export/pdf`,
  exportDocxUrl: (commId: number) => `${api.defaults.baseURL}/deo/communication/${commId}/export/docx`,
  export: async (commId: number, format: ExportFormat) =>
    requestExport(`/deo/communication/${commId}/export/${format}`),
  download: async (commId: number, format: ExportFormat) =>
    downloadExport(
      `/deo/communication/${commId}/export/${format}`,
      `communication_${commId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),
  share: async (commId: number, format: ExportFormat) =>
    shareExport(
      `/deo/communication/${commId}/export/${format}`,
      `communication_${commId}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share Communication #${commId}`
    ),
};

// ─── Translation ──────────────────────────────────────────────────

export const translationService = {
  translate: async (payload: {
    source_language: string;
    target_language: string;
    text: string;
  }) => {
    const { data } = await api.post('/copilot/translate', payload, { timeout: 30000 });
    return data;
  },

  getHistory: async (limit = 20) => {
    const { data } = await api.get('/copilot/translations/history', { params: { limit } });
    return data;
  },

  getDocumentTranslation: async (id: number) => {
    const { data } = await api.get(`/copilot/document-translations/${id}`);
    return data;
  },

  downloadDocumentTranslation: async (id: number, format: ExportFormat) =>
    downloadExport(
      `/copilot/document-translations/${id}/export/${format}`,
      `document_translation_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ),

  shareDocumentTranslation: async (id: number, format: ExportFormat) =>
    shareExport(
      `/copilot/document-translations/${id}/export/${format}`,
      `document_translation_${id}.${format}`,
      format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'GET',
      `Share translated document ${id}`
    ),

  /** Upload a document (PDF/DOCX/TXT) and translate it between Telugu and English. */
  translateDocument: async (
    file: { uri: string; name: string; type: string },
    sourceLanguage: string = 'English',
    targetLanguage: string = 'Telugu',
    documentType?: string,
  ) => {
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.type,
    } as any);
    // Use inline URL params to avoid axios interceptor issues
    let url = `/copilot/translate-document?source_language=${encodeURIComponent(sourceLanguage)}&target_language=${encodeURIComponent(targetLanguage)}`;
    if (documentType) {
      url += `&document_type=${encodeURIComponent(documentType)}`;
    }
    const { data } = await api.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },
};
