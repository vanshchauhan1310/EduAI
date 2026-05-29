import React from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import dayjs from 'dayjs';

const MOCK_ASSIGNMENTS = [
  { id: 1, title: 'Chapter 5 Exercises',   subject: 'Maths',   due: '2025-06-02', submitted: false, priority: 'HIGH' },
  { id: 2, title: 'Essay: My Village',      subject: 'English', due: '2025-06-04', submitted: true,  priority: 'MEDIUM' },
  { id: 3, title: 'Science Lab Report',     subject: 'Science', due: '2025-06-06', submitted: false, priority: 'MEDIUM' },
  { id: 4, title: 'History Map Activity',   subject: 'Social',  due: '2025-06-10', submitted: false, priority: 'LOW' },
];

const SUBJECT_COLORS: Record<string, string> = {
  Maths: Colors.primary[600], English: Colors.secondary[500],
  Science: Colors.success, Social: Colors.warning,
};

export default function AssignmentsScreen() {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="My Assignments" subtitle={`${MOCK_ASSIGNMENTS.filter((a) => !a.submitted).length} pending`} />

      <FlatList
        data={MOCK_ASSIGNMENTS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const daysLeft = dayjs(item.due).diff(dayjs(), 'day');
          const urgent = daysLeft <= 2 && !item.submitted;
          const subjectColor = SUBJECT_COLORS[item.subject] ?? Colors.neutral[500];

          return (
            <Card style={[styles.card, item.submitted && styles.completedCard, urgent && styles.urgentCard]}>
              <View style={styles.cardHeader}>
                <View style={[styles.subjectBadge, { backgroundColor: `${subjectColor}20` }]}>
                  <Text style={[styles.subjectText, { color: subjectColor }]}>{item.subject}</Text>
                </View>
                {item.submitted ? (
                  <View style={styles.doneBadge}>
                    <Ionicons name="checkmark-circle" size={16} color={Colors.success} />
                    <Text style={styles.doneText}>Submitted</Text>
                  </View>
                ) : urgent ? (
                  <View style={styles.urgentBadge}>
                    <Text style={styles.urgentText}>Due soon!</Text>
                  </View>
                ) : null}
              </View>

              <Text style={[styles.title, item.submitted && styles.completedTitle]}>{item.title}</Text>

              <View style={styles.footer}>
                <View style={styles.dueRow}>
                  <Ionicons name="calendar-outline" size={14} color={Colors.neutral[400]} />
                  <Text style={[styles.dueText, urgent && { color: Colors.danger }]}>
                    {item.submitted ? `Due: ${item.due}` : daysLeft < 0 ? 'Overdue!' : daysLeft === 0 ? 'Due today!' : `${daysLeft} days left`}
                  </Text>
                </View>
                {!item.submitted && (
                  <TouchableOpacity style={styles.submitBtn}>
                    <Text style={styles.submitText}>Submit</Text>
                  </TouchableOpacity>
                )}
              </View>
            </Card>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  list: { padding: Spacing.base, gap: Spacing.sm },
  card: { padding: Spacing.md },
  completedCard: { opacity: 0.7 },
  urgentCard: { borderLeftWidth: 3, borderLeftColor: Colors.danger },
  cardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: Spacing.sm },
  subjectBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 3, borderRadius: BorderRadius.full },
  subjectText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  doneBadge: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  doneText: { fontSize: Typography.sizes.xs, color: Colors.success, fontWeight: Typography.weights.semibold },
  urgentBadge: { backgroundColor: '#fef2f2', paddingHorizontal: Spacing.sm, paddingVertical: 3, borderRadius: BorderRadius.full },
  urgentText: { fontSize: Typography.sizes.xs, color: Colors.danger, fontWeight: Typography.weights.bold },
  title: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.md },
  completedTitle: { textDecorationLine: 'line-through', color: Colors.neutral[400] },
  footer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  dueRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  dueText: { fontSize: Typography.sizes.sm, color: Colors.neutral[400] },
  submitBtn: { backgroundColor: Colors.primary[600], paddingHorizontal: Spacing.md, paddingVertical: 6, borderRadius: BorderRadius.full },
  submitText: { color: Colors.white, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold },
});
