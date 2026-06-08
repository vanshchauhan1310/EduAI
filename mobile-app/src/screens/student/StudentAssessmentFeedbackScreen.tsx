import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, FlatList, Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

interface AIInsight {
  question_id: number;
  question_text: string;
  score: number;
  max_score: number;
  semantic_similarity?: number | null;
  rubric_coverage?: number | null;
  feedback?: string | null;
  matched_points?: string[];
  missing_points?: string[];
}

interface StudentAssessmentItem {
  id: number;
  title: string;
  type: string;
  subject: string;
  max_marks: number;
  duration_minutes: number;
  scheduled_date: string | null;
  attempted: boolean;
  is_graded: boolean;
  marks_obtained?: number | null;
  percentage?: number | null;
  grade?: string | null;
  feedback?: string | null;
  ai_insights?: AIInsight[] | null;
  submitted_at?: string;
}

const getGradeColor = (grade?: string | null) => {
  if (!grade) return Colors.neutral[400];
  const g = grade.toUpperCase();
  if (g.startsWith('A')) return Colors.success;
  if (g.startsWith('B')) return Colors.info;
  if (g.startsWith('C')) return Colors.warning;
  return Colors.danger;
};

const getScoreColor = (percentage?: number | null) => {
  if (percentage === null || percentage === undefined) return Colors.neutral[400];
  if (percentage >= 75) return Colors.success;
  if (percentage >= 50) return Colors.warning;
  return Colors.danger;
};

const formatDate = (value?: string | null) => {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
};

export default function StudentAssessmentFeedbackScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<StudentAssessmentItem | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  const { data, isLoading, isRefetching, refetch } = useQuery<StudentAssessmentItem[]>({
    queryKey: ['student', 'assessments', 'my'],
    queryFn: async () => {
      const res = await api.get('/assessments/student/my');
      return res.data;
    },
  });

  const assessments: StudentAssessmentItem[] = data || [];
  const completed = assessments.filter((a: StudentAssessmentItem) => a.attempted);
  const graded = completed.filter((a: StudentAssessmentItem) => a.is_graded);
  const pending = assessments.filter((a: StudentAssessmentItem) => !a.attempted);
  const averageScore = graded.length
    ? Math.round(graded.reduce((sum: number, a: StudentAssessmentItem) => sum + (a.percentage ?? 0), 0) / graded.length)
    : null;

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading your assessments..." />;
  }

  const handlePress = (item: StudentAssessmentItem) => {
    if (!item.attempted) {
      navigation.navigate('TakeAssessment', { assessmentId: item.id });
    } else {
      setSelected(item);
      setShowDetail(true);
    }
  };

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Assessments"
        subtitle={`${assessments.length} published • ${completed.length} completed`}
      />

      <FlatList
        data={assessments}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshing={isRefetching}
        onRefresh={refetch}
        ListHeaderComponent={
          assessments.length > 0 ? (
            <View style={styles.statsRow}>
              <Card style={styles.statCard}>
                <Text style={styles.statValue}>{assessments.length}</Text>
                <Text style={styles.statLabel}>Published</Text>
              </Card>
              <Card style={styles.statCard}>
                <Text style={[styles.statValue, { color: Colors.warning }]}>{pending.length}</Text>
                <Text style={styles.statLabel}>Unattempted</Text>
              </Card>
              <Card style={styles.statCard}>
                <Text style={[styles.statValue, { color: Colors.success }]}>
                  {averageScore !== null ? `${averageScore}%` : '—'}
                </Text>
                <Text style={styles.statLabel}>Avg. Score</Text>
              </Card>
            </View>
          ) : null
        }
        renderItem={({ item }) => {
          const dateLabel = formatDate(item.scheduled_date) || formatDate(item.submitted_at);

          return (
            <TouchableOpacity activeOpacity={0.85} onPress={() => handlePress(item)}>
              <Card
                style={StyleSheet.flatten([
                  styles.assessmentCard,
                  !item.attempted && styles.unattemptedCard,
                ])}
              >
                <View style={styles.cardTopRow}>
                  <View style={styles.cardTitleWrap}>
                    <Text style={styles.assessmentTitle} numberOfLines={1}>{item.title}</Text>
                    <Text style={styles.assessmentMeta}>
                      {item.subject} • {item.type} • {item.max_marks} marks
                    </Text>
                  </View>

                  {!item.attempted ? (
                    <View style={[styles.statusPill, styles.unattemptedPill]}>
                      <Ionicons name="play-circle-outline" size={14} color={Colors.primary[600]} />
                      <Text style={[styles.statusPillText, { color: Colors.primary[600] }]}>Unattempted</Text>
                    </View>
                  ) : item.is_graded ? (
                    <View style={[styles.gradeCircle, { backgroundColor: getGradeColor(item.grade) + '1a' }]}>
                      <Text style={[styles.gradeCircleText, { color: getGradeColor(item.grade) }]}>
                        {item.grade ?? '—'}
                      </Text>
                    </View>
                  ) : (
                    <View style={[styles.statusPill, styles.pendingPill]}>
                      <Ionicons name="hourglass-outline" size={14} color={Colors.warning} />
                      <Text style={[styles.statusPillText, { color: Colors.warning }]}>Awaiting grade</Text>
                    </View>
                  )}
                </View>

                {item.attempted && item.is_graded ? (
                  <>
                    <View style={styles.scoreRow}>
                      <View style={styles.scoreBarBg}>
                        <View
                          style={[
                            styles.scoreBarFill,
                            {
                              width: `${Math.min(item.percentage ?? 0, 100)}%`,
                              backgroundColor: getScoreColor(item.percentage),
                            },
                          ]}
                        />
                      </View>
                      <Text style={styles.scoreText}>
                        {item.marks_obtained}/{item.max_marks} • {Math.round(item.percentage ?? 0)}%
                      </Text>
                    </View>
                    {!!item.feedback && (
                      <Text style={styles.feedbackPreview} numberOfLines={2}>{item.feedback}</Text>
                    )}
                    <View style={styles.cardFooterRow}>
                      {!!item.ai_insights?.length && (
                        <View style={styles.aiTag}>
                          <Ionicons name="sparkles" size={12} color={Colors.secondary[600]} />
                          <Text style={styles.aiTagText}>AI Insights available</Text>
                        </View>
                      )}
                      <View style={styles.spacer} />
                      <Text style={styles.tapHint}>Tap to view feedback</Text>
                    </View>
                  </>
                ) : item.attempted ? (
                  <View style={styles.cardFooterRow}>
                    <Ionicons name="checkmark-circle-outline" size={16} color={Colors.neutral[400]} />
                    <Text style={styles.submittedText}>
                      Submitted{dateLabel ? ` on ${dateLabel}` : ''} • your teacher will grade this soon
                    </Text>
                  </View>
                ) : (
                  <View style={styles.cardFooterRow}>
                    <Ionicons name="time-outline" size={16} color={Colors.neutral[400]} />
                    <Text style={styles.submittedText}>
                      {item.duration_minutes} min{dateLabel ? ` • Scheduled ${dateLabel}` : ''}
                    </Text>
                    <View style={styles.spacer} />
                    <View style={styles.startHint}>
                      <Text style={styles.startHintText}>Start now</Text>
                      <Ionicons name="arrow-forward" size={14} color={Colors.primary[600]} />
                    </View>
                  </View>
                )}
              </Card>
            </TouchableOpacity>
          );
        }}
        ListEmptyComponent={
          <View style={[styles.center, { padding: Spacing.xl, marginTop: Spacing['3xl'] }]}>
            <Ionicons name="document-text-outline" size={64} color={Colors.neutral[200]} />
            <Text style={styles.emptyTitle}>No assessments yet</Text>
            <Text style={styles.emptyText}>
              Your teacher hasn't published any assessments for your class yet. Check back soon.
            </Text>
          </View>
        }
      />

      {/* Detail Modal — feedback / AI Insights */}
      <Modal visible={showDetail} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContainer, { paddingBottom: insets.bottom }]}>
            <Header
              title={selected?.title || 'Assessment'}
              subtitle={`${selected?.subject ?? ''} • ${selected?.type ?? ''}`}
              onBack={() => setShowDetail(false)}
            />

            <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
              {selected && (
                selected.is_graded ? (
                  <>
                    <Card style={styles.scoreSummaryCard}>
                      <View style={styles.scoreSummaryRow}>
                        <View style={styles.scoreSummaryItem}>
                          <Text style={[styles.scoreSummaryValue, { color: getGradeColor(selected.grade) }]}>
                            {selected.grade ?? '—'}
                          </Text>
                          <Text style={styles.scoreSummaryLabel}>Grade</Text>
                        </View>
                        <View style={styles.scoreSummaryDivider} />
                        <View style={styles.scoreSummaryItem}>
                          <Text style={styles.scoreSummaryValue}>
                            {selected.marks_obtained}/{selected.max_marks}
                          </Text>
                          <Text style={styles.scoreSummaryLabel}>Marks</Text>
                        </View>
                        <View style={styles.scoreSummaryDivider} />
                        <View style={styles.scoreSummaryItem}>
                          <Text style={styles.scoreSummaryValue}>{Math.round(selected.percentage ?? 0)}%</Text>
                          <Text style={styles.scoreSummaryLabel}>Score</Text>
                        </View>
                      </View>
                    </Card>

                    {!!selected.feedback && (
                      <Card style={styles.sectionCard}>
                        <View style={styles.sectionHeaderRow}>
                          <Ionicons name="chatbubble-ellipses-outline" size={18} color={Colors.primary[600]} />
                          <Text style={styles.sectionTitle}>Teacher Feedback</Text>
                        </View>
                        <Text style={styles.sectionBodyText}>{selected.feedback}</Text>
                      </Card>
                    )}

                    {!!selected.ai_insights?.length && (
                      <View style={styles.aiInsightsBlock}>
                        <View style={styles.sectionHeaderRow}>
                          <Ionicons name="sparkles" size={18} color={Colors.secondary[600]} />
                          <Text style={styles.sectionTitle}>AI Insights — question by question</Text>
                        </View>
                        {selected.ai_insights.map((q, idx) => (
                          <Card key={q.question_id ?? idx} style={styles.insightCard}>
                            <Text style={styles.insightQuestion} numberOfLines={3}>
                              Q{idx + 1}. {q.question_text}
                            </Text>
                            <View style={styles.insightScoreRow}>
                              <View style={styles.insightScoreBarBg}>
                                <View
                                  style={[
                                    styles.insightScoreBarFill,
                                    {
                                      width: `${Math.min((q.score / Math.max(q.max_score, 1)) * 100, 100)}%`,
                                      backgroundColor: getScoreColor((q.score / Math.max(q.max_score, 1)) * 100),
                                    },
                                  ]}
                                />
                              </View>
                              <Text style={styles.insightScoreText}>{q.score}/{q.max_score}</Text>
                            </View>
                            {!!q.feedback && <Text style={styles.insightFeedback}>{q.feedback}</Text>}
                            {!!q.matched_points?.length && (
                              <View style={styles.pointsBlock}>
                                {q.matched_points.map((p, i) => (
                                  <View key={`m-${i}`} style={styles.pointRow}>
                                    <Ionicons name="checkmark-circle" size={14} color={Colors.success} />
                                    <Text style={styles.pointText}>{p}</Text>
                                  </View>
                                ))}
                              </View>
                            )}
                            {!!q.missing_points?.length && (
                              <View style={styles.pointsBlock}>
                                {q.missing_points.map((p, i) => (
                                  <View key={`x-${i}`} style={styles.pointRow}>
                                    <Ionicons name="close-circle" size={14} color={Colors.danger} />
                                    <Text style={styles.pointText}>{p}</Text>
                                  </View>
                                ))}
                              </View>
                            )}
                          </Card>
                        ))}
                      </View>
                    )}
                  </>
                ) : (
                  <Card style={styles.awaitingCard}>
                    <Ionicons name="hourglass-outline" size={40} color={Colors.warning} />
                    <Text style={styles.awaitingTitle}>Awaiting grading</Text>
                    <Text style={styles.awaitingText}>
                      You submitted this assessment{selected.submitted_at ? ` on ${formatDate(selected.submitted_at)}` : ''}.
                      Your teacher hasn't graded it yet — your marks, feedback and AI insights will appear here once it's graded.
                    </Text>
                  </Card>
                )
              )}
            </ScrollView>

            <View style={styles.modalFooter}>
              <Button title="Close" onPress={() => setShowDetail(false)} variant="outline" fullWidth />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  center: { alignItems: 'center', justifyContent: 'center' },
  listContent: { padding: Spacing.base, paddingBottom: Spacing['2xl'], gap: Spacing.md },

  statsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  statCard: { flex: 1, alignItems: 'center', paddingVertical: Spacing.md },
  statValue: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  statLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },

  assessmentCard: { padding: Spacing.base, ...Shadows.sm },
  unattemptedCard: { borderWidth: 1, borderColor: Colors.primary[100] },
  cardTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: Spacing.sm },
  cardTitleWrap: { flex: 1 },
  assessmentTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  assessmentMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 3 },

  statusPill: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: Spacing.sm, paddingVertical: 5, borderRadius: BorderRadius.full },
  unattemptedPill: { backgroundColor: Colors.primary[50] },
  pendingPill: { backgroundColor: Colors.warning + '1a' },
  statusPillText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },

  gradeCircle: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  gradeCircleText: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold },

  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginTop: Spacing.md },
  scoreBarBg: { flex: 1, height: 6, borderRadius: 3, backgroundColor: Colors.neutral[100], overflow: 'hidden' },
  scoreBarFill: { height: '100%', borderRadius: 3 },
  scoreText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },

  feedbackPreview: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 18, marginTop: Spacing.sm },

  cardFooterRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: Spacing.md },
  spacer: { flex: 1 },
  submittedText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], flexShrink: 1 },
  tapHint: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontStyle: 'italic' },

  aiTag: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.secondary[500] + '14', paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  aiTagText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.secondary[600] },

  startHint: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  startHintText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.primary[600] },

  emptyTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[700], marginTop: Spacing.base },
  emptyText: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], textAlign: 'center', marginTop: Spacing.xs, lineHeight: 20, maxWidth: 280 },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContainer: { height: '88%', backgroundColor: Colors.background, borderTopLeftRadius: BorderRadius['2xl'], borderTopRightRadius: BorderRadius['2xl'], overflow: 'hidden' },
  modalContent: { flex: 1, padding: Spacing.base },

  scoreSummaryCard: { padding: Spacing.lg, marginBottom: Spacing.base },
  scoreSummaryRow: { flexDirection: 'row', alignItems: 'center' },
  scoreSummaryItem: { flex: 1, alignItems: 'center' },
  scoreSummaryDivider: { width: 1, height: 32, backgroundColor: Colors.neutral[100] },
  scoreSummaryValue: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  scoreSummaryLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4 },

  sectionCard: { padding: Spacing.lg, marginBottom: Spacing.base },
  sectionHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  sectionTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  sectionBodyText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },

  aiInsightsBlock: { marginBottom: Spacing.base },
  insightCard: { padding: Spacing.base, marginBottom: Spacing.sm, marginTop: Spacing.xs },
  insightQuestion: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900], lineHeight: 19 },
  insightScoreRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginTop: Spacing.sm },
  insightScoreBarBg: { flex: 1, height: 6, borderRadius: 3, backgroundColor: Colors.neutral[100], overflow: 'hidden' },
  insightScoreBarFill: { height: '100%', borderRadius: 3 },
  insightScoreText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[600], minWidth: 40, textAlign: 'right' },
  insightFeedback: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 18, marginTop: Spacing.sm },
  pointsBlock: { marginTop: Spacing.sm, gap: 4 },
  pointRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 6 },
  pointText: { flex: 1, fontSize: Typography.sizes.xs, color: Colors.neutral[600], lineHeight: 17 },

  awaitingCard: { padding: Spacing.xl, alignItems: 'center', marginTop: Spacing.xl },
  awaitingTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: Spacing.md },
  awaitingText: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], textAlign: 'center', marginTop: Spacing.sm, lineHeight: 20 },

  modalFooter: { flexDirection: 'row', gap: Spacing.sm, padding: Spacing.base, backgroundColor: Colors.white, borderTopWidth: 1, borderTopColor: Colors.border },
});
