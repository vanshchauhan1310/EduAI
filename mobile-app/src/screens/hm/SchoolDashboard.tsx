import React from 'react';
import {
  Alert,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { analyticsService } from '../../services/analyticsService';
import { attendanceService } from '../../services/attendanceService';
import { useAuthStore } from '../../store/authStore';
import { useAppStore } from '../../store/appStore';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

const STAT_CARDS = [
  { label: 'Students', icon: 'people-outline', color: '#2f6df6' },
  { label: 'Teachers', icon: 'person-add-outline', color: '#09b981' },
  { label: 'Attendance', icon: 'trending-up-outline', color: '#16a34a' },
  { label: 'At Risk', icon: 'warning-outline', color: '#ef4444' },
  { label: 'Health Score', icon: 'heart-outline', color: '#ec4899' },
  { label: 'Assignments', icon: 'clipboard-outline', color: '#d6a72f' },
  { label: 'FLN Score', icon: 'book-outline', color: '#2f6df6' },
  { label: 'Operations', icon: 'pulse-outline', color: '#10b981' },
];

const MODULES = [
  {
    title: 'Attendance Intelligence',
    subtitle: 'Real-time attendance monitoring',
    icon: 'trending-up-outline',
    color: '#2f6df6',
    badge: 'today',
    screen: 'AttendanceIntelligence',
  },
  {
    title: 'Dropout Prediction',
    subtitle: 'Students requiring intervention',
    icon: 'warning-outline',
    color: '#ef4444',
    badge: 'Action needed',
    screen: 'DropoutPrediction',
  },
  {
    title: 'Teacher Performance',
    subtitle: 'Teachers monitored',
    icon: 'person-add-outline',
    color: '#09b981',
    badge: 'alerts',
    screen: 'TeacherPerformance',
  },
  {
    title: 'Student Learning',
    subtitle: 'Class-wise performance analytics',
    icon: 'book-outline',
    color: '#f59e0b',
    badge: 'FLN avg',
    screen: 'StudentLearning',
  },
  {
    title: 'School Health',
    subtitle: 'Overall school health score',
    icon: 'heart-outline',
    color: '#ec4899',
    badge: 'score',
    screen: 'SchoolHealthModule',
  },
  {
    title: 'School Operations',
    subtitle: 'Infrastructure and facilities',
    icon: 'business-outline',
    color: '#06b6d4',
    badge: 'pending',
    screen: 'SchoolOperations',
  },
];

export default function SchoolDashboard() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const user = useAuthStore((s) => s.user);
  const academicYear = useAppStore((s) => s.selectedAcademicYear);
  const schoolId = user?.school_id ?? 1;
  const today = dayjs().format('YYYY-MM-DD');

  const { data: perfData, refetch, isRefetching } = useQuery({
    queryKey: ['school-performance', schoolId, academicYear],
    queryFn: () => analyticsService.getSchoolPerformance(schoolId, academicYear),
  });

  const { data: attData } = useQuery({
    queryKey: ['school-daily-att', schoolId, today],
    queryFn: () => attendanceService.getSchoolDailySummary(schoolId, today),
    refetchInterval: 5 * 60 * 1000,
  });

  const { data: healthData } = useQuery({
    queryKey: ['school-health', schoolId],
    queryFn: () => analyticsService.getSchoolHealthScore(schoolId),
  });

  const totalStudents = perfData?.total_students ?? 485;
  const teachers = perfData?.total_teachers ?? 22;
  const attendance = Math.round(attData?.rate ?? 94);
  const riskBreakdown = perfData?.risk_breakdown ?? {};
  const atRisk = (riskBreakdown.HIGH ?? 0) + (riskBreakdown.CRITICAL ?? 0) || 12;
  const healthScore = ((healthData?.health_score ?? 85) / 10).toFixed(1);
  const flnScore = perfData?.average_score ? Math.round(perfData.average_score) : 79;

  const statValues = [
    totalStudents,
    teachers,
    `${attendance}%`,
    atRisk,
    healthScore,
    '86%',
    `${flnScore}%`,
    '91%',
  ];

  const moduleBadges: Record<string, string> = {
    AttendanceIntelligence: `${attendance}% today`,
    DropoutPrediction: `${atRisk} at risk`,
    TeacherPerformance: '2 alerts',
    StudentLearning: `${flnScore}% FLN avg`,
    SchoolHealthModule: `${healthScore} / 10`,
    SchoolOperations: '2 pending',
  };

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.headerRow}>
          <View style={styles.headerText}>
            <Text style={styles.title}>School Command Center</Text>
            <Text style={styles.subtitle}>Head Master - ZPHS Mandal Center</Text>
          </View>
          <TouchableOpacity style={styles.iconButton} onPress={() => navigation.navigate('HMNotifications')}>
            <Ionicons name="notifications-outline" size={24} color="#102044" />
            <View style={styles.notificationDot} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.profileButton} onPress={() => navigation.navigate('Profile')}>
            <Ionicons name="person-outline" size={25} color="#d6b354" />
          </TouchableOpacity>
        </View>

        <View style={styles.statsGrid}>
          {STAT_CARDS.map((item, index) => (
            <View key={item.label} style={styles.statCard}>
              <Ionicons name={item.icon as any} size={24} color={item.color} />
              <Text style={styles.statValue}>{statValues[index]}</Text>
              <Text style={styles.statLabel} numberOfLines={1}>{item.label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.healthPanel}>
          <View>
            <Text style={styles.healthPanelLabel}>Overall School Health</Text>
            <View style={styles.healthScoreRow}>
              <Text style={styles.healthPanelScore}>{healthScore}</Text>
              <Text style={styles.healthPanelMax}>/ 10</Text>
            </View>
            <Text style={styles.healthTrend}>+0.3 vs last month - Excellent</Text>
          </View>
          <View style={styles.healthBars}>
            {[
              ['Academic', 84],
              ['Operational', 92],
              ['Engagement', 78],
            ].map(([label, value]) => (
              <View key={label as string} style={styles.barRow}>
                <Text style={styles.barLabel}>{label}</Text>
                <View style={styles.barTrack}>
                  <View style={[styles.barFill, { width: `${value}%` }]} />
                </View>
              </View>
            ))}
          </View>
        </View>

        <Text style={styles.sectionTitle}>Critical Alerts</Text>
        {[
          ['Class 8B attendance dropped to 82% this week', '1 hour ago'],
          ['3 students absent for 5+ consecutive days', '3 hours ago'],
          ['Maths teacher absent - substitute needed today', '8 am today'],
        ].map(([message, time]) => (
          <TouchableOpacity key={message} style={styles.alertCard} onPress={() => Alert.alert('Alert', message)}>
            <View style={styles.alertIcon}>
              <Ionicons name="warning-outline" size={22} color="#ef4444" />
            </View>
            <View style={styles.alertContent}>
              <Text style={styles.alertText}>{message}</Text>
              <Text style={styles.alertTime}>{time}</Text>
            </View>
          </TouchableOpacity>
        ))}

        <Text style={styles.sectionTitle}>School Intelligence Modules</Text>
        {MODULES.map((module) => (
          <TouchableOpacity key={module.title} style={styles.moduleCard} onPress={() => navigation.navigate(module.screen)} activeOpacity={0.86}>
            <View style={[styles.moduleIcon, { backgroundColor: `${module.color}12` }]}>
              <Ionicons name={module.icon as any} size={30} color={module.color} />
            </View>
            <View style={styles.moduleContent}>
              <Text style={styles.moduleTitle}>{module.title}</Text>
              <Text style={styles.moduleSubtitle}>{module.subtitle}</Text>
            </View>
            <View style={styles.moduleRight}>
              <Text style={styles.moduleBadge}>{moduleBadges[module.screen] ?? module.badge}</Text>
              <Ionicons name="chevron-forward" size={20} color="#8a9ab3" />
            </View>
          </TouchableOpacity>
        ))}

        <View style={styles.insightsCard}>
          <View style={styles.insightsHeader}>
            <Ionicons name="flash-outline" size={22} color="#d6a72f" />
            <Text style={styles.insightsTitle}>AI School Insights</Text>
          </View>
          {[
            'Class 9A shows a 6% performance improvement this month',
            '3 students need immediate dropout intervention - assign counselor',
            'Science lab utilization is only 34% - recommend more lab sessions',
            'Parent engagement score increased after WhatsApp notifications',
          ].map((item) => (
            <View key={item} style={styles.insightRow}>
              <Ionicons name="radio-button-on-outline" size={15} color="#10b981" />
              <Text style={styles.insightText}>{item}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#edf3ff' },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.base },
  headerText: { flex: 1 },
  title: { fontSize: 22, lineHeight: 26, fontWeight: Typography.weights.bold, color: '#071a3a' },
  subtitle: { fontSize: Typography.sizes.base, color: '#536784', marginTop: 2 },
  iconButton: { width: 52, height: 52, borderRadius: 26, backgroundColor: '#f3f6ff', alignItems: 'center', justifyContent: 'center', position: 'relative' },
  notificationDot: { position: 'absolute', top: 11, right: 12, width: 9, height: 9, borderRadius: 5, backgroundColor: '#ef4444' },
  profileButton: { width: 52, height: 52, borderRadius: 26, backgroundColor: '#12244b', alignItems: 'center', justifyContent: 'center' },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginBottom: Spacing.lg },
  statCard: { width: '48%', height: 92, borderRadius: BorderRadius.xl, backgroundColor: '#f3f6ff', alignItems: 'center', justifyContent: 'center', padding: Spacing.sm },
  statValue: { color: '#071a3a', fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, marginTop: 6 },
  statLabel: { color: '#536784', fontSize: 11, marginTop: 2, textAlign: 'center' },
  healthPanel: { flexDirection: 'row', justifyContent: 'space-between', gap: Spacing.md, backgroundColor: '#263f78', borderRadius: BorderRadius.xl, padding: Spacing.lg, marginBottom: Spacing.lg },
  healthPanelLabel: { color: '#e7eefc', fontSize: Typography.sizes.base },
  healthScoreRow: { flexDirection: 'row', alignItems: 'flex-end', marginTop: Spacing.sm },
  healthPanelScore: { color: Colors.white, fontSize: 44, fontWeight: Typography.weights.bold },
  healthPanelMax: { color: '#e7eefc', fontSize: Typography.sizes['2xl'], marginBottom: 6, marginLeft: 4 },
  healthTrend: { color: '#e7eefc', fontSize: Typography.sizes.sm, marginTop: 4 },
  healthBars: { flex: 1, justifyContent: 'center', gap: Spacing.sm },
  barRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  barLabel: { color: '#e7eefc', width: 82, fontSize: Typography.sizes.sm },
  barTrack: { flex: 1, height: 8, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.25)', overflow: 'hidden' },
  barFill: { height: 8, borderRadius: 4, backgroundColor: '#d6b354' },
  sectionTitle: { color: '#071a3a', fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, marginBottom: Spacing.md, marginTop: Spacing.sm },
  alertCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.sm, ...Shadows.sm },
  alertIcon: { width: 40, height: 40, borderRadius: BorderRadius.lg, backgroundColor: '#fee2e2', alignItems: 'center', justifyContent: 'center' },
  alertContent: { flex: 1 },
  alertText: { color: '#071a3a', fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold },
  alertTime: { color: '#8090aa', fontSize: Typography.sizes.sm, marginTop: 3 },
  moduleCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.md, gap: Spacing.md, ...Shadows.sm },
  moduleIcon: { width: 60, height: 60, borderRadius: BorderRadius.lg, alignItems: 'center', justifyContent: 'center' },
  moduleContent: { flex: 1 },
  moduleTitle: { color: '#071a3a', fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold },
  moduleSubtitle: { color: '#536784', fontSize: Typography.sizes.base, marginTop: 3 },
  moduleRight: { alignItems: 'flex-end', gap: Spacing.sm },
  moduleBadge: { color: '#536784', backgroundColor: '#eef3ff', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 5, fontWeight: Typography.weights.semibold, fontSize: Typography.sizes.sm },
  insightsCard: { backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.lg, marginTop: Spacing.sm, ...Shadows.sm },
  insightsHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  insightsTitle: { color: '#071a3a', fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold },
  insightRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm, marginBottom: Spacing.sm },
  insightText: { flex: 1, color: '#071a3a', fontSize: Typography.sizes.base, lineHeight: 22 },
});
