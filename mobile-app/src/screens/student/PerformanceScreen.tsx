import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { analyticsService } from '../../services/analyticsService';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const MOCK_RESULTS = [
  { subject: 'Mathematics', fa1: 38, fa2: 42, sa1: 72, max: 50 },
  { subject: 'Science',     fa1: 44, fa2: 46, sa1: 80, max: 50 },
  { subject: 'English',     fa1: 35, fa2: 40, sa1: 65, max: 50 },
  { subject: 'Telugu',      fa1: 47, fa2: 48, sa1: 88, max: 50 },
  { subject: 'Social',      fa1: 41, fa2: 39, sa1: 70, max: 50 },
];

const GRADE_COLORS: Record<string, string> = {
  'A+': '#16a34a', A: '#22c55e', 'B+': '#65a30d',
  B: '#ca8a04', C: '#ea580c', D: '#dc2626', F: '#7f1d1d',
};

function getGrade(marks: number, max: number): string {
  const pct = (marks / max) * 100;
  if (pct >= 90) return 'A+';
  if (pct >= 80) return 'A';
  if (pct >= 70) return 'B+';
  if (pct >= 60) return 'B';
  if (pct >= 50) return 'C';
  if (pct >= 35) return 'D';
  return 'F';
}

export default function PerformanceScreen() {
  const insets = useSafeAreaInsets();

  const totalMarks = MOCK_RESULTS.reduce((sum, r) => sum + r.sa1, 0);
  const maxTotal = MOCK_RESULTS.length * 100;
  const overallPct = Math.round((totalMarks / maxTotal) * 100);
  const overallGrade = getGrade(totalMarks, maxTotal);

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="My Performance" subtitle="AY 2024-25" />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Overall Card */}
        <Card style={styles.overallCard}>
          <Text style={styles.overallLabel}>Overall Performance</Text>
          <View style={styles.overallRow}>
            <View style={styles.overallScore}>
              <Text style={styles.overallPct}>{overallPct}%</Text>
              <Text style={styles.overallDesc}>Class Rank: 8 / 35</Text>
            </View>
            <View style={[styles.overallGrade, { backgroundColor: `${GRADE_COLORS[overallGrade]}20` }]}>
              <Text style={[styles.overallGradeText, { color: GRADE_COLORS[overallGrade] }]}>{overallGrade}</Text>
            </View>
          </View>
          <View style={styles.progressBg}>
            <View style={[styles.progressFill, {
              width: `${overallPct}%` as any,
              backgroundColor: overallPct >= 75 ? Colors.success : overallPct >= 60 ? Colors.warning : Colors.danger,
            }]} />
          </View>
        </Card>

        {/* Subject-wise Results */}
        <Text style={styles.sectionTitle}>Subject Performance</Text>
        {MOCK_RESULTS.map((result) => {
          const fa1Pct = (result.fa1 / result.max) * 100;
          const sa1Pct = (result.sa1 / 100) * 100;
          const grade = getGrade(result.sa1, 100);
          return (
            <Card key={result.subject} style={styles.subjectCard}>
              <View style={styles.subjectHeader}>
                <Text style={styles.subjectName}>{result.subject}</Text>
                <View style={[styles.gradeBadge, { backgroundColor: `${GRADE_COLORS[grade]}20` }]}>
                  <Text style={[styles.gradeText, { color: GRADE_COLORS[grade] }]}>{grade}</Text>
                </View>
              </View>

              <View style={styles.marksRow}>
                {[
                  { label: 'FA1', marks: result.fa1, max: result.max },
                  { label: 'FA2', marks: result.fa2, max: result.max },
                  { label: 'SA1', marks: result.sa1, max: 100 },
                ].map((test) => (
                  <View key={test.label} style={styles.testBlock}>
                    <Text style={styles.testLabel}>{test.label}</Text>
                    <Text style={styles.testMarks}>{test.marks}</Text>
                    <Text style={styles.testMax}>/{test.max}</Text>
                    <View style={styles.testBarBg}>
                      <View style={[styles.testBarFill, {
                        width: `${(test.marks / test.max) * 100}%` as any,
                        backgroundColor: (test.marks / test.max) >= 0.75 ? Colors.success : (test.marks / test.max) >= 0.6 ? Colors.warning : Colors.danger,
                      }]} />
                    </View>
                  </View>
                ))}
              </View>
            </Card>
          );
        })}

        {/* AI Recommendations */}
        <Card style={styles.aiCard}>
          <Text style={styles.aiTitle}>💡 AI Study Tips</Text>
          {MOCK_RESULTS
            .filter((r) => r.sa1 < 70)
            .map((r) => (
              <Text key={r.subject} style={styles.aiTip}>
                • Focus on <Text style={styles.aiStrong}>{r.subject}</Text> — practice 30 min daily
              </Text>
            ))
          }
          {MOCK_RESULTS.filter((r) => r.sa1 >= 80).length > 0 && (
            <Text style={styles.aiTip}>
              • You're excelling in{' '}
              <Text style={styles.aiStrong}>
                {MOCK_RESULTS.filter((r) => r.sa1 >= 80).map((r) => r.subject).join(', ')}
              </Text>
              — keep it up!
            </Text>
          )}
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  overallCard: { marginBottom: Spacing.md },
  overallLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginBottom: Spacing.sm },
  overallRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  overallScore: {},
  overallPct: { fontSize: Typography.sizes['3xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  overallDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 2 },
  overallGrade: { width: 60, height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center' },
  overallGradeText: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold },
  progressBg: { height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 4 },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md },
  subjectCard: { marginBottom: Spacing.sm, padding: Spacing.md },
  subjectHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  subjectName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  gradeBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  gradeText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  marksRow: { flexDirection: 'row', gap: Spacing.sm },
  testBlock: { flex: 1, alignItems: 'center', gap: 2 },
  testLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontWeight: Typography.weights.semibold },
  testMarks: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  testMax: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  testBarBg: { width: '100%', height: 4, backgroundColor: Colors.neutral[100], borderRadius: 2, overflow: 'hidden' },
  testBarFill: { height: '100%', borderRadius: 2 },
  aiCard: { marginTop: Spacing.sm, backgroundColor: '#f0f9ff' },
  aiTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.primary[700], marginBottom: Spacing.md },
  aiTip: { fontSize: Typography.sizes.sm, color: Colors.primary[800], lineHeight: 22, marginBottom: 4 },
  aiStrong: { fontWeight: Typography.weights.bold },
});
