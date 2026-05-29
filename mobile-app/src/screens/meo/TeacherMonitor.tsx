import React from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import EmptyState from '../../components/common/EmptyState';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const MOCK_TEACHERS = [
  { id: 1, name: 'Ramesh Kumar', subject: 'Mathematics', attendance: 94, performance: 88, classes: '6A,7B', type: 'PERMANENT' },
  { id: 2, name: 'Sunitha Devi', subject: 'Science',     attendance: 88, performance: 91, classes: '8A,8B', type: 'PERMANENT' },
  { id: 3, name: 'Vijay Rao',    subject: 'English',     attendance: 76, performance: 72, classes: '9A,10A', type: 'CONTRACT'  },
  { id: 4, name: 'Lakshmi Bai',  subject: 'Telugu',      attendance: 98, performance: 95, classes: '6B,7A', type: 'PERMANENT' },
];

export default function TeacherMonitor() {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Teacher Monitor" subtitle={`${MOCK_TEACHERS.length} Teachers`} />

      <FlatList
        data={MOCK_TEACHERS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const attColor = item.attendance >= 90 ? Colors.success : item.attendance >= 75 ? Colors.warning : Colors.danger;
          return (
            <Card style={styles.card}>
              <View style={styles.cardTop}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{item.name.charAt(0)}</Text>
                </View>
                <View style={styles.info}>
                  <Text style={styles.name}>{item.name}</Text>
                  <Text style={styles.subject}>{item.subject}</Text>
                  <Text style={styles.classes}>Classes: {item.classes}</Text>
                </View>
                <View style={[styles.typeBadge, item.type === 'CONTRACT' && styles.contractBadge]}>
                  <Text style={[styles.typeText, item.type === 'CONTRACT' && styles.contractText]}>
                    {item.type}
                  </Text>
                </View>
              </View>

              <View style={styles.metricsRow}>
                <View style={styles.metric}>
                  <Text style={styles.metricLabel}>Attendance</Text>
                  <Text style={[styles.metricValue, { color: attColor }]}>{item.attendance}%</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metric}>
                  <Text style={styles.metricLabel}>Performance</Text>
                  <Text style={styles.metricValue}>{item.performance}/100</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metric}>
                  <Ionicons name={item.attendance < 80 ? 'warning-outline' : 'checkmark-circle-outline'} size={16}
                    color={item.attendance < 80 ? Colors.warning : Colors.success} />
                  <Text style={[styles.metricLabel, { marginTop: 2 }]}>
                    {item.attendance < 80 ? 'Alert' : 'Good'}
                  </Text>
                </View>
              </View>

              {item.attendance < 80 && (
                <View style={styles.alert}>
                  <Ionicons name="warning" size={14} color={Colors.warning} />
                  <Text style={styles.alertText}>Attendance below 80% — follow up required</Text>
                </View>
              )}
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
  cardTop: { flexDirection: 'row', gap: Spacing.md, marginBottom: Spacing.md },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary[100],
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.primary[700] },
  info: { flex: 1 },
  name: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  subject: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 1 },
  classes: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 1 },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primary[50],
    alignSelf: 'flex-start',
  },
  contractBadge: { backgroundColor: '#fef3c7' },
  typeText: { fontSize: Typography.sizes.xs, color: Colors.primary[700], fontWeight: Typography.weights.semibold },
  contractText: { color: '#b45309' },
  metricsRow: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: Colors.neutral[100], paddingTop: Spacing.md },
  metric: { flex: 1, alignItems: 'center' },
  metricLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  metricValue: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginTop: 2 },
  metricDivider: { width: 1, backgroundColor: Colors.neutral[100], marginVertical: 2 },
  alert: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#fffbeb',
    borderRadius: BorderRadius.lg,
    padding: Spacing.sm,
    marginTop: Spacing.md,
  },
  alertText: { fontSize: Typography.sizes.xs, color: '#b45309', flex: 1 },
});
