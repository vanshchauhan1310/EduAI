import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

interface AssessmentSummary {
  id: number;
  title: string;
  type: string;
  subject: string;
  class_grade: number;
  section: string | null;
  max_marks: number;
  is_published: boolean;
  has_questions: boolean;
  submissions_count: number;
  created_at: string;
}

export default function AssessmentsListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();

  const { data: assessments, isLoading, refetch, isRefetching } = useQuery<AssessmentSummary[]>({
    queryKey: ['assessments', 'mine'],
    queryFn: async () => {
      const res = await api.get('/assessments/my');
      return res.data;
    },
  });

  React.useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => refetch());
    return unsubscribe;
  }, [navigation, refetch]);

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading assessments..." />;
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Assessments"
        subtitle={`${assessments?.length || 0} created`}
        rightAction={{
          icon: 'add-circle-outline',
          onPress: () => navigation.navigate('CreateAssessment'),
        }}
      />

      <FlatList
        data={assessments || []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshing={isRefetching}
        onRefresh={refetch}
        renderItem={({ item }) => (
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={() =>
              navigation.navigate('AssessmentResults', {
                assessmentId: item.id,
                title: item.title,
                maxMarks: item.max_marks,
                isPublished: item.is_published,
                hasQuestions: item.has_questions,
              })
            }
          >
            <Card style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.title} numberOfLines={1}>{item.title}</Text>
                <View
                  style={[
                    styles.statusBadge,
                    item.is_published ? styles.publishedBadge : styles.draftBadge,
                  ]}
                >
                  <Text
                    style={[
                      styles.statusText,
                      item.is_published ? styles.publishedText : styles.draftText,
                    ]}
                  >
                    {item.is_published ? 'Published' : 'Draft'}
                  </Text>
                </View>
              </View>

              <Text style={styles.meta}>
                {item.subject} · Class {item.class_grade}{item.section ? `-${item.section}` : ''} · {item.type}
              </Text>

              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Ionicons
                    name={item.has_questions ? 'checkmark-circle' : 'help-circle-outline'}
                    size={16}
                    color={item.has_questions ? Colors.success : Colors.neutral[400]}
                  />
                  <Text style={styles.statText}>
                    {item.has_questions ? 'Questions ready' : 'No questions yet'}
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Ionicons name="people-outline" size={16} color={Colors.neutral[500]} />
                  <Text style={styles.statText}>{item.submissions_count} attempted</Text>
                </View>
                <View style={styles.statItem}>
                  <Ionicons name="ribbon-outline" size={16} color={Colors.neutral[500]} />
                  <Text style={styles.statText}>{item.max_marks} marks</Text>
                </View>
              </View>
            </Card>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={[styles.flex, styles.center, { padding: Spacing.xl }]}>
            <Ionicons name="document-text-outline" size={64} color={Colors.neutral[200]} />
            <Text style={styles.emptyText}>No assessments yet</Text>
            <Text style={styles.emptySubtext}>Tap + to create and publish your first assessment</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  center: { justifyContent: 'center', alignItems: 'center' },
  listContent: { padding: Spacing.base, gap: Spacing.sm },
  card: { padding: Spacing.md, marginBottom: Spacing.sm },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  title: { flex: 1, fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginRight: Spacing.sm },
  statusBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  publishedBadge: { backgroundColor: Colors.success + '20' },
  draftBadge: { backgroundColor: Colors.neutral[200] },
  statusText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  publishedText: { color: Colors.success },
  draftText: { color: Colors.neutral[600] },
  meta: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginBottom: Spacing.sm },
  statsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.md },
  statItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  statText: { fontSize: Typography.sizes.xs, color: Colors.neutral[600] },
  emptyText: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[500], marginTop: Spacing.md },
  emptySubtext: { fontSize: Typography.sizes.sm, color: Colors.neutral[400], marginTop: 4, textAlign: 'center' },
});
