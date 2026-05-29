import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import AttendanceDonut from '../../components/common/AttendanceDonut';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useStudentAttendanceSummary, useStudentAttendanceRecords } from '../../hooks/useAttendance';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { ATTENDANCE_STATUS_COLORS } from '../../constants';
import { AttendanceStatus } from '../../types';
import dayjs from 'dayjs';

export default function AttendanceScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const studentId = 101; // In production: from student profile linked to user

  const fromDate = dayjs().startOf('month').format('YYYY-MM-DD');
  const toDate = dayjs().format('YYYY-MM-DD');

  const { data: summary, isLoading: summaryLoading } = useStudentAttendanceSummary(studentId, fromDate, toDate);
  const { data: records = [], isLoading: recordsLoading } = useStudentAttendanceRecords(studentId);

  if (summaryLoading || recordsLoading) return <LoadingSpinner fullScreen message="Loading attendance..." />;

  const pct = summary?.attendance_percentage ?? 0;
  const statusToEmoji = (s: AttendanceStatus) => ({ PRESENT: '✅', ABSENT: '❌', LATE: '⏰', HALF_DAY: '🌓', HOLIDAY: '🎉', LEAVE: '📋' }[s] ?? '?');

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="My Attendance" subtitle={dayjs().format('MMMM YYYY')} />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Attendance Summary Card */}
        <Card style={styles.summaryCard}>
          <View style={styles.donutRow}>
            <AttendanceDonut percentage={pct} size={120} label="This Month" />
            <View style={styles.statsCol}>
              {[
                { label: 'Present', value: summary?.present_days ?? 0, color: Colors.success },
                { label: 'Absent',  value: summary?.absent_days ?? 0,  color: Colors.danger },
                { label: 'Late',    value: summary?.late_days ?? 0,    color: Colors.warning },
              ].map((s) => (
                <View key={s.label} style={styles.statRow}>
                  <View style={[styles.statDot, { backgroundColor: s.color }]} />
                  <Text style={styles.statLabel}>{s.label}</Text>
                  <Text style={styles.statVal}>{s.value}</Text>
                </View>
              ))}
            </View>
          </View>
          {(summary?.consecutive_absences ?? 0) > 0 && (
            <View style={styles.warning}>
              <Text style={styles.warningText}>
                ⚠️ You have {summary?.consecutive_absences} consecutive absence{summary?.consecutive_absences === 1 ? '' : 's'}. Please inform your teacher.
              </Text>
            </View>
          )}
        </Card>

        {/* Recent Records */}
        <Text style={styles.sectionTitle}>Recent Attendance</Text>
        {records.slice(0, 15).map((record: any) => (
          <View key={record.id} style={styles.recordRow}>
            <Text style={styles.recordEmoji}>{statusToEmoji(record.status)}</Text>
            <Text style={styles.recordDate}>{dayjs(record.date).format('ddd, DD MMM')}</Text>
            <View style={[styles.recordBadge, { backgroundColor: `${ATTENDANCE_STATUS_COLORS[record.status as AttendanceStatus]}20` }]}>
              <Text style={[styles.recordStatus, { color: ATTENDANCE_STATUS_COLORS[record.status as AttendanceStatus] }]}>
                {record.status}
              </Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  summaryCard: { marginBottom: Spacing.lg },
  donutRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xl },
  statsCol: { flex: 1, gap: Spacing.md },
  statRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  statDot: { width: 8, height: 8, borderRadius: 4 },
  statLabel: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  statVal: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  warning: {
    backgroundColor: '#fef3c7',
    borderRadius: BorderRadius.lg,
    padding: Spacing.sm,
    marginTop: Spacing.md,
  },
  warningText: { fontSize: Typography.sizes.sm, color: '#92400e', lineHeight: 18 },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md },
  recordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    marginBottom: 8,
    gap: Spacing.md,
    ...require('../../theme').Shadows.sm,
  },
  recordEmoji: { fontSize: 20, width: 28, textAlign: 'center' },
  recordDate: { flex: 1, fontSize: Typography.sizes.base, color: Colors.neutral[700], fontWeight: Typography.weights.medium },
  recordBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  recordStatus: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
});
