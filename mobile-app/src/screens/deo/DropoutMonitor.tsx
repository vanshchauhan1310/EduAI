import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import RiskBadge from '../../components/common/RiskBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing } from '../../theme';
import { RiskLevel } from '../../types';

export default function DropoutMonitor() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const [activeFilter, setActiveFilter] = useState<RiskLevel | 'ALL'>('ALL');
  const schoolId = user?.school_id ?? 1;

  const { data = [], isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['high-risk-students', schoolId],
    queryFn: async () => {
      const res = await api.get(`/students/school/${schoolId}/high-risk`);
      return res.data;
    },
  });

  const filtered = activeFilter === 'ALL'
    ? data
    : data.filter((s: any) => s.risk_level === activeFilter);

  if (isLoading) return <LoadingSpinner fullScreen message="Scanning dropout risks..." />;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Dropout Monitor"
        subtitle={`${data.length} At-Risk Students`}
      />

      {/* Risk Filter Tabs */}
      <View style={styles.tabs}>
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'] as const).map((level) => {
          const count = level === 'ALL' ? data.length
            : data.filter((s: any) => s.risk_level === level).length;
          return (
            <TouchableOpacity
              key={level}
              style={[styles.tab, activeFilter === level && styles.tabActive]}
              onPress={() => setActiveFilter(level)}
            >
              <Text style={[styles.tabLabel, activeFilter === level && styles.tabLabelActive]}>
                {level}
              </Text>
              <View style={[styles.tabCount, activeFilter === level && styles.tabCountActive]}>
                <Text style={[styles.tabCountText, activeFilter === level && styles.tabCountTextActive]}>
                  {count}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {filtered.length === 0 ? (
        <EmptyState
          icon="checkmark-circle-outline"
          title="No At-Risk Students"
          description="All students are currently at low risk."
        />
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item: any) => String(item.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => (
            <Card style={styles.studentCard}>
              <View style={styles.cardRow}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>
                    {item.full_name?.charAt(0)?.toUpperCase()}
                  </Text>
                </View>
                <View style={styles.studentInfo}>
                  <Text style={styles.studentName}>{item.full_name}</Text>
                  <Text style={styles.studentMeta}>
                    Class {item.current_class}{item.section ? `-${item.section}` : ''} • Adm: {item.admission_no}
                  </Text>
                </View>
                <RiskBadge level={item.risk_level as RiskLevel} size="sm" />
              </View>

              {item.dropout_risk_score != null && (
                <View style={styles.riskRow}>
                  <View style={styles.riskBarBg}>
                    <View
                      style={[
                        styles.riskBarFill,
                        {
                          width: `${Math.round(item.dropout_risk_score * 100)}%` as any,
                          backgroundColor:
                            item.dropout_risk_score >= 0.8 ? Colors.danger :
                            item.dropout_risk_score >= 0.65 ? '#f97316' : Colors.warning,
                        },
                      ]}
                    />
                  </View>
                  <Text style={styles.riskPct}>
                    {Math.round(item.dropout_risk_score * 100)}%
                  </Text>
                </View>
              )}

              <TouchableOpacity style={styles.actionBtn}>
                <Ionicons name="person-outline" size={16} color={Colors.primary[600]} />
                <Text style={styles.actionText}>View Profile & Intervene</Text>
              </TouchableOpacity>
            </Card>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  tabs: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: Spacing.sm,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
  },
  tabActive: { backgroundColor: Colors.primary[600] },
  tabLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], fontWeight: Typography.weights.medium },
  tabLabelActive: { color: Colors.white },
  tabCount: {
    backgroundColor: Colors.neutral[100],
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  tabCountActive: { backgroundColor: 'rgba(255,255,255,0.3)' },
  tabCountText: { fontSize: Typography.sizes.xs, color: Colors.neutral[600], fontWeight: Typography.weights.bold },
  tabCountTextActive: { color: Colors.white },
  list: { padding: Spacing.base, gap: Spacing.sm },
  studentCard: { padding: Spacing.md },
  cardRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.md },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary[100],
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.primary[700] },
  studentInfo: { flex: 1 },
  studentName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  studentMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  riskRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  riskBarBg: {
    flex: 1,
    height: 6,
    backgroundColor: Colors.neutral[100],
    borderRadius: 3,
    overflow: 'hidden',
  },
  riskBarFill: { height: '100%', borderRadius: 3 },
  riskPct: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[700], minWidth: 32, textAlign: 'right' },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.neutral[100],
  },
  actionText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
});
