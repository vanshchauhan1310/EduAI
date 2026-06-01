import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TextInput, Alert, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import EmptyState from '../../components/common/EmptyState';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useAuthStore } from '../../store/authStore';
import api from '../../services/api';
import {
  deoIntelligenceService,
  deoRiskMonitorService,
  deoTeacherRationalizationService,
  deoCommunicationService,
} from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

// ─── Module 1: District Intelligence Briefing ─────────────────────

export function DistrictIntelligenceScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const districtId = user?.district_id;
  const [brief, setBrief] = useState<any>(null);

  const generateMutation = useMutation({
    mutationFn: () => deoIntelligenceService.generateBrief(districtId!),
    onSuccess: (data) => setBrief(data),
    onError: (err: any) => {
      console.error('Intelligence brief error:', err);
      Alert.alert('Error', err?.response?.data?.detail || 'Could not generate intelligence brief. Please try again.');
    },
  });

  const handleSharePdf = async () => {
    if (!brief?.id) { Alert.alert('Info', 'No report to share. Generate a brief first.'); return; }
    try {
      await deoIntelligenceService.share(brief.id, 'pdf');
    } catch (err: any) {
      console.error('Share PDF error:', err);
      Alert.alert('Error', 'Could not share PDF. Please try again.');
    }
  };

  const handleShareDocx = async () => {
    if (!brief?.id) { Alert.alert('Info', 'No report to share. Generate a brief first.'); return; }
    try {
      await deoIntelligenceService.share(brief.id, 'docx');
    } catch (err: any) {
      console.error('Share DOCX error:', err);
      Alert.alert('Error', 'Could not share DOCX. Please try again.');
    }
  };

  if (!districtId) return <View style={styles.flex}><Header title="District Intelligence" subtitle="Briefing" /><EmptyState icon="ban" title="District not assigned" description="Contact administrator." /></View>;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="District Intelligence" subtitle="AI-powered briefing" />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card style={styles.infoCard}>
          <Text style={styles.infoTitle}>District Intelligence Briefing</Text>
          <Text style={styles.infoDesc}>Generate an AI-powered daily briefing for your district covering attendance, teacher deployment, risks, and recommendations.</Text>
        </Card>
        <Button title={generateMutation.isPending ? 'Generating…' : 'Generate Intelligence Brief'} onPress={() => generateMutation.mutateAsync()} loading={generateMutation.isPending} fullWidth size="lg" style={styles.generateBtn} />
        {generateMutation.isPending && <LoadingSpinner message="Generating intelligence brief..." />}
        {brief && (
          <>
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

            <Card style={styles.resultCard}>
              <Text style={styles.resultTitle}>District: {brief.district_name}</Text>
              <Text style={styles.resultMeta}>Schools: {brief.total_schools} | Students: {brief.total_students} | Teachers: {brief.total_teachers} | Mandals: {brief.active_mandals}</Text>
              <Text style={styles.resultMeta}>Attendance: {brief.avg_attendance}% | Vacancies: {brief.teacher_vacancies} | High Risk: {brief.high_risk_schools}</Text>
              <Text style={styles.sectionLabel}>AI Briefing</Text>
              <Text style={styles.resultContent}>{brief.content?.ai_briefing}</Text>
            </Card>
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ─── Module 2: Mandal Performance ─────────────────────────────────

export function MandalPerformanceScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const districtId = user?.district_id;

  const { data, isLoading } = useQuery({
    queryKey: ['mandal-performance', districtId],
    queryFn: () => deoIntelligenceService.getMandalPerformance(districtId!),
    enabled: !!districtId,
  });

  const handleSharePdf = async () => {
    if (!districtId) return;
    try {
      await deoIntelligenceService.shareMandalPerformance(districtId, 'pdf');
    } catch (err: any) {
      console.error('Share PDF error:', err);
      Alert.alert('Error', 'Could not share PDF. Please try again.');
    }
  };

  const handleShareDocx = async () => {
    if (!districtId) return;
    try {
      await deoIntelligenceService.shareMandalPerformance(districtId, 'docx');
    } catch (err: any) {
      console.error('Share DOCX error:', err);
      Alert.alert('Error', 'Could not share DOCX. Please try again.');
    }
  };

  if (!districtId) return <View style={styles.flex}><Header title="Mandal Performance" /><EmptyState icon="ban" title="District not assigned" /></View>;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Mandal Performance" subtitle="District mandal rankings" />
      {isLoading ? (
        <LoadingSpinner message="Loading…" />
      ) : (
        <>
          {data && (
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
          )}
          <ScrollView contentContainerStyle={styles.scroll}>
            {data?.best_performing && (
              <Card style={styles.insightCard}>
                <Text style={styles.insightTitle}>Best Performing</Text>
                <Text style={styles.insightValue}>{data.best_performing}</Text>
              </Card>
            )}
            {data?.worst_performing && (
              <Card style={{ ...styles.insightCard, borderLeftColor: '#dc2626' } as any}>
                <Text style={styles.insightTitle}>Needs Attention</Text>
                <Text style={styles.insightValue}>{data.worst_performing}</Text>
              </Card>
            )}
            <Text style={styles.sectionLabel}>Mandal Rankings</Text>
            {data?.mandals?.map((m: any, i: number) => (
              <Card key={m.mandal_id} style={styles.mandalCard}>
                <View style={styles.mandalRow}>
                  <Text style={styles.mandalRank}>#{i + 1}</Text>
                  <View style={styles.mandalInfo}>
                    <Text style={styles.mandalName}>{m.mandal_name}</Text>
                    <Text style={styles.mandalSub}>Schools: {m.schools} | Students: {m.students}</Text>
                  </View>
                  <Text style={styles.mandalScore}>{m.avg_health_score}</Text>
                </View>
              </Card>
            ))}
          </ScrollView>
        </>
      )}
    </View>
  );
}

