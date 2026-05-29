import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const TYPE_COLORS: Record<string, string> = {
  FA1: Colors.success, FA2: '#84cc16', FA3: Colors.warning, FA4: '#f97316',
  SA1: Colors.primary[600], SA2: Colors.secondary[600],
  UNIT_TEST: Colors.neutral[500], ANNUAL: Colors.danger,
};

export default function AssessmentsScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);

  const { data: assessments = [], isLoading } = useQuery({
    queryKey: ['assessments', user?.school_id],
    queryFn: async () => {
      const res = await api.get(`/assessments/school/${user?.school_id ?? 1}`);
      return res.data;
    },
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading assessments..." />;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Assessments"
        subtitle={`${assessments.length} total`}
        rightAction={{ icon: 'add-circle-outline', onPress: () => {} }}
      />

      {assessments.length === 0 ? (
        <EmptyState
          icon="document-text-outline"
          title="No Assessments Yet"
          description="Create your first assessment to get started."
        />
      ) : (
        <FlatList
          data={assessments}
          keyExtractor={(item: any) => String(item.id)}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => {
            const typeColor = TYPE_COLORS[item.type] ?? Colors.neutral[400];
            return (
              <Card style={styles.card}>
                <View style={styles.cardHeader}>
                  <View style={[styles.typeBadge, { backgroundColor: `${typeColor}20` }]}>
                    <Text style={[styles.typeText, { color: typeColor }]}>{item.type}</Text>
                  </View>
                  <View style={[styles.publishedDot, { backgroundColor: item.is_published ? Colors.success : Colors.neutral[300] }]} />
                  <Text style={styles.publishedLabel}>{item.is_published ? 'Published' : 'Draft'}</Text>
                </View>

                <Text style={styles.title}>{item.title}</Text>
                <Text style={styles.subject}>{item.subject} • Class {item.class_grade}</Text>

                <View style={styles.footer}>
                  <View style={styles.marks}>
                    <Ionicons name="ribbon-outline" size={14} color={Colors.neutral[400]} />
                    <Text style={styles.marksText}>Max: {item.max_marks} marks</Text>
                  </View>
                  <View style={styles.footerActions}>
                    <TouchableOpacity style={styles.footerBtn}>
                      <Text style={styles.footerBtnText}>Grades</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.footerBtn}>
                      <Text style={styles.footerBtnText}>Analytics</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </Card>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  list: { padding: Spacing.base, gap: Spacing.sm },
  card: { padding: Spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  typeBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 3, borderRadius: BorderRadius.full },
  typeText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  publishedDot: { width: 8, height: 8, borderRadius: 4 },
  publishedLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  title: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: 4 },
  subject: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginBottom: Spacing.md },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: Colors.neutral[100], paddingTop: Spacing.sm },
  marks: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  marksText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  footerActions: { flexDirection: 'row', gap: Spacing.sm },
  footerBtn: { paddingHorizontal: Spacing.sm, paddingVertical: 4, backgroundColor: Colors.primary[50], borderRadius: BorderRadius.full },
  footerBtnText: { fontSize: Typography.sizes.xs, color: Colors.primary[700], fontWeight: Typography.weights.semibold },
});
