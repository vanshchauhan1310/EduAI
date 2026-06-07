import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { circularService } from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

type Tab = 'upload' | 'history';

interface SummarySection {
  title: string;
  key: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  isList: boolean;
}

const SECTIONS: SummarySection[] = [
  { title: 'Executive Summary',       key: 'summary',                 icon: 'document-text',       color: Colors.primary[600], isList: false },
  { title: 'Key Instructions',        key: 'key_instructions',        icon: 'list',                color: '#7c3aed',           isList: true  },
  { title: 'Action Items',            key: 'action_items',            icon: 'checkmark-circle',    color: '#059669',           isList: true  },
  { title: 'Deadlines',               key: 'deadlines',               icon: 'alarm',               color: Colors.danger,       isList: true  },
  { title: 'Responsible Officers',    key: 'responsible_officers',    icon: 'people',              color: '#d97706',           isList: true  },
  { title: 'Compliance Requirements', key: 'compliance_requirements', icon: 'shield-checkmark',    color: '#0891b2',           isList: true  },
];

export default function CircularSummarizerScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [summary, setSummary] = useState<any>(null);
  const [pickedFile, setPickedFile] = useState<{ uri: string; name: string } | null>(null);

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['circular-history'],
    queryFn: () => circularService.getHistory(),
    enabled: activeTab === 'history',
  });

  const { mutate: upload, isPending: uploading } = useMutation({
    mutationFn: ({ uri, name }: { uri: string; name: string }) =>
      circularService.summarize(uri, name),
    onSuccess: (data) => {
      setSummary(data);
      queryClient.invalidateQueries({ queryKey: ['circular-history'] });
    },
    onError: () => {
      Alert.alert('Error', 'Failed to summarize the circular. Please try again.');
    },
  });

  const { mutate: exportPdf, isPending: exportingPdf } = useMutation({
    mutationFn: (id: number) => circularService.sharePdf(id),
    onSuccess: () => Alert.alert('Shared', 'Circular summary is ready to share.'),
    onError: () => Alert.alert('Share failed', 'Could not share the PDF. Please try again.'),
  });

  const pickFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: 'application/pdf',
      copyToCacheDirectory: true,
    });
    if (!result.canceled && result.assets?.[0]) {
      const asset = result.assets[0];
      setPickedFile({ uri: asset.uri, name: asset.name });
      setSummary(null);
    }
  };

  const handleUpload = () => {
    if (!pickedFile) return;
    upload({ uri: pickedFile.uri, name: pickedFile.name });
  };

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Circular Summarizer" subtitle="AI-Powered PDF Analysis" onBack={() => navigation.goBack()} />

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['upload', 'history'] as Tab[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Ionicons
              name={tab === 'upload' ? 'cloud-upload-outline' : 'time-outline'}
              size={16}
              color={activeTab === tab ? Colors.primary[600] : Colors.neutral[400]}
            />
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab === 'upload' ? 'Upload' : 'History'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeTab === 'upload' ? (
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {!summary ? (
            <>
              {/* Drop Zone */}
              <TouchableOpacity style={styles.dropZone} onPress={pickFile} activeOpacity={0.8}>
                <View style={styles.dropIcon}>
                  <Ionicons name="cloud-upload" size={48} color={Colors.primary[600]} />
                </View>
                <Text style={styles.dropTitle}>
                  {pickedFile ? pickedFile.name : 'Upload Government Circular'}
                </Text>
                <Text style={styles.dropSub}>
                  {pickedFile ? 'Tap to change file' : 'Tap to select a PDF file (max 20 MB)'}
                </Text>
                {pickedFile && (
                  <View style={styles.fileChip}>
                    <Ionicons name="document" size={14} color={Colors.primary[600]} />
                    <Text style={styles.fileChipText}>{pickedFile.name}</Text>
                  </View>
                )}
              </TouchableOpacity>

              {pickedFile && (
                <Button
                  title={uploading ? 'Analysing with AI...' : 'Summarize Circular'}
                  onPress={handleUpload}
                  loading={uploading}
                  disabled={uploading}
                  fullWidth
                  size="lg"
                  style={styles.uploadBtn}
                />
              )}

              {uploading && (
                <Card style={styles.processingCard}>
                  <ActivityIndicator color={Colors.primary[600]} />
                  <View style={styles.processingText}>
                    <Text style={styles.processingTitle}>AI is processing your circular...</Text>
                    <Text style={styles.processingSub}>Extracting text, analysing instructions, structuring action items</Text>
                  </View>
                </Card>
              )}

              {/* How it works */}
              <Card style={styles.howCard}>
                <Text style={styles.howTitle}>How it works</Text>
                {[
                  { step: '1', text: 'Upload a PDF circular from the Education Dept.' },
                  { step: '2', text: 'AI extracts and analyses the full text' },
                  { step: '3', text: 'Get a structured summary: instructions, deadlines & actions' },
                  { step: '4', text: 'Download the summary as PDF for records' },
                ].map((s) => (
                  <View key={s.step} style={styles.howStep}>
                    <View style={styles.stepNum}>
                      <Text style={styles.stepNumText}>{s.step}</Text>
                    </View>
                    <Text style={styles.stepText}>{s.text}</Text>
                  </View>
                ))}
              </Card>
            </>
          ) : (
            /* Summary Result */
            <>
              <View style={styles.resultHeader}>
                <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
                <Text style={styles.resultTitle}>Summary Generated!</Text>
                <Text style={styles.resultFile}>{summary.file_name}</Text>
              </View>

              {SECTIONS.map((section) => {
                const value = summary.summary_json?.[section.key];
                if (!value || (Array.isArray(value) && value.length === 0)) return null;
                return (
                  <Card key={section.key} style={styles.sectionCard}>
                    <View style={styles.sectionHeader}>
                      <View style={[styles.sectionIcon, { backgroundColor: `${section.color}18` }]}>
                        <Ionicons name={section.icon} size={18} color={section.color} />
                      </View>
                      <Text style={[styles.sectionTitle, { color: section.color }]}>{section.title}</Text>
                    </View>
                    {section.isList ? (
                      (value as string[]).map((item: string, idx: number) => (
                        <View key={idx} style={styles.bulletRow}>
                          <View style={[styles.bullet, { backgroundColor: section.color }]} />
                          <Text style={styles.bulletText}>{item}</Text>
                        </View>
                      ))
                    ) : (
                      <Text style={styles.summaryText}>{value as string}</Text>
                    )}
                  </Card>
                );
              })}

              <View style={styles.resultActions}>
                <Button
                  title="New Circular"
                  variant="outline"
                  onPress={() => { setSummary(null); setPickedFile(null); }}
                  style={styles.actionBtn}
                />
                <Button
                  title={exportingPdf ? 'Sharing...' : 'Export PDF'}
                  loading={exportingPdf}
                  onPress={() => summary?.id && exportPdf(summary.id)}
                  style={styles.actionBtn}
                />
              </View>
            </>
          )}
        </ScrollView>
      ) : (
        /* History Tab */
        historyLoading ? (
          <LoadingSpinner message="Loading history…" />
        ) : history.length === 0 ? (
          <EmptyState icon="document-text-outline" title="No History" description="Upload your first circular to get started." />
        ) : (
          <ScrollView contentContainerStyle={styles.scroll}>
            {history.map((item: any) => (
              <TouchableOpacity
                key={item.id}
                style={styles.historyCard}
                onPress={() => {
                  circularService.getById(item.id).then((data) => {
                    setSummary(data);
                    setActiveTab('upload');
                  });
                }}
              >
                <Ionicons name="document-text" size={24} color={Colors.primary[600]} />
                <View style={styles.historyInfo}>
                  <Text style={styles.historyName} numberOfLines={1}>{item.file_name}</Text>
                  <Text style={styles.historyPreview} numberOfLines={2}>{item.summary_preview}</Text>
                  <Text style={styles.historyDate}>{new Date(item.created_at).toLocaleDateString('en-IN')}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={Colors.neutral[400]} />
              </TouchableOpacity>
            ))}
          </ScrollView>
        )
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  tabs: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  tab: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: Spacing.md, paddingVertical: 8, borderRadius: BorderRadius.full, backgroundColor: Colors.neutral[100] },
  tabActive: { backgroundColor: Colors.primary[50] },
  tabText: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], fontWeight: Typography.weights.medium },
  tabTextActive: { color: Colors.primary[600], fontWeight: Typography.weights.bold },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },

  dropZone: {
    borderWidth: 2,
    borderColor: Colors.primary[200],
    borderStyle: 'dashed',
    borderRadius: 20,
    backgroundColor: Colors.primary[50],
    padding: Spacing['2xl'],
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  dropIcon: { width: 80, height: 80, borderRadius: 40, backgroundColor: Colors.primary[100], justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.md },
  dropTitle: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.neutral[800], textAlign: 'center' },
  dropSub: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 4, textAlign: 'center' },
  fileChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: Spacing.md,
    backgroundColor: Colors.primary[100],
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
  },
  fileChipText: { fontSize: Typography.sizes.sm, color: Colors.primary[700], fontWeight: Typography.weights.medium },
  uploadBtn: { marginBottom: Spacing.lg },

  processingCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.lg, backgroundColor: Colors.primary[50] },
  processingText: { flex: 1 },
  processingTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.primary[700] },
  processingSub: { fontSize: Typography.sizes.sm, color: Colors.primary[500], marginTop: 2 },

  howCard: { backgroundColor: Colors.neutral[50] },
  howTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginBottom: Spacing.md },
  howStep: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.md, marginBottom: Spacing.md },
  stepNum: { width: 28, height: 28, borderRadius: 14, backgroundColor: Colors.primary[600], justifyContent: 'center', alignItems: 'center' },
  stepNumText: { color: Colors.white, fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  stepText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20 },

  resultHeader: { alignItems: 'center', marginBottom: Spacing.lg, gap: 4 },
  resultTitle: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  resultFile: { fontSize: Typography.sizes.sm, color: Colors.neutral[500] },

  sectionCard: { marginBottom: Spacing.sm },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  sectionIcon: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  sectionTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  bulletRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: 6, alignItems: 'flex-start' },
  bullet: { width: 6, height: 6, borderRadius: 3, marginTop: 6 },
  bulletText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 20 },
  summaryText: { fontSize: Typography.sizes.base, color: Colors.neutral[700], lineHeight: 22 },

  resultActions: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.md, flexWrap: 'wrap' },
  actionBtn: { flex: 1 },
  shareBtn: { marginTop: Spacing.sm },

  historyCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    ...Shadows.sm,
  },
  historyInfo: { flex: 1 },
  historyName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  historyPreview: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], marginTop: 2, lineHeight: 18 },
  historyDate: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 4 },
});
