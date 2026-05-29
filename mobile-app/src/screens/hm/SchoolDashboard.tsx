import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import StatsCard from '../../components/common/StatsCard';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AttendanceDonut from '../../components/common/AttendanceDonut';
import { analyticsService } from '../../services/analyticsService';
import { attendanceService } from '../../services/attendanceService';
import { useAuthStore } from '../../store/authStore';
import { useAppStore } from '../../store/appStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { formatPercentage } from '../../utils/helpers';
import dayjs from 'dayjs';

export default function SchoolDashboard() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const academicYear = useAppStore((s) => s.selectedAcademicYear);
  const schoolId = user?.school_id ?? 1;
  const today = dayjs().format('YYYY-MM-DD');

  const { data: perfData, isLoading: perfLoading, refetch, isRefetching } = useQuery({
    queryKey: ['school-performance', schoolId, academicYear],
    queryFn: () => analyticsService.getSchoolPerformance(schoolId, academicYear),
  });

  const { data: attData, isLoading: attLoading } = useQuery({
    queryKey: ['school-daily-att', schoolId, today],
    queryFn: () => attendanceService.getSchoolDailySummary(schoolId, today),
    refetchInterval: 5 * 60 * 1000,
  });

  const { data: healthData } = useQuery({
    queryKey: ['school-health', schoolId],
    queryFn: () => analyticsService.getSchoolHealthScore(schoolId),
  });

  if (perfLoading || attLoading) return <LoadingSpinner fullScreen message="Loading school data..." />;

  const attRate = attData?.rate ?? 0;
  const totalStudents = perfData?.total_students ?? 0;
  const riskBreakdown = perfData?.risk_breakdown ?? {};
  const highRiskCount = (riskBreakdown['HIGH'] ?? 0) + (riskBreakdown['CRITICAL'] ?? 0);

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="School Dashboard"
        subtitle={user?.full_name ?? 'Headmaster'}
        rightAction={{ icon: 'notifications-outline', onPress: () => {} }}
      />

      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Welcome */}
        <View style={styles.welcome}>
          <Text style={styles.welcomeName}>Good Morning, {user?.full_name?.split(' ')[0]} 👋</Text>
          <Text style={styles.welcomeRole}>Headmaster • {dayjs().format('dddd, D MMMM')}</Text>
        </View>

        {/* Health Score Banner */}
        {healthData && (
          <Card style={[styles.healthBanner, {
            backgroundColor: (healthData.health_score ?? 0) >= 80 ? '#f0fdf4' : (healthData.health_score ?? 0) >= 60 ? '#fffbeb' : '#fef2f2',
          }]}>
            <View style={styles.healthRow}>
              <View>
                <Text style={styles.healthLabel}>School Health Score</Text>
                <Text style={styles.healthScore}>{(healthData.health_score ?? 0).toFixed(0)}/100</Text>
                <Text style={styles.healthGrade}>Grade: {healthData.grade}</Text>
              </View>
              <View style={[styles.healthBadge, {
                backgroundColor: (healthData.health_score ?? 0) >= 80 ? '#22c55e' : (healthData.health_score ?? 0) >= 60 ? '#f59e0b' : '#ef4444',
              }]}>
                <Text style={styles.healthBadgeText}>{healthData.grade}</Text>
              </View>
            </View>
          </Card>
        )}

        {/* Today's Attendance */}
        <Text style={styles.sectionTitle}>Today's Attendance</Text>
        <Card style={styles.attCard}>
          <View style={styles.attRow}>
            <AttendanceDonut percentage={attRate} size={110} label="Today" />
            <View style={styles.attStats}>
              <View style={styles.attStat}>
                <View style={[styles.attDot, { backgroundColor: Colors.success }]} />
                <Text style={styles.attStatLabel}>Present</Text>
                <Text style={styles.attStatValue}>{attData?.present ?? 0}</Text>
              </View>
              <View style={styles.attStat}>
                <View style={[styles.attDot, { backgroundColor: Colors.danger }]} />
                <Text style={styles.attStatLabel}>Absent</Text>
                <Text style={styles.attStatValue}>{attData?.absent ?? 0}</Text>
              </View>
              <View style={styles.attStat}>
                <View style={[styles.attDot, { backgroundColor: Colors.neutral[300] }]} />
                <Text style={styles.attStatLabel}>Total</Text>
                <Text style={styles.attStatValue}>{attData?.total ?? 0}</Text>
              </View>
            </View>
          </View>
        </Card>

        {/* KPIs */}
        <View style={styles.kpiRow}>
          <StatsCard
            label="Total Students"
            value={totalStudents}
            icon="people-outline"
            accent={Colors.primary[600]}
            style={styles.kpiCard}
          />
          <StatsCard
            label="High Risk Students"
            value={highRiskCount}
            icon="alert-circle-outline"
            accent={Colors.danger}
            style={styles.kpiCard}
          />
        </View>

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actions}>
          {[
            { icon: 'checkbox-outline',     label: 'Mark Attendance',   color: Colors.primary[600] },
            { icon: 'people-outline',        label: 'Student Monitor',   color: Colors.secondary[600] },
            { icon: 'document-text-outline', label: 'Assessments',       color: Colors.success },
            { icon: 'chatbubbles-outline',   label: 'Parent Messages',   color: Colors.warning },
            { icon: 'analytics-outline',     label: 'AI Insights',       color: Colors.danger },
            { icon: 'ribbon-outline',        label: 'Achievements',      color: '#8b5cf6' },
          ].map((a) => (
            <TouchableOpacity key={a.label} style={styles.actionItem}>
              <View style={[styles.actionIcon, { backgroundColor: `${a.color}18` }]}>
                <Ionicons name={a.icon as any} size={24} color={a.color} />
              </View>
              <Text style={styles.actionLabel}>{a.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  welcome: { marginBottom: Spacing.lg },
  welcomeName: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  welcomeRole: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 2 },
  healthBanner: { marginBottom: Spacing.md, borderRadius: 16, padding: Spacing.md },
  healthRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  healthLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },
  healthScore: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: 2 },
  healthGrade: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },
  healthBadge: {
    width: 52,
    height: 52,
    borderRadius: 26,
    justifyContent: 'center',
    alignItems: 'center',
  },
  healthBadgeText: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.white },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md, marginTop: Spacing.sm },
  attCard: { marginBottom: Spacing.md },
  attRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xl },
  attStats: { flex: 1, gap: Spacing.sm },
  attStat: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  attDot: { width: 8, height: 8, borderRadius: 4 },
  attStatLabel: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginLeft: Spacing.sm },
  attStatValue: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  kpiRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  kpiCard: { flex: 1 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  actionItem: {
    width: '30%',
    flexGrow: 1,
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: Spacing.md,
    alignItems: 'center',
    gap: Spacing.sm,
    ...require('../../theme').Shadows.sm,
  },
  actionIcon: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
  actionLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[700], textAlign: 'center', fontWeight: Typography.weights.medium },
});
