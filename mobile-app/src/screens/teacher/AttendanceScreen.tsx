import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, Switch } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import { useBulkMarkAttendance } from '../../hooks/useAttendance';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { AttendanceStatus } from '../../types';
import dayjs from 'dayjs';

const MOCK_CLASS = [
  { id: 201, name: 'Aditya Varma',  roll: '01' },
  { id: 202, name: 'Bhavana Reddy', roll: '02' },
  { id: 203, name: 'Charan Kumar',  roll: '03' },
  { id: 204, name: 'Deepika Rao',   roll: '04' },
  { id: 205, name: 'Eswar Naidu',   roll: '05' },
  { id: 206, name: 'Fathima Banu',  roll: '06' },
];

type StatusMap = Record<number, AttendanceStatus>;

export default function AttendanceScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const { mutate: bulkMark, isPending } = useBulkMarkAttendance();
  const [status, setStatus] = useState<StatusMap>(() =>
    Object.fromEntries(MOCK_CLASS.map((s) => [s.id, 'PRESENT' as AttendanceStatus]))
  );
  const [done, setDone] = useState(false);

  const presentCount = Object.values(status).filter((v) => v === 'PRESENT').length;

  const handleSubmit = () => {
    bulkMark({
      reference_type: 'STUDENT',
      school_id: user?.school_id ?? 1,
      class_id: 7,
      date: dayjs().format('YYYY-MM-DD'),
      records: MOCK_CLASS.map((s) => ({ reference_id: s.id, status: status[s.id] })),
    }, { onSuccess: () => setDone(true) });
  };

  if (done) {
    return (
      <View style={[styles.flex, styles.center, { paddingBottom: insets.bottom }]}>
        <Ionicons name="checkmark-circle" size={72} color={Colors.success} />
        <Text style={styles.doneTitle}>Attendance Saved!</Text>
        <Text style={styles.doneSub}>{presentCount}/{MOCK_CLASS.length} present today</Text>
        <Button title="Mark Another" onPress={() => setDone(false)} style={styles.doneBtn} />
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Mark Attendance" subtitle={`Class 7 • ${dayjs().format('DD MMM')}`} />

      <View style={styles.summary}>
        <Text style={styles.summaryText}>
          <Text style={styles.bold}>{presentCount}</Text> present •{' '}
          <Text style={[styles.bold, { color: Colors.danger }]}>{MOCK_CLASS.length - presentCount}</Text> absent
        </Text>
        <TouchableOpacity
          onPress={() => setStatus(Object.fromEntries(MOCK_CLASS.map((s) => [s.id, 'PRESENT'])))}
        >
          <Text style={styles.markAll}>All Present</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={MOCK_CLASS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => {
          const isPresent = status[item.id] === 'PRESENT';
          return (
            <View style={[styles.row, !isPresent && styles.absentRow]}>
              <Text style={styles.roll}>{item.roll}</Text>
              <View style={styles.nameBlock}>
                <Text style={[styles.name, !isPresent && { color: Colors.neutral[400] }]}>{item.name}</Text>
              </View>
              <Text style={[styles.statusLabel, { color: isPresent ? Colors.success : Colors.danger }]}>
                {isPresent ? 'P' : 'A'}
              </Text>
              <Switch
                value={isPresent}
                onValueChange={() => setStatus((p) => ({
                  ...p,
                  [item.id]: p[item.id] === 'PRESENT' ? 'ABSENT' : 'PRESENT',
                }))}
                trackColor={{ false: '#fca5a5', true: '#86efac' }}
                thumbColor={isPresent ? Colors.success : Colors.danger}
              />
            </View>
          );
        }}
        ListFooterComponent={
          <View style={styles.footer}>
            <Button title="Submit Attendance" onPress={handleSubmit} loading={isPending} fullWidth size="lg" />
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  center: { justifyContent: 'center', alignItems: 'center', padding: Spacing['2xl'] },
  summary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  summaryText: { fontSize: Typography.sizes.base, color: Colors.neutral[700] },
  bold: { fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  markAll: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.semibold },
  list: { padding: Spacing.base, gap: 8 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    gap: Spacing.md,
    ...require('../../theme').Shadows.sm,
  },
  absentRow: { backgroundColor: '#fff5f5' },
  roll: { width: 28, fontSize: Typography.sizes.sm, color: Colors.neutral[400], fontWeight: Typography.weights.bold },
  nameBlock: { flex: 1 },
  name: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.medium, color: Colors.neutral[900] },
  statusLabel: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, width: 24, textAlign: 'center' },
  footer: { padding: Spacing.base },
  doneTitle: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: Spacing.lg },
  doneSub: { fontSize: Typography.sizes.base, color: Colors.neutral[500], marginTop: Spacing.sm },
  doneBtn: { marginTop: Spacing.xl },
});
