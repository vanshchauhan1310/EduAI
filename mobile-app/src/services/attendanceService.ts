import api from './api';
import { AttendanceRecord, AttendanceSummary, AttendanceStatus } from '../types';

interface MarkAttendancePayload {
  reference_type: 'STUDENT' | 'TEACHER';
  reference_id: number;
  school_id: number;
  date: string;
  status: AttendanceStatus;
  session?: string;
  class_id?: number;
  section?: string;
  latitude?: number;
  longitude?: number;
  remarks?: string;
}

interface BulkAttendanceItem {
  reference_id: number;
  status: AttendanceStatus;
  remarks?: string;
}

interface BulkAttendancePayload {
  reference_type: 'STUDENT' | 'TEACHER';
  school_id: number;
  class_id?: number;
  section?: string;
  date: string;
  session?: string;
  records: BulkAttendanceItem[];
  latitude?: number;
  longitude?: number;
}

export const attendanceService = {
  mark: async (payload: MarkAttendancePayload): Promise<AttendanceRecord> => {
    const { data } = await api.post('/attendance/mark', payload);
    return data;
  },

  bulkMark: async (payload: BulkAttendancePayload): Promise<{ marked: number; skipped: number }> => {
    const { data } = await api.post('/attendance/mark/bulk', payload);
    return data;
  },

  getStudentSummary: async (
    studentId: number, fromDate: string, toDate: string
  ): Promise<AttendanceSummary> => {
    const { data } = await api.get(`/attendance/student/${studentId}/summary`, {
      params: { from_date: fromDate, to_date: toDate },
    });
    return data;
  },

  getStudentRecords: async (
    studentId: number, fromDate: string, toDate: string
  ): Promise<AttendanceRecord[]> => {
    const { data } = await api.get(`/attendance/student/${studentId}/records`, {
      params: { from_date: fromDate, to_date: toDate },
    });
    return data;
  },

  getSchoolDailySummary: async (schoolId: number, date: string) => {
    const { data } = await api.get(`/attendance/school/${schoolId}/daily`, {
      params: { report_date: date },
    });
    return data;
  },
};
