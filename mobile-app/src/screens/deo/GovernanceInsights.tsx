import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { analyticsService } from '../../services/analyticsService';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

interface InsightItem {
  id: number;
  type: string;
  summary: string;
  recommendations: string | null;
  risk_score: number | null;
  is_actioned: boolean;
  created_at: string;
}

const TYPE_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  DROPOUT_RISK:        { icon: 'alert-circle', color: Colors.danger, label: 'Dropout Risk' },
  ATTENDANCE_ANOMALY:  { icon: 'calendar', color: Colors.warning, label: 'Attendance Anomaly' },
  SCHOOL_HEALTH:       { icon: 'fitness', color: Colors.primary[600], label: 'School Health' },
  PERFORMANCE_DECLINE: { icon: 'trending-down', color: '#f97316', label: 'Performance Decline' },
};

export default function GovernanceInsights() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const districtId = user?.district_id ?? 1;

  const { data = [], isLoading } = useQuery<InsightItem[]>({
    queryKey: ['district-insights', districtId],
    queryFn: () => analyticsService.getInsights('DISTRICT', districtId),
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Generating AI insights..." />;

  const unactioned = data.filter((i) => !i.is_actioned);
  const actioned = data.filter((i) => i.is_actioned);

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Governance Insights" subtitle={`${unactioned.length} Active Alerts`} />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* AI Insights Banner */}
        <View style={styles.aiBanner}>
          <Ionicons name="sparkles" size={24} color={Colors.white} />
          <View style={styles.aiBannerText}>
            <Text style={styles.aiBannerTitle}>AI-Powered Insights</Text>
            <Text style={styles.aiBannerSub}>
              {unactioned.length} active recommendations require attention
            </Text>
          </View>
        </View>

        {/* Active Insights */}
        <Text style={styles.sectionTitle}>Active Alerts ({unactioned.length})</Text>
        {unactioned.length === 0 ? (
          <Card style={styles.emptyCard}>
            <Ionicons name="checkmark-circle" size={40} color={Colors.success} />
            <Text style={styles.emptyText}>No active alerts. District performing well!</Text>
          </Card>
        ) : (
          unactioned.map((insight) => {
            const cfg = TYPE_CONFIG[insight.type] ?? { icon: 'bulb', color: Colors.primary[600], label: insight.type };
            return (
              <Card key={insight.id} style={styles.insightCard}>
                <View style={styles.insightHeader}>
                  <View style={[styles.insightIcon, { backgroundColor: `${cfg.color}18` }]}>
                    <Ionicons name={cfg.icon as any} size={22} color={cfg.color} />
                  </View>
                  <View style={styles.insightMeta}>
                    <Text style={[styles.insightType, { color: cfg.color }]}>{cfg.label}</Text>
                    {insight.risk_score != null && (
                      <Text style={styles.riskScore}>Risk: {Math.round(insight.risk_score * 100)}%</Text>
                    )}
                  </View>
                  <Ionicons name="chevron-forward" size={18} color={Colors.neutral[400]} />
                </View>
                <Text style={styles.insightSummary}>{insight.summary}</Text>
                {insight.recommendations && (
                  <View style={styles.recoBox}>
                    <Text style={styles.recoTitle}>Recommendation</Text>
                    <Text style={styles.recoText}>
                      {insight.recommendations.replace(/[\[\]'"]/g, '').trim()}
                    </Text>
                  </View>
                )}
                <TouchableOpacity style={styles.actionBtn}>
                  <Text style={styles.actionText}>Mark as Actioned</Text>
                </TouchableOpacity>
              </Card>
            );
          })
        )}

        {/* Resolved */}
        {actioned.length > 0 && (
          <>
            <Text style={[styles.sectionTitle, styles.mt]}>Resolved ({actioned.length})</Text>
            {actioned.map((insight) => (
              <Card key={insight.id} style={[styles.insightCard, styles.resolved]} variant="outlined">
                <View style={styles.resolvedRow}>
                  <Ionicons name="checkmark-circle" size={18} color={Colors.success} />
                  <Text style={styles.resolvedText}>{insight.summary}</Text>
                </View>
              </Card>
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  aiBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primary[700],
    borderRadius: 16,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
    gap: Spacing.md,
  },
  aiBannerText: { flex: 1 },
  aiBannerTitle: { color: Colors.white, fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  aiBannerSub: { color: 'rgba(255,255,255,0.75)', fontSize: Typography.sizes.sm, marginTop: 2 },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md },
  mt: { marginTop: Spacing.lg },
  emptyCard: { alignItems: 'center', padding: Spacing.xl, gap: Spacing.md },
  emptyText: { fontSize: Typography.sizes.base, color: Colors.neutral[500], textAlign: 'center' },
  insightCard: { marginBottom: Spacing.sm, padding: Spacing.md },
  insightHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.md },
  insightIcon: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  insightMeta: { flex: 1 },
  insightType: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  riskScore: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  insightSummary: { fontSize: Typography.sizes.base, color: Colors.neutral[700], lineHeight: 22, marginBottom: Spacing.md },
  recoBox: {
    backgroundColor: Colors.primary[50],
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  recoTitle: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.primary[700], marginBottom: 4 },
  recoText: { fontSize: Typography.sizes.sm, color: Colors.primary[700], lineHeight: 18 },
  actionBtn: {
    alignSelf: 'flex-end',
    paddingVertical: 6,
    paddingHorizontal: Spacing.md,
    backgroundColor: Colors.neutral[100],
    borderRadius: BorderRadius.full,
  },
  actionText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], fontWeight: Typography.weights.medium },
  resolved: { backgroundColor: Colors.neutral[50], marginBottom: Spacing.sm },
  resolvedRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  resolvedText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[500], lineHeight: 18 },
});
