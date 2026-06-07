import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert,
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
import { reportService } from '../../services/copilotService';
import { useAuthStore } from '../../store/authStore';
import { useAppStore } from '../../store/appStore';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

type Step = 'config' | 'result' | 'history';

const REPORT_TYPES = [
  { key: 'school_performance',  label: 'School Performance',  icon: 'school',     color: '#2563eb', desc: 'Academic results, risk distribution, pass rates' },
  { key: 'attendance',          label: 'Attendance Report',    icon: 'calendar',   color: '#7c3aed', desc: 'Attendance rates, trends, absenteeism patterns' },
  { key: 'teacher_performance', label: 'Teacher Performance',  icon: 'people',     color: '#059669', desc: 'Teacher attendance, workload, performance metrics' },
  { key: 'school_health',       label: 'School Health Score',  icon: 'fitness',    color: '#dc2626', desc: 'Infrastructure, resources, composite health grade' },
];

const SCOPE_OPTIONS = [
  { key: 'school',   label: 'School',   icon: 'business'  },
  { key: 'mandal',   label: 'Mandal',   icon: 'map'       },
  { key: 'district', label: 'District', icon: 'globe'     },
];

function SectionCard({ title, content, icon, color }: { title: string; content: string | string[]; icon: string; color: string }) {
  return (
    <Card style={styles.sectionCard}>
      <View style={styles.sectionHeader}>
        <View style={[styles.sectionIcon, { backgroundColor: `${color}18` }]}>
          <Ionicons name={icon as any} size={18} color={color} />
        </View>
        <Text style={[styles.sectionTitle, { color }]}>{title}</Text>
      </View>
      {Array.isArray(content)
        ? content.map((item, i) => (
          <View key={i} style={styles.bulletRow}>
            <View style={[styles.bullet, { backgroundColor: color }]} />
            <Text style={styles.bulletText}>{item}</Text>
          </View>
        ))
        : <Text style={styles.sectionContent}>{content}</Text>
      }
    </Card>
  );
}

