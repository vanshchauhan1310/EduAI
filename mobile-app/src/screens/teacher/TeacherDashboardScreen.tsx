import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Card from '../../components/common/Card';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { useAuthStore } from '../../store/authStore';

interface StatCard {
  id: string;
  label: string;
  value: string;
  trend: string;
  trendUp: boolean;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
}

interface QuickAction {
  id: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  onPress: (navigation: any) => void;
}

interface ScheduleItem {
  id: string;
  time: string;
  subject: string;
  classLabel: string;
  room: string;
  status: 'done' | 'now' | 'upcoming';
}

interface ActivityItem {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  title: string;
  subtitle: string;
  time: string;
}

const STATS: StatCard[] = [
  { id: 'students', label: 'Total Students', value: '186', trend: '+4 this term', trendUp: true, icon: 'people', tint: Colors.primary[600] },
  { id: 'classes', label: "Today's Classes", value: '5', trend: '2 remaining', trendUp: true, icon: 'calendar', tint: Colors.secondary[600] },
  { id: 'pending', label: 'Pending Reviews', value: '12', trend: '3 urgent', trendUp: false, icon: 'document-text', tint: Colors.warning },
  { id: 'attendance', label: 'Avg. Attendance', value: '94%', trend: '+1.2% vs last month', trendUp: true, icon: 'checkmark-done-circle', tint: Colors.success },
];

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'attendance',
    label: 'Take Attendance',
    icon: 'checkbox',
    tint: Colors.primary[600],
    onPress: (navigation) => navigation.navigate('Attendance'),
  },
  {
    id: 'assessment',
    label: 'New Assessment',
    icon: 'add-circle',
    tint: Colors.secondary[600],
    onPress: (navigation) => navigation.navigate('Assessments', { screen: 'CreateAssessment' }),
  },
  {
    id: 'assignments',
    label: 'Assignments',
    icon: 'book',
    tint: Colors.warning,
    onPress: (navigation) => navigation.navigate('Assignments'),
  },
];

const SCHEDULE: ScheduleItem[] = [
  { id: '1', time: '8:30 – 9:15', subject: 'Mathematics', classLabel: 'Class 7 · A', room: 'Room 12', status: 'done' },
  { id: '2', time: '9:20 – 10:05', subject: 'Mathematics', classLabel: 'Class 8 · B', room: 'Room 12', status: 'done' },
  { id: '3', time: '10:30 – 11:15', subject: 'Mathematics', classLabel: 'Class 7 · B', room: 'Room 9', status: 'now' },
  { id: '4', time: '12:00 – 12:45', subject: 'Remedial Class', classLabel: 'Class 6 · A', room: 'Lab 2', status: 'upcoming' },
  { id: '5', time: '1:30 – 2:15', subject: 'Mathematics', classLabel: 'Class 9 · A', room: 'Room 14', status: 'upcoming' },
];

const ACTIVITY: ActivityItem[] = [
  { id: '1', icon: 'checkmark-circle', tint: Colors.success, title: '18 submissions received', subtitle: '"End Semester – Mathematics" · Class 7-A', time: '12 min ago' },
  { id: '2', icon: 'sparkles', tint: Colors.primary[600], title: 'AI grading completed', subtitle: '6 students auto-graded for "Unit Test 3"', time: '1 hr ago' },
  { id: '3', icon: 'people', tint: Colors.secondary[600], title: 'Attendance marked', subtitle: 'Class 8-B · 42/45 present', time: '3 hrs ago' },
  { id: '4', icon: 'megaphone', tint: Colors.warning, title: 'New circular from HM', subtitle: 'Parent-teacher meeting on Friday', time: 'Yesterday' },
];

const CLASS_PERFORMANCE = [
  { id: '1', label: 'Class 7 · A', score: 82 },
  { id: '2', label: 'Class 7 · B', score: 76 },
  { id: '3', label: 'Class 8 · A', score: 88 },
  { id: '4', label: 'Class 8 · B', score: 71 },
  { id: '5', label: 'Class 9 · A', score: 79 },
];

