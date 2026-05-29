import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const RESULTS = [
  { subject: 'Maths',   fa1: 38, fa2: 42, sa1: 72  },
  { subject: 'Science', fa1: 44, fa2: 46, sa1: 80  },
  { subject: 'English', fa1: 35, fa2: 40, sa1: 65  },
  { subject: 'Telugu',  fa1: 47, fa2: 48, sa1: 88  },
  { subject: 'Social',  fa1: 41, fa2: 39, sa1: 70  },
];

function getGrade(pct: number): string {
  if (pct >= 90) return 'A+';
  if (pct >= 80) return 'A';
  if (pct >= 70) return 'B+';
  if (pct >= 60) return 'B';
  if (pct >= 50) return 'C';
  if (pct >= 35) return 'D';
  return 'F';
}

const GRADE_COLORS: Record<string, string> = {
  'A+': Colors.success, A: '#22c55e', 'B+': '#65a30d',
  B: Colors.warning, C: '#f97316', D: Colors.danger, F: '#7f1d1d',
};

export default function ChildPerformance() {
  const insets = useSafeAreaInsets();
  const overall = Math.round(RESULTS.reduce((s, r) => s + r.sa1, 0) / RESULTS.length);
  const grade = getGrade(overall);

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Child Performance" subtitle="Arjun Kumar" />

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Overall Summary */}
        <Card style={[styles.overallCard, { borderLeftColor: GRADE_COLORS[grade], borderLeftWidth: 4 }]}>
          <Text style={styles.overallLabel}>Overall Average</Text>
          <View style={styles.overallRow}>
            <View>
              <Text style={styles.overallPct}>{overall}%</Text>
              <Text style={styles.overallSub}>Class Rank: 8 / 35</Text>
            </View>
            <View style={[styles.gradeBadge, { backgroundColor: `${GRADE_COLORS[grade]}20` }]}>
              <Text style={[styles.gradeText, { color: GRADE_COLORS[grade] }]}>{grade}</Text>
            </View>
          </View>
        </Card>

        {/* Subject-wise */}
        <Text style={styles.sectionTitle}>Subject-wise SA1 Results</Text>
        {RESULTS.map((r) => {
          const g = getGrade(r.sa1);
          return (
            <View key={r.subject} style={styles.subjectRow}>
              <Text style={styles.subjectName}>{r.subject}</Text>
              <View style={styles.barBg}>
                <View style={[styles.barFill, {
                  width: `${r.sa1}%` as any,
                  backgroundColor: r.sa1 >= 75 ? Colors.success : r.sa1 >= 60 ? Colors.warning : Colors.danger,
                }]} />
              </View>
              <Text style={styles.marksText}>{r.sa1}</Text>
              <View style={[styles.gradePill, { backgroundColor: `${GRADE_COLORS[g]}20` }]}>
                <Text style={[styles.gradePillText, { color: GRADE_COLORS[g] }]}>{g}</Text>
              </View>
            </View>
          );
        })}

        {/* Teacher Comment Card */}
        <Card style={styles.commentCard}>
          <Text style={styles.commentTitle}>🏫 Teacher's Note</Text>
          <Text style={styles.commentText}>
            Arjun is performing consistently in Science and Telugu. Needs additional support in English comprehension.
            Please encourage daily reading at home.
          </Text>
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['2xl'] },
  overallCard: { marginBottom: Spacing.md, borderRadius: 16 },
  overallLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginBottom: Spacing.sm },
  overallRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  overallPct: { fontSize: Typography.sizes['3xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  overallSub: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 2 },
  gradeBadge: { width: 56, height: 56, borderRadius: 28, justifyContent: 'center', alignItems: 'center' },
  gradeText: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md },
  subjectRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    marginBottom: 8,
    gap: Spacing.sm,
    ...require('../../theme').Shadows.sm,
  },
  subjectName: { width: 64, fontSize: Typography.sizes.sm, color: Colors.neutral[700], fontWeight: Typography.weights.medium },
  barBg: { flex: 1, height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 4 },
  marksText: { width: 32, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[700], textAlign: 'right' },
  gradePill: { paddingHorizontal: Spacing.sm, paddingVertical: 3, borderRadius: BorderRadius.full },
  gradePillText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  commentCard: { marginTop: Spacing.md, backgroundColor: '#f0fdf4' },
  commentTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: '#166534', marginBottom: Spacing.sm },
  commentText: { fontSize: Typography.sizes.sm, color: '#14532d', lineHeight: 20 },
});
