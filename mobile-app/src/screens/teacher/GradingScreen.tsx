import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, TextInput, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const MAX_MARKS = 50;
const MOCK_STUDENTS = [
  { id: 301, name: 'Aditya Varma',  roll: '01' },
  { id: 302, name: 'Bhavana Reddy', roll: '02' },
  { id: 303, name: 'Charan Kumar',  roll: '03' },
  { id: 304, name: 'Deepika Rao',   roll: '04' },
];

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

const GRADE_COLORS: Record<string, string> = {
  'A+': Colors.success, A: '#4ade80', 'B+': '#84cc16',
  B: Colors.warning, C: '#f97316', D: '#fb923c', F: Colors.danger,
};

export default function GradingScreen() {
  const insets = useSafeAreaInsets();
  const [marks, setMarks] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => setSubmitted(true);

  if (submitted) {
    return (
      <View style={[styles.flex, styles.successContainer, { paddingBottom: insets.bottom }]}>
        <Text style={styles.successEmoji}>🎉</Text>
        <Text style={styles.successTitle}>Grades Submitted!</Text>
        <Text style={styles.successSub}>FA1 Mathematics grades have been recorded.</Text>
        <Button title="Grade Another Test" onPress={() => setSubmitted(false)} style={styles.resetBtn} />
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Grading" subtitle="FA1 • Mathematics • Class 7" />

      <View style={styles.testInfo}>
        <Text style={styles.testLabel}>Max Marks: <Text style={styles.testValue}>{MAX_MARKS}</Text></Text>
        <Text style={styles.testLabel}>Students: <Text style={styles.testValue}>{MOCK_STUDENTS.length}</Text></Text>
      </View>

      <FlatList
        data={MOCK_STUDENTS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => {
          const val = marks[item.id] ?? '';
          const numVal = parseFloat(val);
          const grade = val && !isNaN(numVal) && numVal >= 0 ? getGrade(numVal, MAX_MARKS) : null;

          return (
            <View style={styles.row}>
              <Text style={styles.roll}>{item.roll}</Text>
              <Text style={styles.name}>{item.name}</Text>
              <TextInput
                style={styles.marksInput}
                value={val}
                onChangeText={(text) => setMarks((p) => ({ ...p, [item.id]: text }))}
                placeholder="0"
                placeholderTextColor={Colors.neutral[300]}
                keyboardType="numeric"
                maxLength={3}
              />
              <Text style={styles.maxLabel}>/{MAX_MARKS}</Text>
              {grade && (
                <View style={[styles.gradeBadge, { backgroundColor: `${GRADE_COLORS[grade]}20` }]}>
                  <Text style={[styles.gradeText, { color: GRADE_COLORS[grade] }]}>{grade}</Text>
                </View>
              )}
            </View>
          );
        }}
        ListFooterComponent={
          <View style={styles.footer}>
            <Button title="Submit All Grades" onPress={handleSubmit} fullWidth size="lg" />
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  testInfo: {
    flexDirection: 'row',
    gap: Spacing.xl,
    backgroundColor: Colors.white,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  testLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },
  testValue: { fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  list: { padding: Spacing.base, gap: 8 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    gap: Spacing.sm,
    ...require('../../theme').Shadows.sm,
  },
  roll: { width: 28, fontSize: Typography.sizes.sm, color: Colors.neutral[400], fontWeight: Typography.weights.bold },
  name: { flex: 1, fontSize: Typography.sizes.base, fontWeight: Typography.weights.medium, color: Colors.neutral[900] },
  marksInput: {
    width: 60,
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    padding: Spacing.sm,
    textAlign: 'center',
    fontSize: Typography.sizes.base,
    fontWeight: Typography.weights.bold,
    color: Colors.neutral[900],
    backgroundColor: Colors.neutral[50],
  },
  maxLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[400] },
  gradeBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
    minWidth: 32,
    alignItems: 'center',
  },
  gradeText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  footer: { padding: Spacing.base },
  successContainer: { justifyContent: 'center', alignItems: 'center', padding: Spacing['2xl'] },
  successEmoji: { fontSize: 64, marginBottom: Spacing.md },
  successTitle: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  successSub: { fontSize: Typography.sizes.base, color: Colors.neutral[500], marginTop: Spacing.sm, textAlign: 'center' },
  resetBtn: { marginTop: Spacing.xl },
});
