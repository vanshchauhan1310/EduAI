import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  Alert,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import EmptyState from '../../components/common/EmptyState';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useAuthStore } from '../../store/authStore';
import { meoReportService } from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { CopilotStackParams } from '../../navigation/CopilotNavigator';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import dayjs from 'dayjs';

type Nav = NativeStackNavigationProp<CopilotStackParams>;

interface TemplateField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'textarea' | 'select';
  required: boolean;
  default?: string;
  options?: string[];
}

interface Template {
  key: string;
  name: string;
  description: string;
  fields: TemplateField[];
}

interface ReportResult {
  id: number;
  report_type: string;
  mandal_id: number;
  mandal_name?: string;
  reference_number: string;
  content: string;
  created_at: string;
}

// ─── Main Template Selection Screen ─────────────────────────────

// ─── Keep old exports for backward compatibility ─────────────────

const MEO_TEMPLATES = [
  { key: 'early_warning', name: 'Early Warning Briefing', icon: 'warning-outline' as const },
  { key: 'teacher_vacancy', name: 'Teacher Vacancy & Deployment', icon: 'people-outline' as const },
  { key: 'governance_communication', name: 'Governance Communication', icon: 'chatbubbles-outline' as const },
  { key: 'cluster_briefing', name: 'Cluster Governance Briefing', icon: 'layers-outline' as const },
];

export function EarlyWarningAssistantScreen() {
  return <MEOCopilotHomeScreen />;
}
export function TeacherVacancyAssistantScreen() {
  return <MEOCopilotHomeScreen />;
}
export function GovernanceCommunicationAssistantScreen() {
  return <MEOCopilotHomeScreen />;
}
export function ClusterGovernanceBriefingScreen() {
  return <MEOCopilotHomeScreen />;
}

