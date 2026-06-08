import React, { useState, useRef } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  TextInput, Modal, ActivityIndicator, Animated,
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
import { useAuthStore } from '../../store/authStore';

interface Question {
  question_id: string;
  question_text: string;
  marks: number;
  question_type: string;
}

interface StudentAnswer {
  question_id: string;
  answer_text: string;
}

export default function StudentAssessmentScreen({ route, navigation }: any) {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const { assessmentId } = route.params || {};

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<StudentAnswer[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // Fetch questions for this assessment
  const { data: questionsData, isLoading } = useQuery({
    queryKey: ['assessment', assessmentId, 'questions'],
    queryFn: async () => {
      const res = await api.get(`/assessments/${assessmentId}/questions`);
      return res.data;
    },
    enabled: !!assessmentId,
  });

  // Submit assessment mutation
  const { mutate: submitAssessment, isPending: isSubmitting } = useMutation({
    mutationFn: async (answersData: StudentAnswer[]) => {
      const res = await api.post(`/assessments/${assessmentId}/student-submission`, answersData);
      return res.data;
    },
    onSuccess: () => {
      setSubmitted(true);
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }).start();
    },
    onError: (error: any) => {
      alert(`Submission failed: ${error.response?.data?.detail || error.message}`);
    },
  });

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading assessment..." />;
  }

  const questions = questionsData?.questions || [];
  if (!questions.length) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Assessment" subtitle="No questions available" />
        <View style={styles.center}>
          <Ionicons name="alert-circle-outline" size={64} color={Colors.danger} />
          <Text style={styles.errorText}>Assessment has no questions yet.</Text>
          <Button
            title="Go Back"
            onPress={() => navigation.goBack()}
            style={styles.backBtn}
          />
        </View>
      </View>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = answers.find((a) => a.question_id === currentQuestion.question_id);
  const progressPercent = ((currentQuestionIndex + 1) / questions.length) * 100;
  const answeredCount = answers.length;

  const handleAnswerChange = (text: string) => {
    setAnswers((prev) => {
      const existing = prev.find((a) => a.question_id === currentQuestion.question_id);
      if (existing) {
        return prev.map((a) =>
          a.question_id === currentQuestion.question_id ? { ...a, answer_text: text } : a
        );
      }
      return [...prev, { question_id: currentQuestion.question_id, answer_text: text }];
    });
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleJumpToQuestion = (idx: number) => {
    setCurrentQuestionIndex(idx);
  };

  const handleSubmit = () => {
    if (answeredCount < questions.length) {
      alert(
        `You have answered ${answeredCount} of ${questions.length} questions. ` +
        `Unanswered questions will receive 0 marks. Continue?`
      );
    }
    setShowConfirmModal(true);
  };

  const confirmSubmit = () => {
    setShowConfirmModal(false);
    submitAssessment(answers);
  };

  if (submitted) {
    return (
      <Animated.View style={[styles.flex, { opacity: fadeAnim, paddingBottom: insets.bottom }]}>
        <Header title="Submitted!" subtitle="Your assessment has been recorded" />

        <View style={[styles.flex, styles.center, styles.successContainer]}>
          <Ionicons name="checkmark-circle" size={80} color={Colors.success} />
          <Text style={styles.successTitle}>Assessment Submitted Successfully!</Text>
          <Text style={styles.successText}>
            You answered <Text style={styles.boldText}>{answeredCount}</Text> of{' '}
            <Text style={styles.boldText}>{questions.length}</Text> questions
          </Text>

          <Card style={styles.summaryCard}>
            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{answeredCount}</Text>
                <Text style={styles.summaryLabel}>Answered</Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{questions.length - answeredCount}</Text>
                <Text style={styles.summaryLabel}>Unanswered</Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>
                  {questions.reduce((sum, q) => sum + q.marks, 0)}
                </Text>
                <Text style={styles.summaryLabel}>Total Marks</Text>
              </View>
            </View>
          </Card>

          <Text style={styles.feedbackText}>
            ✨ Your responses will be reviewed by your teacher and graded with AI assistance.
          </Text>
          <Text style={styles.feedbackSubText}>
            You'll receive detailed feedback within 24 hours.
          </Text>

          <Button
            title="Back to Assessments"
            onPress={() => navigation.navigate('Assessments')}
            size="lg"
            fullWidth
            style={styles.doneBtn}
          />
        </View>
      </Animated.View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title={`Question ${currentQuestionIndex + 1}/${questions.length}`}
        subtitle="Answer and review before submitting"
      />

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBg}>
          <View style={[styles.progressFill, { width: `${progressPercent}%` }]} />
        </View>
        <Text style={styles.progressText}>
          {answeredCount} answered • {questions.length - answeredCount} remaining
        </Text>
      </View>

      <ScrollView style={styles.contentArea} showsVerticalScrollIndicator={false}>
        {/* Current Question Card */}
        <Card style={styles.questionCard}>
          <View style={styles.questionHeader}>
            <View>
              <Text style={styles.questionNumber}>Question {currentQuestionIndex + 1}</Text>
              <Text style={styles.questionMarks}>{currentQuestion.marks} marks</Text>
            </View>
            {currentAnswer && (
              <View style={styles.answeredBadge}>
                <Ionicons name="checkmark-circle" size={20} color={Colors.success} />
                <Text style={styles.answeredLabel}>Answered</Text>
              </View>
            )}
          </View>

          <Text style={styles.questionType}>{currentQuestion.question_type}</Text>
          <Text style={styles.questionText}>{currentQuestion.question_text}</Text>

          {/* Answer Input */}
          <View style={styles.answerSection}>
            <Text style={styles.answerLabel}>Your Answer</Text>
            <TextInput
              style={styles.answerInput}
              placeholder="Type your answer here..."
              placeholderTextColor={Colors.neutral[300]}
              value={currentAnswer?.answer_text || ''}
              onChangeText={handleAnswerChange}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
            />
            <Text style={styles.charCount}>
              {(currentAnswer?.answer_text || '').length} characters
            </Text>
          </View>

          {/* Question Navigator */}
          <View style={styles.questionNav}>
            <Text style={styles.navLabel}>Navigate</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.questionGrid}
              contentContainerStyle={styles.questionGridContent}
            >
              {questions.map((q, idx) => {
                const isAnswered = answers.some((a) => a.question_id === q.question_id);
                const isActive = idx === currentQuestionIndex;
                return (
                  <TouchableOpacity
                    key={idx}
                    style={[
                      styles.navBtn,
                      isActive && styles.navBtnActive,
                      isAnswered && !isActive && styles.navBtnAnswered,
                    ]}
                    onPress={() => handleJumpToQuestion(idx)}
                  >
                    <Text
                      style={[
                        styles.navBtnText,
                        isActive && styles.navBtnTextActive,
                        isAnswered && !isActive && styles.navBtnTextAnswered,
                      ]}
                    >
                      {idx + 1}
                    </Text>
                    {isAnswered && !isActive && (
                      <Ionicons name="checkmark-circle" size={12} color={Colors.success} style={styles.navCheckmark} />
                    )}
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        </Card>
      </ScrollView>

      {/* Navigation & Submit */}
      <View style={styles.bottomBar}>
        <Button
          title="← Previous"
          onPress={handlePrevQuestion}
          variant="outline"
          disabled={currentQuestionIndex === 0}
          style={styles.bottomBarBtn}
        />
        {currentQuestionIndex < questions.length - 1 ? (
          <Button
            title="Next →"
            onPress={handleNextQuestion}
            style={styles.bottomBarBtn}
          />
        ) : (
          <Button
            title="Submit ✓"
            onPress={handleSubmit}
            variant="danger"
            style={styles.bottomBarBtn}
          />
        )}
      </View>

      {/* Confirm Submit Modal */}
      <Modal visible={showConfirmModal} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <Card style={styles.confirmModal}>
            <Ionicons name="alert-circle-outline" size={48} color={Colors.warning} style={styles.modalIcon} />
            <Text style={styles.confirmTitle}>Submit Assessment?</Text>
            <Text style={styles.confirmMessage}>
              You have answered <Text style={{ fontWeight: 'bold' }}>{answeredCount}</Text> of{' '}
              <Text style={{ fontWeight: 'bold' }}>{questions.length}</Text> questions.
            </Text>
            <Text style={styles.confirmWarning}>
              Once submitted, you cannot make changes. Unanswered questions will receive 0 marks.
            </Text>

            <View style={styles.modalButtons}>
              <Button
                title="Cancel"
                onPress={() => setShowConfirmModal(false)}
                variant="outline"
                fullWidth
              />
              <Button
                title="Submit"
                onPress={confirmSubmit}
                loading={isSubmitting}
                variant="danger"
                fullWidth
              />
            </View>
          </Card>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  center: { justifyContent: 'center', alignItems: 'center' },
  errorText: { marginTop: Spacing.md, fontSize: Typography.sizes.base, color: Colors.danger },
  backBtn: { marginTop: Spacing.md },
  progressContainer: { paddingHorizontal: Spacing.base, paddingVertical: Spacing.md, backgroundColor: Colors.white },
  progressBg: { height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden', marginBottom: Spacing.sm },
  progressFill: { height: '100%', backgroundColor: Colors.primary[600], borderRadius: 4 },
  progressText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  contentArea: { flex: 1, padding: Spacing.base },
  questionCard: { padding: Spacing.lg, marginBottom: Spacing.xl },
  questionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: Spacing.md, paddingBottom: Spacing.md, borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  questionNumber: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  questionMarks: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.primary[600], marginTop: 4 },
  answeredBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.success + '20', paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  answeredLabel: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.success },
  questionType: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginBottom: Spacing.md },
  questionText: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900], lineHeight: 24, marginBottom: Spacing.lg },
  answerSection: { marginBottom: Spacing.xl },
  answerLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.sm },
  answerInput: { borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, padding: Spacing.md, fontSize: Typography.sizes.base, color: Colors.neutral[900], minHeight: 140, backgroundColor: Colors.neutral[50] },
  charCount: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 4 },
  questionNav: { marginTop: Spacing.lg },
  navLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.sm },
  questionGrid: { marginHorizontal: -Spacing.sm },
  questionGridContent: { paddingHorizontal: Spacing.sm, gap: Spacing.xs },
  navBtn: { width: 44, height: 44, borderRadius: 22, borderWidth: 1.5, borderColor: Colors.border, justifyContent: 'center', alignItems: 'center' },
  navBtnActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[600] },
  navBtnAnswered: { borderColor: Colors.success, backgroundColor: Colors.success + '10' },
  navBtnText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[600] },
  navBtnTextActive: { color: Colors.white },
  navBtnTextAnswered: { color: Colors.success },
  navCheckmark: { position: 'absolute', bottom: -2, right: -2 },
  bottomBar: { flexDirection: 'row', gap: Spacing.sm, padding: Spacing.base, backgroundColor: Colors.white, borderTopWidth: 1, borderTopColor: Colors.border },
  bottomBarBtn: { flex: 1 },
  successContainer: { padding: Spacing['2xl'] },
  successTitle: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: Spacing.md },
  successText: { fontSize: Typography.sizes.base, color: Colors.neutral[600], marginTop: Spacing.sm },
  boldText: { fontWeight: 'bold' },
  summaryCard: { marginVertical: Spacing.lg, padding: Spacing.lg },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-around' },
  summaryItem: { alignItems: 'center' },
  summaryValue: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  summaryLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[600], marginTop: 4 },
  feedbackText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], textAlign: 'center', marginTop: Spacing.lg },
  feedbackSubText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], textAlign: 'center', marginTop: 4 },
  doneBtn: { marginTop: Spacing.lg },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: Spacing.lg },
  confirmModal: { padding: Spacing.lg, marginHorizontal: Spacing.lg },
  modalIcon: { alignSelf: 'center', marginBottom: Spacing.md },
  confirmTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.sm },
  confirmMessage: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginBottom: Spacing.md },
  confirmWarning: { fontSize: Typography.sizes.xs, color: Colors.danger, marginBottom: Spacing.lg },
  modalButtons: { gap: Spacing.md },
});
