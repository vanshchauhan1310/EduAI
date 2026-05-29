import React, { useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity, Switch,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import { useBulkMarkAttendance } from '../../hooks/useAttendance';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { ATTENDANCE_STATUS_COLORS } from '../../constants';
import { AttendanceStatus } from '../../types';
import dayjs from 'dayjs';

const MOCK_STUDENTS = [
  { id: 101, name: 'Arjun Reddy',    admission_no: 'A001' },
  { id: 102, name: 'Priya Sharma',   admission_no: 'A002' },
  { id: 103, name: 'Venkat Rao',     admission_no: 'A003' },
  { id: 104, name: 'Lakshmi Devi',   admission_no: 'A004' },
  { id: 105, name: 'Rahul Kumar',    admission_no: 'A005' },
  { id: 106, name: 'Divya Patel',    admission_no: 'A006' },
];

type AttendanceMap = Record<number, AttendanceStatus>;

export default function AttendanceScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const { mutate: bulkMark, isPending } = useBulkMarkAttendance();
  const today = dayjs().format('YYYY-MM-DD');

  const [attendance, setAttendance] = useState<AttendanceMap>(() =>
    Object.fromEntries(MOCK_STUDENTS.map((s) => [s.id, 'PRESENT' as AttendanceStatus]))
  );
  const [submitted, setSubmitted] = useState(false);

  const toggle = (id: number) => {
    setAttendance((prev) => ({
      ...prev,
      [id]: prev[id] === 'PRESENT' ? 'ABSENT' : 'PRESENT',
    }));
  };

  const presentCount = Object.values(attendance).filter((v) => v === 'PRESENT').length;
  const absentCount = MOCK_STUDENTS.length - presentCount;

  const handleSubmit = () => {
    bulkMark({
      reference_type: 'STUDENT',
      school_id: user?.school_id ?? 1,
      date: today,
      records: MOCK_STUDENTS.map((s) => ({ reference_id: s.id, status: attendance[s.id] })),
    }, {
      onSuccess: () => setSubmitted(true),
    });
  };

  if (submitted) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Attendance" />
        <View style={styles.successState}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>Attendance Submitted!</Text>
          <Text style={styles.successSub}>
            {presentCount} present • {absentCount} absent
          </Text>
          <Button title="Mark Another Class" onPress={() => setSubmitted(false)} style={styles.resetBtn} />
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Mark Attendance" subtitle={dayjs().format('DD MMM YYYY')} />

      {/* Summary Bar */}
      <View style={styles.summary}>
        <View style={styles.summaryItem}>
          <View style={[styles.summaryDot, { backgroundColor: Colors.success }]} />
          <Text style={styles.summaryText}>Present: <Text style={styles.summaryBold}>{presentCount}</Text></Text>
        </View>
        <View style={styles.summaryItem}>
          <View style={[styles.summaryDot, { backgroundColor: Colors.danger }]} />
          <Text style={styles.summaryText}>Absent: <Text style={styles.summaryBold}>{absentCount}</Text></Text>
        </View>
        <TouchableOpacity onPress={() => setAttendance(Object.fromEntries(MOCK_STUDENTS.map((s) => [s.id, 'PRESENT'])))}>
          <Text style={styles.markAll}>Mark All Present</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={MOCK_STUDENTS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const status = attendance[item.id];
          const isPresent = status === 'PRESENT';
          return (
            <View style={[styles.studentRow, !isPresent && styles.absentRow]}>
              <View style={[styles.avatar, { backgroundColor: isPresent ? Colors.primary[100] : Colors.neutral[100] }]}>
                <Text style={[styles.avatarText, { color: isPresent ? Colors.primary[700] : Colors.neutral[400] }]}>
                  {item.name.charAt(0)}
                </Text>
              </View>
              <View style={styles.nameBlock}>
                <Text style={[styles.studentName, !isPresent && styles.absentText]}>{item.name}</Text>
                <Text style={styles.admNo}>{item.admission_no}</Text>
              </View>
              <View style={[styles.statusBadge, { backgroundColor: isPresent ? '#dcfce7' : '#fee2e2' }]}>
                <Text style={[styles.statusText, { color: isPresent ? '#166534' : '#991b1b' }]}>
                  {status}
                </Text>
              </View>
              <Switch
                value={isPresent}
                onValueChange={() => toggle(item.id)}
                trackColor={{ false: '#fca5a5', true: '#86efac' }}
                thumbColor={isPresent ? Colors.success : Colors.danger}
              />
            </View>
          );
        }}
        ListFooterComponent={
          <View style={styles.footer}>
            <Button
              title={`Submit Attendance (${MOCK_STUDENTS.length} students)`}
              onPress={handleSubmit}
              loading={isPending}
              fullWidth
              size="lg"
            />
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  summary: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: Spacing.lg,
  },
  summaryItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  summaryDot: { width: 8, height: 8, borderRadius: 4 },
  summaryText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  summaryBold: { fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  markAll: { marginLeft: 'auto', fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
  list: { padding: Spacing.base, gap: Spacing.sm },
  studentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    gap: Spacing.md,
    ...require('../../theme').Shadows.sm,
  },
  absentRow: { backgroundColor: '#fff5f5' },
  avatar: { width: 42, height: 42, borderRadius: 21, justifyContent: 'center', alignItems: 'center' },
  avatarText: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold },
  nameBlock: { flex: 1 },
  studentName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  absentText: { color: Colors.neutral[400] },
  admNo: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 1 },
  statusBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  statusText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  footer: { padding: Spacing.lg },
  successState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: Spacing['2xl'] },
  successIcon: { fontSize: 64, marginBottom: Spacing.lg },
  successTitle: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  successSub: { fontSize: Typography.sizes.base, color: Colors.neutral[500], marginTop: Spacing.sm },
  resetBtn: { marginTop: Spacing.xl },
});
