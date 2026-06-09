import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, TextInput, ActivityIndicator, LayoutAnimation, Platform, UIManager,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import GradientPanel from '../../components/common/GradientPanel';
import ConceptImageStrip from '../../components/common/ConceptImageStrip';
import MasteryRing from '../../components/common/MasteryRing';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { PASS_THRESHOLD } from '../../constants';
import { useGenerateLesson, useGradeQuiz } from '../../hooks/useAiTutor';
import { TutorLanguage, TutorLesson } from '../../types';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

type Step = 'lesson' | 'quiz' | 'result';
const STEPS: { key: Step; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { key: 'lesson', label: 'Lesson', icon: 'book' },
  { key: 'quiz', label: 'Quiz', icon: 'help-circle' },
  { key: 'result', label: 'Result', icon: 'trophy' },
];

const DIFFICULTY_STYLE: Record<string, { color: string; bg: string }> = {
  Easy: { color: Colors.success, bg: '#dcfce7' },
  Medium: { color: Colors.warning, bg: '#fef3c7' },
  Hard: { color: Colors.danger, bg: '#fee2e2' },
};

const LANG_OPTIONS: { value: TutorLanguage; label: string }[] = [
  { value: 'english', label: 'EN' },
  { value: 'telugu', label: 'తె' },
  { value: 'both', label: 'EN + తె' },
];

function lessonSections(lesson: TutorLesson) {
  return [
    { key: 'real_life_examples', icon: 'earth' as const, title: 'Real-life examples', color: Colors.primary[600], items: lesson.real_life_examples },
    { key: 'worked_examples', icon: 'construct' as const, title: 'Worked examples', color: Colors.secondary[600], items: lesson.worked_examples },
    { key: 'common_mistakes', icon: 'warning' as const, title: 'Common mistakes', color: Colors.warning, items: lesson.common_mistakes },
    { key: 'revision_notes', icon: 'bookmark' as const, title: 'Revision notes', color: Colors.success, items: lesson.revision_notes },
  ];
}

function expand() {
  LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
}