export function MEOCopilotHomeScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const user = useAuthStore((s) => s.user);

  const { data: templates, isLoading, isError } = useQuery({
    queryKey: ['meo-templates'],
    queryFn: () => meoReportService.listTemplates(),
    enabled: !!user?.mandal_id,
    retry: false,
  });

  if (!user?.mandal_id) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="MEO Report Generator" subtitle="Template-based reports" />
        <EmptyState
          icon="ban"
          title="Mandal not assigned"
          description="Your MEO account needs a mandal association to access this module. Contact your system administrator."
        />
      </View>
    );
  }

  if (isLoading) return <LoadingSpinner fullScreen message="Loading templates…" />;

  if (isError) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="MEO Report Generator" subtitle="Template-based reports" />
        <EmptyState icon="warning" title="Unable to load" description="Could not load templates. Try again later." />
      </View>
    );
  }

  const templateList: Template[] = templates ?? [];
  const iconMap: Record<string, keyof typeof Ionicons.glyphMap> = {
    early_warning: 'warning-outline',
    teacher_vacancy: 'people-outline',
    governance_communication: 'chatbubbles-outline',
    cluster_briefing: 'layers-outline',
  };

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
      <Header title="MEO Report Generator" subtitle="Select a template to generate an official report" />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionLabel}>Available Report Templates</Text>
        {templateList.map((template) => (
          <TouchableOpacity
            key={template.key}
            style={styles.templateCard}
            onPress={() => navigation.navigate('MEOReportForm', { template } as any)}
          >
            <View style={styles.templateIconWrap}>
              <Ionicons name={iconMap[template.key] ?? 'document-text-outline'} size={24} color={Colors.primary[600]} />
            </View>
            <View style={styles.templateInfo}>
              <Text style={styles.templateName}>{template.name}</Text>
              <Text style={styles.templateDesc} numberOfLines={2}>{template.description}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={Colors.neutral[400]} />
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

// ─── Report Form Screen ─────────────────────────────────────────

export function MEOReportFormScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const route = useRoute<RouteProp<CopilotStackParams, 'MEOReportForm'>>();
  const template = route.params?.template as Template;
  const user = useAuthStore((s) => s.user);

  const [fieldValues, setFieldValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    template?.fields?.forEach((f) => {
      initial[f.key] = f.default ?? '';
    });
    // No auto-population needed; mandal_name, district_name, and meo_name
    // are all auto-fetched from the database on the backend side
    return initial;
  });
  const [result, setResult] = useState<ReportResult | null>(null);

  const generateMutation = useMutation({
    mutationFn: (payload: { report_type: string; template_fields: Record<string, any> }) =>
      meoReportService.generate(payload),
    onSuccess: (data) => setResult(data),
    onError: () => Alert.alert('Generation failed', 'Could not generate the report. Please try again.'),
  });

  const isGenerating = generateMutation.isPending;

  const updateField = (key: string, value: string) => {
    setFieldValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleGenerate = () => {
    // Validate required fields
    const missing = template?.fields
      ?.filter((f) => f.required && !fieldValues[f.key]?.trim())
      .map((f) => f.label);
    if (missing && missing.length > 0) {
      Alert.alert('Required fields', `Please fill in: ${missing.join(', ')}`);
      return;
    }
    generateMutation.mutate({
      report_type: template.key,
      template_fields: { ...fieldValues },
    });
  };

  const handleSharePdf = async () => {
    if (!result) return;
    try {
      await meoReportService.share(result.id, 'pdf');
    } catch {
      Alert.alert('Error', 'Could not share PDF.');
    }
  };

  const handleShareDocx = async () => {
    if (!result) return;
    try {
      await meoReportService.share(result.id, 'docx');
    } catch {
      Alert.alert('Error', 'Could not share DOCX.');
    }
  };

  const handleDownloadPdf = async () => {
    if (!result) return;
    try {
      const uri = await meoReportService.download(result.id, 'pdf');
      Alert.alert('Downloaded', `PDF saved to: ${uri}`);
    } catch {
      Alert.alert('Error', 'Could not download PDF.');
    }
  };

  const renderField = (field: TemplateField) => {
    const value = fieldValues[field.key] ?? '';
    const isRequired = field.required;
    const label = `${field.label}${isRequired ? ' *' : ''}`;

    if (field.type === 'textarea') {
      return (
        <View key={field.key} style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>{label}</Text>
          <TextInput
            value={value}
            onChangeText={(v) => updateField(field.key, v)}
            placeholder={`Enter ${field.label.toLowerCase()}`}
            style={styles.textAreaInput}
            multiline
            textAlignVertical="top"
            numberOfLines={4}
          />
        </View>
      );
    }

    return (
      <View key={field.key} style={styles.fieldGroup}>
        <Text style={styles.fieldLabel}>{label}</Text>
        <TextInput
          value={value}
          onChangeText={(v) => updateField(field.key, v)}
          placeholder={`Enter ${field.label.toLowerCase()}`}
          style={styles.textInput}
          keyboardType={field.type === 'number' ? 'numeric' : 'default'}
        />
      </View>
    );
  };

  // Result view after generation
  if (result) {
    return (
      <ResultView
        result={result}
        onBack={() => setResult(null)}
        onSharePdf={handleSharePdf}
        onShareDocx={handleShareDocx}
        onDownloadPdf={handleDownloadPdf}
        insets={insets}
        navigation={navigation}
      />
    );
  }

  if (!template) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="Error" subtitle="No template selected" onBack={() => navigation.goBack()} />
        <EmptyState icon="alert-circle" title="Template not found" description="Please go back and select a template." />
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
      <Header title={template.name} subtitle={template.description} onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card style={styles.infoCard}>
          <Text style={styles.infoTitle}>{template.name}</Text>
          <Text style={styles.infoDesc}>{template.description}</Text>
        </Card>

        {template.fields.map(renderField)}

        <Button
          title={isGenerating ? 'Generating Report…' : `Generate ${template.name}`}
          onPress={handleGenerate}
          loading={isGenerating}
          fullWidth
          size="lg"
          style={styles.generateBtn}
        />
      </ScrollView>
    </View>
  );
}

// ─── Result View ────────────────────────────────────────────────

function ResultView({
  result,
  onBack,
  onSharePdf,
  onShareDocx,
  onDownloadPdf,
  insets,
  navigation,
}: {
  result: ReportResult;
  onBack: () => void;
  onSharePdf: () => void;
  onShareDocx: () => void;
  onDownloadPdf: () => void;
  insets: any;
  navigation: any;
}) {
  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
      <Header title="Report Generated" subtitle={result.reference_number} onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card style={[styles.resultBanner, { borderLeftColor: '#2563eb', borderLeftWidth: 4 }]}> 
          <Text style={styles.resultTitle}>{result.mandal_name ?? 'MEO Report'}</Text>
          <Text style={styles.resultRef}>Ref: {result.reference_number}</Text>
          <Text style={styles.resultDate}>{dayjs(result.created_at).format('DD MMM YYYY, h:mm A')}</Text>
        </Card>

        {/* Export buttons */}
        <View style={styles.exportRow}>
          <TouchableOpacity style={styles.exportBtn} onPress={onSharePdf}>
            <Ionicons name="share-outline" size={18} color={Colors.white} />
            <Text style={styles.exportBtnText}>Share PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.exportBtn, styles.exportBtnDocx]} onPress={onShareDocx}>
            <Ionicons name="share-outline" size={18} color={Colors.white} />
            <Text style={styles.exportBtnText}>Share DOCX</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.exportBtn, styles.exportBtnDownload]} onPress={onDownloadPdf}>
            <Ionicons name="download-outline" size={18} color={Colors.white} />
            <Text style={styles.exportBtnText}>Download PDF</Text>
          </TouchableOpacity>
        </View>

        <Card style={styles.contentCard}>
          <Text style={styles.contentTitle}>Generated Report</Text>
          <Text style={styles.contentText}>{result.content}</Text>
        </Card>

        <Button title="Generate Another Report" variant="outline" onPress={onBack} fullWidth style={{ marginTop: Spacing.md }} />
      </ScrollView>
    </View>
  );
}

