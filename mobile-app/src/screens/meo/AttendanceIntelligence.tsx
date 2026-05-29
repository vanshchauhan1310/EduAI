import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import StatsCard from '../../components/common/StatsCard';
import AttendanceDonut from '../../components/common/AttendanceDonut';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { attendanceService } from '../../services/attendanceService';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import dayjs from 'dayjs';

export default function AttendanceIntelligence() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const schoolId = user?.school_id ?? 1;
  const today = dayjs().format('YYYY-MM-DD');

  const { data, isLoading } = useQuery({
    queryKey: ['school-daily-att', schoolId, today],
    queryFn: () => attendanceService.getSchoolDailySummary(schoolId, today),
    refetchInterval: 3 * 60 * 1000,
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading attendance data..." />;

  const rate = data?.rate ?? 0;
  const total = data?.total ?? 0;
  const present = data?.present ?? 0;
  const absent = data?.absent ?? 0;

  const alerts = [];
  if (rate < 75) alerts.push({ msg: `Low attendance: ${rate.toFixed(1)}%`, level: 'CRITICAL' });
  else if (rate < 85) alerts.push({ msg: `Attendance below target: ${rate.toFixed(1)}%`, level: 'HIGH' });

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Attendance Intelligence" subtitle={dayjs().format('dddd, D MMMM')} />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Today's Overview */}
        <Card style={styles.todayCard}>
          <Text style={styles.todayLabel}>Today's District Attendance</Text>
          <View style={styles.donutRow}>
            <AttendanceDonut percentage={rate} size={120} label="Today" />
            <View style={styles.statsBlock}>
              <View style={styles.statItem}>
                <View style={[styles.dot, { backgroundColor: Colors.success }]} />
                <View>
                  <Text style={styles.statCount}>{present}</Text>
                  <Text style={styles.statDesc}>Present</Text>
                </View>
              </View>
              <View style={styles.statItem}>
                <View style={[styles.dot, { backgroundColor: Colors.danger }]} />
                <View>
                  <Text style={styles.statCount}>{absent}</Text>
                  <Text style={styles.statDesc}>Absent</Text>
                </View>
              </View>
              <View style={styles.statItem}>
                <View style={[styles.dot, { backgroundColor: Colors.neutral[300] }]} />
                <View>
                  <Text style={styles.statCount}>{total}</Text>
                  <Text style={styles.statDesc}>Total</Text>
                </View>
              </View>
            </View>
          </View>
        </Card>

        {/* Anomaly Alerts */}
        {alerts.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Anomaly Alerts</Text>
            {alerts.map((a, i) => (
              <Card key={i} style={[styles.alertCard, { borderColor: a.level === 'CRITICAL' ? Colors.danger : Colors.warning }]} variant="outlined">
                <View style={styles.alertRow}>
                  <Ionicons
                    name="warning"
                    size={20}
                    color={a.level === 'CRITICAL' ? Colors.danger : Colors.warning}
                  />
                  <Text style={[styles.alertText, { color: a.level === 'CRITICAL' ? Colors.danger : '#b45309' }]}>
                    {a.msg}
                  </Text>
                </View>
              </Card>
            ))}
          </>
        )}

        {/* Weekly Trend (placeholder bars) */}
        <Text style={styles.sectionTitle}>This Week's Trend</Text>
        <Card style={styles.trendCard}>
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].map((day, i) => {
            const mockRate = 75 + Math.random() * 20;
            const color = mockRate >= 85 ? Colors.success : mockRate >= 75 ? Colors.warning : Colors.danger;
            return (
              <View key={day} style={styles.trendItem}>
                <View style={styles.trendBarBg}>
                  <View style={[styles.trendBarFill, { height: `${mockRate}%` as any, backgroundColor: color }]} />
                </View>
                <Text style={styles.trendPct}>{mockRate.toFixed(0)}%</Text>
                <Text style={styles.trendDay}>{day}</Text>
              </View>
            );
          })}
        </Card>

        {/* Insight Tips */}
        <Card style={styles.tipsCard}>
          <View style={styles.tipsHeader}>
            <Ionicons name="bulb-outline" size={20} color={Colors.primary[600]} />
            <Text style={styles.tipsTitle}>AI Insights</Text>
          </View>
          <Text style={styles.tipText}>
            • {absent > 10 ? `${absent} students absent today — consider parent WhatsApp alerts` : 'Attendance is within normal range today'}
          </Text>
          <Text style={styles.tipText}>
            • Monitor mid-week dips — highest risk of chronic absenteeism on Wednesdays
          </Text>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  todayCard: { marginBottom: Spacing.md },
  todayLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginBottom: Spacing.md, fontWeight: Typography.weights.semibold },
  donutRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xl },
  statsBlock: { flex: 1, gap: Spacing.md },
  statItem: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  dot: { width: 10, height: 10, borderRadius: 5 },
  statCount: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  statDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.sm, marginTop: Spacing.sm },
  alertCard: { marginBottom: Spacing.sm },
  alertRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  alertText: { fontSize: Typography.sizes.sm, flex: 1, fontWeight: Typography.weights.medium },
  trendCard: {
    flexDirection: 'row',
    gap: Spacing.sm,
    justifyContent: 'space-between',
    height: 140,
    alignItems: 'flex-end',
    padding: Spacing.md,
  },
  trendItem: { flex: 1, alignItems: 'center', gap: 4 },
  trendBarBg: {
    flex: 1,
    width: '100%',
    backgroundColor: Colors.neutral[100],
    borderRadius: 4,
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },
  trendBarFill: { width: '100%', borderRadius: 4 },
  trendPct: { fontSize: Typography.sizes.xs, color: Colors.neutral[600], fontWeight: Typography.weights.semibold },
  trendDay: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  tipsCard: { marginTop: Spacing.md },
  tipsHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  tipsTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.primary[700] },
  tipText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20, marginBottom: 6 },
});