function getInitials(name?: string) {
  if (!name) return 'T';
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || 'T';
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function TeacherDashboardScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const firstName = (user?.full_name || 'Teacher').split(' ')[0];
  const today = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <View style={styles.flex}>
      {/* Hero header */}
      <View style={[styles.hero, { paddingTop: insets.top + Spacing.md }]}>
        <View style={styles.heroRow}>
          <View style={styles.heroTextWrap}>
            <Text style={styles.heroGreeting}>{getGreeting()}, {firstName} 👋</Text>
            <Text style={styles.heroDate}>{today}</Text>
          </View>
          <TouchableOpacity
            style={styles.avatar}
            onPress={() => navigation.navigate('Profile')}
            activeOpacity={0.8}
          >
            <Text style={styles.avatarText}>{getInitials(user?.full_name)}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.heroBanner}>
          <Ionicons name="trending-up" size={18} color={Colors.white} />
          <Text style={styles.heroBannerText}>
            Your classes are averaging <Text style={styles.heroBannerStrong}>79%</Text> this term — up 3 points from last month.
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.flex}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + Spacing.xl }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Stat cards */}
        <View style={styles.statsGrid}>
          {STATS.map((stat) => (
            <Card key={stat.id} style={styles.statCard} padding="md">
              <View style={[styles.statIconWrap, { backgroundColor: stat.tint + '16' }]}>
                <Ionicons name={stat.icon} size={20} color={stat.tint} />
              </View>
              <Text style={styles.statValue}>{stat.value}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
              <View style={styles.statTrendRow}>
                <Ionicons
                  name={stat.trendUp ? 'arrow-up' : 'alert-circle'}
                  size={12}
                  color={stat.trendUp ? Colors.success : Colors.warning}
                />
                <Text style={[styles.statTrend, { color: stat.trendUp ? Colors.success : Colors.warning }]} numberOfLines={1}>
                  {stat.trend}
                </Text>
              </View>
            </Card>
          ))}
        </View>

        {/* Quick actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsGrid}>
          {QUICK_ACTIONS.map((action) => (
            <TouchableOpacity
              key={action.id}
              style={styles.actionTile}
              activeOpacity={0.75}
              onPress={() => action.onPress(navigation)}
            >
              <View style={[styles.actionIconWrap, { backgroundColor: action.tint + '16' }]}>
                <Ionicons name={action.icon} size={22} color={action.tint} />
              </View>
              <Text style={styles.actionLabel}>{action.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Today's schedule */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Today's Schedule</Text>
          <View style={styles.liveBadge}>
            <View style={styles.liveDot} />
            <Text style={styles.liveBadgeText}>1 in progress</Text>
          </View>
        </View>
        <Card style={styles.scheduleCard} padding="none">
          {SCHEDULE.map((item, idx) => (
            <View
              key={item.id}
              style={[styles.scheduleRow, idx !== SCHEDULE.length - 1 && styles.scheduleRowDivider]}
            >
              <View style={styles.scheduleTimeWrap}>
                <Text style={[styles.scheduleTime, item.status === 'now' && styles.scheduleTimeNow]}>{item.time}</Text>
                {item.status === 'now' && <View style={styles.nowDot} />}
              </View>
              <View style={styles.scheduleDivider} />
              <View style={styles.scheduleInfo}>
                <Text style={styles.scheduleSubject}>{item.subject}</Text>
                <Text style={styles.scheduleMeta}>{item.classLabel} · {item.room}</Text>
              </View>
              {item.status === 'done' ? (
                <Ionicons name="checkmark-circle" size={20} color={Colors.success} />
              ) : item.status === 'now' ? (
                <View style={styles.nowBadge}>
                  <Text style={styles.nowBadgeText}>Now</Text>
                </View>
              ) : (
                <Ionicons name="chevron-forward" size={18} color={Colors.neutral[300]} />
              )}
            </View>
          ))}
        </Card>

        {/* Class performance */}
        <Text style={styles.sectionTitle}>Class Performance — This Term</Text>
        <Card style={styles.performanceCard}>
          {CLASS_PERFORMANCE.map((cls) => (
            <View key={cls.id} style={styles.perfRow}>
              <Text style={styles.perfLabel}>{cls.label}</Text>
              <View style={styles.perfBarBg}>
                <View
                  style={[
                    styles.perfBarFill,
                    {
                      width: `${cls.score}%`,
                      backgroundColor: cls.score >= 80 ? Colors.success : cls.score >= 70 ? Colors.primary[600] : Colors.warning,
                    },
                  ]}
                />
              </View>
              <Text style={styles.perfScore}>{cls.score}%</Text>
            </View>
          ))}
        </Card>

        {/* Recent activity */}
        <Text style={styles.sectionTitle}>Recent Activity</Text>
        <Card style={styles.activityCard} padding="none">
          {ACTIVITY.map((item, idx) => (
            <View
              key={item.id}
              style={[styles.activityRow, idx !== ACTIVITY.length - 1 && styles.scheduleRowDivider]}
            >
              <View style={[styles.activityIconWrap, { backgroundColor: item.tint + '16' }]}>
                <Ionicons name={item.icon} size={18} color={item.tint} />
              </View>
              <View style={styles.activityTextWrap}>
                <Text style={styles.activityTitle}>{item.title}</Text>
                <Text style={styles.activitySubtitle}>{item.subtitle}</Text>
              </View>
              <Text style={styles.activityTime}>{item.time}</Text>
            </View>
          ))}
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  hero: {
    backgroundColor: Colors.primary[600],
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.xl,
    borderBottomLeftRadius: BorderRadius['2xl'],
    borderBottomRightRadius: BorderRadius['2xl'],
  },
  heroRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  heroTextWrap: { flex: 1 },
  heroGreeting: { color: Colors.white, fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold },
  heroDate: { color: 'rgba(255,255,255,0.8)', fontSize: Typography.sizes.sm, marginTop: 2 },
  avatar: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderWidth: 1.5, borderColor: 'rgba(255,255,255,0.4)',
    justifyContent: 'center', alignItems: 'center',
  },
  avatarText: { color: Colors.white, fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  heroBanner: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.sm,
    backgroundColor: 'rgba(255,255,255,0.14)',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginTop: Spacing.lg,
  },
  heroBannerText: { flex: 1, color: Colors.white, fontSize: Typography.sizes.sm, lineHeight: 18 },
  heroBannerStrong: { fontWeight: Typography.weights.bold },
  scrollContent: { padding: Spacing.base, paddingTop: Spacing.lg },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginBottom: Spacing.xl },
  statCard: { width: '48%' },
  statIconWrap: { width: 36, height: 36, borderRadius: BorderRadius.md, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.sm },
  statValue: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  statLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  statTrendRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: Spacing.sm },
  statTrend: { fontSize: 10, fontWeight: Typography.weights.semibold, flexShrink: 1 },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.md },
  sectionHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  liveBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: Colors.success + '16', paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.success },
  liveBadgeText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.success },
  actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginBottom: Spacing.xl },
  actionTile: {
    width: '31%',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xs,
    ...Shadows.sm,
  },
  actionIconWrap: { width: 44, height: 44, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.sm },
  actionLabel: { fontSize: 11, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], textAlign: 'center' },
  scheduleCard: { marginBottom: Spacing.xl, overflow: 'hidden' },
  scheduleRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.md },
  scheduleRowDivider: { borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  scheduleTimeWrap: { width: 78 },
  scheduleTime: { fontSize: 11, fontWeight: Typography.weights.semibold, color: Colors.neutral[500] },
  scheduleTimeNow: { color: Colors.primary[600] },
  nowDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.primary[600], marginTop: 4 },
  scheduleDivider: { width: 1, height: 32, backgroundColor: Colors.neutral[100] },
  scheduleInfo: { flex: 1 },
  scheduleSubject: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  scheduleMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  nowBadge: { backgroundColor: Colors.primary[600], paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  nowBadgeText: { fontSize: 10, fontWeight: Typography.weights.bold, color: Colors.white },
  performanceCard: { marginBottom: Spacing.xl, padding: Spacing.lg, gap: Spacing.md },
  perfRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  perfLabel: { width: 76, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[700] },
  perfBarBg: { flex: 1, height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden' },
  perfBarFill: { height: '100%', borderRadius: 4 },
  perfScore: { width: 38, textAlign: 'right', fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  activityCard: { overflow: 'hidden' },
  activityRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.md },
  activityIconWrap: { width: 38, height: 38, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  activityTextWrap: { flex: 1 },
  activityTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  activitySubtitle: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  activityTime: { fontSize: 10, color: Colors.neutral[400] },
});
