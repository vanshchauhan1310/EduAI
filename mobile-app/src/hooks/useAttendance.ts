import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceService } from '../services/attendanceService';
import { QUERY_KEYS } from '../constants';
import { AttendanceStatus } from '../types';
import dayjs from 'dayjs';

export function useStudentAttendanceSummary(
  studentId: number,
  fromDate?: string,
  toDate?: string
) {
  const from = fromDate ?? dayjs().startOf('month').format('YYYY-MM-DD');
  const to = toDate ?? dayjs().format('YYYY-MM-DD');

  return useQuery({
    queryKey: [QUERY_KEYS.ATTENDANCE, 'student', studentId, from, to],
    queryFn: () => attendanceService.getStudentSummary(studentId, from, to),
    enabled: studentId > 0,
  });
}

export function useStudentAttendanceRecords(
  studentId: number,
  fromDate?: string,
  toDate?: string
) {
  const from = fromDate ?? dayjs().subtract(30, 'day').format('YYYY-MM-DD');
  const to = toDate ?? dayjs().format('YYYY-MM-DD');

  return useQuery({
    queryKey: [QUERY_KEYS.ATTENDANCE, 'records', studentId, from, to],
    queryFn: () => attendanceService.getStudentRecords(studentId, from, to),
    enabled: studentId > 0,
  });
}

export function useSchoolDailyAttendance(schoolId: number, date?: string) {
  const attendanceDate = date ?? dayjs().format('YYYY-MM-DD');

  return useQuery({
    queryKey: [QUERY_KEYS.ATTENDANCE, 'school-daily', schoolId, attendanceDate],
    queryFn: () => attendanceService.getSchoolDailySummary(schoolId, attendanceDate),
    enabled: schoolId > 0,
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 min
  });
}

export function useMarkAttendance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: {
      reference_type: 'STUDENT' | 'TEACHER';
      reference_id: number;
      school_id: number;
      date: string;
      status: AttendanceStatus;
      class_id?: number;
      section?: string;
    }) => attendanceService.mark(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ATTENDANCE] });
    },
  });
}

export function useBulkMarkAttendance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: attendanceService.bulkMark,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ATTENDANCE] });
    },
  });
}
