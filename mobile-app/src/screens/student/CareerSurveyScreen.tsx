import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Animated } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { useCareerSurvey, useSubmitCareerSurvey } from '../../hooks/useCareer';
import { CareerSurveyResponse } from '../../types';

export default function CareerSurveyScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const { data, isLoading } = useCareerSurvey();
  const { mutate: submitSurvey, isPending: isSubmitting } = useSubmitCareerSurvey();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<CareerSurveyResponse[]>([]);
  const [submitted, setSubmitted] = useState(false);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading survey..." />;
  }

  const questions = data?.questions || [];
  if (!questions.length) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Career Survey" subtitle="No questions available" />
        <View style={styles.center}>
          <Ionicons name="alert-circle-outline" size={64} color={Colors.danger} />
          <Text style={styles.errorText}>The survey isn't available right now.</Text>
          <Button title="Go Back" onPress={() => navigation.goBack()} style={styles.backBtn} />
        </View>
      </View>
    );
  }

  const currentQuestion = questions[currentIndex];
  const currentResponse = responses.find((r) => r.question_id === currentQuestion.question_id);
  const answeredCount = responses.length;
  const progressPercent = ((currentIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentIndex === questions.length - 1;

  const selectOption = (option: string) => {
    setResponses((prev) => {
      const existing = prev.find((r) => r.question_id === currentQuestion.question_id);
      if (existing) {
        return prev.map((r) => (r.question_id === currentQuestion.question_id ? { ...r, answer: option } : r));
      }
      return [...prev, { question_id: currentQuestion.question_id, answer: option }];
    });

    // Auto-advance to keep the wizard moving — feels lighter for a short survey
    if (currentIndex < questions.length - 1) {
      setTimeout(() => setCurrentIndex((idx) => idx + 1), 220);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) setCurrentIndex(currentIndex + 1);
  };

  const handleSubmit = () => {
    submitSurvey(responses, {
      onSuccess: () => {
        setSubmitted(true);
        Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
      },
      onError: (error: any) => {
        alert(`Could not save your answers: ${error.response?.data?.detail || error.message}`);
      },
    });
  };

  if (submitted) {
    return (
      <Animated.View style={[styles.flex, { opacity: fadeAnim, paddingBottom: insets.bottom }]}>
        <Header title="All set!" subtitle="Your survey has been saved" />
        <View style={[styles.flex, styles.center, styles.successContainer]}>
          <Ionicons name="checkmark-circle" size={80} color={Colors.success} />
          <Text style={styles.successTitle}>Survey Completed!</Text>
          <Text style={styles.successText}>
            Thanks for sharing your interests — we'll combine this with your academic record to
            build your personalised career profile.
          </Text>
          <Button
            title="See My Recommendations"
            onPress={() => navigation.navigate('CareerHome')}
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
        title={`Question ${currentIndex + 1}/${questions.length}`}
        subtitle="Pick the option that feels most like you"
      />

      <View style={styles.progressContainer}>
        <View style={styles.progressBg}>
          <View style={[styles.progressFill, { width: `${progressPercent}%` }]} />
        </View>
        <Text style={styles.progressText}>
          {answeredCount} answered • {questions.length - answeredCount} remaining
        </Text>
      </View>

      <ScrollView style={styles.contentArea} showsVerticalScrollIndicator={false}>
        <Card style={styles.questionCard}>
          <Text style={styles.questionNumber}>Question {currentIndex + 1}</Text>
          <Text style={styles.questionText}>{currentQuestion.question_text}</Text>

          <View style={styles.optionsList}>
            {currentQuestion.options.map((option: string, idx: number) => {
              const isSelected = currentResponse?.answer === option;
              return (
                <TouchableOpacity
                  key={idx}
                  activeOpacity={0.75}
                  style={[styles.optionChip, isSelected && styles.optionChipSelected]}
                  onPress={() => selectOption(option)}
                >
                  <View style={[styles.optionRadio, isSelected && styles.optionRadioSelected]}>
                    {isSelected && <Ionicons name="checkmark" size={12} color={Colors.white} />}
                  </View>
                  <Text style={[styles.optionText, isSelected && styles.optionTextSelected]}>{option}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </Card>
      </ScrollView>

      <View style={styles.bottomBar}>
        <Button
          title="← Previous"
          onPress={handlePrev}
          variant="outline"
          disabled={currentIndex === 0}
          style={styles.bottomBarBtn}
        />
        {!isLastQuestion ? (
          <Button
            title="Next →"
            onPress={handleNext}
            disabled={!currentResponse}
            style={styles.bottomBarBtn}
          />
        ) : (
          <Button
            title="Submit ✓"
            onPress={handleSubmit}
            loading={isSubmitting}
            disabled={answeredCount < questions.length}
            style={styles.bottomBarBtn}
          />
        )}
      </View>
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
  progressFill: { height: '100%', backgroundColor: Colors.secondary[600], borderRadius: 4 },
  progressText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  contentArea: { flex: 1, padding: Spacing.base },
  questionCard: { padding: Spacing.lg, marginBottom: Spacing.xl },
  questionNumber: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[600], marginBottom: Spacing.xs },
  questionText: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900], lineHeight: 26, marginBottom: Spacing.lg },
  optionsList: { gap: Spacing.sm },
  optionChip: {
    flexDirection: 'row', alignItems: 'center', gap: Spacing.md,
    borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg,
    padding: Spacing.md, backgroundColor: Colors.neutral[50],
  },
  optionChipSelected: { borderColor: Colors.secondary[600], backgroundColor: Colors.secondary[600] + '0F' },
  optionRadio: {
    width: 22, height: 22, borderRadius: 11, borderWidth: 1.5, borderColor: Colors.neutral[300],
    justifyContent: 'center', alignItems: 'center',
  },
  optionRadioSelected: { borderColor: Colors.secondary[600], backgroundColor: Colors.secondary[600] },
  optionText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },
  optionTextSelected: { color: Colors.neutral[900], fontWeight: Typography.weights.semibold },
  bottomBar: { flexDirection: 'row', gap: Spacing.sm, padding: Spacing.base, backgroundColor: Colors.white, borderTopWidth: 1, borderTopColor: Colors.border },
  bottomBarBtn: { flex: 1 },
  successContainer: { padding: Spacing['2xl'] },
  successTitle: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: Spacing.md },
  successText: { fontSize: Typography.sizes.base, color: Colors.neutral[600], marginTop: Spacing.sm, textAlign: 'center', lineHeight: 22 },
  doneBtn: { marginTop: Spacing.xl },
});
