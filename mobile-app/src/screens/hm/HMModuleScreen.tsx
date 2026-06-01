import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

const MODULE_CONTENT: Record<string, {
  title: string;
  subtitle: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  stats: Array<[string, string]>;
  insights: string[];
}> = {
  AttendanceIntelligence: {
    title: 'Attendance Intelligence',
    subtitle: 'Real-time attendance monitoring',
    icon: 'trending-up-outline',
    color: '#2f6df6',
    stats: [['94%', 'Today'], ['82%', 'Lowest class'], ['18', 'Absent']],
    insights: ['Class 8B needs attention this week', 'Morning attendance is stronger than afternoon sessions', '3 students crossed the 5-day absence threshold'],
  },
  DropoutPrediction: {
    title: 'Dropout Prediction',
    subtitle: 'Early intervention queue',
    icon: 'warning-outline',
    color: '#ef4444',
    stats: [['12', 'At risk'], ['3', 'Critical'], ['5', 'Follow-ups']],
    insights: ['Assign counselor follow-up for critical students', 'Attendance decline is the strongest risk signal', 'Parent contact is pending for 5 students'],
  },
  TeacherPerformance: {
    title: 'Teacher Performance',
    subtitle: 'Teacher attendance and classroom indicators',
    icon: 'person-add-outline',
    color: '#09b981',
    stats: [['22', 'Teachers'], ['2', 'Alerts'], ['91%', 'Coverage']],
    insights: ['Maths substitute needed today', 'Science lab periods can be increased', 'Two teachers need monthly observation review'],
  },
  StudentLearning: {
    title: 'Student Learning',
    subtitle: 'Class-wise performance analytics',
    icon: 'book-outline',
    color: '#f59e0b',
    stats: [['79%', 'FLN avg'], ['6%', 'Growth'], ['4', 'Weak areas']],
    insights: ['Class 9A improved 6% this month', 'Science and Maths need remedial blocks', 'Reading fluency is improving in primary grades'],
  },
  SchoolHealthModule: {
    title: 'School Health',
    subtitle: 'Overall school health score',
    icon: 'heart-outline',
    color: '#ec4899',
    stats: [['8.5', 'Score'], ['A', 'Grade'], ['2', 'Actions']],
    insights: ['Operational readiness is strong', 'Library usage needs improvement', 'Drinking water and toilets are compliant'],
  },
  SchoolOperations: {
    title: 'School Operations',
    subtitle: 'Infrastructure and facilities',
    icon: 'business-outline',
    color: '#06b6d4',
    stats: [['91%', 'Ready'], ['2', 'Pending'], ['34%', 'Lab use']],
    insights: ['Science lab utilization is low', 'Two facility requests need approval', 'Computer lab schedule can support more classes'],
  },
};

export default function HMModuleScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const route = useRoute();
  const module = MODULE_CONTENT[route.name] ?? MODULE_CONTENT.AttendanceIntelligence;

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color="#071a3a" />
        </TouchableOpacity>
        <View style={[styles.headerIcon, { backgroundColor: `${module.color}14` }]}>
          <Ionicons name={module.icon} size={26} color={module.color} />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title}>{module.title}</Text>
          <Text style={styles.subtitle}>{module.subtitle}</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.statsRow}>
          {module.stats.map(([value, label]) => (
            <View key={label} style={styles.statCard}>
              <Text style={styles.statValue}>{value}</Text>
              <Text style={styles.statLabel}>{label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.panel}>
          <Text style={styles.panelTitle}>Priority Actions</Text>
          {module.insights.map((item) => (
            <TouchableOpacity key={item} style={styles.actionRow} activeOpacity={0.82}>
              <View style={[styles.dot, { backgroundColor: module.color }]} />
              <Text style={styles.actionText}>{item}</Text>
              <Ionicons name="chevron-forward" size={18} color="#8a9ab3" />
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.panel}>
          <Text style={styles.panelTitle}>AI Recommendation</Text>
          <Text style={styles.recommendation}>
            Review the highest-priority item today, assign an owner, and record the follow-up status before end of day.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#edf3ff' },
  header: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, padding: Spacing.base, backgroundColor: '#edf3ff' },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.white, alignItems: 'center', justifyContent: 'center', ...Shadows.sm },
  headerIcon: { width: 52, height: 52, borderRadius: BorderRadius.lg, alignItems: 'center', justifyContent: 'center' },
  headerText: { flex: 1 },
  title: { color: '#071a3a', fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold },
  subtitle: { color: '#536784', fontSize: Typography.sizes.sm, marginTop: 2 },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  statsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.lg },
  statCard: { flex: 1, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.lg, alignItems: 'center', ...Shadows.sm },
  statValue: { color: '#071a3a', fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold },
  statLabel: { color: '#536784', fontSize: Typography.sizes.sm, marginTop: 4, textAlign: 'center' },
  panel: { backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.lg, marginBottom: Spacing.md, ...Shadows.sm },
  panelTitle: { color: '#071a3a', fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, marginBottom: Spacing.md },
  actionRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, paddingVertical: Spacing.md, borderBottomWidth: 1, borderBottomColor: '#eef2f7' },
  dot: { width: 8, height: 8, borderRadius: 4 },
  actionText: { flex: 1, color: '#071a3a', fontSize: Typography.sizes.base, lineHeight: 21 },
  recommendation: { color: '#536784', fontSize: Typography.sizes.base, lineHeight: 23 },
});
