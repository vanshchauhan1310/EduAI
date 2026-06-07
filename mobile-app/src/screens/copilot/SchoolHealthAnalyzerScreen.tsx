import React, { useEffect, useMemo, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useQuery, useMutation } from '@tanstack/react-query';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { useAuthStore } from '../../store/authStore';
import { analyticsService } from '../../services/analyticsService';
import { reportService, schoolHealthService } from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const MAX_SELECTION = 5;

export default function SchoolHealthAnalyzerScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const user = useAuthStore((s) => s.user);
  const [selectedSchools, setSelectedSchools] = useState<number[]>([]);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  const { data: mandalOverview, isLoading, isError } = useQuery({
    queryKey: ['mandal-overview', user?.mandal_id],
    queryFn: () => analyticsService.getMandalOverview(user?.mandal_id ?? 0),
    enabled: !!user?.mandal_id,
    retry: false,
  });

  const analysisMutation = useMutation({
    mutationFn: (payload: { mandal_id?: number; school_ids?: number[] }) => reportService.analyzeSchoolHealth(payload),
    onSuccess: (data) => {
      setAnalysisResult(data);
    },
    onError: () => Alert.alert('Analysis failed', 'Could not generate the school health analysis. Please try again.'),
  });
  const isAnalyzing = analysisMutation.isPending;

  useEffect(() => {
    if (mandalOverview?.schools && selectedSchools.length === 0) {
      setSelectedSchools(mandalOverview.schools.slice(0, MAX_SELECTION).map((school: any) => school.school_id));
    }
  }, [mandalOverview, selectedSchools.length]);

  const selectedItems = useMemo(() => new Set(selectedSchools), [selectedSchools]);

  const toggleSchool = (schoolId: number) => {
    if (selectedItems.has(schoolId)) {
      setSelectedSchools((prev) => prev.filter((id) => id !== schoolId));
      return;
    }
    if (selectedSchools.length >= MAX_SELECTION) {
      Alert.alert('Selection limit', `You can select up to ${MAX_SELECTION} schools only.`);
      return;
    }
    setSelectedSchools((prev) => [...prev, schoolId]);
  };

  const runAnalysis = () => {
    if (!user?.mandal_id) {
      Alert.alert('Mandal required', 'Your user profile must include a mandal assignment to run this analyzer.');
      return;
    }
    if (selectedSchools.length === 0) {
      Alert.alert('Select schools', 'Choose at least one school to analyze.');
      return;
    }
    analysisMutation.mutateAsync({ mandal_id: user.mandal_id, school_ids: selectedSchools });
  };

  const renderSchoolTile = (school: any) => {
    const active = selectedItems.has(school.school_id);
    return (
      <TouchableOpacity
        key={school.school_id}
        style={[styles.schoolTile, active && styles.schoolTileActive]}
        onPress={() => toggleSchool(school.school_id)}
      >
        <View style={styles.schoolMeta}>
          <Text style={styles.schoolName}>{school.name}</Text>
          <Text style={styles.schoolCode}>{school.dise_code}</Text>
        </View>
        <View style={[styles.schoolBadge, { backgroundColor: active ? '#2563eb' : '#e5e7eb' }]}> 
          <Text style={[styles.schoolBadgeText, { color: active ? Colors.white : Colors.neutral[700] }]}>
            {active ? 'Selected' : 'Tap'}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  const renderResult = () => {
    const analysisId = analysisResult?.id;
    const handleSharePdf = async () => {
      if (!analysisId) { Alert.alert('Error', 'Report not saved yet.'); return; }
      try {
        await schoolHealthService.share(analysisId, 'pdf');
      } catch {
        Alert.alert('Error', 'Could not share PDF.');
      }
    };
    const handleShareDocx = async () => {
      if (!analysisId) { Alert.alert('Error', 'Report not saved yet.'); return; }
      try {
        await schoolHealthService.share(analysisId, 'docx');
      } catch {
        Alert.alert('Error', 'Could not share DOCX.');
      }
    };

    return (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <Card style={[styles.resultBanner, { borderLeftColor: '#2563eb', borderLeftWidth: 4 }]}> 
        <Text style={styles.resultTitle}>School Health Cluster Analysis</Text>
        <Text style={styles.resultMeta}>{analysisResult?.mandal_name}</Text>
        <Text style={styles.resultSub}>Selected schools: {analysisResult?.selected_school_count}</Text>
      </Card>

      {/* Export buttons */}
      {analysisId && (
        <View style={styles.exportRow}>
          <TouchableOpacity style={styles.exportBtn} onPress={handleSharePdf}>
            <Text style={styles.exportBtnText}>Share PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.exportBtn, styles.exportBtnDocx]} onPress={handleShareDocx}>
            <Text style={styles.exportBtnText}>Share DOCX</Text>
          </TouchableOpacity>
        </View>
      )}

      <Card style={styles.resultBlock}>
        <Text style={styles.sectionTitle}>Cluster Insights</Text>
        <Text style={styles.sectionContent}>{analysisResult?.cluster_insights}</Text>
      </Card>

      <Card style={styles.resultBlock}>
        <Text style={styles.sectionTitle}>Strengths</Text>
        {analysisResult?.strengths?.map((item: string, index: number) => (
          <Text key={index} style={styles.bulletText}>• {item}</Text>
        ))}
      </Card>

      <Card style={styles.resultBlock}>
        <Text style={styles.sectionTitle}>Concerns</Text>
        {analysisResult?.concerns?.map((item: string, index: number) => (
          <Text key={index} style={styles.bulletText}>• {item}</Text>
        ))}
      </Card>

      <Card style={styles.resultBlock}>
        <Text style={styles.sectionTitle}>Recommendations</Text>
        {analysisResult?.recommendations?.map((item: string, index: number) => (
          <Text key={index} style={styles.bulletText}>• {item}</Text>
        ))}
      </Card>

      <Card style={styles.resultBlock}>
        <Text style={styles.sectionTitle}>Action Plan</Text>
        {analysisResult?.action_plan?.map((item: string, index: number) => (
          <Text key={index} style={styles.bulletText}>• {item}</Text>
        ))}
      </Card>

      <Card style={styles.resultBlock}>
        <Text style={styles.sectionTitle}>School Breakdown</Text>
        {analysisResult?.school_breakdown?.map((school: any) => (
          <View key={school.school_id} style={styles.breakdownRow}>
            <Text style={styles.breakdownSchool}>{school.school_name}</Text>
            <Text style={styles.breakdownMeta}>Score: {school.health_score.toFixed(1)} | Grade: {school.health_score >= 80 ? 'A' : school.health_score >= 65 ? 'B' : school.health_score >= 50 ? 'C' : 'D'}</Text>
          </View>
        ))}
      </Card>

      <Button title="Analyze Another Cluster" variant="outline" onPress={() => setAnalysisResult(null)} fullWidth style={{ marginTop: Spacing.sm }} />
    </ScrollView>
  );
  };

  if (!user?.mandal_id) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="School Health Analyzer" subtitle="MEO only" onBack={() => navigation.goBack()} />
        <EmptyState icon="ban" title="Mandal not assigned" description="Your user account needs a mandal assignment to use this feature." />
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="School Health Analyzer" subtitle="MEO only" onBack={() => navigation.goBack()} />
        <LoadingSpinner message="Loading mandal schools…" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
        <Header title="School Health Analyzer" subtitle="MEO only" onBack={() => navigation.goBack()} />
        <EmptyState icon="warning" title="Unable to load schools" description="Try again later or contact support." />
      </View>
    );
  }

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}> 
      <Header title="School Health Analyzer" subtitle="MEO cluster health" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionLabel}>Select up to {MAX_SELECTION} schools</Text>
        {mandalOverview?.schools?.map((school: any) => renderSchoolTile(school))}

        <Card style={styles.infoCard}>
          <Text style={styles.infoText}>This analyzer compares the selected schools and generates cluster-level strengths, risks, and action steps for the MEO portal.</Text>
        </Card>

        <Button
          title={isAnalyzing ? 'Analyzing school health…' : 'Run School Health Analysis'}
          onPress={runAnalysis}
          loading={isAnalyzing}
          fullWidth
          size="lg"
          style={styles.generateBtn}
        />

        {analysisResult ? renderResult() : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#f5f7fb' },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  sectionLabel: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginBottom: Spacing.sm, fontWeight: Typography.weights.semibold },
  schoolTile: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.sm,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  schoolTileActive: {
    borderColor: '#2563eb',
    backgroundColor: '#eff6ff',
  },
  schoolMeta: { flex: 1, marginRight: Spacing.sm },
  schoolName: { fontSize: Typography.sizes.md, color: Colors.neutral[900], fontWeight: Typography.weights.bold },
  schoolCode: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  schoolBadge: { borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 6 },
  schoolBadgeText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },
  infoCard: { marginVertical: Spacing.md, borderLeftWidth: 4, borderLeftColor: '#2563eb' },
  infoText: { color: Colors.neutral[700], fontSize: Typography.sizes.sm, lineHeight: 20 },
  generateBtn: { marginTop: Spacing.md },
  resultBanner: { marginTop: Spacing.md, padding: Spacing.base, backgroundColor: Colors.white, borderRadius: BorderRadius.md, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  exportRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.md, marginBottom: Spacing.sm },
  exportBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#2563eb', borderRadius: BorderRadius.md, paddingVertical: Spacing.sm, paddingHorizontal: Spacing.sm },
  exportBtnDocx: { backgroundColor: '#059669' },
  exportBtnText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },
  resultTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  resultMeta: { marginTop: Spacing.xs, color: Colors.neutral[500] },
  resultSub: { marginTop: Spacing.sm, color: Colors.neutral[600], fontSize: Typography.sizes.sm },
  resultBlock: { marginTop: Spacing.md, padding: Spacing.base },
  sectionTitle: { fontSize: Typography.sizes.sm, color: Colors.neutral[900], fontWeight: Typography.weights.bold, marginBottom: Spacing.xs },
  sectionContent: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },
  bulletText: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20, marginBottom: Spacing.xs },
  breakdownRow: { marginBottom: Spacing.sm },
  breakdownSchool: { fontSize: Typography.sizes.sm, color: Colors.neutral[900], fontWeight: Typography.weights.bold },
  breakdownMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
});