// ─── History Screen ─────────────────────────────────────────────

export function MEOReportHistoryScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const user = useAuthStore((s) => s.user);

  const { data: history, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['meo-report-history'],
    queryFn: () => meoReportService.getHistory(),
    enabled: !!user?.mandal_id,
  });

  if (!user?.mandal_id) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="Report History" subtitle="MEO generated reports" onBack={() => navigation.goBack()} />
        <EmptyState icon="ban" title="Mandal not assigned" description="Your account needs a mandal assignment." />
      </View>
    );
  }

  if (isLoading) return <LoadingSpinner fullScreen message="Loading history…" />;

  const items = history ?? [];

  if (items.length === 0) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="Report History" subtitle="MEO generated reports" onBack={() => navigation.goBack()} />
        <EmptyState icon="document-text-outline" title="No reports yet" description="Generate your first MEO report to see history here." />
      </View>
    );
  }

  const typeLabels: Record<string, string> = {
    early_warning: 'Early Warning Briefing',
    teacher_vacancy: 'Teacher Vacancy Report',
    governance_communication: 'Governance Communication',
    cluster_briefing: 'Cluster Governance Briefing',
  };

  const typeIcons: Record<string, keyof typeof Ionicons.glyphMap> = {
    early_warning: 'warning-outline',
    teacher_vacancy: 'people-outline',
    governance_communication: 'chatbubbles-outline',
    cluster_briefing: 'layers-outline',
  };

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
      <Header title="Report History" subtitle="MEO generated reports" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionLabel}>Previously Generated Reports</Text>
        {items.map((item: any) => (
          <TouchableOpacity
            key={item.id}
            style={styles.historyCard}
            onPress={() => navigation.navigate('MEOReportDetail', { reportId: item.id } as any)}
          >
            <View style={styles.historyIconWrap}>
              <Ionicons name={typeIcons[item.report_type] ?? 'document-text-outline'} size={22} color={Colors.primary[600]} />
            </View>
            <View style={styles.historyInfo}>
              <Text style={styles.historyType}>{typeLabels[item.report_type] ?? item.report_type}</Text>
              <Text style={styles.historyRef}>Ref: {item.reference_number}</Text>
              <Text style={styles.historyDate}>{dayjs(item.created_at).format('DD MMM YYYY')}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={Colors.neutral[400]} />
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

// ─── Report Detail Screen ───────────────────────────────────────

export function MEOReportDetailScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const route = useRoute<RouteProp<CopilotStackParams, 'MEOReportDetail'>>();
  const reportId = route.params?.reportId as number;

  const { data: report, isLoading, isError } = useQuery({
    queryKey: ['meo-report', reportId],
    queryFn: () => meoReportService.getById(reportId),
    enabled: !!reportId,
  });

  const handleSharePdf = async () => {
    try {
      await meoReportService.share(reportId, 'pdf');
    } catch {
      Alert.alert('Error', 'Could not share PDF.');
    }
  };

  const handleShareDocx = async () => {
    try {
      await meoReportService.share(reportId, 'docx');
    } catch {
      Alert.alert('Error', 'Could not share DOCX.');
    }
  };

  if (isLoading) return <LoadingSpinner fullScreen message="Loading report…" />;

  if (isError || !report) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="Report Detail" subtitle="Error" onBack={() => navigation.goBack()} />
        <EmptyState icon="alert-circle" title="Report not found" description="This report may have been deleted." />
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
      <Header title="Report Detail" subtitle={report.reference_number} onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card style={[styles.resultBanner, { borderLeftColor: '#2563eb', borderLeftWidth: 4 }]}> 
          <Text style={styles.resultTitle}>{report.mandal_name ?? 'MEO Report'}</Text>
          <Text style={styles.resultRef}>Ref: {report.reference_number}</Text>
          <Text style={styles.resultDate}>{dayjs(report.created_at).format('DD MMM YYYY, h:mm A')}</Text>
        </Card>

        <View style={styles.exportRow}>
          <TouchableOpacity style={styles.exportBtn} onPress={handleSharePdf}>
            <Ionicons name="share-outline" size={18} color={Colors.white} />
            <Text style={styles.exportBtnText}>Share PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.exportBtn, styles.exportBtnDocx]} onPress={handleShareDocx}>
            <Ionicons name="share-outline" size={18} color={Colors.white} />
            <Text style={styles.exportBtnText}>Share DOCX</Text>
          </TouchableOpacity>
        </View>

        <Card style={styles.contentCard}>
          <Text style={styles.contentTitle}>Report Content</Text>
          <Text style={styles.contentText}>{report.content}</Text>
        </Card>
      </ScrollView>
    </View>
  );
}

