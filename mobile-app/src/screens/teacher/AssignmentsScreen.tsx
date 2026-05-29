import React from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const MOCK_ASSIGNMENTS = [
  { id: 1, title: 'Chapter 5 Exercise', subject: 'Mathematics', class: '7A', due: '2025-06-02', submissions: 18, total: 24 },
  { id: 2, title: 'Essay: My Village',  subject: 'English',     class: '7B', due: '2025-06-04', submissions: 22, total: 22 },
  { id: 3, title: 'Science Lab Report', subject: 'Science',     class: '8A', due: '2025-06-06', submissions: 10, total: 28 },
  { id: 4, title: 'History Timeline',   subject: 'Social',      class: '8B', due: '2025-06-08', submissions: 0,  total: 26 },
];

export default function AssignmentsScreen() {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Assignments"
        subtitle={`${MOCK_ASSIGNMENTS.length} active`}
        rightAction={{ icon: 'add-circle-outline', onPress: () => {} }}
      />

      <FlatList
        data={MOCK_ASSIGNMENTS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const submissionRate = (item.submissions / item.total) * 100;
          const color = submissionRate >= 90 ? Colors.success : submissionRate >= 50 ? Colors.warning : Colors.danger;
          return (
            <Card style={styles.card}>
              <View style={styles.cardHeader}>
                <View style={styles.subjectBadge}>
                  <Text style={styles.subjectText}>{item.subject}</Text>
                </View>
                <Text style={styles.classText}>{item.class}</Text>
              </View>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.due}>Due: {item.due}</Text>

              <View style={styles.progressRow}>
                <View style={styles.progressBg}>
                  <View style={[styles.progressFill, { width: `${submissionRate}%` as any, backgroundColor: color }]} />
                </View>
                <Text style={[styles.progressText, { color }]}>
                  {item.submissions}/{item.total} submitted
                </Text>
              </View>

              <View style={styles.footer}>
                <TouchableOpacity style={styles.footerBtn}>
                  <Ionicons name="eye-outline" size={14} color={Colors.primary[600]} />
                  <Text style={styles.footerBtnText}>View Submissions</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.footerBtn}>
                  <Ionicons name="megaphone-outline" size={14} color={Colors.warning} />
                  <Text style={[styles.footerBtnText, { color: Colors.warning }]}>Remind</Text>
                </TouchableOpacity>
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
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  subjectBadge: {
    backgroundColor: Colors.primary[50],
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.full,
  },
  subjectText: { fontSize: Typography.sizes.xs, color: Colors.primary[700], fontWeight: Typography.weights.bold },
  classText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  title: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: 4 },
  due: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginBottom: Spacing.md },
  progressRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  progressBg: { flex: 1, height: 6, backgroundColor: Colors.neutral[100], borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3 },
  progressText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, minWidth: 80, textAlign: 'right' },
  footer: {
    flexDirection: 'row',
    gap: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.neutral[100],
    paddingTop: Spacing.sm,
  },
  footerBtn: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  footerBtnText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
});
