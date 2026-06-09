import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, TextInput, Switch, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import EmptyState from '../../components/common/EmptyState';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { TUTOR_CURRICULUM } from '../../constants';
import { useKnowledgeBaseSources, useIngestPdf, useSearchKnowledgeBase } from '../../hooks/useAiTutor';
import { KnowledgeBaseSource } from '../../types';

export default function TutorKnowledgeBaseScreen({ route, navigation }: any) {
  const insets = useSafeAreaInsets();
  const subjects = Object.keys(TUTOR_CURRICULUM);
  const [subject, setSubject] = useState<string>(route.params?.subject ?? subjects[0]);
  const chapters = Object.keys(TUTOR_CURRICULUM[subject].chapters);
  const [chapter, setChapter] = useState<string>(route.params?.chapter ?? chapters[0]);

  const [pickedFile, setPickedFile] = useState<{ uri: string; name: string } | null>(null);
  const [useOcr, setUseOcr] = useState(false);
  const [pageStart, setPageStart] = useState('1');
  const [pageEnd, setPageEnd] = useState('20');
  const [progress, setProgress] = useState(0);

  const [previewQuery, setPreviewQuery] = useState('');

  const sourcesQuery = useKnowledgeBaseSources();
  const ingestMutation = useIngestPdf();
  const previewMutation = useSearchKnowledgeBase();

  const sources = sourcesQuery.data ?? [];
  const hasSources = sources.length > 0;

  const pickFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: 'application/pdf', copyToCacheDirectory: true });
    if (!result.canceled && result.assets?.[0]) {
      const asset = result.assets[0];
      setPickedFile({ uri: asset.uri, name: asset.name });
      ingestMutation.reset();
      setProgress(0);
    }
  };

  const handleUpload = () => {
    if (!pickedFile) return;
    setProgress(0);
    ingestMutation.mutate({
      fileUri: pickedFile.uri,
      fileName: pickedFile.name,
      opts: {
        subject, chapter, useOcr,
        pageStart: useOcr ? Number(pageStart) || 1 : undefined,
        pageEnd: useOcr ? Number(pageEnd) || 20 : undefined,
      },
      onProgress: setProgress,
    }, {
      onError: () => Alert.alert('Upload failed', 'Could not process this PDF. Please try a different file or try again.'),
    });
  };

  const result = ingestMutation.data;

  const onPreview = () => {
    if (!previewQuery.trim()) return;
    previewMutation.mutate(previewQuery.trim());
  };

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <Header title="My Study Material" subtitle="Ground your lessons in your own textbook" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing['2xl'] }]} showsVerticalScrollIndicator={false}>
        {/* ── Status banner ──────────────────────────────────────────── */}
        <View style={[styles.banner, hasSources ? styles.bannerGood : styles.bannerNeutral]}>
          <Ionicons name={hasSources ? 'shield-checkmark' : 'information-circle'} size={20} color={hasSources ? Colors.success : Colors.neutral[500]} />
          <Text style={[styles.bannerText, { color: hasSources ? '#166534' : Colors.neutral[600] }]}>
            {hasSources
              ? `Grounded in ${sources.length} uploaded source${sources.length > 1 ? 's' : ''} — your lessons & quizzes draw from these first.`
              : 'No material uploaded yet — your tutor is using built-in notes. Add your textbook chapter for lessons tailored exactly to what your school teaches.'}
          </Text>
        </View>

        {/* ── Upload card ────────────────────────────────────────────── */}
        <Text style={styles.sectionTitle}>Add a chapter or notes</Text>
        <Card style={styles.uploadCard}>
          <Text style={styles.fieldLabel}>Subject</Text>
          <View style={styles.pillRow}>
            {subjects.map((s) => {
              const active = s === subject;
              return (
                <TouchableOpacity key={s} onPress={() => { setSubject(s); setChapter(Object.keys(TUTOR_CURRICULUM[s].chapters)[0]); }}
                  style={[styles.pill, active && styles.pillActive]} activeOpacity={0.85}>
                  <Text style={[styles.pillText, active && styles.pillTextActive]}>{s}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text style={styles.fieldLabel}>Chapter</Text>
          <View style={styles.pillRow}>
            {chapters.map((c) => {
              const active = c === chapter;
              return (
                <TouchableOpacity key={c} onPress={() => setChapter(c)} style={[styles.pill, active && styles.pillActive]} activeOpacity={0.85}>
                  <Text style={[styles.pillText, active && styles.pillTextActive]} numberOfLines={1}>{c}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <TouchableOpacity style={styles.dropZone} onPress={pickFile} activeOpacity={0.8}>
            <View style={styles.dropIcon}>
              <Ionicons name="cloud-upload" size={36} color={Colors.secondary[600]} />
            </View>
            <Text style={styles.dropTitle} numberOfLines={1}>{pickedFile ? pickedFile.name : 'Select a PDF (chapter, notes or scanned pages)'}</Text>
            <Text style={styles.dropSub}>{pickedFile ? 'Tap to choose a different file' : 'Tap to browse · max ~20 MB'}</Text>
          </TouchableOpacity>

          <View style={styles.ocrRow}>
            <View style={styles.ocrTextBlock}>
              <Text style={styles.fieldLabel}>Use OCR</Text>
              <Text style={styles.ocrHint}>Turn this on for scanned pages or phone photos — we'll read the text out of the images (slower, page-by-page).</Text>
            </View>
            <Switch
              value={useOcr}
              onValueChange={setUseOcr}
              trackColor={{ false: Colors.neutral[200], true: '#ddd6fe' }}
              thumbColor={useOcr ? Colors.secondary[600] : Colors.neutral[50]}
            />
          </View>

          {useOcr && (
            <View style={styles.pageRangeRow}>
              <View style={styles.pageField}>
                <Text style={styles.fieldLabel}>From page</Text>
                <TextInput style={styles.pageInput} value={pageStart} onChangeText={setPageStart} keyboardType="number-pad" placeholder="1" placeholderTextColor={Colors.neutral[400]} />
              </View>
              <View style={styles.pageField}>
                <Text style={styles.fieldLabel}>To page</Text>
                <TextInput style={styles.pageInput} value={pageEnd} onChangeText={setPageEnd} keyboardType="number-pad" placeholder="20" placeholderTextColor={Colors.neutral[400]} />
              </View>
            </View>
          )}

          {ingestMutation.isPending && (
            <View style={styles.progressBlock}>
              <View style={styles.progressBg}>
                <View style={[styles.progressFill, { width: `${Math.round(progress * 100)}%` }]} />
              </View>
              <Text style={styles.progressLabel}>
                {useOcr ? 'Reading pages with OCR…' : 'Uploading & indexing…'} {Math.round(progress * 100)}%
              </Text>
            </View>
          )}

          {result && (
            <View style={[styles.resultBanner, result.success ? styles.resultBannerGood : styles.resultBannerBad]}>
              <Ionicons name={result.success ? 'checkmark-circle' : 'alert-circle'} size={18} color={result.success ? Colors.success : Colors.danger} />
              <Text style={[styles.resultBannerText, { color: result.success ? '#166534' : '#991b1b' }]}>
                {result.success
                  ? `Indexed “${result.source}” — ${result.pages} page${result.pages === 1 ? '' : 's'}, ${result.chunks} chunks ready for grounding.`
                  : (result.error || 'Could not extract readable text from this PDF.')}
              </Text>
            </View>
          )}

          <Button
            title={ingestMutation.isPending ? 'Processing…' : '📤 Add to my study material'}
            onPress={handleUpload}
            loading={ingestMutation.isPending}
            disabled={!pickedFile || ingestMutation.isPending}
            size="lg" fullWidth style={styles.ctaPrimary}
          />
        </Card>

        {/* ── My uploaded material ───────────────────────────────────── */}
        <Text style={styles.sectionTitle}>My uploaded material</Text>
        {sourcesQuery.isLoading ? (
          <Card style={styles.loadingCard}><Text style={styles.loadingText}>Loading your material…</Text></Card>
        ) : !hasSources ? (
          <Card padding="lg">
            <EmptyState icon="library-outline" title="Nothing uploaded yet" description="Add your first chapter above to see it listed here, ready to ground your lessons." />
          </Card>
        ) : (
          sources.map((s: KnowledgeBaseSource) => (
            <Card key={s.id} style={styles.sourceCard}>
              <View style={styles.sourceIconWrap}>
                <Ionicons name="document-text" size={20} color={Colors.secondary[600]} />
              </View>
              <View style={styles.sourceInfo}>
                <Text style={styles.sourceName} numberOfLines={1}>{s.source}</Text>
                <Text style={styles.sourceMeta}>{s.subject} · {s.chapter} · {s.chunks} chunks</Text>
                <Text style={styles.sourceDate}>Added {new Date(s.uploaded_at).toLocaleDateString('en-IN')}</Text>
              </View>
              <View style={styles.groundedBadge}>
                <Ionicons name="document" size={11} color={Colors.secondary[600]} />
              </View>
            </Card>
          ))
        )}

        {/* ── RAG preview search ─────────────────────────────────────── */}
        <Text style={styles.sectionTitle}>🔎 Preview what the tutor sees</Text>
        <Card style={styles.previewCard}>
          <Text style={styles.previewHint}>Type a question to see the exact passages the tutor would retrieve to ground its answer — a quick way to sanity-check your uploaded material.</Text>
          <View style={styles.previewInputRow}>
            <TextInput
              style={styles.previewInput}
              value={previewQuery}
              onChangeText={setPreviewQuery}
              placeholder="e.g. What is Ohm's law?"
              placeholderTextColor={Colors.neutral[400]}
              onSubmitEditing={onPreview}
              returnKeyType="search"
            />
            <TouchableOpacity style={styles.previewSearchBtn} onPress={onPreview} disabled={!previewQuery.trim() || previewMutation.isPending}>
              <Ionicons name="search" size={18} color={Colors.white} />
            </TouchableOpacity>
          </View>

          {previewMutation.isPending && <Text style={styles.previewStatus}>Searching your knowledge bank…</Text>}
          {previewMutation.isSuccess && (
            previewMutation.data.length === 0 ? (
              <Text style={styles.previewStatus}>No close matches — the tutor would fall back to built-in notes for this query.</Text>
            ) : (
              <View style={styles.previewResults}>
                {previewMutation.data.map((r, i) => (
                  <View key={i} style={styles.previewResultRow}>
                    <Ionicons name={r.kind === 'pdf' ? 'document-text' : 'create'} size={14} color={Colors.secondary[600]} />
                    <View style={styles.previewResultText}>
                      <Text style={styles.previewResultMeta}>{r.concept} · {Math.round(r.score * 100)}% match{r.source ? ` · ${r.source}` : ''}</Text>
                      <Text style={styles.previewResultExcerpt} numberOfLines={3}>{r.text}</Text>
                    </View>
                  </View>
                ))}
              </View>
            )
          )}
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, gap: Spacing.md },

  banner: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm, borderRadius: BorderRadius.lg, padding: Spacing.md },
  bannerGood: { backgroundColor: '#dcfce7' },
  bannerNeutral: { backgroundColor: Colors.neutral[100] },
  bannerText: { flex: 1, fontSize: Typography.sizes.sm, lineHeight: 20 },

  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginTop: Spacing.xs },

  uploadCard: { gap: Spacing.sm },
  fieldLabel: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[500], textTransform: 'uppercase', letterSpacing: 0.4 },
  pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs },
  pill: { backgroundColor: Colors.neutral[100], borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 6, maxWidth: 220 },
  pillActive: { backgroundColor: Colors.secondary[600] },
  pillText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  pillTextActive: { color: Colors.white },

  dropZone: { borderWidth: 2, borderColor: '#ddd6fe', borderStyle: 'dashed', borderRadius: BorderRadius.lg, backgroundColor: `${Colors.secondary[600]}08`, padding: Spacing.lg, alignItems: 'center', marginTop: Spacing.xs },
  dropIcon: { width: 64, height: 64, borderRadius: 32, backgroundColor: Colors.white, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.sm, ...Shadows.sm },
  dropTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[800], textAlign: 'center', maxWidth: '100%' },
  dropSub: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2, textAlign: 'center' },

  ocrRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginTop: Spacing.xs },
  ocrTextBlock: { flex: 1, gap: 2 },
  ocrHint: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], lineHeight: 16 },

  pageRangeRow: { flexDirection: 'row', gap: Spacing.sm },
  pageField: { flex: 1, gap: 4 },
  pageInput: { backgroundColor: Colors.neutral[50], borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.md, paddingHorizontal: Spacing.sm, paddingVertical: Spacing.xs + 2, fontSize: Typography.sizes.sm, color: Colors.neutral[800] },

  progressBlock: { gap: 6 },
  progressBg: { height: 6, backgroundColor: Colors.neutral[100], borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: Colors.secondary[600], borderRadius: 3 },
  progressLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], fontWeight: Typography.weights.medium },

  resultBanner: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.sm, borderRadius: BorderRadius.md, padding: Spacing.sm },
  resultBannerGood: { backgroundColor: '#dcfce7' },
  resultBannerBad: { backgroundColor: '#fee2e2' },
  resultBannerText: { flex: 1, fontSize: Typography.sizes.xs, lineHeight: 17, fontWeight: Typography.weights.medium },

  ctaPrimary: { backgroundColor: Colors.secondary[600], marginTop: Spacing.xs },

  loadingCard: { alignItems: 'center', paddingVertical: Spacing.lg },
  loadingText: { fontSize: Typography.sizes.sm, color: Colors.neutral[400] },

  sourceCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  sourceIconWrap: { width: 40, height: 40, borderRadius: BorderRadius.md, backgroundColor: `${Colors.secondary[600]}14`, justifyContent: 'center', alignItems: 'center' },
  sourceInfo: { flex: 1, gap: 1 },
  sourceName: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  sourceMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500] },
  sourceDate: { fontSize: Typography.sizes.xs - 1, color: Colors.neutral[400] },
  groundedBadge: { width: 26, height: 26, borderRadius: 13, backgroundColor: `${Colors.secondary[600]}16`, justifyContent: 'center', alignItems: 'center' },

  previewCard: { gap: Spacing.sm },
  previewHint: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], lineHeight: 17 },
  previewInputRow: { flexDirection: 'row', gap: Spacing.sm },
  previewInput: { flex: 1, backgroundColor: Colors.neutral[50], borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.lg, paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm, fontSize: Typography.sizes.sm, color: Colors.neutral[900] },
  previewSearchBtn: { width: 44, height: 44, borderRadius: BorderRadius.lg, backgroundColor: Colors.secondary[600], justifyContent: 'center', alignItems: 'center' },
  previewStatus: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], fontStyle: 'italic' },
  previewResults: { gap: Spacing.sm, paddingTop: Spacing.xs, borderTopWidth: 1, borderTopColor: Colors.neutral[100] },
  previewResultRow: { flexDirection: 'row', gap: Spacing.xs, alignItems: 'flex-start' },
  previewResultText: { flex: 1 },
  previewResultMeta: { fontSize: Typography.sizes.xs - 1, fontWeight: Typography.weights.semibold, color: Colors.neutral[700] },
  previewResultExcerpt: { fontSize: Typography.sizes.xs - 1, color: Colors.neutral[500], lineHeight: 15, marginTop: 1 },
});