// ─── Styles ─────────────────────────────────────────────────────

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#f5f7fb' },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  sectionLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginBottom: Spacing.sm, fontWeight: Typography.weights.semibold },

  // Template cards
  templateCard: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  templateIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  templateInfo: { flex: 1 },
  templateName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  templateDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2, lineHeight: 16 },

  // Form fields
  fieldGroup: { marginBottom: Spacing.md },
  fieldLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.xs },
  textInput: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: Spacing.base,
    fontSize: Typography.sizes.sm,
    color: Colors.neutral[900],
  },
  textAreaInput: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: '#d1d5db',
    padding: Spacing.base,
    minHeight: 100,
    fontSize: Typography.sizes.sm,
    color: Colors.neutral[900],
    textAlignVertical: 'top',
  },
  infoCard: { marginBottom: Spacing.md, padding: Spacing.base },
  infoTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  infoDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4, lineHeight: 16 },
  generateBtn: { marginTop: Spacing.md },

  // Result view
  resultBanner: { marginBottom: Spacing.md, padding: Spacing.base, backgroundColor: Colors.white, borderRadius: BorderRadius.md, ...(Shadows.sm as any) },
  resultTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  resultRef: { marginTop: Spacing.xs, fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
  resultDate: { marginTop: 2, fontSize: Typography.sizes.xs, color: Colors.neutral[500] },

  // Export buttons
  exportRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  exportBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#2563eb',
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.sm,
  },
  exportBtnDocx: { backgroundColor: '#059669' },
  exportBtnDownload: { backgroundColor: '#7c3aed' },
  exportBtnText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },

  // Content
  contentCard: { padding: Spacing.base, marginBottom: Spacing.md },
  contentTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.sm },
  contentText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },

  // History
  historyCard: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  historyIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  historyInfo: { flex: 1 },
  historyType: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  historyRef: { fontSize: Typography.sizes.xs, color: Colors.primary[600], marginTop: 2 },
  historyDate: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 1 },
});