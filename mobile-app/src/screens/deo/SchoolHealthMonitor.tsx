import React, { useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity, RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { analyticsService } from '../../services/analyticsService';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

type FilterGrade = 'ALL' | 'A' | 'B' | 'C' | 'D';

const GRADE_COLOR: Record<string, string> = {
  A: Colors.success, B: '#84cc16', C: Colors.warning, D: Colors.danger,
};

function HealthScoreBar({ score }: { score: number }) {
  const color = score >= 80 ? Colors.success : score >= 65 ? '#84cc16' : score >= 50 ? Colors.warning : Colors.danger;
  return (
    <View style={styles.barContainer}>
      <View style={[styles.barFill, { width: `${score}%` as any, backgroundColor: color }]} />
    </View>
  );
}

export default function SchoolHealthMonitor() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const [filter, setFilter] = useState<FilterGrade>('ALL');
  const mandalId = user?.mandal_id ?? 1;

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['mandal_overview', mandalId],
    queryFn: () => analyticsService.getMandalOverview(mandalId),
  });

  const schools: any[] = data?.schools ?? [];
  const filtered = filter === 'ALL' ? schools : schools.filter((s: any) => {
    const score = s.health_score ?? 0;
    if (filter === 'A') return score >= 80;
    if (filter === 'B') return score >= 65 && score < 80;
    if (filter === 'C') return score >= 50 && score < 65;
    if (filter === 'D') return score < 50;
    return true;
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading school health data..." />;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="School Health Monitor" subtitle={`${schools.length} Schools`} />

      {/* Grade Filters */}
      <View style={styles.filterRow}>
        {(['ALL', 'A', 'B', 'C', 'D'] as FilterGrade[]).map((g) => (
          <TouchableOpacity
            key={g}
            style={[styles.filterChip, filter === g && styles.filterChipActive]}
            onPress={() => setFilter(g)}
          >
            <Text style={[styles.filterText, filter === g && styles.filterTextActive]}>{g}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.school_id)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const score = item.health_score ?? 0;
          const grade = score >= 80 ? 'A' : score >= 65 ? 'B' : score >= 50 ? 'C' : 'D';
          return (
            <Card style={styles.schoolCard}>
              <View style={styles.cardHeader}>
                <View style={styles.gradeBadge}>
                  <Text style={[styles.gradeText, { color: GRADE_COLOR[grade] }]}>{grade}</Text>
                </View>
                <View style={styles.schoolInfo}>
                  <Text style={styles.schoolName} numberOfLines={2}>{item.name}</Text>
                  <Text style={styles.dise}>DISE: {item.dise_code}</Text>
                </View>
                <Text style={[styles.scoreText, { color: GRADE_COLOR[grade] }]}>
                  {score.toFixed(0)}
                </Text>
              </View>
              <HealthScoreBar score={score} />
              <View style={styles.metaRow}>
                <View style={styles.metaItem}>
                  <Ionicons name="people-outline" size={14} color={Colors.neutral[400]} />
                  <Text style={styles.metaText}>{item.total_students} students</Text>
                </View>
                <TouchableOpacity style={styles.viewBtn}>
                  <Text style={styles.viewBtnText}>View Details</Text>
                  <Ionicons name="chevron-forward" size={14} color={Colors.primary[600]} />
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
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  filterChip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.neutral[200],
    backgroundColor: Colors.white,
  },
  filterChipActive: { backgroundColor: Colors.primary[600], borderColor: Colors.primary[600] },
  filterText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], fontWeight: Typography.weights.medium },
  filterTextActive: { color: Colors.white },
  list: { padding: Spacing.base, gap: Spacing.sm },
  schoolCard: { padding: Spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.md },
  gradeBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.neutral[100],
    justifyContent: 'center',
    alignItems: 'center',
  },
  gradeText: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold },
  schoolInfo: { flex: 1 },
  schoolName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  dise: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 2 },
  scoreText: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold },
  barContainer: {
    height: 6,
    backgroundColor: Colors.neutral[100],
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  barFill: { height: '100%', borderRadius: 3 },
  metaRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  viewBtn: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  viewBtnText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
});
