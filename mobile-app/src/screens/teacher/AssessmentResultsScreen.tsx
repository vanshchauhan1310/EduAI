import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Modal, FlatList,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';

import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

interface StudentSubmission {
  id: number;
  student_id: number;
  student_name: string;
  marks_obtained: number | null;
  percentage: number | null;
  grade: string | null;
  is_absent: boolean;
  is_graded: boolean;
  feedback: string | null;
  submitted_at: string;
}

interface SubmissionsResponse {
  assessment_id: number;
  assessment_title: string;
  max_marks: number;
  submissions: StudentSubmission[];
}

export default function AssessmentResultsScreen({ route, navigation }: any) {
  const insets = useSafeAreaInsets();
  const { assessmentId, title, maxMarks, isPublished, hasQuestions } = route?.params || {};

  const [selectedSubmission, setSelectedSubmission] = useState<StudentSubmission | null>(null);
  const [showResultModal, setShowResultModal] = useState(false);
  const [aiResult, setAiResult] = useState<any | null>(null);
  const [published, setPublished] = useState<boolean>(!!isPublished);

  const { data, isLoading, refetch } = useQuery<SubmissionsResponse>({
    queryKey: ['assessment', assessmentId, 'submissions'],
    queryFn: async () => {
      const res = await api.get(`/assessments/${assessmentId}/submissions`);
      return res.data;
    },
    enabled: !!assessmentId,
  });

  const { mutate: publishAssessment, isPending: isPublishing } = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/assessments/${assessmentId}/publish`);
      return res.data;
    },
    onSuccess: () => {
      setPublished(true);
      alert('✅ Assessment published successfully!');
    },
    onError: (error: any) => {
      alert(`Failed to publish: ${error.response?.data?.detail || error.message}`);
    },
  });

  const { mutate: gradeWithAI, isPending: isAIGrading } = useMutation({
    mutationFn: async (studentId: number) => {
      const res = await api.post(
        `/assessments/${assessmentId}/ai-grade`,
        { student_id: studentId },
        { timeout: 120000 }
      );
      return res.data;
    },
    onSuccess: (resultData) => {
      setAiResult(resultData);
      refetch();
    },
    onError: (error: any) => {
      alert(`AI Grading failed: ${error.response?.data?.detail || error.message}`);
    },
  });

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading submissions..." />;
  }

  const submissions: StudentSubmission[] = data?.submissions || [];
  const gradedCount = submissions.filter((s: StudentSubmission) => s.is_graded).length;
  const ungradedSubmissions = submissions.filter((s: StudentSubmission) => !s.is_graded && !s.is_absent);
  const effectiveMaxMarks = data?.max_marks ?? maxMarks ?? 0;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title={data?.assessment_title || title || 'Results'}
        subtitle={`${gradedCount}/${submissions.length} graded`}
        onBack={() => navigation.goBack()}
      />

      {/* Draft / Publish Banner */}
      {!published && (
        <View style={styles.progressSection}>
          <Card style={styles.draftCard}>
            <View style={styles.draftRow}>
              <Ionicons name="alert-circle-outline" size={24} color={Colors.warning} />
              <View style={styles.draftTextWrap}>
                <Text style={styles.draftTitle}>This assessment is still a draft</Text>
                <Text style={styles.draftSubtitle}>
                  {hasQuestions
                    ? 'Students cannot attempt it until you publish it.'
                    : 'Generate questions for it before publishing.'}
                </Text>
              </View>
            </View>
            <Button
              title={isPublishing ? 'Publishing...' : 'Publish Now'}
              onPress={() => publishAssessment()}
              loading={isPublishing}
              disabled={!hasQuestions}
              fullWidth
              style={styles.draftPublishBtn}
            />
          </Card>
        </View>
      )}

      {/* Progress Summary */}
      <View style={styles.progressSection}>
        <Card style={styles.progressCard}>
          <View style={styles.progressRow}>
            <View style={styles.progressItem}>
              <Ionicons name="checkmark-circle" size={32} color={Colors.success} />
              <Text style={styles.progressValue}>{gradedCount}</Text>
              <Text style={styles.progressLabel}>Graded</Text>
            </View>
            <View style={styles.progressItem}>
              <Ionicons name="hourglass-outline" size={32} color={Colors.warning} />
              <Text style={styles.progressValue}>{ungradedSubmissions.length}</Text>
              <Text style={styles.progressLabel}>Pending</Text>
            </View>
            <View style={styles.progressItem}>
              <Ionicons name="file-tray-full-outline" size={32} color={Colors.primary[600]} />
              <Text style={styles.progressValue}>{submissions.length}</Text>
              <Text style={styles.progressLabel}>Total</Text>
            </View>
          </View>
        </Card>
      </View>

      {/* Submissions List */}
      <FlatList
        data={submissions}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <Card
            style={StyleSheet.flatten([
              styles.submissionCard,
              item.is_graded ? styles.gradedCard : styles.ungradedCard,
            ])}
          >
            <TouchableOpacity
              style={styles.cardTouchable}
              onPress={() => {
                setSelectedSubmission(item);
                setAiResult(null);
                setShowResultModal(true);
              }}
              activeOpacity={0.7}
            >
              <View style={styles.cardHeader}>
                <View style={styles.studentInfo}>
                  <View style={[styles.avatar, { backgroundColor: Colors.primary[100] }]}>
                    <Text style={styles.avatarText}>{item.student_name.charAt(0)}</Text>
                  </View>
                  <View>
                    <Text style={styles.studentName}>{item.student_name}</Text>
                    <Text style={styles.submittedDate}>
                      Submitted: {new Date(item.submitted_at).toLocaleString()}
                    </Text>
                  </View>
                </View>

                <View style={styles.statusArea}>
                  {item.is_absent ? (
                    <View style={styles.absentBadge}>
                      <Text style={styles.absentText}>Absent</Text>
                    </View>
                  ) : item.is_graded ? (
                    <>
                      <View style={styles.gradeBadge}>
                        <Text style={styles.gradeText}>{item.grade}</Text>
                      </View>
                      <Text style={styles.scoreText}>
                        {item.marks_obtained}/{effectiveMaxMarks}
                      </Text>
                    </>
                  ) : (
                    <View style={styles.pendingBadge}>
                      <Text style={styles.pendingText}>Pending</Text>
                    </View>
                  )}
                </View>
              </View>

              {item.percentage !== null && (
                <View style={styles.progressBar}>
                  <View style={styles.progressBg}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${Math.min(item.percentage, 100)}%`,
                          backgroundColor:
                            item.percentage >= 75
                              ? Colors.success
                              : item.percentage >= 50
                              ? Colors.warning
                              : Colors.danger,
                        },
                      ]}
                    />
                  </View>
                  <Text style={styles.percentText}>{Math.round(item.percentage)}%</Text>
                </View>
              )}
            </TouchableOpacity>
          </Card>
        )}
        ListEmptyComponent={
          <View style={[styles.flex, styles.center, { padding: Spacing.xl }]}>
            <Ionicons name="file-tray-outline" size={64} color={Colors.neutral[200]} />
            <Text style={styles.emptyText}>No students have attempted this assessment yet</Text>
          </View>
        }
      />

      {/* Result / AI Grading Modal */}
      <Modal visible={showResultModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContainer, { paddingBottom: insets.bottom }]}>
            <Header
              title={selectedSubmission?.student_name || ''}
              subtitle="AI-assisted grading"
              onBack={() => setShowResultModal(false)}
            />

            <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
              <Card style={styles.aiGradingCard}>
                <Text style={styles.cardTitle}>🤖 AI-Assisted Grading</Text>
                <Text style={styles.cardDescription}>
                  Let AI analyze the student's answers against the rubric and assign a score & feedback automatically.
                </Text>

                <Button
                  title={
                    isAIGrading
                      ? 'Analyzing...'
                      : selectedSubmission?.is_graded
                      ? 'Re-run AI Grading'
                      : 'Run AI Grading'
                  }
                  onPress={() => selectedSubmission && gradeWithAI(selectedSubmission.student_id)}
                  loading={isAIGrading}
                  fullWidth
                  size="lg"
                  style={styles.aiGradeBtn}
                />

                {(aiResult || selectedSubmission?.is_graded) && (
                  <Card style={styles.aiResultCard}>
                    <Text style={styles.resultLabel}>Grading Result</Text>
                    <View style={styles.resultRow}>
                      <Text style={styles.resultKey}>Score</Text>
                      <Text style={styles.resultValue}>
                        {aiResult?.score ?? selectedSubmission?.marks_obtained}/{effectiveMaxMarks}
                      </Text>
                    </View>
                    <View style={styles.resultRow}>
                      <Text style={styles.resultKey}>Grade</Text>
                      <Text style={styles.resultValue}>{aiResult?.grade ?? selectedSubmission?.grade}</Text>
                    </View>
                    <View style={styles.resultRow}>
                      <Text style={styles.resultKey}>Feedback</Text>
                      <Text style={styles.resultValue}>{aiResult?.feedback ?? selectedSubmission?.feedback}</Text>
                    </View>
                  </Card>
                )}
              </Card>
            </ScrollView>

            <View style={styles.modalFooter}>
              <Button
                title="Close"
                onPress={() => setShowResultModal(false)}
                variant="outline"
                fullWidth
              />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  center: { justifyContent: 'center', alignItems: 'center' },
  progressSection: { padding: Spacing.base },
  progressCard: { padding: Spacing.lg },
  draftCard: { padding: Spacing.lg, backgroundColor: Colors.warning + '0c' },
  draftRow: { flexDirection: 'row', alignItems: 'flex-start' },
  draftTextWrap: { flex: 1, marginLeft: Spacing.sm },
  draftTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  draftSubtitle: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginTop: 2 },
  draftPublishBtn: { marginTop: Spacing.md },
  progressRow: { flexDirection: 'row', justifyContent: 'space-around' },
  progressItem: { alignItems: 'center' },
  progressValue: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.primary[600], marginVertical: 4 },
  progressLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[600] },
  listContent: { paddingHorizontal: Spacing.base, paddingBottom: Spacing.base, gap: Spacing.sm },
  submissionCard: { overflow: 'hidden' },
  gradedCard: { backgroundColor: Colors.success + '08' },
  ungradedCard: { backgroundColor: Colors.warning + '08' },
  cardTouchable: { padding: Spacing.md },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  studentInfo: { flexDirection: 'row', gap: Spacing.md, flex: 1 },
  avatar: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
  avatarText: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  studentName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  submittedDate: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  statusArea: { alignItems: 'flex-end', gap: 4 },
  gradeBadge: { backgroundColor: Colors.success, paddingHorizontal: Spacing.md, paddingVertical: 4, borderRadius: BorderRadius.full },
  gradeText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.white },
  scoreText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  pendingBadge: { backgroundColor: Colors.warning + '20', paddingHorizontal: Spacing.md, paddingVertical: 4, borderRadius: BorderRadius.full },
  pendingText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.warning },
  absentBadge: { backgroundColor: Colors.danger + '20', paddingHorizontal: Spacing.md, paddingVertical: 4, borderRadius: BorderRadius.full },
  absentText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.danger },
  progressBar: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  progressBg: { flex: 1, height: 6, backgroundColor: Colors.neutral[100], borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: 3 },
  percentText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, minWidth: 32 },
  emptyText: { fontSize: Typography.sizes.base, color: Colors.neutral[400], marginTop: Spacing.md, textAlign: 'center' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContainer: { height: '85%', backgroundColor: Colors.background, borderTopLeftRadius: BorderRadius.xl, borderTopRightRadius: BorderRadius.xl, overflow: 'hidden' },
  modalContent: { flex: 1, padding: Spacing.base },
  aiGradingCard: { padding: Spacing.lg, marginBottom: Spacing.lg },
  cardTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.md },
  cardDescription: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginBottom: Spacing.lg, lineHeight: 20 },
  aiGradeBtn: { marginBottom: Spacing.md },
  aiResultCard: { padding: Spacing.md, marginTop: Spacing.md, backgroundColor: Colors.success + '10' },
  resultLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[700], marginBottom: Spacing.md },
  resultRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: Spacing.sm, borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  resultKey: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  resultValue: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  modalFooter: { flexDirection: 'row', gap: Spacing.sm, padding: Spacing.base, backgroundColor: Colors.white, borderTopWidth: 1, borderTopColor: Colors.border },
});