// ─── Module 3: District Risk Monitor ──────────────────────────────

export function DistrictRiskScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const districtId = user?.district_id;
  const [risk, setRisk] = useState<any>(null);

  const scanMutation = useMutation({
    mutationFn: () => deoRiskMonitorService.scanRisks(districtId!),
    onSuccess: (data) => setRisk(data),
    onError: (err: any) => {
      console.error('Risk scan error:', err);
      Alert.alert('Error', err?.response?.data?.detail || 'Could not scan risks. Please try again.');
    },
  });

  const handleSharePdf = async () => {
    if (!risk?.id) { Alert.alert('Info', 'No report to share. Scan risks first.'); return; }
    try {
      await deoRiskMonitorService.share(risk.id, 'pdf');
    } catch (err: any) {
      console.error('Share PDF error:', err);
      Alert.alert('Error', 'Could not share PDF. Please try again.');
    }
  };

  const handleShareDocx = async () => {
    if (!risk?.id) { Alert.alert('Info', 'No report to share. Scan risks first.'); return; }
    try {
      await deoRiskMonitorService.share(risk.id, 'docx');
    } catch (err: any) {
      console.error('Share DOCX error:', err);
      Alert.alert('Error', 'Could not share DOCX. Please try again.');
    }
  };

  if (!districtId) return <View style={styles.flex}><Header title="District Risk Monitor" /><EmptyState icon="ban" title="District not assigned" /></View>;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="District Risk Monitor" subtitle="Risk detection and escalation" />
      <ScrollView contentContainerStyle={styles.scroll}>
        <Button title={scanMutation.isPending ? 'Scanning…' : 'Scan District Risks'} onPress={() => scanMutation.mutateAsync()} loading={scanMutation.isPending} fullWidth size="lg" />
        {scanMutation.isPending && <LoadingSpinner message="Scanning district risks..." />}
        {risk && (
          <>
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

            <View style={styles.statsRow}>
              <Card style={styles.statCard}>
                <Text style={styles.statValue}>{risk.critical_schools}</Text>
                <Text style={styles.statLabel}>Critical Schools</Text>
              </Card>
              <Card style={styles.statCard}>
                <Text style={styles.statValue}>{risk.high_risk_mandals}</Text>
                <Text style={styles.statLabel}>High Risk Mandals</Text>
              </Card>
            </View>
            <Card style={styles.resultCard}>
              <Text style={styles.sectionLabel}>AI Risk Analysis</Text>
              <Text style={styles.resultContent}>{risk.ai_analysis}</Text>
            </Card>
            {risk.alerts?.length > 0 && (
              <Card style={styles.alertCard}>
                <Text style={styles.sectionLabel}>Active Alerts ({risk.alerts.length})</Text>
                {risk.alerts.slice(0, 10).map((a: any) => (
                  <View key={a.id} style={styles.alertItem}>
                    <View style={[styles.severityDot, { backgroundColor: a.severity === 'CRITICAL' ? '#dc2626' : a.severity === 'HIGH' ? '#f97316' : '#f59e0b' }]} />
                    <Text style={styles.alertText}>{a.title}</Text>
                  </View>
                ))}
              </Card>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ─── Module 4: Teacher Rationalization ────────────────────────────

export function TeacherRationalizationScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const districtId = user?.district_id;
  const [result, setResult] = useState<any>(null);

  const analysisMutation = useMutation({
    mutationFn: () => deoTeacherRationalizationService.analyze(districtId!),
    onSuccess: (data) => setResult(data),
    onError: (err: any) => {
      console.error('Teacher rationalization error:', err);
      Alert.alert('Error', err?.response?.data?.detail || 'Could not analyze teacher allocation. Please try again.');
    },
  });

  const handleSharePdf = async () => {
    if (!result?.id) { Alert.alert('Info', 'No report to share. Analyze teacher allocation first.'); return; }
    try {
      await deoTeacherRationalizationService.share(result.id, 'pdf');
    } catch (err: any) {
      console.error('Share PDF error:', err);
      Alert.alert('Error', 'Could not share PDF. Please try again.');
    }
  };

  const handleShareDocx = async () => {
    if (!result?.id) { Alert.alert('Info', 'No report to share. Analyze teacher allocation first.'); return; }
    try {
      await deoTeacherRationalizationService.share(result.id, 'docx');
    } catch (err: any) {
      console.error('Share DOCX error:', err);
      Alert.alert('Error', 'Could not share DOCX. Please try again.');
    }
  };

  if (!districtId) return <View style={styles.flex}><Header title="Teacher Rationalization" /><EmptyState icon="ban" title="District not assigned" /></View>;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Teacher Rationalization" subtitle="Teacher allocation optimization" />
      <ScrollView contentContainerStyle={styles.scroll}>
        <Button title={analysisMutation.isPending ? 'Analyzing…' : 'Analyze Teacher Allocation'} onPress={() => analysisMutation.mutateAsync()} loading={analysisMutation.isPending} fullWidth size="lg" />
        {analysisMutation.isPending && <LoadingSpinner message="Analyzing teacher allocation..." />}
        {result && (
          <>
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

            <View style={styles.statsRow}>
              <Card style={styles.statCard}>
                <Text style={[styles.statValue, { color: '#22c55e' }]}>{result.total_surplus}</Text>
                <Text style={styles.statLabel}>Surplus</Text>
              </Card>
              <Card style={styles.statCard}>
                <Text style={[styles.statValue, { color: '#dc2626' }]}>{result.total_deficit}</Text>
                <Text style={styles.statLabel}>Deficit</Text>
              </Card>
              <Card style={styles.statCard}>
                <Text style={styles.statValue}>{result.schools_analyzed}</Text>
                <Text style={styles.statLabel}>Schools</Text>
              </Card>
            </View>
            <Card style={styles.resultCard}>
              <Text style={styles.sectionLabel}>AI Recommendations</Text>
              <Text style={styles.resultContent}>{result.ai_recommendations}</Text>
            </Card>
            {result.schools?.slice(0, 10).map((s: any) => (
              <Card key={s.school_id} style={styles.schoolCard}>
                <View style={styles.schoolRow}>
                  <Text style={styles.schoolName}>{s.school_name}</Text>
                  <View style={[styles.priorityBadge, { backgroundColor: s.priority === 'HIGH' ? '#dc2626' : s.priority === 'SURPLUS' ? '#22c55e' : '#f59e0b' }]}>
                    <Text style={styles.priorityText}>{s.priority}</Text>
                  </View>
                </View>
                <Text style={styles.schoolSub}>Students: {s.enrollment} | Teachers: {s.current_teachers} | Required: {s.required_teachers} | Shortage: {s.shortage}</Text>
              </Card>
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ─── Module 5: Governance Communication Assistant ─────────────────

export function GovernanceCommunicationScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);

  const templatesQuery = useQuery({
    queryKey: ['comm-templates'],
    queryFn: () => deoCommunicationService.listTemplates(),
  });

  const generateMutation = useMutation({
    mutationFn: () => deoCommunicationService.generate({
      communication_type: selectedTemplate.key,
      template_fields: fields,
      language: fields.language || 'English',
    }),
    onSuccess: (data) => setResult(data),
    onError: (err: any) => {
      console.error('Communication error:', err);
      Alert.alert('Error', err?.response?.data?.detail || 'Could not generate communication.');
    },
  });

  const handleSharePdf = async () => {
    if (!result?.id) { Alert.alert('Info', 'No communication to share.'); return; }
    try {
      await deoCommunicationService.share(result.id, 'pdf');
    } catch (err: any) {
      console.error('Share PDF error:', err);
      Alert.alert('Error', 'Could not share PDF.');
    }
  };

  const handleShareDocx = async () => {
    if (!result?.id) { Alert.alert('Info', 'No communication to share.'); return; }
    try {
      await deoCommunicationService.share(result.id, 'docx');
    } catch (err: any) {
      console.error('Share DOCX error:', err);
      Alert.alert('Error', 'Could not share DOCX.');
    }
  };

  if (!user?.district_id) return <View style={styles.flex}><Header title="Communication Assistant" /><EmptyState icon="ban" title="District not assigned" /></View>;

  if (result) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Generated Communication" subtitle={result.reference_number} onBack={() => setResult(null)} />
        <ScrollView contentContainerStyle={styles.scroll}>
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

          <Card style={styles.resultCard}>
            <Text style={styles.resultTitle}>{result.subject}</Text>
            <Text style={styles.resultMeta}>Ref: {result.reference_number} | Priority: {result.priority}</Text>
            <Text style={styles.sectionLabel}>Communication</Text>
            <Text style={styles.resultContent}>{result.content}</Text>
          </Card>
          <Button title="Generate Another" variant="outline" onPress={() => { setResult(null); setFields({}); setSelectedTemplate(null); }} fullWidth />
        </ScrollView>
      </View>
    );
  }

  if (selectedTemplate) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title={selectedTemplate.name} subtitle={selectedTemplate.description} onBack={() => setSelectedTemplate(null)} />
        <ScrollView contentContainerStyle={styles.scroll}>
          {selectedTemplate.fields.map((f: any) => (
            <View key={f.key} style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>{f.label}{f.required ? ' *' : ''}</Text>
              {f.type === 'textarea' ? (
                <TextInput
                  value={fields[f.key] || ''}
                  onChangeText={(v) => setFields({ ...fields, [f.key]: v })}
                  style={styles.textAreaInput}
                  multiline
                  textAlignVertical="top"
                  numberOfLines={4}
                />
              ) : (
                <TextInput
                  value={fields[f.key] || ''}
                  onChangeText={(v) => setFields({ ...fields, [f.key]: v })}
                  style={styles.textInput}
                  keyboardType={f.type === 'number' ? 'numeric' : 'default'}
                />
              )}
            </View>
          ))}
          <Button title={generateMutation.isPending ? 'Generating…' : 'Generate Communication'} onPress={() => generateMutation.mutateAsync()} loading={generateMutation.isPending} fullWidth size="lg" />
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Communication Assistant" subtitle="Official district communications" />
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.sectionLabel}>Select a Communication Template</Text>
        {templatesQuery.isLoading ? (
          <LoadingSpinner />
        ) : (
          templatesQuery.data?.map((t: any) => (
            <TouchableOpacity key={t.key} style={styles.templateCard} onPress={() => setSelectedTemplate(t)}>
              <View style={styles.templateIcon}>
                <Ionicons name="document-text-outline" size={24} color={Colors.primary[600]} />
              </View>
              <View style={styles.templateInfo}>
                <Text style={styles.templateName}>{t.name}</Text>
                <Text style={styles.templateDesc}>{t.description}</Text>
              </View>
              <Ionicons name="chevron-forward" size={20} color={Colors.neutral[400]} />
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#f5f7fb' },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  sectionLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginBottom: Spacing.sm, fontWeight: Typography.weights.semibold, marginTop: Spacing.md },
  infoCard: { marginBottom: Spacing.md, padding: Spacing.base },
  infoTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  infoDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4, lineHeight: 16 },
  generateBtn: { marginTop: Spacing.md },
  resultCard: { marginTop: Spacing.md, padding: Spacing.base },
  resultTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  resultMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4 },
  resultContent: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20, marginTop: Spacing.sm },
  statsRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  statCard: { flex: 1, padding: Spacing.base, alignItems: 'center' },
  statValue: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  statLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4 },
  insightCard: { marginBottom: Spacing.sm, padding: Spacing.base, borderLeftWidth: 4, borderLeftColor: '#22c55e' },
  insightTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[600] },
  insightValue: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginTop: 4 },
  mandalCard: { marginBottom: Spacing.sm, padding: Spacing.md },
  mandalRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  mandalRank: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  mandalInfo: { flex: 1 },
  mandalName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  mandalSub: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  mandalScore: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  alertCard: { marginTop: Spacing.md, padding: Spacing.base },
  alertItem: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  severityDot: { width: 8, height: 8, borderRadius: 4 },
  alertText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], flex: 1 },
  schoolCard: { marginBottom: Spacing.sm, padding: Spacing.md },
  schoolRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  schoolName: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  schoolSub: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 4 },
  priorityBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  priorityText: { fontSize: Typography.sizes.xs, color: Colors.white, fontWeight: Typography.weights.semibold },
  templateCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.md, padding: Spacing.base, marginBottom: Spacing.sm, borderWidth: 1, borderColor: '#e5e7eb' },
  templateIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#eef2ff', justifyContent: 'center', alignItems: 'center' },
  templateInfo: { flex: 1 },
  templateName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  templateDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  fieldGroup: { marginBottom: Spacing.md },
  fieldLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.xs },
  textInput: { backgroundColor: Colors.white, borderRadius: BorderRadius.md, borderWidth: 1, borderColor: '#d1d5db', padding: Spacing.base, fontSize: Typography.sizes.sm, color: Colors.neutral[900] },
  textAreaInput: { backgroundColor: Colors.white, borderRadius: BorderRadius.md, borderWidth: 1, borderColor: '#d1d5db', padding: Spacing.base, minHeight: 100, fontSize: Typography.sizes.sm, color: Colors.neutral[900], textAlignVertical: 'top' },
  // Export buttons - with proper padding
  exportRow: { flexDirection: 'row', gap: Spacing.md, marginBottom: Spacing.lg, marginTop: Spacing.md },
  exportBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#2563eb',
    borderRadius: BorderRadius.lg,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    minHeight: 48,
    elevation: 2,
    shadowColor: '#2563eb',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  exportBtnDocx: {
    backgroundColor: '#059669',
    shadowColor: '#059669',
  },
  exportBtnText: {
    color: Colors.white,
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.semibold,
  },
});