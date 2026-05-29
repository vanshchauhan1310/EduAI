import React from 'react';
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import StatsCard from '../../components/common/StatsCard';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import RiskBadge from '../../components/common/RiskBadge';
import { analyticsService } from '../../services/analyticsService';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing } from '../../theme';
import { QUERY_KEYS } from '../../constants';
import { formatPercentage } from '../../utils/helpers';

export default function DistrictDashboard() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const districtId = user?.district_id ?? 1;

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: [QUERY_KEYS.DISTRICT_OVERVIEW, districtId],
    queryFn: () => analyticsService.getDistrictOverview(districtId),
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading district data..." />;

  const today = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="District Dashboard"
        subtitle={today}
        rightAction={{ icon: 'notifications-outline', onPress: () => {} }}
      />

      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Greeting */}
        <View style={styles.greeting}>
          <Text style={styles.greetUser}>Good Morning, {user?.full_name?.split(' ')[0]} 👋</Text>
          <Text style={styles.greetRole}>District Education Officer</Text>
        </View>

        {/* KPI Grid */}
        <Text style={styles.sectionTitle}>District Overview</Text>
        <View style={styles.statsGrid}>
          <StatsCard
            label="Total Schools"
            value={data?.total_schools ?? 0}
            icon="school-outline"
            accent={Colors.primary[600]}
            style={styles.statHalf}
          />
          <StatsCard
            label="Total Students"
            value={data?.total_students?.toLocaleString() ?? 0}
            icon="people-outline"
            accent={Colors.secondary[600]}
            style={styles.statHalf}
          />
        </View>
        <View style={styles.statsGrid}>
          <StatsCard
            label="Attendance Rate"
            value={formatPercentage(data?.attendance_rate_this_month ?? 0)}
            icon="calendar-outline"
            accent={Colors.success}
            trend={{ value: 2.1, label: 'vs last month' }}
            style={styles.statHalf}
          />
          <StatsCard
            label="High-Risk Students"
            value={data?.high_risk_students ?? 0}
            icon="alert-circle-outline"
            accent={Colors.danger}
            style={styles.statHalf}
          />
        </View>

        {/* Alert Banner */}
        {(data?.high_risk_students ?? 0) > 0 && (
          <Card style={styles.alertCard} variant="outlined">
            <View style={styles.alertRow}>
              <View style={styles.alertIcon}>
                <Ionicons name="warning" size={22} color="#b45309" />
              </View>
              <View style={styles.alertContent}>
                <Text style={styles.alertTitle}>Dropout Risk Alert</Text>
                <Text style={styles.alertBody}>
                  {data?.high_risk_students} students are at high/critical dropout risk district-wide.
                  Immediate intervention recommended.
                </Text>
              </View>
            </View>
            <TouchableOpacity style={styles.alertBtn}>
              <Text style={styles.alertBtnText}>View Details →</Text>
            </TouchableOpacity>
          </Card>
        )}

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          {[
            { icon: 'analytics-outline', label: 'School Health', color: Colors.primary[600] },
            { icon: 'trending-down-outline', label: 'Dropout Monitor', color: Colors.danger },
            { icon: 'people-outline', label: 'Teacher Ratio', color: Colors.secondary[600] },
            { icon: 'document-text-outline', label: 'Reports', color: Colors.success },
          ].map((action) => (
            <TouchableOpacity key={action.label} style={styles.actionCard}>
              <View style={[styles.actionIcon, { backgroundColor: `${action.color}18` }]}>
                <Ionicons name={action.icon as any} size={26} color={action.color} />
              </View>
              <Text style={styles.actionLabel}>{action.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Dropout Risk Rate */}
        <Card style={styles.rateCard}>
          <View style={styles.rateRow}>
            <View>
              <Text style={styles.rateLabel}>District Dropout Risk Rate</Text>
              <Text style={styles.rateValue}>
                {formatPercentage(data?.dropout_risk_rate ?? 0)}
              </Text>
            </View>
            <RiskBadge
              level={
                (data?.dropout_risk_rate ?? 0) > 15 ? 'CRITICAL' :
                (data?.dropout_risk_rate ?? 0) > 10 ? 'HIGH' :
                (data?.dropout_risk_rate ?? 0) > 5  ? 'MEDIUM' : 'LOW'
              }
            />
          </View>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  greeting: { marginBottom: Spacing.lg },
  greetUser: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  greetRole: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 2 },
  sectionTitle: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    color: Colors.neutral[800],
    marginBottom: Spacing.md,
    marginTop: Spacing.lg,
  },
  statsGrid: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  statHalf: { flex: 1 },
  alertCard: {
    marginTop: Spacing.md,
    borderColor: '#fbbf24',
    backgroundColor: '#fffbeb',
  },
  alertRow: { flexDirection: 'row', gap: Spacing.md, alignItems: 'flex-start', marginBottom: Spacing.md },
  alertIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#fef3c7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  alertContent: { flex: 1 },
  alertTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: '#92400e' },
  alertBody: { fontSize: Typography.sizes.sm, color: '#78350f', marginTop: 2, lineHeight: 18 },
  alertBtn: { alignSelf: 'flex-end' },
  alertBtnText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.semibold },
  actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  actionCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: Spacing.md,
    alignItems: 'center',
    gap: Spacing.sm,
    ...require('../../theme').Shadows.sm,
  },
  actionIcon: { width: 52, height: 52, borderRadius: 26, justifyContent: 'center', alignItems: 'center' },
  actionLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.medium, color: Colors.neutral[700], textAlign: 'center' },
  rateCard: { marginTop: Spacing.md },
  rateRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rateLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },
  rateValue: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: 2 },
});
