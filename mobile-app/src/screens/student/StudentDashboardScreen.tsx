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

interface QuickInsight {
  id: string;
  label: string;
  summary: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  route: string;
}

interface ScheduleItem {
  id: string;
  time: string;
  subject: string;
  room: string;
  status: 'done' | 'now' | 'upcoming';
}

interface DeadlineItem {
  id: string;
  title: string;
  subject: string;
  type: 'Assignment' | 'Assessment';
  dueIn: string;
  urgent: boolean;
}

interface SubjectScore {
  id: string;
  subject: string;
  score: number;
}

interface ActivityItem {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  title: string;
  subtitle: string;
  time: string;
}

interface AIInsightCard {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  tag: string;
  title: string;
  text: string;
}

const STATS: StatCard[] = [
  { id: 'attendance', label: 'Attendance', value: '92%', trend: '+3% vs last month', trendUp: true, icon: 'calendar', tint: Colors.success },
  { id: 'performance', label: 'Avg. Score', value: '84%', trend: 'Top 12% of class', trendUp: true, icon: 'trophy', tint: Colors.primary[600] },
  { id: 'assignments', label: 'Assignments Due', value: '3', trend: '1 due tomorrow', trendUp: false, icon: 'book', tint: Colors.warning },
  { id: 'assessments', label: 'Assessments', value: '2', trend: '1 awaiting grading', trendUp: true, icon: 'clipboard', tint: Colors.secondary[600] },
];

const QUICK_INSIGHTS: QuickInsight[] = [
  { id: 'assignments', label: 'Assignments', summary: '5 pending · 14 completed this term', icon: 'book', tint: Colors.primary[600], route: 'Assignments' },
  { id: 'attendance', label: 'Attendance', summary: '92% present · 2 absences this month', icon: 'calendar', tint: Colors.success, route: 'Attendance' },
  { id: 'performance', label: 'Performance', summary: 'Avg. 84% · Ranked 5 of 48 in class', icon: 'trophy', tint: Colors.secondary[600], route: 'Performance' },
];

const SCHEDULE: ScheduleItem[] = [
  { id: '1', time: '9:00 – 9:45', subject: 'Mathematics', room: 'Room 12', status: 'done' },
  { id: '2', time: '9:50 – 10:35', subject: 'Science', room: 'Room 9', status: 'done' },
  { id: '3', time: '10:50 – 11:35', subject: 'English', room: 'Room 14', status: 'now' },
  { id: '4', time: '12:15 – 1:00', subject: 'Social Studies', room: 'Room 6', status: 'upcoming' },
  { id: '5', time: '1:45 – 2:30', subject: 'Computer Science', room: 'Lab 1', status: 'upcoming' },
];

const DEADLINES: DeadlineItem[] = [
  { id: '1', title: 'Algebra Worksheet 5', subject: 'Mathematics', type: 'Assignment', dueIn: 'Due tomorrow', urgent: true },
  { id: '2', title: 'Unit Test 2', subject: 'Science', type: 'Assessment', dueIn: 'Due in 3 days', urgent: false },
  { id: '3', title: 'Essay: My Favourite Festival', subject: 'English', type: 'Assignment', dueIn: 'Due in 5 days', urgent: false },
];

const SUBJECT_PERFORMANCE: SubjectScore[] = [
  { id: '1', subject: 'Mathematics', score: 88 },
  { id: '2', subject: 'Science', score: 81 },
  { id: '3', subject: 'English', score: 76 },
  { id: '4', subject: 'Social Studies', score: 85 },
  { id: '5', subject: 'Computer Science', score: 92 },
];