export default function TutorSessionScreen({ route, navigation }: any) {
  const insets = useSafeAreaInsets();
  const { subject, chapter, concept, mastery, language: initialLanguage } = route.params || {};

  const [step, setStep] = useState<Step>('lesson');
  const [language, setLanguage] = useState<TutorLanguage>(initialLanguage ?? 'english');
  const [openSection, setOpenSection] = useState<string | null>('real_life_examples');

  const [numQuestions, setNumQuestions] = useState(5);
  const [quizIndex, setQuizIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});

  const generateMutation = useGenerateLesson();
  const gradeMutation = useGradeQuiz();

  const handleGenerate = () => generateMutation.mutate({
    subject, chapter, concept, mastery,
    language: 'both',
    num_questions: numQuestions,
    question_types: ['MCQ', 'MSQ', 'Short Answer'],
  });

  const lesson = generateMutation.data?.lesson;
  const quiz = generateMutation.data?.quiz ?? [];
  const ragSources = generateMutation.data?.rag_sources ?? [];
  const currentQuestion = quiz[quizIndex];
  const grade = gradeMutation.data;

  const setAnswer = (value: string) => setAnswers((prev) => ({ ...prev, [quizIndex]: value }));
  const toggleMsqOption = (option: string) => {
    setAnswers((prev) => {
      const current = (prev[quizIndex] || '').split(', ').filter(Boolean);
      const next = current.includes(option) ? current.filter((o) => o !== option) : [...current, option];
      return { ...prev, [quizIndex]: next.join(', ') };
    });
  };

  const goToQuiz = () => setStep('quiz');
  const submitQuiz = () => {
    gradeMutation.mutate(
      { subject, chapter, concept, mastery, quiz, answers },
      { onSuccess: () => setStep('result') },
    );
  };
  const toggleSection = (key: string) => {
    expand();
    setOpenSection((prev) => (prev === key ? null : key));
  };

  const headerSubtitle = STEPS.find((s) => s.key === step)?.label ?? '';

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <Header title={concept ?? 'AI Tutor'} subtitle={headerSubtitle} onBack={() => navigation.goBack()} />

      <View style={styles.stepIndicatorRow}>
        {STEPS.map((s, i) => {
          const idx = STEPS.findIndex((x) => x.key === step);
          const state = i < idx ? 'done' : i === idx ? 'active' : 'pending';
          return (
            <React.Fragment key={s.key}>
              {i > 0 && <View style={[styles.stepLine, state !== 'pending' && styles.stepLineActive]} />}
              <View style={styles.stepDotWrap}>
                <View style={[styles.stepDot, state === 'active' && styles.stepDotActive, state === 'done' && styles.stepDotDone]}>
                  {state === 'done'
                    ? <Ionicons name="checkmark" size={14} color={Colors.white} />
                    : <Ionicons name={s.icon} size={14} color={state === 'active' ? Colors.white : Colors.neutral[400]} />}
                </View>
                <Text style={[styles.stepLabel, state !== 'pending' && styles.stepLabelActive]}>{s.label}</Text>
              </View>
            </React.Fragment>
          );
        })}
      </View>

      {/* ── Idle / configure session ─────────────────────────────────── */}
      {generateMutation.isIdle && (
        <ScrollView contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing['2xl'] }]} showsVerticalScrollIndicator={false}>
          <GradientPanel colors={[Colors.secondary[500], Colors.primary[600]]} style={styles.lessonHero} radius={BorderRadius.xl}>
            <View style={styles.lessonHeroBadge}>
              <Ionicons name="sparkles" size={13} color={Colors.white} />
              <Text style={styles.lessonHeroBadgeText}>{subject} · {chapter}</Text>
            </View>
            <Text style={styles.lessonHeroTitle}>{concept}</Text>
          </GradientPanel>

          <Card>
            <Text style={styles.configLabel}>How many quiz questions?</Text>
            <View style={styles.configChipRow}>
              {[5, 10, 15, 20].map((n) => (
                <TouchableOpacity key={n} onPress={() => setNumQuestions(n)} activeOpacity={0.7}
                  style={[styles.configChip, n === numQuestions && styles.configChipActive]}>
                  <Text style={[styles.configChipText, n === numQuestions && styles.configChipTextActive]}>{n}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.configHint}>
              Generation takes ~{numQuestions <= 5 ? '60' : numQuestions <= 10 ? '90' : '120'} seconds
            </Text>
          </Card>

          <Button title="Generate lesson & quiz →" onPress={handleGenerate} size="lg" fullWidth style={styles.ctaPrimary} />
        </ScrollView>
      )}

      {/* ── Generating state ─────────────────────────────────────────── */}
      {generateMutation.isPending && (
        <View style={styles.center}>
          <GradientPanel colors={[Colors.secondary[500], Colors.primary[600]]} style={styles.loadingOrb} radius={48}>
            <ActivityIndicator color={Colors.white} size="large" />
          </GradientPanel>
          <Text style={styles.loadingTitle}>Crafting your personalised lesson…</Text>
          <Text style={styles.loadingSub}>Reading your textbook, checking your mastery on “{concept}”, and building an adaptive quiz just for you.</Text>
        </View>
      )}

      {generateMutation.isError && (
        <View style={styles.center}>
          <Ionicons name="cloud-offline-outline" size={56} color={Colors.danger} />
          <Text style={styles.loadingTitle}>Couldn't generate your lesson</Text>
          <Text style={styles.loadingSub}>The AI Tutor service may not be reachable yet. Please try again in a moment.</Text>
          <Button title="Retry" onPress={handleGenerate} style={styles.retryBtn} />
        </View>
      )}

      {/* ── Lesson step ──────────────────────────────────────────────── */}
      {step === 'lesson' && lesson && (
        <ScrollView contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing['2xl'] }]} showsVerticalScrollIndicator={false}>
          <GradientPanel colors={[Colors.secondary[500], Colors.primary[600]]} style={styles.lessonHero} radius={BorderRadius.xl}>
            <View style={styles.lessonHeroBadge}>
              <Ionicons name="sparkles" size={13} color={Colors.white} />
              <Text style={styles.lessonHeroBadgeText}>{subject} · {chapter}</Text>
            </View>
            <Text style={styles.lessonHeroTitle}>{lesson.concept}</Text>
            {ragSources.length > 0 && (
              <View style={styles.groundedChip}>
                <Ionicons name="document-text" size={13} color={Colors.white} />
                <Text style={styles.groundedChipText} numberOfLines={1}>
                  Grounded in {ragSources[0].kind === 'pdf' ? 'your uploaded PDF' : 'your study notes'} · {ragSources.length} source{ragSources.length > 1 ? 's' : ''}
                </Text>
              </View>
            )}
          </GradientPanel>

          <View style={styles.langRow}>
            {LANG_OPTIONS.map((l) => {
              const active = l.value === language;
              return (
                <TouchableOpacity key={l.value} onPress={() => setLanguage(l.value)} activeOpacity={0.85}
                  style={[styles.langPill, active && styles.langPillActive]}>
                  <Text style={[styles.langPillText, active && styles.langPillTextActive]}>{l.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <ConceptImageStrip images={generateMutation.data?.images} />

          <Card>
            {(language === 'english' || language === 'both') && (
              <Text style={styles.explanationText}>{lesson.english_explanation}</Text>
            )}
            {language === 'both' && lesson.telugu_explanation ? <View style={styles.explanationDivider} /> : null}
            {(language === 'telugu' || language === 'both') && (
              <Text style={styles.explanationText}>{lesson.telugu_explanation}</Text>
            )}
          </Card>

          {lessonSections(lesson).filter((s) => s.items?.length).map((section) => {
            const open = openSection === section.key;
            return (
              <Card key={section.key} padding="none" style={styles.sectionCard}>
                <TouchableOpacity style={styles.sectionHeader} activeOpacity={0.7} onPress={() => toggleSection(section.key)}>
                  <View style={[styles.sectionIconWrap, { backgroundColor: `${section.color}16` }]}>
                    <Ionicons name={section.icon} size={18} color={section.color} />
                  </View>
                  <Text style={styles.sectionTitle}>{section.title}</Text>
                  <Text style={styles.sectionCount}>{section.items.length}</Text>
                  <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={18} color={Colors.neutral[400]} />
                </TouchableOpacity>
                {open && (
                  <View style={styles.sectionBody}>
                    {section.items.map((item, i) => (
                      <View key={i} style={styles.sectionItemRow}>
                        <View style={[styles.sectionBullet, { backgroundColor: section.color }]} />
                        <Text style={styles.sectionItemText}>{item}</Text>
                      </View>
                    ))}
                  </View>
                )}
              </Card>
            );
          })}

          <Button title="Start adaptive quiz →" onPress={goToQuiz} size="lg" fullWidth style={styles.ctaPrimary} />
        </ScrollView>
      )}

      {/* ── Quiz step ────────────────────────────────────────────────── */}
      {step === 'quiz' && currentQuestion && (
        <View style={styles.flex}>
          <View style={styles.progressContainer}>
            <View style={styles.progressBg}>
              <View style={[styles.progressFill, { width: `${((quizIndex + 1) / quiz.length) * 100}%` }]} />
            </View>
            <Text style={styles.progressLabel}>Question {quizIndex + 1} of {quiz.length}</Text>
          </View>

          <ScrollView contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing['2xl'] }]} showsVerticalScrollIndicator={false}>
            <View style={styles.quizMetaRow}>
              <View style={[styles.difficultyChip, { backgroundColor: DIFFICULTY_STYLE[currentQuestion.difficulty]?.bg ?? Colors.neutral[100] }]}>
                <Text style={[styles.difficultyChipText, { color: DIFFICULTY_STYLE[currentQuestion.difficulty]?.color ?? Colors.neutral[600] }]}>
                  {currentQuestion.difficulty}
                </Text>
              </View>
              <View style={styles.typeChip}>
                <Text style={styles.typeChipText}>{currentQuestion.type}</Text>
              </View>
            </View>

            <Card>
              <Text style={styles.questionText}>{currentQuestion.question}</Text>
            </Card>

            {(currentQuestion.type === 'MCQ' || currentQuestion.type === 'MSQ') && (
              <View style={styles.optionsBlock}>
                {currentQuestion.options.map((opt) => {
                  const selected = currentQuestion.type === 'MCQ'
                    ? answers[quizIndex] === opt
                    : (answers[quizIndex] || '').split(', ').includes(opt);
                  const onPress = () => (currentQuestion.type === 'MCQ' ? setAnswer(opt) : toggleMsqOption(opt));
                  return (
                    <TouchableOpacity key={opt} onPress={onPress} activeOpacity={0.7}
                      style={[styles.optionRow, selected && styles.optionRowActive]}>
                      <View style={[
                        currentQuestion.type === 'MCQ' ? styles.radio : styles.checkbox,
                        selected && (currentQuestion.type === 'MCQ' ? styles.radioActive : styles.checkboxActive),
                      ]}>
                        {selected && (currentQuestion.type === 'MCQ'
                          ? <View style={styles.radioDot} />
                          : <Ionicons name="checkmark" size={14} color={Colors.white} />)}
                      </View>
                      <Text style={[styles.optionText, selected && styles.optionTextActive]}>{opt}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}

            {(currentQuestion.type === 'Short Answer' || currentQuestion.type === 'Long Answer') && (
              <TextInput
                style={[styles.answerInput, currentQuestion.type === 'Long Answer' && styles.answerInputLong]}
                placeholder={currentQuestion.type === 'Long Answer' ? 'Write a detailed answer…' : 'Type your answer…'}
                placeholderTextColor={Colors.neutral[400]}
                multiline={currentQuestion.type === 'Long Answer'}
                value={answers[quizIndex] || ''}
                onChangeText={setAnswer}
                textAlignVertical="top"
              />
            )}

            <View style={styles.navRow}>
              <Button title="← Previous" variant="outline" onPress={() => setQuizIndex((i) => Math.max(0, i - 1))} disabled={quizIndex === 0} style={styles.navBtn} />
              {quizIndex < quiz.length - 1 ? (
                <Button title="Next →" onPress={() => setQuizIndex((i) => Math.min(quiz.length - 1, i + 1))} style={styles.navBtn} />
              ) : (
                <Button title={gradeMutation.isPending ? 'Grading…' : 'Submit quiz'} onPress={submitQuiz} loading={gradeMutation.isPending} style={styles.submitBtn} />
              )}
            </View>

            <View style={styles.dotsRow}>
              {quiz.map((_, i) => (
                <TouchableOpacity key={i} onPress={() => setQuizIndex(i)} style={[
                  styles.qDot,
                  i === quizIndex && styles.qDotActive,
                  !!answers[i] && i !== quizIndex && styles.qDotAnswered,
                ]} />
              ))}
            </View>
          </ScrollView>
        </View>
      )}

      {/* ── Result step ──────────────────────────────────────────────── */}
      {step === 'result' && grade && (
        <ScrollView contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing['2xl'] }]} showsVerticalScrollIndicator={false}>
          <View style={styles.resultHeader}>
            <MasteryRing value={grade.percentage} size={140} strokeWidth={12} label="score" sublabel={`${grade.correct}/${grade.scored} correct`} gradientId="resultRing" trackColor={Colors.neutral[200]} />
            <Text style={styles.resultMessage}>{grade.message}</Text>
          </View>

          <Card style={styles.masteryShiftCard}>
            <Text style={styles.masteryShiftLabel}>Mastery on “{concept}”</Text>
            <View style={styles.masteryShiftRow}>
              <Text style={styles.masteryShiftValue}>{Math.round(grade.old_mastery)}</Text>
              <Ionicons name="arrow-forward" size={18} color={Colors.neutral[400]} />
              <Text style={[styles.masteryShiftValue, styles.masteryShiftValueNew]}>{Math.round(grade.new_mastery)}</Text>
              <View style={[styles.masteryDelta, { backgroundColor: grade.new_mastery >= grade.old_mastery ? '#dcfce7' : '#fee2e2' }]}>
                <Text style={[styles.masteryDeltaText, { color: grade.new_mastery >= grade.old_mastery ? Colors.success : Colors.danger }]}>
                  {grade.new_mastery >= grade.old_mastery ? '+' : ''}{Math.round(grade.new_mastery - grade.old_mastery)}
                </Text>
              </View>
            </View>
            <View style={styles.masteryTrack}>
              <View style={[styles.masteryTrackFill, { width: `${Math.min(100, Math.max(0, grade.new_mastery))}%` }]} />
              <View style={[styles.masteryTrackMarker, { left: `${Math.min(100, Math.max(0, grade.old_mastery))}%` }]} />
            </View>
          </Card>

          {grade.passed ? (
            <GradientPanel colors={[Colors.secondary[500], Colors.primary[600]]} style={styles.celebrationCard} radius={BorderRadius.xl}>
              <Ionicons name="rocket" size={28} color={Colors.white} />
              <Text style={styles.celebrationTitle}>You've cleared the {PASS_THRESHOLD}% pass mark! 🎉</Text>
              {grade.next_concept && (
                <Text style={styles.celebrationSub}>Ready to advance to <Text style={styles.celebrationBold}>{grade.next_concept}</Text></Text>
              )}
              {grade.next_concept && (
                <Button title={`Continue to "${grade.next_concept}" →`} variant="ghost"
                  onPress={() => navigation.replace('TutorSession', { subject, chapter, concept: grade.next_concept, mastery: grade.new_mastery, language })}
                  style={styles.celebrationBtn} textStyle={{ color: Colors.primary[700] }} />
              )}
            </GradientPanel>
          ) : (
            <Card style={styles.reviewCard}>
              <View style={styles.reviewHeader}>
                <Ionicons name="refresh-circle" size={24} color={Colors.warning} />
                <Text style={styles.reviewTitle}>A little more practice will help</Text>
              </View>
              <Text style={styles.reviewSub}>You're below the {PASS_THRESHOLD}% mark — here's what to revisit before trying again:</Text>
              <View style={styles.reviewChipRow}>
                {grade.review_topics.map((t) => (
                  <View key={t} style={styles.reviewChip}><Text style={styles.reviewChipText}>{t}</Text></View>
                ))}
              </View>
              <Button title="Try this quiz again" onPress={() => { setStep('lesson'); setQuizIndex(0); setAnswers({}); gradeMutation.reset(); }} style={styles.ctaPrimary} />
            </Card>
          )}

          <Text style={styles.breakdownTitle}>Question-by-question review</Text>
          {grade.results.map((r) => (
            <Card key={r.index} style={styles.breakdownCard}>
              <View style={styles.breakdownHeader}>
                <Ionicons name={r.is_correct ? 'checkmark-circle' : r.is_correct === false ? 'close-circle' : 'help-circle'}
                  size={20} color={r.is_correct ? Colors.success : r.is_correct === false ? Colors.danger : Colors.neutral[400]} />
                <Text style={styles.breakdownQuestion} numberOfLines={2}>{r.index + 1}. {r.question}</Text>
              </View>
              <Text style={styles.breakdownAnswer}>Correct answer: <Text style={styles.breakdownAnswerBold}>{r.correct_answer}</Text></Text>
              <Text style={styles.breakdownExplanation}>{r.explanation}</Text>
            </Card>
          ))}

          <Button title="Back to AI Tutor" variant="outline" onPress={() => navigation.popToTop()} size="lg" fullWidth style={styles.backHomeBtn} />
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, gap: Spacing.md },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: Spacing.xl, gap: Spacing.sm },

  stepIndicatorRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'center', paddingHorizontal: Spacing.xl, paddingVertical: Spacing.sm, backgroundColor: Colors.white, borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  stepDotWrap: { alignItems: 'center', gap: 4, width: 64 },
  stepDot: { width: 28, height: 28, borderRadius: 14, backgroundColor: Colors.neutral[100], justifyContent: 'center', alignItems: 'center' },
  stepDotActive: { backgroundColor: Colors.secondary[600] },
  stepDotDone: { backgroundColor: Colors.success },
  stepLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontWeight: Typography.weights.medium },
  stepLabelActive: { color: Colors.neutral[700], fontWeight: Typography.weights.semibold },
  stepLine: { height: 2, backgroundColor: Colors.neutral[100], flex: 1, marginTop: 14, maxWidth: 40 },
  stepLineActive: { backgroundColor: Colors.secondary[600] },

  loadingOrb: { width: 96, height: 96, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.sm },
  loadingTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], textAlign: 'center' },
  loadingSub: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], textAlign: 'center', lineHeight: 20, maxWidth: 320 },
  retryBtn: { marginTop: Spacing.sm, paddingHorizontal: Spacing.xl },

  lessonHero: { padding: Spacing.lg, gap: Spacing.sm },
  lessonHeroBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', backgroundColor: 'rgba(255,255,255,0.18)', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 3 },
  lessonHeroBadgeText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },
  lessonHeroTitle: { color: Colors.white, fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold },
  groundedChip: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start', backgroundColor: 'rgba(255,255,255,0.16)', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 5, maxWidth: '100%' },
  groundedChipText: { color: 'rgba(255,255,255,0.92)', fontSize: Typography.sizes.xs, fontWeight: Typography.weights.medium, flexShrink: 1 },

  langRow: { flexDirection: 'row', gap: Spacing.sm },
  langPill: { flex: 1, alignItems: 'center', backgroundColor: Colors.white, borderRadius: BorderRadius.lg, paddingVertical: Spacing.sm - 2, borderWidth: 1.5, borderColor: Colors.border },
  langPillActive: { backgroundColor: Colors.primary[600], borderColor: Colors.primary[600] },
  langPillText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  langPillTextActive: { color: Colors.white },

  explanationText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 22 },
  explanationDivider: { height: 1, backgroundColor: Colors.neutral[100], marginVertical: Spacing.sm },

  sectionCard: { overflow: 'hidden' },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, padding: Spacing.base },
  sectionIconWrap: { width: 36, height: 36, borderRadius: BorderRadius.md, justifyContent: 'center', alignItems: 'center' },
  sectionTitle: { flex: 1, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[800] },
  sectionCount: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontWeight: Typography.weights.medium },
  sectionBody: { paddingHorizontal: Spacing.base, paddingBottom: Spacing.base, gap: Spacing.sm },
  sectionItemRow: { flexDirection: 'row', gap: Spacing.sm, alignItems: 'flex-start' },
  sectionBullet: { width: 6, height: 6, borderRadius: 3, marginTop: 7 },
  sectionItemText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20 },

  ctaPrimary: { backgroundColor: Colors.secondary[600] },

  progressContainer: { paddingHorizontal: Spacing.base, paddingTop: Spacing.sm, paddingBottom: Spacing.xs, backgroundColor: Colors.white },
  progressBg: { height: 6, backgroundColor: Colors.neutral[100], borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: Colors.secondary[600], borderRadius: 3 },
  progressLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 6, fontWeight: Typography.weights.medium },

  quizMetaRow: { flexDirection: 'row', gap: Spacing.sm },
  difficultyChip: { borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 4 },
  difficultyChipText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  typeChip: { borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 4, backgroundColor: Colors.neutral[100] },
  typeChipText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },

  questionText: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.semibold, color: Colors.neutral[900], lineHeight: 24 },

  optionsBlock: { gap: Spacing.sm },
  optionRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, backgroundColor: Colors.white, borderRadius: BorderRadius.lg, padding: Spacing.sm + 2, borderWidth: 1.5, borderColor: Colors.border },
  optionRowActive: { borderColor: Colors.secondary[600], backgroundColor: `${Colors.secondary[600]}0c` },
  radio: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: Colors.neutral[300], justifyContent: 'center', alignItems: 'center' },
  radioActive: { borderColor: Colors.secondary[600] },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: Colors.secondary[600] },
  checkbox: { width: 20, height: 20, borderRadius: 5, borderWidth: 2, borderColor: Colors.neutral[300], justifyContent: 'center', alignItems: 'center' },
  checkboxActive: { borderColor: Colors.secondary[600], backgroundColor: Colors.secondary[600] },
  optionText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[700] },
  optionTextActive: { color: Colors.neutral[900], fontWeight: Typography.weights.semibold },

  answerInput: { backgroundColor: Colors.white, borderRadius: BorderRadius.lg, borderWidth: 1.5, borderColor: Colors.border, padding: Spacing.md, fontSize: Typography.sizes.sm, color: Colors.neutral[800], minHeight: 52 },
  answerInputLong: { minHeight: 140 },

  navRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.xs },
  navBtn: { flex: 1 },
  submitBtn: { flex: 1, backgroundColor: Colors.secondary[600] },
  dotsRow: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginTop: Spacing.sm },
  qDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: Colors.neutral[200] },
  qDotActive: { backgroundColor: Colors.secondary[600], width: 22 },
  qDotAnswered: { backgroundColor: Colors.primary[400] },

  resultHeader: { alignItems: 'center', gap: Spacing.md, paddingVertical: Spacing.sm },
  resultMessage: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.semibold, color: Colors.neutral[800], textAlign: 'center', maxWidth: 320 },

  masteryShiftCard: { gap: Spacing.sm },
  masteryShiftLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], fontWeight: Typography.weights.medium },
  masteryShiftRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  masteryShiftValue: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[400] },
  masteryShiftValueNew: { color: Colors.neutral[900] },
  masteryDelta: { borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 3, marginLeft: 'auto' },
  masteryDeltaText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  masteryTrack: { height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'visible' },
  masteryTrackFill: { height: '100%', backgroundColor: Colors.secondary[600], borderRadius: 4 },
  masteryTrackMarker: { position: 'absolute', top: -3, width: 2, height: 14, backgroundColor: Colors.neutral[400] },

  celebrationCard: { padding: Spacing.lg, gap: Spacing.xs, alignItems: 'flex-start' },
  celebrationTitle: { color: Colors.white, fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold },
  celebrationSub: { color: 'rgba(255,255,255,0.9)', fontSize: Typography.sizes.sm },
  celebrationBold: { fontWeight: Typography.weights.bold, color: Colors.white },
  celebrationBtn: { backgroundColor: Colors.white, marginTop: Spacing.xs, alignSelf: 'flex-start' },

  reviewCard: { gap: Spacing.sm },
  reviewHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  reviewTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  reviewSub: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], lineHeight: 20 },
  reviewChipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs },
  reviewChip: { backgroundColor: '#fef3c7', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 4 },
  reviewChipText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: '#92400e' },

  breakdownTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginTop: Spacing.xs },
  breakdownCard: { gap: Spacing.xs },
  breakdownHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm },
  breakdownQuestion: { flex: 1, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[800], lineHeight: 20 },
  breakdownAnswer: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  breakdownAnswerBold: { fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  breakdownExplanation: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], lineHeight: 18 },

  backHomeBtn: { marginTop: Spacing.sm },

  configLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.sm },
  configChipRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.sm },
  configChip: { flex: 1, alignItems: 'center', backgroundColor: Colors.neutral[100], borderRadius: BorderRadius.lg, paddingVertical: Spacing.sm + 2, borderWidth: 1.5, borderColor: Colors.border },
  configChipActive: { backgroundColor: Colors.secondary[600], borderColor: Colors.secondary[600] },
  configChipText: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[500] },
  configChipTextActive: { color: Colors.white },
  configHint: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
});
