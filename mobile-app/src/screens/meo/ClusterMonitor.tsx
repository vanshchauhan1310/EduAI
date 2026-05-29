import React from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import StatsCard from '../../components/common/StatsCard';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { analyticsService } from '../../services/analyticsService';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { formatPercentage } from '../../utils/helpers';

export default function ClusterMonitor() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const mandalId = user?.mandal_id ?? 1;

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['mandal_overview', mandalId],
    queryFn: () => analyticsService.getMandalOverview(mandalId),
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading cluster data..." />;

  const schools: any[] = data?.schools ?? [];

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Cluster Monitor" subtitle={`Mandal: ${user?.full_name ?? 'MEO'}`} />

      <FlatList
        data={schools}
        keyExtractor={(item) => String(item.school_id)}
        ListHeaderComponent={
          <>
            <View style={styles.statsRow}>
              <StatsCard
                label="Total Schools"
                value={data?.total_schools ?? 0}
                icon="school-outline"
                accent={Colors.primary[600]}
                style={styles.statCard}
              />
              <StatsCard
                label="Total Students"
                value={data?.total_students?.toLocaleString() ?? 0}
                icon="people-outline"
                accent={Colors.secondary[600]}
                style={styles.statCard}
              />
            </View>
            <View style={styles.statsRow}>
              <StatsCard
                label="High Risk Students"
                value={data?.high_risk_students ?? 0}
                icon="alert-circle-outline"
                accent={Colors.danger}
                style={styles.statCard}
              />
              <StatsCard
                label="Avg Attendance"
                value={formatPercentage(data?.avg_attendance_rate ?? 0)}
                icon="trending-up-outline"
                accent={Colors.success}
                style={styles.statCard}
              />
            </View>
            <Text style={styles.sectionTitle}>Schools in Mandal</Text>
          </>
        }
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const score = item.health_score ?? 0;
          const grade = score >= 80 ? 'A' : score >= 65 ? 'B' : score >= 50 ? 'C' : 'D';
          const gradeColor = { A: Colors.success, B: '#84cc16', C: Colors.warning, D: Colors.danger }[grade];
          return (
            <Card style={styles.schoolCard}>
              <View style={styles.schoolRow}>
                <View style={[styles.gradeCircle, { backgroundColor: `${gradeColor}18` }]}>
                  <Text style={[styles.gradeLabel, { color: gradeColor }]}>{grade}</Text>
                </View>
                <View style={styles.schoolDetails}>
                  <Text style={styles.schoolName} numberOfLines={2}>{item.name}</Text>
                  <Text style={styles.schoolSub}>{item.total_students} students</Text>
                </View>
                <View style={styles.scoreBlock}>
                  <Text style={[styles.scoreNum, { color: gradeColor }]}>
                    {score > 0 ? score.toFixed(0) : 'N/A'}
                  </Text>
                  <Text style={styles.scoreLabel}>Health</Text>
                </View>
              </View>
              <View style={styles.schoolFooter}>
                <TouchableOpacity style={styles.footerBtn}>
                  <Ionicons name="eye-outline" size={14} color={Colors.primary[600]} />
                  <Text style={styles.footerBtnText}>View School</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.footerBtn}>
                  <Ionicons name="alert-outline" size={14} color={Colors.danger} />
                  <Text style={[styles.footerBtnText, { color: Colors.danger }]}>Risk Check</Text>
                </TouchableOpacity>
              </View>
            </Card>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  statsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  statCard: { flex: 1 },
  sectionTitle: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    color: Colors.neutral[800],
    marginBottom: Spacing.md,
    marginTop: Spacing.sm,
  },
  list: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  schoolCard: { marginBottom: Spacing.sm, padding: Spacing.md },
  schoolRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.sm },
  gradeCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  gradeLabel: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold },
  schoolDetails: { flex: 1 },
  schoolName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  schoolSub: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  scoreBlock: { alignItems: 'flex-end' },
  scoreNum: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold },
  scoreLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  schoolFooter: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: Colors.neutral[100],
    paddingTop: Spacing.sm,
    gap: Spacing.lg,
  },
  footerBtn: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  footerBtnText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
});