const ACTIVITY: ActivityItem[] = [
  { id: '1', icon: 'checkmark-circle', tint: Colors.success, title: 'Assignment graded', subtitle: '"Algebra Worksheet 4" scored 18/20', time: '2 hrs ago' },
  { id: '2', icon: 'sparkles', tint: Colors.primary[600], title: 'New assessment published', subtitle: '"Unit test 2" is now available to attempt', time: '5 hrs ago' },
  { id: '3', icon: 'calendar', tint: Colors.secondary[600], title: 'Attendance marked', subtitle: 'Present · Marked by Mrs. Sharma', time: 'Yesterday' },
];

const AI_INSIGHTS: AIInsightCard[] = [
  {
    id: '1',
    icon: 'trending-up',
    tint: Colors.success,
    tag: 'Strength',
    title: 'Excelling in Mathematics',
    text: "You've scored above 85% in your last 4 Mathematics assessments — among the top performers in your class. Keep up the consistent daily practice!",
  },
  {
    id: '2',
    icon: 'bulb',
    tint: Colors.warning,
    tag: 'Suggestion',
    title: 'Focus on diagram-based questions',
    text: 'AI grading shows you tend to lose marks on diagram-labelling questions in Science. Spending 15 extra minutes a week practising labelled diagrams could lift your average by 4–5%.',
  },
  {
    id: '3',
    icon: 'alert-circle',
    tint: Colors.danger,
    tag: 'Watch-out',
    title: 'Attendance dips on Mondays',
    text: 'Your Monday attendance is noticeably lower than other weekdays this term. Starting the week strong helps you stay on top of new topics introduced early in the week.',
  },
  {
    id: '4',
    icon: 'rocket',
    tint: Colors.primary[600],
    tag: 'Forecast',
    title: 'On track for an A grade',
    text: "Based on your current trend across all subjects, you're projected to close this term with an overall A grade — about 6% above your previous term's average.",
  },
];

