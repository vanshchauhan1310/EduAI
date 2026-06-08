import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity,
  ActivityIndicator, Switch,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { useAuthStore } from '../../store/authStore';

interface Chapter {
  id: string;
  name: string;
  subject: string;
}

interface AssessmentFormData {
  title: string;
  assessment_type: string;
  subject: string;
  class_grade: number;
  section: string;
  academic_year: string;
  max_marks: number;
  passing_marks: number;
  duration_minutes: number;
  description: string;
  // AI Generation fields
  use_ai_generation: boolean;
  chapter_id: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  num_questions: number;
}

const ASSESSMENT_TYPES = ['FORMATIVE', 'SUMMATIVE', 'UNIT_TEST', 'FA1', 'FA2', 'FA3', 'FA4', 'SA1', 'SA2'];
const SUBJECTS = ['Mathematics', 'English', 'Science', 'Social Studies', 'Hindi'];
const CLASSES = [6, 7, 8, 9, 10];
const SECTIONS = ['A', 'B', 'C', 'D', 'E'];

export default function CreateAssessmentScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const [form, setForm] = useState<AssessmentFormData>({
    title: '',
    assessment_type: 'FORMATIVE',
    subject: 'Mathematics',
    class_grade: 7,
    section: 'A',
    academic_year: new Date().getFullYear().toString(),
    max_marks: 50,
    passing_marks: 17.5,
    duration_minutes: 45,
    description: '',
    use_ai_generation: true,
    chapter_id: '',
    difficulty: 'MEDIUM',
    num_questions: 5,
  });

  const [step, setStep] = useState<'basic' | 'questions' | 'publish'>('basic');
  const [showTypeDropdown, setShowTypeDropdown] = useState(false);
  const [showSubjectDropdown, setShowSubjectDropdown] = useState(false);
  const [showClassDropdown, setShowClassDropdown] = useState(false);
  const [generatedQuestions, setGeneratedQuestions] = useState<any[]>([]);
  const [creatingAssessment, setCreatingAssessment] = useState(false);
  const [generatingQuestions, setGeneratingQuestions] = useState(false);
  const [assessmentId, setAssessmentId] = useState<number | null>(null);
  const [publishing, setPublishing] = useState(false);

  // Mock chapters data - in production, fetch from backend
  const chapters: Chapter[] = [
    { id: 'ch1', name: 'Rational Numbers', subject: 'Mathematics' },
    { id: 'ch2', name: 'Linear Equations', subject: 'Mathematics' },
    { id: 'ch3', name: 'Polynomials', subject: 'Mathematics' },
  ];

  const handleCreateBasicAssessment = async () => {
    if (!form.title || !form.section) {
      alert('Please fill all required fields');
      return;
    }

    setCreatingAssessment(true);
    try {
      const response = await api.post('/assessments', {
        title: form.title,
        assessment_type: form.assessment_type,
        subject: form.subject,
        class_grade: form.class_grade,
        section: form.section,
        school_id: user?.school_id || 1,
        academic_year: form.academic_year,
        max_marks: form.max_marks,
        passing_marks: form.passing_marks,
        duration_minutes: form.duration_minutes,
        description: form.description,
      });

      setAssessmentId(response.data.id);

      if (form.use_ai_generation && form.chapter_id) {
        setStep('questions');
        await handleGenerateQuestions(response.data.id);
      } else {
        setStep('publish');
      }
    } catch (error: any) {
      alert(`Failed to create assessment: ${error.response?.data?.detail || error.message}`);
    } finally {
      setCreatingAssessment(false);
    }
  };

  const handleGenerateQuestions = async (assessmentId: number) => {
    setGeneratingQuestions(true);
    try {
      // AI question generation calls an LLM once per question — can take
      // well over the default client timeout, so allow more time here.
      const response = await api.post(`/assessments/${assessmentId}/generate-questions`, {
        chapter_id: form.chapter_id,
        subject: form.subject,
        class_grade: form.class_grade,
        difficulty: form.difficulty,
        num_questions: form.num_questions,
      }, { timeout: 120000 });

      setGeneratedQuestions(response.data.questions || []);
      alert(`✅ Generated ${response.data.questions_generated} questions!`);
    } catch (error: any) {
      alert(`Failed to generate questions: ${error.response?.data?.detail || error.message}`);
    } finally {
      setGeneratingQuestions(false);
    }
  };

  const handlePublishAssessment = async () => {
    if (!assessmentId) {
      alert('Cannot publish: assessment was not created.');
      return;
    }

    setPublishing(true);
    try {
      await api.post(`/assessments/${assessmentId}/publish`);
      alert('✅ Assessment published successfully!');
      navigation.navigate('AssessmentsList');
    } catch (error: any) {
      alert(`Failed to publish assessment: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPublishing(false);
    }
  };

  if (step === 'basic') {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Create Assessment" subtitle="Set up a new test or assignment" />

        <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
          {/* Basic Info Section */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📋 Assessment Details</Text>

            <View style={styles.field}>
              <Text style={styles.label}>Assessment Title *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., FA1 Mathematics"
                value={form.title}
                onChangeText={(text) => setForm({ ...form, title: text })}
              />
            </View>

            {/* Type Dropdown */}
            <View style={styles.field}>
              <Text style={styles.label}>Assessment Type</Text>
              <TouchableOpacity
                style={styles.dropdown}
                onPress={() => setShowTypeDropdown(!showTypeDropdown)}
              >
                <Text style={styles.dropdownValue}>{form.assessment_type}</Text>
                <Ionicons name={showTypeDropdown ? 'chevron-up' : 'chevron-down'} size={20} color={Colors.neutral[400]} />
              </TouchableOpacity>
              {showTypeDropdown && (
                <View style={styles.dropdownMenu}>
                  {ASSESSMENT_TYPES.map((type) => (
                    <TouchableOpacity
                      key={type}
                      style={styles.dropdownItem}
                      onPress={() => {
                        setForm({ ...form, assessment_type: type });
                        setShowTypeDropdown(false);
                      }}
                    >
                      <Text style={styles.dropdownItemText}>{type}</Text>
                      {form.assessment_type === type && (
                        <Ionicons name="checkmark" size={18} color={Colors.success} />
                      )}
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            {/* Subject Dropdown */}
            <View style={styles.field}>
              <Text style={styles.label}>Subject</Text>
              <TouchableOpacity
                style={styles.dropdown}
                onPress={() => setShowSubjectDropdown(!showSubjectDropdown)}
              >
                <Text style={styles.dropdownValue}>{form.subject}</Text>
                <Ionicons name={showSubjectDropdown ? 'chevron-up' : 'chevron-down'} size={20} color={Colors.neutral[400]} />
              </TouchableOpacity>
              {showSubjectDropdown && (
                <View style={styles.dropdownMenu}>
                  {SUBJECTS.map((subject) => (
                    <TouchableOpacity
                      key={subject}
                      style={styles.dropdownItem}
                      onPress={() => {
                        setForm({ ...form, subject });
                        setShowSubjectDropdown(false);
                      }}
                    >
                      <Text style={styles.dropdownItemText}>{subject}</Text>
                      {form.subject === subject && (
                        <Ionicons name="checkmark" size={18} color={Colors.success} />
                      )}
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            {/* Class & Section */}
            <View style={styles.row}>
              <View style={[styles.field, { flex: 1, marginRight: Spacing.sm }]}>
                <Text style={styles.label}>Class</Text>
                <TouchableOpacity
                  style={styles.dropdown}
                  onPress={() => setShowClassDropdown(!showClassDropdown)}
                >
                  <Text style={styles.dropdownValue}>Class {form.class_grade}</Text>
                  <Ionicons name={showClassDropdown ? 'chevron-up' : 'chevron-down'} size={20} color={Colors.neutral[400]} />
                </TouchableOpacity>
                {showClassDropdown && (
                  <View style={styles.dropdownMenu}>
                    {CLASSES.map((cls) => (
                      <TouchableOpacity
                        key={cls}
                        style={styles.dropdownItem}
                        onPress={() => {
                          setForm({ ...form, class_grade: cls });
                          setShowClassDropdown(false);
                        }}
                      >
                        <Text style={styles.dropdownItemText}>Class {cls}</Text>
                        {form.class_grade === cls && (
                          <Ionicons name="checkmark" size={18} color={Colors.success} />
                        )}
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </View>

              <View style={[styles.field, { flex: 1 }]}>
                <Text style={styles.label}>Section</Text>
                <View style={styles.pillRow}>
                  {SECTIONS.map((sec) => (
                    <TouchableOpacity
                      key={sec}
                      style={[
                        styles.pill,
                        form.section === sec && styles.pillActive,
                      ]}
                      onPress={() => setForm({ ...form, section: sec })}
                    >
                      <Text
                        style={[
                          styles.pillText,
                          form.section === sec && styles.pillTextActive,
                        ]}
                      >
                        {sec}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            </View>
          </View>

          {/* Marks & Duration */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>⏱️ Marks & Duration</Text>

            <View style={styles.row}>
              <View style={[styles.field, { flex: 1, marginRight: Spacing.sm }]}>
                <Text style={styles.label}>Max Marks</Text>
                <TextInput
                  style={styles.input}
                  placeholder="50"
                  keyboardType="numeric"
                  value={form.max_marks.toString()}
                  onChangeText={(text) => setForm({ ...form, max_marks: parseInt(text) || 0 })}
                />
              </View>

              <View style={[styles.field, { flex: 1 }]}>
                <Text style={styles.label}>Duration (min)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="45"
                  keyboardType="numeric"
                  value={form.duration_minutes.toString()}
                  onChangeText={(text) => setForm({ ...form, duration_minutes: parseInt(text) || 0 })}
                />
              </View>
            </View>
          </View>

          {/* AI Question Generation */}
          <View style={styles.section}>
            <View style={styles.aiToggleHeader}>
              <Text style={styles.sectionTitle}>✨ AI Question Generation</Text>
              <Switch
                value={form.use_ai_generation}
                onValueChange={(value) => setForm({ ...form, use_ai_generation: value })}
                trackColor={{ false: Colors.neutral[200], true: Colors.success + '40' }}
                thumbColor={form.use_ai_generation ? Colors.success : Colors.neutral[300]}
              />
            </View>

            {form.use_ai_generation && (
              <>
                <View style={styles.field}>
                  <Text style={styles.label}>Select Chapter</Text>
                  <View style={styles.chapterList}>
                    {chapters.map((chapter) => (
                      <TouchableOpacity
                        key={chapter.id}
                        style={[
                          styles.chapterCard,
                          form.chapter_id === chapter.id && styles.chapterCardActive,
                        ]}
                        onPress={() => setForm({ ...form, chapter_id: chapter.id })}
                      >
                        <Text
                          style={[
                            styles.chapterName,
                            form.chapter_id === chapter.id && styles.chapterNameActive,
                          ]}
                        >
                          {chapter.name}
                        </Text>
                        {form.chapter_id === chapter.id && (
                          <Ionicons name="checkmark-circle" size={18} color={Colors.success} />
                        )}
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>

                <View style={styles.row}>
                  <View style={[styles.field, { flex: 1, marginRight: Spacing.sm }]}>
                    <Text style={styles.label}>Difficulty</Text>
                    <View style={styles.difficultyRow}>
                      {(['EASY', 'MEDIUM', 'HARD'] as const).map((diff) => (
                        <TouchableOpacity
                          key={diff}
                          style={[
                            styles.diffBtn,
                            form.difficulty === diff && styles.diffBtnActive,
                          ]}
                          onPress={() => setForm({ ...form, difficulty: diff })}
                        >
                          <Text
                            style={[
                              styles.diffBtnText,
                              form.difficulty === diff && styles.diffBtnTextActive,
                            ]}
                          >
                            {diff}
                          </Text>
                        </TouchableOpacity>
                      ))}
                    </View>
                  </View>

                  <View style={[styles.field, { flex: 1 }]}>
                    <Text style={styles.label}>No. of Questions</Text>
                    <View style={styles.stepper}>
                      <TouchableOpacity
                        style={styles.stepperBtn}
                        onPress={() => setForm({ ...form, num_questions: Math.max(1, form.num_questions - 1) })}
                      >
                        <Ionicons name="remove" size={20} color={Colors.primary[600]} />
                      </TouchableOpacity>
                      <TextInput
                        style={styles.stepperInput}
                        keyboardType="numeric"
                        value={form.num_questions.toString()}
                        onChangeText={(text) => {
                          const val = parseInt(text);
                          setForm({ ...form, num_questions: isNaN(val) ? 1 : Math.max(1, Math.min(50, val)) });
                        }}
                      />
                      <TouchableOpacity
                        style={styles.stepperBtn}
                        onPress={() => setForm({ ...form, num_questions: Math.min(50, form.num_questions + 1) })}
                      >
                        <Ionicons name="add" size={20} color={Colors.primary[600]} />
                      </TouchableOpacity>
                    </View>
                  </View>
                </View>
              </>
            )}
          </View>

          {/* Description */}
          <View style={styles.section}>
            <View style={styles.field}>
              <Text style={styles.label}>Description (Optional)</Text>
              <TextInput
                style={[styles.input, styles.textarea]}
                placeholder="Add instructions or notes..."
                value={form.description}
                onChangeText={(text) => setForm({ ...form, description: text })}
                multiline
                numberOfLines={4}
              />
            </View>
          </View>

          <View style={styles.section}>
            <Button
              title={creatingAssessment ? 'Creating...' : 'Continue →'}
              onPress={handleCreateBasicAssessment}
              loading={creatingAssessment}
              fullWidth
              size="lg"
            />
          </View>
        </ScrollView>
      </View>
    );
  }

  if (step === 'questions') {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Generated Questions" subtitle={`${generatedQuestions.length} questions created`} />

        {generatingQuestions ? (
          <View style={[styles.flex, styles.center]}>
            <ActivityIndicator size={48} color={Colors.primary[600]} />
            <Text style={styles.loadingText}>Generating questions with AI...</Text>
          </View>
        ) : (
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.questionsList}>
            {generatedQuestions.length > 0 ? (
              generatedQuestions.map((q, idx) => (
                <Card key={idx} style={styles.questionCard}>
                  <View style={styles.questionHeader}>
                    <Text style={styles.questionNum}>Q{idx + 1}</Text>
                    <Text style={styles.questionMarks}>{q.marks || 2} marks</Text>
                  </View>
                  <Text style={styles.questionText}>{q.question_text}</Text>
                  <Text style={styles.sampleLabel}>Sample Answer:</Text>
                  <Text style={styles.sampleText}>{q.sample_answer}</Text>
                </Card>
              ))
            ) : (
              <View style={styles.center}>
                <Text style={styles.emptyText}>No questions generated yet</Text>
              </View>
            )}
          </ScrollView>
        )}

        <View style={styles.questionFooter}>
          <Button
            title="← Back"
            onPress={() => setStep('basic')}
            variant="outline"
            size="lg"
            style={styles.questionFooterBtn}
          />
          <Button
            title="Publish →"
            onPress={() => setStep('publish')}
            size="lg"
            style={styles.questionFooterBtn}
          />
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Publish Assessment" subtitle="Review and publish" />

      <ScrollView showsVerticalScrollIndicator={false} style={styles.scrollView}>
        <Card style={styles.summaryCard}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Assessment</Text>
            <Text style={styles.summaryValue}>{form.title}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Type</Text>
            <Text style={styles.summaryValue}>{form.assessment_type}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Class & Section</Text>
            <Text style={styles.summaryValue}>
              Class {form.class_grade} - {form.section}
            </Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Max Marks</Text>
            <Text style={styles.summaryValue}>{form.max_marks}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Duration</Text>
            <Text style={styles.summaryValue}>{form.duration_minutes} minutes</Text>
          </View>
          {form.use_ai_generation && generatedQuestions.length > 0 && (
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Questions</Text>
              <Text style={styles.summaryValue}>{generatedQuestions.length} AI-generated</Text>
            </View>
          )}
        </Card>

        <View style={styles.section}>
          <Button
            title={publishing ? 'Publishing...' : 'Publish & Make Live'}
            onPress={handlePublishAssessment}
            loading={publishing}
            fullWidth
            size="lg"
          />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scrollView: { flex: 1, padding: Spacing.base },
  center: { justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: Spacing.md, fontSize: Typography.sizes.base, color: Colors.neutral[600] },
  section: { marginBottom: Spacing.lg, backgroundColor: Colors.white, padding: Spacing.md, borderRadius: BorderRadius.xl },
  sectionTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.md },
  aiToggleHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  field: { marginBottom: Spacing.md },
  label: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: 4 },
  input: { borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm, fontSize: Typography.sizes.base, color: Colors.neutral[900] },
  textarea: { paddingVertical: Spacing.md, textAlignVertical: 'top', minHeight: 100 },
  row: { flexDirection: 'row', gap: Spacing.sm },
  dropdown: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm },
  dropdownValue: { fontSize: Typography.sizes.base, color: Colors.neutral[900] },
  dropdownMenu: { position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 4, backgroundColor: Colors.white, borderRadius: BorderRadius.lg, borderWidth: 1, borderColor: Colors.border, zIndex: 999 },
  dropdownItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm, borderBottomWidth: 1, borderBottomColor: Colors.border },
  dropdownItemText: { fontSize: Typography.sizes.base, color: Colors.neutral[900] },
  pillRow: { flexDirection: 'row', gap: Spacing.sm },
  pill: { flex: 1, borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.full, paddingVertical: Spacing.sm, alignItems: 'center' },
  pillActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  pillText: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  pillTextActive: { color: Colors.primary[600] },
  chapterList: { gap: Spacing.sm },
  chapterCard: { borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  chapterCardActive: { borderColor: Colors.success, backgroundColor: Colors.success + '10' },
  chapterName: { fontSize: Typography.sizes.base, color: Colors.neutral[900] },
  chapterNameActive: { fontWeight: Typography.weights.semibold, color: Colors.success },
  difficultyRow: { flexDirection: 'row', gap: Spacing.sm },
  diffBtn: { flex: 1, borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingVertical: Spacing.sm, alignItems: 'center' },
  diffBtnActive: { borderColor: Colors.warning, backgroundColor: Colors.warning + '10' },
  diffBtnText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  diffBtnTextActive: { color: Colors.warning },
  questionsList: { padding: Spacing.base, gap: Spacing.sm },
  questionCard: { padding: Spacing.md, marginBottom: Spacing.sm },
  questionHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: Spacing.sm },
  questionNum: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  questionMarks: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },
  questionText: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900], marginBottom: Spacing.sm },
  sampleLabel: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[600], marginTop: Spacing.sm },
  sampleText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginTop: 4 },
  questionFooter: { flexDirection: 'row', padding: Spacing.base, gap: Spacing.sm },
  questionFooterBtn: { flex: 1 },
  summaryCard: { padding: Spacing.md },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: Spacing.sm, borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  summaryLabel: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  summaryValue: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  emptyText: { fontSize: Typography.sizes.base, color: Colors.neutral[400] },
  stepper: { flexDirection: 'row', alignItems: 'center', borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, overflow: 'hidden' },
  stepperBtn: { width: 40, height: 44, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.primary[50] },
  stepperInput: { flex: 1, textAlign: 'center', fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900], paddingVertical: Spacing.sm },
});
