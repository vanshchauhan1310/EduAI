/**
 * TranslationScreen — Document Translator for HM Portal
 *
 * Features:
 * 1. Upload PDF/DOCX/TXT document
 * 2. Select source language (English/Telugu)
 * 3. Select target language (Telugu/English)
 * 4. Select document type (Circular/Letter/Notice/Report/General)
 * 5. "Translate Document" button → extracts text → translates
 * 6. Side-by-side preview: original + translated text
 * 7. Copy translated text
 * 8. Text-to-text translation tab (fallback)
 */

import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  Clipboard,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import { translationService } from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

type Lang = 'English' | 'Telugu';
type DocType = 'Circular' | 'Letter' | 'Notice' | 'Report' | 'General';
type Tab = 'document' | 'text' | 'history';

const DOC_TYPES: DocType[] = ['Circular', 'Letter', 'Notice', 'Report', 'General'];
const CHAR_LIMIT = 10_000;

export default function TranslationScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const queryClient = useQueryClient();

  // Tab state
  const [tab, setTab] = useState<Tab>('document');

  // Text translation state (existing)
  const [sourceLang, setSourceLang] = useState<Lang>('Telugu');
  const [targetLang, setTargetLang] = useState<Lang>('English');
  const [inputText, setInputText] = useState('');
  const [textResult, setTextResult] = useState<any>(null);

  // Document translation state
  const [docSourceLang, setDocSourceLang] = useState<Lang>('English');
  const [docTargetLang, setDocTargetLang] = useState<Lang>('Telugu');
  const [docType, setDocType] = useState<DocType>('General');
  const [selectedFile, setSelectedFile] = useState<{ uri: string; name: string; type: string } | null>(null);
  const [docResult, setDocResult] = useState<any>(null);
  const [showOriginal, setShowOriginal] = useState(true);

  // History
  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['translation-history'],
    queryFn: () => translationService.getHistory(),
    enabled: tab === 'history',
  });

  // Text translation mutation
  const { mutate: translateText, isPending: textTranslating } = useMutation({
    mutationFn: () => translationService.translate({
      source_language: sourceLang,
      target_language: targetLang,
      text: inputText,
    }),
    onSuccess: (data) => {
      setTextResult(data);
      queryClient.invalidateQueries({ queryKey: ['translation-history'] });
    },
    onError: () => Alert.alert('Error', 'Translation failed. Please try again.'),
  });

  // Document translation mutation
  const { mutate: translateDoc, isPending: docTranslating } = useMutation({
    mutationFn: () => translationService.translateDocument(
      selectedFile!,
      docSourceLang,
      docTargetLang,
      docType,
    ),
    onSuccess: (data) => {
      setDocResult(data);
      setShowOriginal(false);
      queryClient.invalidateQueries({ queryKey: ['translation-history'] });
    },
    onError: (error: any) => {
      Alert.alert('Translation Failed', error?.response?.data?.detail || error?.message || 'Failed to translate document');
    },
  });


  const swapLanguages = () => {
    const prev = sourceLang;
    setSourceLang(targetLang);
    setTargetLang(prev);
    if (textResult) {
      setInputText(textResult.translated_text);
      setTextResult(null);
    }
  };

  const swapDocLanguages = () => {
    const prev = docSourceLang;
    setDocSourceLang(docTargetLang);
    setDocTargetLang(prev);
  };

  const copyToClipboard = (text: string) => {
    Clipboard.setString(text);
    Alert.alert('Copied!', 'Text copied to clipboard.');
  };

  const handlePickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: [
          'application/pdf',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'application/msword',
          'text/plain',
        ],
        copyToCacheDirectory: true,
      });
      if (result.canceled || !result.assets?.[0]) return;
      const file = result.assets[0];
      setSelectedFile({
        uri: file.uri,
        name: file.name || 'document',
        type: file.mimeType || 'application/octet-stream',
      });
      setDocResult(null);
    } catch (error: any) {
      Alert.alert('Error', error?.message || 'Failed to pick file');
    }
  };

  const getFileIcon = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return 'document-text-outline';
    if (ext === 'docx' || ext === 'doc') return 'document-text-outline';
    return 'document-outline';
  };

  const getFileColor = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return '#ef4444';
    if (ext === 'docx' || ext === 'doc') return '#2f6df6';
    return '#8090aa';
  };

  const openHistoryItem = async (item: any) => {
    if (item.type === 'document') {
      try {
        const data = await translationService.getDocumentTranslation(item.id);
        setDocResult(data);
        setDocSourceLang(data.source_language);
        setDocTargetLang(data.target_language);
        if (data.document_type) setDocType(data.document_type);
        setSelectedFile({ uri: '', name: data.file_name, type: 'application/octet-stream' });
        setShowOriginal(false);
        setTab('document');
      } catch (error: any) {
        Alert.alert('Error', error?.response?.data?.detail || 'Could not open document translation.');
      }
      return;
    }

    setInputText(item.source_text || item.preview || '');
    setSourceLang(item.source_language);
    setTargetLang(item.target_language);
    setTextResult(null);
    setTab('text');
  };

  const renderHistorySection = (items: any[], title: string, emptyMessage: string, isDocument = false) => (
    <View style={styles.historySection}>
      <Text style={styles.historySectionTitle}>{title}</Text>
      {items.length === 0 ? (
        <View style={styles.historyEmptyRow}>
          <Text style={styles.historyEmptyText}>{emptyMessage}</Text>
        </View>
      ) : items.map((item: any) => (
        <TouchableOpacity key={item.id} style={styles.historyCard} onPress={() => openHistoryItem(item)}>
          <View style={styles.historyLangPair}>
            <Text style={styles.historyLang}>{item.source_language?.slice(0, 2).toUpperCase()}</Text>
            <Ionicons name="arrow-forward" size={12} color={Colors.neutral[400]} />
            <Text style={styles.historyLang}>{item.target_language?.slice(0, 2).toUpperCase()}</Text>
          </View>
          <View style={styles.historyInfo}>
            <View style={styles.historyRowTop}>
              <Text style={styles.historyTitle} numberOfLines={1}>
                {isDocument ? item.file_name || 'Document translation' : 'Text translation'}
              </Text>
              <View style={[styles.historyBadge, isDocument ? styles.historyBadgeDoc : styles.historyBadgeLight]}>
                <Text style={styles.historyBadgeLabel}>{isDocument ? 'Document' : 'Text'}</Text>
              </View>
            </View>
            {isDocument && item.document_type ? (
              <Text style={styles.historySubTitle}>{item.document_type}</Text>
            ) : null}
            <Text style={styles.historyPreview} numberOfLines={3}>{item.preview}</Text>
            <View style={styles.historyMetaRow}>
              <Text style={styles.historyMeta}>{item.word_count ? `${item.word_count} words · ` : ''}</Text>
              <Text style={styles.historyMeta}>{new Date(item.created_at).toLocaleDateString('en-IN')}</Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={18} color={Colors.neutral[300]} />
        </TouchableOpacity>
      ))}
    </View>
  );

  // ── Render: Document Translate Tab ──
  const renderDocumentTab = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      {/* Language Selector */}
      <View style={styles.langRow}>
        <View style={styles.langBox}>
          <Text style={styles.langBoxLabel}>From</Text>
          {(['English', 'Telugu'] as Lang[]).map((l) => (
            <TouchableOpacity
              key={l}
              style={[styles.langChip, docSourceLang === l && styles.langChipActive]}
              onPress={() => { if (l !== docTargetLang) setDocSourceLang(l); }}
            >
              <Text style={[styles.langChipText, docSourceLang === l && styles.langChipTextActive]}>
                {l === 'Telugu' ? '🇮🇳 తెలుగు' : '🇬🇧 English'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.swapBtn} onPress={swapDocLanguages}>
          <Ionicons name="swap-horizontal" size={22} color={Colors.primary[600]} />
        </TouchableOpacity>

        <View style={styles.langBox}>
          <Text style={styles.langBoxLabel}>To</Text>
          {(['English', 'Telugu'] as Lang[]).map((l) => (
            <TouchableOpacity
              key={l}
              style={[styles.langChip, docTargetLang === l && styles.langChipActive]}
              onPress={() => { if (l !== docSourceLang) setDocTargetLang(l); }}
            >
              <Text style={[styles.langChipText, docTargetLang === l && styles.langChipTextActive]}>
                {l === 'Telugu' ? '🇮🇳 తెలుగు' : '🇬🇧 English'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Document Type Selector */}
      <Text style={styles.sectionLabel}>Document Type</Text>
      <View style={styles.docTypeRow}>
        {DOC_TYPES.map((dt) => (
          <TouchableOpacity
            key={dt}
            style={[styles.docTypeChip, docType === dt && styles.docTypeChipActive]}
            onPress={() => setDocType(dt)}
          >
            <Text style={[styles.docTypeText, docType === dt && styles.docTypeTextActive]}>{dt}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* File Picker */}
      <TouchableOpacity style={styles.filePicker} onPress={handlePickDocument}>
        <Ionicons name="cloud-upload-outline" size={32} color={selectedFile ? '#2f6df6' : '#8090aa'} />
        <Text style={styles.filePickerTitle}>
          {selectedFile ? 'Tap to change file' : 'Upload Document'}
        </Text>
        <Text style={styles.filePickerSubtitle}>
          Supports PDF, DOCX, DOC, TXT files
        </Text>
      </TouchableOpacity>

      {/* Selected File Info */}
      {selectedFile && (
        <View style={styles.selectedFileCard}>
          <View style={[styles.fileIconWrap, { backgroundColor: getFileColor(selectedFile.name) + '20' }]}>
            <Ionicons name={getFileIcon(selectedFile.name) as any} size={24} color={getFileColor(selectedFile.name)} />
          </View>
          <View style={styles.fileInfo}>
            <Text style={styles.fileName} numberOfLines={1}>{selectedFile.name}</Text>
            <Text style={styles.fileHint}>Ready for translation</Text>
          </View>
          <TouchableOpacity onPress={() => { setSelectedFile(null); setDocResult(null); }}>
            <Ionicons name="close-circle" size={22} color="#8090aa" />
          </TouchableOpacity>
        </View>
      )}

      {/* Translate Button */}
      <TouchableOpacity
        style={[
          styles.translateBtn,
          (!selectedFile || docTranslating) && styles.translateBtnDisabled,
        ]}
        onPress={() => translateDoc()}
        disabled={!selectedFile || docTranslating}
      >
        {docTranslating ? (
          <ActivityIndicator size="small" color="#fff" />
        ) : (
          <Ionicons name="language-outline" size={20} color="#fff" />
        )}
        <Text style={styles.translateBtnText}>
          {docTranslating
            ? 'Extracting & Translating...'
            : `Translate to ${docTargetLang}`}
        </Text>
      </TouchableOpacity>

      {/* Document Result */}
      {docResult && (
        <>
          {/* Original / Translated Toggle */}
          <View style={styles.resultToggle}>
            <TouchableOpacity
              style={[styles.toggleBtn, showOriginal && styles.toggleBtnActive]}
              onPress={() => setShowOriginal(true)}
            >
              <Text style={[styles.toggleText, showOriginal && styles.toggleTextActive]}>
                Original ({docSourceLang})
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleBtn, !showOriginal && styles.toggleBtnActive]}
              onPress={() => setShowOriginal(false)}
            >
              <Text style={[styles.toggleText, !showOriginal && styles.toggleTextActive]}>
                Translated ({docTargetLang})
              </Text>
            </TouchableOpacity>
          </View>

          {/* Text Content */}
          <View style={styles.docResultCard}>
            <View style={styles.docResultHeader}>
              <Text style={styles.docResultTitle}>
                {showOriginal ? 'Original Text' : 'Translated Text'}
              </Text>
              {!showOriginal && (
                <TouchableOpacity onPress={() => copyToClipboard(docResult.translated_text)}>
                  <Ionicons name="copy-outline" size={20} color={Colors.primary[600]} />
                </TouchableOpacity>
              )}
            </View>
            <Text style={styles.docResultText} selectable>
              {showOriginal ? docResult.original_text : docResult.translated_text}
            </Text>
          </View>

          {/* Meta Info */}
          <View style={styles.docMetaRow}>
            <View style={styles.docMetaItem}>
              <Text style={styles.docMetaLabel}>File</Text>
              <Text style={styles.docMetaValue}>{docResult.file_name}</Text>
            </View>
            <View style={styles.docMetaItem}>
              <Text style={styles.docMetaLabel}>Words</Text>
              <Text style={styles.docMetaValue}>{docResult.word_count}</Text>
            </View>
            <View style={styles.docMetaItem}>
              <Text style={styles.docMetaLabel}>Direction</Text>
              <Text style={styles.docMetaValue}>{docSourceLang} → {docTargetLang}</Text>
            </View>
          </View>
        </>
      )}
    </ScrollView>
  );

  // ── Render: Text Translate Tab ──
  const renderTextTab = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
      {/* Language Selector */}
      <View style={styles.langRow}>
        <View style={styles.langBox}>
          <Text style={styles.langBoxLabel}>From</Text>
          {(['Telugu', 'English'] as Lang[]).map((l) => (
            <TouchableOpacity
              key={l}
              style={[styles.langChip, sourceLang === l && styles.langChipActive]}
              onPress={() => { if (l !== targetLang) setSourceLang(l); }}
            >
              <Text style={[styles.langChipText, sourceLang === l && styles.langChipTextActive]}>
                {l === 'Telugu' ? '🇮🇳 తెలుగు' : '🇬🇧 English'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <TouchableOpacity style={styles.swapBtn} onPress={swapLanguages}>
          <Ionicons name="swap-horizontal" size={22} color={Colors.primary[600]} />
        </TouchableOpacity>
        <View style={styles.langBox}>
          <Text style={styles.langBoxLabel}>To</Text>
          {(['Telugu', 'English'] as Lang[]).map((l) => (
            <TouchableOpacity
              key={l}
              style={[styles.langChip, targetLang === l && styles.langChipActive]}
              onPress={() => { if (l !== sourceLang) setTargetLang(l); }}
            >
              <Text style={[styles.langChipText, targetLang === l && styles.langChipTextActive]}>
                {l === 'Telugu' ? '🇮🇳 తెలుగు' : '🇬🇧 English'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Input Area */}
      <View style={styles.inputCard}>
        <View style={styles.inputCardHeader}>
          <Text style={styles.inputCardTitle}>{sourceLang}</Text>
          {inputText.length > 0 && (
            <TouchableOpacity onPress={() => { setInputText(''); setTextResult(null); }}>
              <Ionicons name="close-circle" size={18} color={Colors.neutral[400]} />
            </TouchableOpacity>
          )}
        </View>
        <TextInput
          style={styles.textArea}
          value={inputText}
          onChangeText={(t) => { setInputText(t); setTextResult(null); }}
          placeholder={sourceLang === 'Telugu' ? 'ఇక్కడ టెక్స్ట్ అతికించండి...' : 'Paste or type text here...'}
          placeholderTextColor={Colors.neutral[400]}
          multiline
          textAlignVertical="top"
          maxLength={CHAR_LIMIT}
        />
        <Text style={styles.charCount}>{inputText.length.toLocaleString()} / {CHAR_LIMIT.toLocaleString()}</Text>
      </View>

      {/* Translate Button */}
      <TouchableOpacity
        style={[styles.translateBtn, (!inputText.trim() || textTranslating) && styles.translateBtnDisabled]}
        onPress={() => translateText()}
        disabled={!inputText.trim() || textTranslating}
      >
        {textTranslating ? (
          <ActivityIndicator size="small" color="#fff" />
        ) : (
          <Ionicons name="language-outline" size={20} color="#fff" />
        )}
        <Text style={styles.translateBtnText}>
          {textTranslating ? 'Translating...' : `Translate to ${targetLang}`}
        </Text>
      </TouchableOpacity>

      {/* Result */}
      {textResult && (
        <View style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <View style={styles.resultLangBadge}><Text style={styles.resultLangText}>{targetLang}</Text></View>
            <TouchableOpacity onPress={() => copyToClipboard(textResult.translated_text)}>
              <Ionicons name="copy-outline" size={20} color={Colors.primary[600]} />
            </TouchableOpacity>
          </View>
          <Text style={styles.resultText} selectable>{textResult.translated_text}</Text>
          <Text style={styles.resultMeta}>{textResult.word_count} words translated</Text>
        </View>
      )}
    </ScrollView>
  );

  // ── Render: History Tab ──
  const renderHistoryTab = () => {
    const documentHistory = history.filter((item: any) => item.type === 'document');
    const textHistory = history.filter((item: any) => item.type === 'text');

    return historyLoading ? (
      <View style={styles.loadingWrap}><ActivityIndicator size="large" color={Colors.primary[600]} /><Text style={styles.loadingText}>Loading history...</Text></View>
    ) : history.length === 0 ? (
      <View style={styles.emptyWrap}>
        <Ionicons name="language-outline" size={56} color={Colors.neutral[300]} />
        <Text style={styles.emptyTitle}>No Translations Yet</Text>
        <Text style={styles.emptySubtitle}>Translate text or documents to see your history here.</Text>
      </View>
    ) : (
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.historyHeadline}>Translation History</Text>
        <Text style={styles.historySubtitle}>Separate records for document translations and text translations.</Text>
        {renderHistorySection(documentHistory, 'Document Translation History', 'No document translation records yet. Translate a document to store the full translation here.', true)}
        {renderHistorySection(textHistory, 'Text Translation History', 'No text translation records yet. Translate text to save it here.')}
      </ScrollView>
    );
  };

  // ── Main Render ──
  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      {/* Header */}
      <View style={styles.headerBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color="#071a3a" />
        </TouchableOpacity>
        <View style={styles.headerIconWrap}>
          <Ionicons name="language-outline" size={24} color="#2f6df6" />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.headerTitle}>Document Translator</Text>
          <Text style={styles.headerSubtitle}>Telugu ↔ English document & text translation</Text>
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {([
          { key: 'document' as Tab, label: 'Document', icon: 'document-text-outline' },
          { key: 'text' as Tab, label: 'Text', icon: 'language-outline' },
          { key: 'history' as Tab, label: 'History', icon: 'time-outline' },
        ]).map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[styles.tab, tab === t.key && styles.tabActive]}
            onPress={() => setTab(t.key)}
          >
            <Ionicons name={t.icon as any} size={16} color={tab === t.key ? Colors.primary[600] : Colors.neutral[400]} />
            <Text style={[styles.tabText, tab === t.key && styles.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Tab Content */}
      {tab === 'document' ? renderDocumentTab() : tab === 'text' ? renderTextTab() : renderHistoryTab()}
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },

  // Header
  headerBar: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 12, paddingHorizontal: 16,
    backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e8edf5',
  },
  backBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#f5f7fb', alignItems: 'center', justifyContent: 'center' },
  headerIconWrap: { width: 40, height: 40, borderRadius: 10, backgroundColor: '#eff6ff', alignItems: 'center', justifyContent: 'center' },
  headerText: { flex: 1 },
  headerTitle: { color: '#071a3a', fontSize: 18, fontWeight: '700' },
  headerSubtitle: { color: '#536784', fontSize: 12, marginTop: 2 },

  // Tabs
  tabs: { flexDirection: 'row', backgroundColor: Colors.white, borderBottomWidth: 1, borderBottomColor: Colors.border, paddingHorizontal: Spacing.base, paddingVertical: Spacing.sm, gap: Spacing.sm },
  tab: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: Spacing.md, paddingVertical: 8, borderRadius: BorderRadius.full, backgroundColor: Colors.neutral[100] },
  tabActive: { backgroundColor: Colors.primary[50] },
  tabText: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], fontWeight: Typography.weights.medium },
  tabTextActive: { color: Colors.primary[600], fontWeight: Typography.weights.bold },

  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  loadingWrap: { paddingVertical: 60, alignItems: 'center' },
  loadingText: { color: '#8090aa', fontSize: 14, marginTop: 12 },
  emptyWrap: { paddingVertical: 60, alignItems: 'center', gap: 12 },
  emptyTitle: { color: '#071a3a', fontSize: 18, fontWeight: '700' },
  emptySubtitle: { color: '#8090aa', fontSize: 14, textAlign: 'center', paddingHorizontal: 40 },

  // Language Selector
  langRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  langBox: { flex: 1 },
  langBoxLabel: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[500], marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  langSelector: { gap: 6 },
  langChip: { padding: Spacing.sm, borderRadius: BorderRadius.lg, borderWidth: 1.5, borderColor: Colors.border, alignItems: 'center', backgroundColor: Colors.neutral[50], marginBottom: 4 },
  langChipActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  langChipText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  langChipTextActive: { color: Colors.primary[700], fontWeight: Typography.weights.bold },
  swapBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: Colors.primary[50], justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: Colors.primary[600], marginTop: Spacing.xl },

  // Document Type
  sectionLabel: { fontSize: 12, fontWeight: '700', color: '#6b7fa3', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  docTypeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 16 },
  docTypeChip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: '#f5f7fb', borderWidth: 1, borderColor: '#e8edf5' },
  docTypeChipActive: { backgroundColor: '#2f6df6', borderColor: '#2f6df6' },
  docTypeText: { fontSize: 12, color: '#536784', fontWeight: '500' },
  docTypeTextActive: { color: '#fff' },

  // File Picker
  filePicker: {
    borderWidth: 2, borderColor: '#dbe3ef', borderStyle: 'dashed',
    borderRadius: 16, padding: 24, alignItems: 'center', justifyContent: 'center',
    backgroundColor: '#f8fafc', marginBottom: 12,
  },
  filePickerTitle: { color: '#071a3a', fontSize: 15, fontWeight: '600', marginTop: 8 },
  filePickerSubtitle: { color: '#8090aa', fontSize: 12, marginTop: 4 },

  // Selected File
  selectedFileCard: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: '#fff', borderRadius: 12, padding: 12,
    borderWidth: 1, borderColor: '#dbeafe', marginBottom: 16,
  },
  fileIconWrap: { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  fileInfo: { flex: 1 },
  fileName: { color: '#071a3a', fontSize: 14, fontWeight: '600' },
  fileHint: { color: '#8090aa', fontSize: 11, marginTop: 2 },

  // Translate Button
  translateBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: '#16a34a', paddingVertical: 14, borderRadius: 12, marginBottom: 16,
  },
  translateBtnDisabled: { backgroundColor: '#9ca3af', opacity: 0.7 },
  translateBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },

  // Result Toggle
  resultToggle: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  toggleBtn: {
    flex: 1, paddingVertical: 10, borderRadius: 10,
    backgroundColor: '#f5f7fb', alignItems: 'center', borderWidth: 1, borderColor: '#e8edf5',
  },
  toggleBtnActive: { backgroundColor: '#eff6ff', borderColor: '#2f6df6' },
  toggleText: { fontSize: 12, color: '#536784', fontWeight: '600' },
  toggleTextActive: { color: '#2f6df6' },

  // Document Result
  docResultCard: {
    backgroundColor: '#fff', borderRadius: 12, padding: 14,
    borderWidth: 1, borderColor: '#e8edf5', marginBottom: 12,
  },
  docResultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  docResultTitle: { color: '#2f6df6', fontSize: 13, fontWeight: '700' },
  docResultText: { color: '#334155', fontSize: 13, lineHeight: 20 },
  docMetaRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  docMetaItem: {
    flex: 1, backgroundColor: '#f8fafc', borderRadius: 10,
    padding: 10, alignItems: 'center',
  },
  docMetaLabel: { fontSize: 10, color: '#8090aa', textTransform: 'uppercase', letterSpacing: 0.3 },
  docMetaValue: { fontSize: 12, color: '#071a3a', fontWeight: '600', marginTop: 4 },

  // Text Input
  inputCard: { backgroundColor: '#fff', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#e8edf5', marginBottom: 12 },
  inputCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  inputCardTitle: { fontSize: 13, fontWeight: '700', color: Colors.primary[700] },
  textArea: { fontSize: Typography.sizes.base, color: Colors.neutral[900], minHeight: 120, textAlignVertical: 'top', lineHeight: 22 },
  charCount: { fontSize: 11, color: '#8090aa', textAlign: 'right', marginTop: 8 },

  // Text Result
  resultCard: { backgroundColor: '#f0f9ff', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#dbeafe' },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  resultLangBadge: { backgroundColor: Colors.primary[600], paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  resultLangText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  resultText: { color: '#334155', fontSize: 14, lineHeight: 22, marginBottom: 8 },
  resultMeta: { fontSize: 11, color: '#8090aa' },

  // History
  historyHeadline: { fontSize: 18, fontWeight: '700', color: '#071a3a', marginBottom: 4 },
  historySubtitle: { fontSize: 13, color: '#64748b', marginBottom: 16 },
  historySection: { marginBottom: 24 },
  historySectionTitle: { fontSize: 15, fontWeight: '700', color: '#0f172a', marginBottom: 10 },
  historyEmptyRow: { padding: 16, borderRadius: 14, backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#dbeafe' },
  historyEmptyText: { color: '#64748b', fontSize: 13, lineHeight: 20 },
  historyCard: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: '#fff', borderRadius: 18, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: '#e2e8f0' },
  historyLangPair: { width: 56, height: 56, borderRadius: 18, backgroundColor: '#eff6ff', justifyContent: 'center', alignItems: 'center', gap: 2 },
  historyLang: { fontSize: 11, fontWeight: '700', color: Colors.primary[700] },
  historyInfo: { flex: 1 },
  historyRowTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6, gap: 8 },
  historyTitle: { fontSize: 14, fontWeight: '700', color: '#0f172a', flex: 1 },
  historySubTitle: { fontSize: 12, color: '#475569', marginBottom: 6 },
  historyPreview: { fontSize: 13, color: '#334155', lineHeight: 20 },
  historyMetaRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 10, gap: 6 },
  historyMeta: { fontSize: 11, color: '#64748b' },
  historyBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999, borderWidth: 1, borderColor: Colors.neutral[200], backgroundColor: '#f8fafc' },
  historyBadgeDoc: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  historyBadgeLight: { borderColor: Colors.neutral[200], backgroundColor: Colors.neutral[100] },
  historyBadgeLabel: { fontSize: 10, fontWeight: '700', color: Colors.neutral[700] },
});
