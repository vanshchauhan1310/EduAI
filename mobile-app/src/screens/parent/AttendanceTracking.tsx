import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import AttendanceDonut from '../../components/common/AttendanceDonut';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import dayjs from 'dayjs';

const MOCK_CHILD = { name: 'Arjun Kumar', class: '7A', admission_no: 'A001', school: 'ZPHS Venkatapuram' };

const MOCK_MONTHLY = [
  { month: 'March', present: 22, total: 24, rate: 91.7 },
  { month: 'April', present: 20, total: 24, rate: 83.3 },
  { month: 'May',   present: 19, total: 22, rate: 86.4 },
];

const RECENT = [
  { date: '2025-05-29', status: 'PRESENT' },
  { date: '2025-05-28', status: 'PRESENT' },
  { date: '2025-05-27', status: 'ABSENT' },
  { date: '2025-05-26', status: 'PRESENT' },
  { date: '2025-05-25', status: 'LATE' },
];

const STATUS_COLORS: Record<string, string> = { PRESENT: Colors.success, ABSENT: Colors.danger, LATE: Colors.warning };
const STATUS_EMOJI: Record<string, string> = { PRESENT: '✅', ABSENT: '❌', LATE: '⏰' };

export default function AttendanceTracking() {
  const insets = useSafeAreaInsets();
  const currentMonth = MOCK_MONTHLY[MOCK_MONTHLY.length - 1];

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Attendance Tracker" subtitle={MOCK_CHILD.name} />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Child Summary */}
        <Card style={styles.childCard}>
          <View style={styles.childRow}>
            <View style={styles.childAvatar}>
              <Text style={styles.childAvatarText}>{MOCK_CHILD.name.charAt(0)}</Text>
            </View>
            <View>
              <Text style={styles.childName}>{MOCK_CHILD.name}</Text>
              <Text style={styles.childMeta}>Class {MOCK_CHILD.class} • {MOCK_CHILD.admission_no}</Text>
              <Text style={styles.childSchool}>{MOCK_CHILD.school}</Text>
            </View>
          </View>
        </Card>

        {/* This Month */}
        <Card style={styles.monthCard}>
          <Text style={styles.monthLabel}>This Month ({dayjs().format('MMMM YYYY')})</Text>
          <View style={styles.donutRow}>
            <AttendanceDonut percentage={currentMonth.rate} size={110} label="Attendance" />
            <View style={styles.statsCol}>
              <View style={styles.statRow}>
                <View style={[styles.dot, { backgroundColor: Colors.success }]} />
                <Text style={styles.statLabel}>Present</Text>
                <Text style={styles.statVal}>{currentMonth.present} days</Text>
              </View>
              <View style={styles.statRow}>
                <View style={[styles.dot, { backgroundColor: Colors.danger }]} />
                <Text style={styles.statLabel}>Absent</Text>
                <Text style={styles.statVal}>{currentMonth.total - currentMonth.present} days</Text>
              </View>
              <View style={styles.statRow}>
                <View style={[styles.dot, { backgroundColor: Colors.neutral[300] }]} />
                <Text style={styles.statLabel}>School Days</Text>
                <Text style={styles.statVal}>{currentMonth.total} days</Text>
              </View>
            </View>
          </View>
        </Card>

        {/* 3-Month Trend */}
        <Text style={styles.sectionTitle}>Monthly Trend</Text>
        <Card>
          {MOCK_MONTHLY.map((m) => (
            <View key={m.month} style={styles.trendRow}>
              <Text style={styles.trendMonth}>{m.month}</Text>
              <View style={styles.trendBarBg}>
                <View style={[styles.trendBarFill, {
                  width: `${m.rate}%` as any,
                  backgroundColor: m.rate >= 85 ? Colors.success : m.rate >= 75 ? Colors.warning : Colors.danger,
                }]} />
              </View>
              <Text style={[styles.trendPct, { color: m.rate >= 85 ? Colors.success : m.rate >= 75 ? Colors.warning : Colors.danger }]}>
                {m.rate.toFixed(1)}%
              </Text>
            </View>
          ))}
        </Card>

        {/* Recent Days */}
        <Text style={styles.sectionTitle}>Recent Days</Text>
        {RECENT.map((r) => (
          <View key={r.date} style={styles.recentRow}>
            <Text style={styles.recentEmoji}>{STATUS_EMOJI[r.status] ?? '?'}</Text>
            <Text style={styles.recentDate}>{dayjs(r.date).format('ddd, DD MMM')}</Text>
            <View style={[styles.statusBadge, { backgroundColor: `${STATUS_COLORS[r.status]}20` }]}>
              <Text style={[styles.statusText, { color: STATUS_COLORS[r.status] }]}>{r.status}</Text>
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
  childCard: { marginBottom: Spacing.md },
  childRow: { flexDirection: 'row', gap: Spacing.md, alignItems: 'center' },
  childAvatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: Colors.primary[600], justifyContent: 'center', alignItems: 'center' },
  childAvatarText: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.white },
  childName: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  childMeta: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 2 },
  childSchool: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 1 },
  monthCard: { marginBottom: Spacing.md },
  monthLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginBottom: Spacing.md, fontWeight: Typography.weights.semibold },
  donutRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xl },
  statsCol: { flex: 1, gap: Spacing.md },
  statRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  dot: { width: 8, height: 8, borderRadius: 4 },
  statLabel: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  statVal: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.sm, marginTop: Spacing.md },
  trendRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.md },
  trendMonth: { width: 48, fontSize: Typography.sizes.sm, color: Colors.neutral[600], fontWeight: Typography.weights.medium },
  trendBarBg: { flex: 1, height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden' },
  trendBarFill: { height: '100%', borderRadius: 4 },
  trendPct: { width: 42, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, textAlign: 'right' },
  recentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    marginBottom: 8,
    gap: Spacing.md,
    ...require('../../theme').Shadows.sm,
  },
  recentEmoji: { fontSize: 20, width: 28, textAlign: 'center' },
  recentDate: { flex: 1, fontSize: Typography.sizes.base, color: Colors.neutral[700], fontWeight: Typography.weights.medium },
  statusBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  statusText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
});