export default function ReportGeneratorScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const user = useAuthStore((s) => s.user);
  const academicYear = useAppStore((s) => s.selectedAcademicYear);
  const queryClient = useQueryClient();

  const [step, setStep] = useState<Step>('config');
  const [reportType, setReportType] = useState('');
  const [scope, setScope] = useState('school');
  const [report, setReport] = useState<any>(null);

  const scopeId = scope === 'school' ? (user?.school_id ?? 1)
    : scope === 'mandal' ? (user?.mandal_id ?? 1)
    : (user?.district_id ?? 1);

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['report-history'],
    queryFn: () => reportService.getHistory(),
    enabled: step === 'history',
  });

  const { mutate: generate, isPending: generating } = useMutation({
    mutationFn: () => reportService.generate({
      report_type: reportType,
      report_scope: scope,
      scope_id: scopeId,
      academic_year: academicYear,
    }),
    onSuccess: (data) => {
      setReport(data);
      setStep('result');
      queryClient.invalidateQueries({ queryKey: ['report-history'] });
    },
    onError: () => Alert.alert('Error', 'Failed to generate report. Please try again.'),
  });

  const { mutate: exportReport, isPending: exportingReport } = useMutation({
    mutationFn: ({ id, format }: { id: number; format: 'pdf' | 'docx' }) =>
      reportService.share(id, format),
    onSuccess: (_data, variables) => {
      Alert.alert('Shared', `Report ${variables.format.toUpperCase()} is ready to share.`);
    },
    onError: () => Alert.alert('Share failed', 'Could not share the report. Please try again.'),
  });

  const selected = REPORT_TYPES.find((r) => r.key === reportType);

  const renderConfig = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      {/* Report Type */}
      <Text style={styles.sectionLabel}>1. Select Report Type</Text>
      <View style={styles.typesGrid}>
        {REPORT_TYPES.map((rt) => (
          <TouchableOpacity
            key={rt.key}
            style={[styles.typeCard, reportType === rt.key && { borderColor: rt.color, borderWidth: 2 }]}
            onPress={() => setReportType(rt.key)}
          >
            <View style={[styles.typeIcon, { backgroundColor: `${rt.color}18` }]}>
              <Ionicons name={rt.icon as any} size={26} color={rt.color} />
            </View>
            <Text style={styles.typeLabel}>{rt.label}</Text>
            <Text style={styles.typeDesc}>{rt.desc}</Text>
            {reportType === rt.key && (
              <View style={[styles.checkMark, { backgroundColor: rt.color }]}>
                <Ionicons name="checkmark" size={12} color={Colors.white} />
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>

      {/* Scope */}
      <Text style={styles.sectionLabel}>2. Select Scope</Text>
      <View style={styles.scopeRow}>
        {SCOPE_OPTIONS.filter((s) => {
          if (user?.role === 'HM') return s.key === 'school';
          if (user?.role === 'MEO') return s.key !== 'district';
          return true;
        }).map((s) => (
          <TouchableOpacity
            key={s.key}
            style={[styles.scopeOption, scope === s.key && styles.scopeOptionActive]}
            onPress={() => setScope(s.key)}
          >
            <Ionicons name={s.icon as any} size={18} color={scope === s.key ? Colors.primary[600] : Colors.neutral[400]} />
            <Text style={[styles.scopeText, scope === s.key && styles.scopeTextActive]}>{s.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Info card */}
      {selected && (
        <Card style={[styles.infoCard, { borderLeftColor: selected.color, borderLeftWidth: 4 }]}>
          <Text style={styles.infoTitle}>{selected.label}</Text>
          <Text style={styles.infoDesc}>{selected.desc}</Text>
          <Text style={styles.infoMeta}>Scope: {scope.toUpperCase()} • AY {academicYear}</Text>
        </Card>
      )}

      <Button
        title={generating ? 'Generating with AI...' : 'Generate Report'}
        onPress={() => generate()}
        loading={generating}
        disabled={!reportType || generating}
        fullWidth
        size="lg"
        style={styles.generateBtn}
      />
    </ScrollView>
  );

  const renderResult = () => {
    const json = report?.content_json;
    const reportTypeCfg = REPORT_TYPES.find((r) => r.key === report?.report_type);

    return (
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={[styles.resultBanner, { backgroundColor: reportTypeCfg?.color ?? Colors.primary[600] }]}>
          <Ionicons name="document-text" size={32} color={Colors.white} />
          <View>
            <Text style={styles.resultTitle}>{reportTypeCfg?.label ?? 'Report'}</Text>
            <Text style={styles.resultMeta}>{report?.report_scope?.toUpperCase()} · {new Date(report?.created_at).toLocaleDateString('en-IN')}</Text>
          </View>
        </View>

        {json && (
          <>
            <SectionCard title="Executive Summary"  content={json.executive_summary} icon="analytics"        color="#1d4ed8" />
            <SectionCard title="KPI Analysis"       content={json.kpi_analysis}      icon="bar-chart"        color="#7c3aed" />
            <SectionCard title="Trends"             content={json.trends}            icon="trending-up"      color="#059669" />
            <SectionCard title="Risk Areas"         content={json.risks}             icon="alert-circle"     color="#dc2626" />
            <SectionCard title="Recommendations"    content={json.recommendations}   icon="bulb"             color="#d97706" />
            <SectionCard title="Action Plan"        content={json.action_plan}       icon="list"             color="#0891b2" />
          </>
        )}

        {/* Export */}
        <Text style={styles.sectionLabel}>Export Report</Text>
        <View style={styles.exportRow}>
          <TouchableOpacity
            style={[styles.exportBtn, { backgroundColor: '#dc2626' }]}
            disabled={exportingReport}
            onPress={() => report?.id && exportReport({ id: report.id, format: 'pdf' })}
          >
            <Ionicons name="document" size={20} color={Colors.white} />
            <Text style={styles.exportBtnText}>{exportingReport ? 'Sharing...' : 'Export PDF'}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.exportBtn, { backgroundColor: '#2563eb' }]}
            disabled={exportingReport}
            onPress={() => report?.id && exportReport({ id: report.id, format: 'docx' })}
          >
            <Ionicons name="document-attach" size={20} color={Colors.white} />
            <Text style={styles.exportBtnText}>{exportingReport ? 'Sharing...' : 'Export DOCX'}</Text>
          </TouchableOpacity>
        </View>



        <Button title="Generate New Report" variant="outline" onPress={() => { setStep('config'); setReport(null); setReportType(''); }} fullWidth style={{ marginTop: Spacing.sm }} />
      </ScrollView>
    );
  };

  const renderHistory = () => (
    historyLoading ? <LoadingSpinner message="Loading history…" /> :
    history.length === 0 ? (
      <EmptyState icon="stats-chart-outline" title="No Reports Yet" description="Generate your first report to get started." />
    ) : (
      <ScrollView contentContainerStyle={styles.scroll}>
        {history.map((item: any) => {
          const cfg = REPORT_TYPES.find((r) => r.key === item.report_type);
          return (
            <TouchableOpacity key={item.id} style={styles.historyCard}
              onPress={() => reportService.getById(item.id).then((d) => { setReport(d); setStep('result'); })}>
              <View style={[styles.historyIcon, { backgroundColor: `${cfg?.color ?? Colors.primary[600]}18` }]}>
                <Ionicons name={(cfg?.icon ?? 'document') as any} size={20} color={cfg?.color ?? Colors.primary[600]} />
              </View>
              <View style={styles.historyInfo}>
                <Text style={styles.historyType}>{cfg?.label ?? item.report_type}</Text>
                <Text style={styles.historyScope}>{item.report_scope?.toUpperCase()}</Text>
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
      <Header title="Report Generator" subtitle="AI-Powered Data Reports" onBack={() => navigation.goBack()} />

      <View style={styles.tabs}>
        {[
          { key: 'config',  label: 'Generate', icon: 'create-outline' },
          { key: 'history', label: 'History',  icon: 'time-outline'   },
        ].map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[styles.tab, step === t.key && styles.tabActive]}
            onPress={() => setStep(t.key as Step)}
          >
            <Ionicons name={t.icon as any} size={16} color={step === t.key ? Colors.primary[600] : Colors.neutral[400]} />
            <Text style={[styles.tabText, step === t.key && styles.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {step === 'config'  && renderConfig()}
      {step === 'result'  && renderResult()}
      {step === 'history' && renderHistory()}
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
  sectionLabel: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md, marginTop: Spacing.sm },

  typesGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, marginBottom: Spacing.sm },
  typeCard: {
    width: '48%',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    borderWidth: 1.5,
    borderColor: Colors.border,
    ...Shadows.sm,
    position: 'relative',
  },
  typeIcon: { width: 46, height: 46, borderRadius: 23, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.sm },
  typeLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: 2 },
  typeDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], lineHeight: 16 },
  checkMark: { position: 'absolute', top: 8, right: 8, width: 20, height: 20, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },

  scopeRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  scopeOption: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, padding: Spacing.md, borderRadius: BorderRadius.xl, borderWidth: 1.5, borderColor: Colors.border, backgroundColor: Colors.neutral[50] },
  scopeOptionActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  scopeText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], fontWeight: Typography.weights.medium },
  scopeTextActive: { color: Colors.primary[700], fontWeight: Typography.weights.bold },

  infoCard: { marginBottom: Spacing.md, borderRadius: 16, padding: Spacing.md, backgroundColor: Colors.white, ...Shadows.sm },
  infoTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  infoDesc: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginTop: 2 },
  infoMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 4 },
  generateBtn: { marginTop: Spacing.md },

  resultBanner: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, padding: Spacing.lg, borderRadius: 20, marginBottom: Spacing.md },
  resultTitle: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.white },
  resultMeta: { fontSize: Typography.sizes.sm, color: 'rgba(255,255,255,0.75)', marginTop: 2 },

  sectionCard: { marginBottom: Spacing.sm },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  sectionIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  sectionTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  sectionContent: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },
  bulletRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: 6, alignItems: 'flex-start' },
  bullet: { width: 6, height: 6, borderRadius: 3, marginTop: 6 },
  bulletText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },

  exportRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  exportBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: Spacing.sm, padding: Spacing.md, borderRadius: BorderRadius.xl },
  exportBtnText: { color: Colors.white, fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  shareSectionTitle: { marginTop: Spacing.lg },
  shareBtn: { flex: 1 },
  historyCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.sm, ...Shadows.sm },
  historyIcon: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  historyInfo: { flex: 1 },
  historyType: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  historyScope: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 1 },
  historyDate: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 1 },
});
