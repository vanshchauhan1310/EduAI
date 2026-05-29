import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import Header from '../../components/common/Header';
import StatsCard from '../../components/common/StatsCard';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { analyticsService } from '../../services/analyticsService';
import { useAuthStore } from '../../store/authStore';
import { useAppStore } from '../../store/appStore';
import { Colors, Typography, Spacing } from '../../theme';
import { formatPercentage } from '../../utils/helpers';

export default function SchoolPerformance() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const academicYear = useAppStore((s) => s.selectedAcademicYear);
  const schoolId = user?.school_id ?? 1;

  const { data, isLoading } = useQuery({
    queryKey: ['school-performance', schoolId, academicYear],
    queryFn: () => analyticsService.getSchoolPerformance(schoolId, academicYear),
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading performance data..." />;

  const risk = data?.risk_breakdown ?? {};

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="School Performance" subtitle={`AY ${academicYear}`} />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.statsRow}>
          <StatsCard
            label="Total Students"
            value={data?.total_students ?? 0}
            icon="people-outline"
            accent={Colors.primary[600]}
            style={styles.statCard}
          />
          <StatsCard
            label="Attendance Rate"
            value={formatPercentage(data?.attendance_rate_30d ?? 0)}
            icon="calendar-outline"
            accent={Colors.success}
            style={styles.statCard}
          />
        </View>

        {/* Risk Breakdown */}
        <Text style={styles.sectionTitle}>Dropout Risk Breakdown</Text>
        <Card style={styles.riskCard}>
          {[
            { level: 'CRITICAL', color: Colors.danger },
            { level: 'HIGH',     color: '#f97316' },
            { level: 'MEDIUM',   color: Colors.warning },
            { level: 'LOW',      color: Colors.success },
          ].map(({ level, color }) => {
            const count = risk[level] ?? 0;
            const total = data?.total_students ?? 1;
            const pct = (count / total) * 100;
            return (
              <View key={level} style={styles.riskRow}>
                <View style={[styles.riskDot, { backgroundColor: color }]} />
                <Text style={styles.riskLevel}>{level}</Text>
                <View style={styles.riskBarBg}>
                  <View style={[styles.riskBarFill, { width: `${pct}%` as any, backgroundColor: color }]} />
                </View>
                <Text style={styles.riskCount}>{count}</Text>
              </View>
            );
          })}
        </Card>

        {/* AI Recommendation */}
        <Card style={styles.aiCard}>
          <View style={styles.aiHeader}>
            <View style={styles.aiIconBg}>
              <Text style={styles.aiIcon}>🤖</Text>
            </View>
            <Text style={styles.aiTitle}>AI Performance Insight</Text>
          </View>
          <Text style={styles.aiText}>
            {(risk['HIGH'] ?? 0) + (risk['CRITICAL'] ?? 0) > 5
              ? `${(risk['HIGH'] ?? 0) + (risk['CRITICAL'] ?? 0)} students require urgent intervention. Focus on attendance improvement and remedial classes.`
              : 'School performance indicators are within acceptable range. Continue monitoring monthly.'}
          </Text>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  statsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  statCard: { flex: 1 },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md, marginTop: Spacing.sm },
  riskCard: { gap: Spacing.md },
  riskRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  riskDot: { width: 10, height: 10, borderRadius: 5 },
  riskLevel: { width: 70, fontSize: Typography.sizes.sm, color: Colors.neutral[700], fontWeight: Typography.weights.medium },
  riskBarBg: { flex: 1, height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden' },
  riskBarFill: { height: '100%', borderRadius: 4 },
  riskCount: { width: 28, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[700], textAlign: 'right' },
  aiCard: { marginTop: Spacing.md, backgroundColor: Colors.primary[50] },
  aiHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  aiIconBg: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.primary[100], justifyContent: 'center', alignItems: 'center' },
  aiIcon: { fontSize: 18 },
  aiTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.primary[700] },
  aiText: { fontSize: Typography.sizes.sm, color: Colors.primary[800], lineHeight: 20 },
});