function getInitials(name?: string) {
  if (!name) return 'S';
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || 'S';
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function StudentDashboardScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const firstName = (user?.full_name || 'Student').split(' ')[0];
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
          <Ionicons name="sparkles" size={18} color={Colors.white} />
          <Text style={styles.heroBannerText}>
            You're <Text style={styles.heroBannerStrong}>on track for an A grade</Text> this term — your AI insights are ready below.
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.flex}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + Spacing.xl }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Overall summary */}
        <Text style={styles.sectionTitle}>Your Overview</Text>
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
                  name={stat.trendUp ? 'arrow-up' : 'time'}
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

        {/* Quick insights — tap to jump to the relevant tab */}
        <Text style={styles.sectionTitle}>Quick Insights</Text>
        <View style={styles.insightsList}>
          {QUICK_INSIGHTS.map((insight) => (
            <TouchableOpacity
              key={insight.id}
              activeOpacity={0.75}
              onPress={() => navigation.navigate(insight.route)}
            >
              <Card style={styles.insightCard} padding="md">
                <View style={[styles.insightIconWrap, { backgroundColor: insight.tint + '16' }]}>
                  <Ionicons name={insight.icon} size={22} color={insight.tint} />
                </View>
                <View style={styles.insightTextWrap}>
                  <Text style={styles.insightLabel}>{insight.label}</Text>
                  <Text style={styles.insightSummary}>{insight.summary}</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={Colors.neutral[300]} />
              </Card>
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
              style={[styles.scheduleRow, idx !== SCHEDULE.length - 1 && styles.rowDivider]}
            >
              <View style={styles.scheduleTimeWrap}>
                <Text style={[styles.scheduleTime, item.status === 'now' && styles.scheduleTimeNow]}>{item.time}</Text>
                {item.status === 'now' && <View style={styles.nowDot} />}
              </View>
              <View style={styles.scheduleDivider} />
              <View style={styles.scheduleInfo}>
                <Text style={styles.scheduleSubject}>{item.subject}</Text>
                <Text style={styles.scheduleMeta}>{item.room}</Text>
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

        {/* Upcoming deadlines */}
        <Text style={styles.sectionTitle}>Upcoming Deadlines</Text>
        <Card style={styles.deadlineCard} padding="none">
          {DEADLINES.map((item, idx) => (
            <View
              key={item.id}
              style={[styles.deadlineRow, idx !== DEADLINES.length - 1 && styles.rowDivider]}
            >
              <View style={[styles.deadlineTypeWrap, { backgroundColor: (item.type === 'Assessment' ? Colors.secondary[500] : Colors.primary[600]) + '16' }]}>
                <Ionicons
                  name={item.type === 'Assessment' ? 'clipboard' : 'book'}
                  size={18}
                  color={item.type === 'Assessment' ? Colors.secondary[600] : Colors.primary[600]}
                />
              </View>
              <View style={styles.deadlineInfo}>
                <Text style={styles.deadlineTitle} numberOfLines={1}>{item.title}</Text>
                <Text style={styles.deadlineMeta}>{item.subject} • {item.type}</Text>
              </View>
              <View style={[styles.dueBadge, item.urgent && styles.dueBadgeUrgent]}>
                <Text style={[styles.dueBadgeText, item.urgent && styles.dueBadgeTextUrgent]}>{item.dueIn}</Text>
              </View>
            </View>
          ))}
        </Card>

        {/* Subject-wise performance */}
        <Text style={styles.sectionTitle}>Subject-wise Performance</Text>
        <Card style={styles.performanceCard}>
          {SUBJECT_PERFORMANCE.map((subj) => (
            <View key={subj.id} style={styles.perfRow}>
              <Text style={styles.perfLabel}>{subj.subject}</Text>
              <View style={styles.perfBarBg}>
                <View
                  style={[
                    styles.perfBarFill,
                    {
                      width: `${subj.score}%`,
                      backgroundColor: subj.score >= 85 ? Colors.success : subj.score >= 70 ? Colors.primary[600] : Colors.warning,
                    },
                  ]}
                />
              </View>
              <Text style={styles.perfScore}>{subj.score}%</Text>
            </View>
          ))}
        </Card>

        {/* Recent activity */}
        <Text style={styles.sectionTitle}>Recent Updates</Text>
        <Card style={styles.activityCard} padding="none">
          {ACTIVITY.map((item, idx) => (
            <View
              key={item.id}
              style={[styles.activityRow, idx !== ACTIVITY.length - 1 && styles.rowDivider]}
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

        {/* Career & Skill Recommender entry point */}
        <TouchableOpacity activeOpacity={0.85} onPress={() => navigation.navigate('Career')}>
          <Card style={styles.careerCard} padding="lg">
            <View style={[styles.careerIconWrap, { backgroundColor: Colors.secondary[600] + '16' }]}>
              <Ionicons name="compass" size={26} color={Colors.secondary[600]} />
            </View>
            <View style={styles.careerTextWrap}>
              <Text style={styles.careerTitle}>Discover Your Path</Text>
              <Text style={styles.careerText}>
                Get AI-matched stream, career and scholarship recommendations based on your aptitude,
                interests and academic record.
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={Colors.neutral[300]} />
          </Card>
        </TouchableOpacity>

        {/* AI Insights */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Your AI Insights</Text>
          <View style={styles.aiBadge}>
            <Ionicons name="sparkles" size={12} color={Colors.secondary[600]} />
            <Text style={styles.aiBadgeText}>Personalised</Text>
          </View>
        </View>
        <Text style={styles.aiIntro}>
          Generated from your recent assessments, assignments and attendance trends.
        </Text>
        <View style={styles.aiList}>
          {AI_INSIGHTS.map((insight) => (
            <Card key={insight.id} style={styles.aiCard} padding="lg">
              <View style={styles.aiCardHeader}>
                <View style={[styles.aiIconWrap, { backgroundColor: insight.tint + '16' }]}>
                  <Ionicons name={insight.icon} size={20} color={insight.tint} />
                </View>
                <View style={[styles.aiTagPill, { backgroundColor: insight.tint + '16' }]}>
                  <Text style={[styles.aiTagText, { color: insight.tint }]}>{insight.tag}</Text>
                </View>
              </View>
              <Text style={styles.aiCardTitle}>{insight.title}</Text>
              <Text style={styles.aiCardText}>{insight.text}</Text>
            </Card>
          ))}
        </View>
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

  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.md },
  sectionHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },

  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginBottom: Spacing.xl },
  statCard: { width: '48%' },
  statIconWrap: { width: 36, height: 36, borderRadius: BorderRadius.md, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.sm },
  statValue: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  statLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  statTrendRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: Spacing.sm },
  statTrend: { fontSize: 10, fontWeight: Typography.weights.semibold, flexShrink: 1 },

  insightsList: { gap: Spacing.sm, marginBottom: Spacing.xl },
  insightCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  insightIconWrap: { width: 46, height: 46, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  insightTextWrap: { flex: 1 },
  insightLabel: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  insightSummary: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },

  liveBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: Colors.success + '16', paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.success },
  liveBadgeText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.success },

  scheduleCard: { marginBottom: Spacing.xl, overflow: 'hidden' },
  scheduleRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.md },
  rowDivider: { borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  scheduleTimeWrap: { width: 86 },
  scheduleTime: { fontSize: 11, fontWeight: Typography.weights.semibold, color: Colors.neutral[500] },
  scheduleTimeNow: { color: Colors.primary[600] },
  nowDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.primary[600], marginTop: 4 },
  scheduleDivider: { width: 1, height: 32, backgroundColor: Colors.neutral[100] },
  scheduleInfo: { flex: 1 },
  scheduleSubject: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  scheduleMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  nowBadge: { backgroundColor: Colors.primary[600], paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  nowBadgeText: { fontSize: 10, fontWeight: Typography.weights.bold, color: Colors.white },

  deadlineCard: { marginBottom: Spacing.xl, overflow: 'hidden' },
  deadlineRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.md },
  deadlineTypeWrap: { width: 38, height: 38, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  deadlineInfo: { flex: 1 },
  deadlineTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  deadlineMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  dueBadge: { backgroundColor: Colors.neutral[100], paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  dueBadgeUrgent: { backgroundColor: Colors.danger + '16' },
  dueBadgeText: { fontSize: 10, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  dueBadgeTextUrgent: { color: Colors.danger },

  performanceCard: { marginBottom: Spacing.xl, padding: Spacing.lg, gap: Spacing.md },
  perfRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  perfLabel: { width: 96, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[700] },
  perfBarBg: { flex: 1, height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden' },
  perfBarFill: { height: '100%', borderRadius: 4 },
  perfScore: { width: 38, textAlign: 'right', fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },

  activityCard: { marginBottom: Spacing.xl, overflow: 'hidden' },
  activityRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.md },
  activityIconWrap: { width: 38, height: 38, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  activityTextWrap: { flex: 1 },
  activityTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  activitySubtitle: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  activityTime: { fontSize: 10, color: Colors.neutral[400] },

  careerCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.xl, ...Shadows.sm },
  careerIconWrap: { width: 52, height: 52, borderRadius: BorderRadius.xl, justifyContent: 'center', alignItems: 'center' },
  careerTextWrap: { flex: 1 },
  careerTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  careerText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4, lineHeight: 17 },

  aiBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.secondary[500] + '16', paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  aiBadgeText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.secondary[600] },
  aiIntro: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: -Spacing.sm, marginBottom: Spacing.md, lineHeight: 19 },
  aiList: { gap: Spacing.sm },
  aiCard: { ...Shadows.sm },
  aiCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  aiIconWrap: { width: 40, height: 40, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  aiTagPill: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  aiTagText: { fontSize: 10, fontWeight: Typography.weights.bold, textTransform: 'uppercase', letterSpacing: 0.5 },
  aiCardTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.xs },
  aiCardText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20 },
});
