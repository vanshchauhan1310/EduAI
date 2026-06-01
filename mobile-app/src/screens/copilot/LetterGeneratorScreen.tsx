import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  TextInput, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { letterService } from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

type Step = 'template' | 'form' | 'preview' | 'history';

const TEMPLATE_ICONS: Record<string, { icon: string; color: string }> = {
  leave_approval:           { icon: 'calendar',      color: '#2563eb' },
  teacher_transfer:         { icon: 'swap-horizontal', color: '#7c3aed' },
  infrastructure_request:   { icon: 'construct',     color: '#059669' },
  parent_notice:            { icon: 'people',        color: '#d97706' },
  scholarship_recommendation: { icon: 'ribbon',     color: '#dc2626' },
  compliance_submission:    { icon: 'shield-checkmark', color: '#0891b2' },
  budget_request:           { icon: 'cash',          color: '#16a34a' },
};

export default function LetterGeneratorScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const queryClient = useQueryClient();

  const [step, setStep] = useState<Step>('template');
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [generatedLetter, setGeneratedLetter] = useState<any>(null);
  const [language, setLanguage] = useState<'English' | 'Telugu'>('English');

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['letter-templates'],
    queryFn: letterService.listTemplates,
  });

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['letter-history'],
    queryFn: () => letterService.getHistory(),
    enabled: step === 'history',
  });

  const { mutate: generate, isPending: generating } = useMutation({
    mutationFn: () => letterService.generate({
      letter_type: selectedTemplate.key,
      template_fields: formValues,
      language,
    }),
    onSuccess: (data) => {
      setGeneratedLetter(data);
      setStep('preview');
      queryClient.invalidateQueries({ queryKey: ['letter-history'] });
    },
    onError: () => Alert.alert('Error', 'Failed to generate letter. Please try again.'),
  });

  const { mutate: exportLetter, isPending: exportingLetter } = useMutation({
    mutationFn: ({ id, format }: { id: number; format: 'pdf' | 'docx' }) =>
      letterService.share(id, format),
    onSuccess: (_data, variables) => {
      Alert.alert('Shared', `Letter ${variables.format.toUpperCase()} is ready to share.`);
    },
    onError: () => Alert.alert('Share failed', 'Could not share the letter. Please try again.'),
  });

  const handleSelectTemplate = (template: any) => {
    setSelectedTemplate(template);
    setFormValues({});
    setStep('form');
  };

  const isFormValid = selectedTemplate?.fields?.every(
    (f: any) => !f.required || (formValues[f.key] && formValues[f.key].trim())
  );

  const renderTemplateStep = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <Text style={styles.sectionTitle}>Select Letter Template</Text>
      {templatesLoading ? (
        <LoadingSpinner message="Loading templates…" />
      ) : (
        templates.map((t: any) => {
          const cfg = TEMPLATE_ICONS[t.key] ?? { icon: 'document', color: Colors.primary[600] };
          return (
            <TouchableOpacity key={t.key} style={styles.templateCard} onPress={() => handleSelectTemplate(t)}>
              <View style={[styles.templateIcon, { backgroundColor: `${cfg.color}18` }]}>
                <Ionicons name={cfg.icon as any} size={24} color={cfg.color} />
              </View>
              <View style={styles.templateInfo}>
                <Text style={styles.templateName}>{t.name}</Text>
                <Text style={styles.templateDesc}>{t.description}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={Colors.neutral[300]} />
            </TouchableOpacity>
          );
        })
      )}
    </ScrollView>
  );

  const renderFormStep = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.stepHeader}>
        <TouchableOpacity onPress={() => setStep('template')} style={styles.backChip}>
          <Ionicons name="arrow-back" size={16} color={Colors.primary[600]} />
          <Text style={styles.backChipText}>Templates</Text>
        </TouchableOpacity>
        <Text style={styles.stepTitle}>{selectedTemplate?.name}</Text>
      </View>

      {/* Language toggle */}
      <Card style={styles.langCard}>
        <Text style={styles.langLabel}>Output Language</Text>
        <View style={styles.langToggle}>
          {(['English', 'Telugu'] as const).map((lang) => (
            <TouchableOpacity
              key={lang}
              style={[styles.langOption, language === lang && styles.langOptionActive]}
              onPress={() => setLanguage(lang)}
            >
              <Text style={[styles.langOptionText, language === lang && styles.langOptionTextActive]}>
                {lang === 'English' ? '🇬🇧 English' : '🇮🇳 Telugu'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </Card>

      {/* Dynamic form fields */}
      {selectedTemplate?.fields?.map((field: any) => (
        <View key={field.key} style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>
            {field.label} {field.required && <Text style={styles.required}>*</Text>}
          </Text>
          {field.type === 'select' ? (
            <View style={styles.selectWrap}>
              {field.options.map((opt: string) => (
                <TouchableOpacity
                  key={opt}
                  style={[styles.selectOption, formValues[field.key] === opt && styles.selectOptionActive]}
                  onPress={() => setFormValues((prev) => ({ ...prev, [field.key]: opt }))}
                >
                  <Text style={[styles.selectOptionText, formValues[field.key] === opt && styles.selectOptionTextActive]}>
                    {opt}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          ) : field.type === 'textarea' ? (
            <TextInput
              style={[styles.input, styles.textarea]}
              value={formValues[field.key] ?? ''}
              onChangeText={(v) => setFormValues((prev) => ({ ...prev, [field.key]: v }))}
              placeholder={`Enter ${field.label.toLowerCase()}…`}
              placeholderTextColor={Colors.neutral[400]}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
          ) : (
            <TextInput
              style={styles.input}
              value={formValues[field.key] ?? ''}
              onChangeText={(v) => setFormValues((prev) => ({ ...prev, [field.key]: v }))}
              placeholder={`Enter ${field.label.toLowerCase()}…`}
              placeholderTextColor={Colors.neutral[400]}
              keyboardType={field.type === 'number' ? 'numeric' : 'default'}
            />
          )}
        </View>
      ))}

      <Button
        title={generating ? 'Generating with AI...' : 'Generate Letter'}
        onPress={() => generate()}
        loading={generating}
        disabled={!isFormValid || generating}
        fullWidth
        size="lg"
        style={styles.generateBtn}
      />
    </ScrollView>
  );

  const renderPreviewStep = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      {/* Result Header */}
      <View style={styles.previewHeader}>
        <Ionicons name="checkmark-circle" size={28} color={Colors.success} />
        <Text style={styles.previewTitle}>Letter Generated!</Text>
        <Text style={styles.previewRef}>Ref: {generatedLetter?.reference_number}</Text>
      </View>

      {/* Letter Content */}
      <Card style={styles.letterCard}>
        <View style={styles.letterTop}>
          <Ionicons name="document-text" size={16} color={Colors.primary[600]} />
          <Text style={styles.letterTopText}>Official Letter Preview</Text>
        </View>
        <Text style={styles.letterContent}>{generatedLetter?.content}</Text>
      </Card>

      {/* Export Actions */}
      <Text style={styles.sectionTitle}>Export As</Text>
      <View style={styles.exportRow}>
        <TouchableOpacity style={[styles.exportBtn, { backgroundColor: '#dc2626' }]}
          disabled={exportingLetter}
          onPress={() => generatedLetter?.id && exportLetter({ id: generatedLetter.id, format: 'pdf' })}>
          <Ionicons name="document" size={20} color={Colors.white} />
          <Text style={styles.exportBtnText}>{exportingLetter ? 'Sharing...' : 'PDF'}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.exportBtn, { backgroundColor: '#2563eb' }]}
          disabled={exportingLetter}
          onPress={() => generatedLetter?.id && exportLetter({ id: generatedLetter.id, format: 'docx' })}>
          <Ionicons name="document-attach" size={20} color={Colors.white} />
          <Text style={styles.exportBtnText}>{exportingLetter ? 'Sharing...' : 'DOCX'}</Text>
        </TouchableOpacity>
      </View>

      <Button
        title="Generate Another Letter"
        variant="outline"
        onPress={() => { setStep('template'); setGeneratedLetter(null); setFormValues({}); }}
        fullWidth
        style={styles.anotherBtn}
      />
    </ScrollView>
  );

  const renderHistoryStep = () => (
    historyLoading ? <LoadingSpinner message="Loading history…" /> :
    history.length === 0 ? (
      <EmptyState icon="create-outline" title="No Letters Yet" description="Generate your first official letter." />
    ) : (
      <ScrollView contentContainerStyle={styles.scroll}>
        {history.map((item: any) => {
          const cfg = TEMPLATE_ICONS[item.letter_type] ?? { icon: 'document', color: Colors.primary[600] };
          return (
            <TouchableOpacity key={item.id} style={styles.historyCard}
              onPress={() => letterService.getById(item.id).then((d) => { setGeneratedLetter(d); setStep('preview'); })}>
              <View style={[styles.historyIcon, { backgroundColor: `${cfg.color}18` }]}>
                <Ionicons name={cfg.icon as any} size={20} color={cfg.color} />
              </View>
              <View style={styles.historyInfo}>
                <Text style={styles.historyType}>{item.letter_type.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</Text>
                <Text style={styles.historyRef}>Ref: {item.reference_number || 'N/A'}</Text>
                <Text style={styles.historyDate}>{new Date(item.created_at).toLocaleDateString('en-IN')}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={Colors.neutral[300]} />
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    )
  );

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Letter Generator" subtitle="Official Document Automation" onBack={() => navigation.goBack()} />

      {/* Step Tabs */}
      <View style={styles.tabs}>
        {([
          { key: 'template', label: 'Templates', icon: 'albums-outline' },
          { key: 'history',  label: 'History',   icon: 'time-outline' },
        ] as const).map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[styles.tab, (step === t.key || (step === 'form' && t.key === 'template') || (step === 'preview' && t.key === 'template')) && styles.tabActive]}
            onPress={() => setStep(t.key as Step)}
          >
            <Ionicons name={t.icon} size={16} color={(step === t.key) ? Colors.primary[600] : Colors.neutral[400]} />
            <Text style={[styles.tabText, step === t.key && styles.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {step === 'template' && renderTemplateStep()}
      {step === 'form'     && renderFormStep()}
      {step === 'preview'  && renderPreviewStep()}
      {step === 'history'  && renderHistoryStep()}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  tabs: { flexDirection: 'row', backgroundColor: Colors.white, borderBottomWidth: 1, borderBottomColor: Colors.border, paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm, gap: Spacing.sm },
  tab: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: Spacing.md, paddingVertical: 8, borderRadius: BorderRadius.full, backgroundColor: Colors.neutral[100] },
  tabActive: { backgroundColor: Colors.primary[50] },
  tabText: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], fontWeight: Typography.weights.medium },
  tabTextActive: { color: Colors.primary[600], fontWeight: Typography.weights.bold },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md },

  templateCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.sm, ...Shadows.sm },
  templateIcon: { width: 48, height: 48, borderRadius: 24, justifyContent: 'center', alignItems: 'center' },
  templateInfo: { flex: 1 },
  templateName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  templateDesc: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 2 },

  stepHeader: { marginBottom: Spacing.lg },
  backChip: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', backgroundColor: Colors.primary[50], paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full, marginBottom: Spacing.sm },
  backChipText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
  stepTitle: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },

  langCard: { marginBottom: Spacing.md },
  langLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.sm },
  langToggle: { flexDirection: 'row', gap: Spacing.sm },
  langOption: { flex: 1, padding: Spacing.md, borderRadius: BorderRadius.lg, borderWidth: 1.5, borderColor: Colors.border, alignItems: 'center' },
  langOptionActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  langOptionText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], fontWeight: Typography.weights.medium },
  langOptionTextActive: { color: Colors.primary[700], fontWeight: Typography.weights.bold },

  fieldGroup: { marginBottom: Spacing.md },
  fieldLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.xs },
  required: { color: Colors.danger },
  input: { borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, padding: Spacing.md, fontSize: Typography.sizes.base, color: Colors.neutral[900], backgroundColor: Colors.neutral[50] },
  textarea: { minHeight: 90, textAlignVertical: 'top' },
  selectWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  selectOption: { paddingHorizontal: Spacing.md, paddingVertical: 8, borderRadius: BorderRadius.full, borderWidth: 1.5, borderColor: Colors.border, backgroundColor: Colors.neutral[50] },
  selectOptionActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  selectOptionText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  selectOptionTextActive: { color: Colors.primary[700], fontWeight: Typography.weights.semibold },
  generateBtn: { marginTop: Spacing.md },

  previewHeader: { alignItems: 'center', marginBottom: Spacing.lg, gap: 4 },
  previewTitle: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  previewRef: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },
  letterCard: { marginBottom: Spacing.lg },
  letterTop: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: Spacing.md, paddingBottom: Spacing.md, borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  letterTopText: { fontSize: Typography.sizes.sm, color: Colors.primary[700], fontWeight: Typography.weights.semibold },
  letterContent: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 22, fontFamily: 'monospace' },
  exportRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  exportBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: Spacing.sm, padding: Spacing.md, borderRadius: BorderRadius.xl },
  exportBtnText: { color: Colors.white, fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  shareSectionTitle: { marginTop: Spacing.lg },
  shareBtn: { flex: 1 },
  anotherBtn: { marginTop: Spacing.sm },

  historyCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.sm, ...Shadows.sm },
  historyIcon: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  historyInfo: { flex: 1 },
  historyType: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  historyRef: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 1 },
  historyDate: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 1 },
});
