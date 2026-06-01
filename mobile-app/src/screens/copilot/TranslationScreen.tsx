import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, TextInput,
  Alert, Clipboard,
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
import { translationService } from '../../services/copilotService';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

type Lang = 'Telugu' | 'English';
type Tab = 'translate' | 'history';

const CHAR_LIMIT = 10_000;
const CONTENT_TYPES = ['Circular', 'Letter', 'Notice', 'Report', 'General'];

export default function TranslationScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const queryClient = useQueryClient();

  const [tab, setTab] = useState<Tab>('translate');
  const [sourceLang, setSourceLang] = useState<Lang>('Telugu');
  const [targetLang, setTargetLang] = useState<Lang>('English');
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<any>(null);

  const { data: history = [], isLoading: historyLoading } = useQuery({
    queryKey: ['translation-history'],
    queryFn: () => translationService.getHistory(),
    enabled: tab === 'history',
  });

  const { mutate: translate, isPending: translating } = useMutation({
    mutationFn: () => translationService.translate({
      source_language: sourceLang,
      target_language: targetLang,
      text: inputText,
    }),
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['translation-history'] });
    },
    onError: () => Alert.alert('Error', 'Translation failed. Please try again.'),
  });

  const swapLanguages = () => {
    const prev = sourceLang;
    setSourceLang(targetLang);
    setTargetLang(prev);
    if (result) {
      setInputText(result.translated_text);
      setResult(null);
    }
  };

  const copyToClipboard = (text: string) => {
    Clipboard.setString(text);
    Alert.alert('Copied!', 'Translation copied to clipboard.');
  };

  const charCount = inputText.length;
  const charColor = charCount > CHAR_LIMIT * 0.9 ? Colors.danger : Colors.neutral[400];

  const renderTranslateTab = () => (
    <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
      {/* Language Selector */}
      <View style={styles.langRow}>
        <View style={styles.langBox}>
          <Text style={styles.langBoxLabel}>From</Text>
          <View style={styles.langSelector}>
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
        </View>

        {/* Swap Button */}
        <TouchableOpacity style={styles.swapBtn} onPress={swapLanguages}>
          <Ionicons name="swap-horizontal" size={22} color={Colors.primary[600]} />
        </TouchableOpacity>

        <View style={styles.langBox}>
          <Text style={styles.langBoxLabel}>To</Text>
          <View style={styles.langSelector}>
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
      </View>

      {/* Input Area */}
      <Card style={styles.inputCard}>
        <View style={styles.inputCardHeader}>
          <Text style={styles.inputCardTitle}>{sourceLang}</Text>
          {inputText.length > 0 && (
            <TouchableOpacity onPress={() => { setInputText(''); setResult(null); }}>
              <Ionicons name="close-circle" size={18} color={Colors.neutral[400]} />
            </TouchableOpacity>
          )}
        </View>
        <TextInput
          style={styles.textArea}
          value={inputText}
          onChangeText={(t) => { setInputText(t); setResult(null); }}
          placeholder={
            sourceLang === 'Telugu'
              ? 'ఇక్కడ టెక్స్ట్ అతికించండి లేదా టైప్ చేయండి...'
              : 'Paste or type your text here...'
          }
          placeholderTextColor={Colors.neutral[400]}
          multiline
          textAlignVertical="top"
          maxLength={CHAR_LIMIT}
        />
        <Text style={[styles.charCount, { color: charColor }]}>
          {charCount.toLocaleString()} / {CHAR_LIMIT.toLocaleString()} characters
        </Text>
      </Card>

      {/* Quick Content Chips */}
      <View style={styles.contentTypeRow}>
        <Text style={styles.contentTypeLabel}>Content type hint:</Text>
        {CONTENT_TYPES.map((ct) => (
          <View key={ct} style={styles.contentChip}>
            <Text style={styles.contentChipText}>{ct}</Text>
          </View>
        ))}
      </View>

      {/* Translate Button */}
      <Button
        title={translating ? 'Translating…' : `Translate to ${targetLang}`}
        onPress={() => translate()}
        loading={translating}
        disabled={!inputText.trim() || translating}
        fullWidth
        size="lg"
        style={styles.translateBtn}
      />

      {/* Result */}
      {result && (
        <Card style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <View style={styles.resultLangBadge}>
              <Text style={styles.resultLangText}>{targetLang}</Text>
            </View>
            <TouchableOpacity onPress={() => copyToClipboard(result.translated_text)}>
              <Ionicons name="copy-outline" size={20} color={Colors.primary[600]} />
            </TouchableOpacity>
          </View>
          <Text style={styles.resultText} selectable>{result.translated_text}</Text>
          <View style={styles.resultMeta}>
            <Text style={styles.resultMetaText}>{result.word_count} words translated</Text>
            <TouchableOpacity
              style={styles.copyBtn}
              onPress={() => copyToClipboard(result.translated_text)}
            >
              <Ionicons name="copy" size={14} color={Colors.white} />
              <Text style={styles.copyBtnText}>Copy</Text>
            </TouchableOpacity>
          </View>
        </Card>
      )}
    </ScrollView>
  );

  const renderHistoryTab = () => (
    historyLoading ? <LoadingSpinner message="Loading history…" /> :
    history.length === 0 ? (
      <EmptyState icon="language-outline" title="No Translations Yet" description="Translate your first document to get started." />
    ) : (
      <ScrollView contentContainerStyle={styles.scroll}>
        {history.map((item: any) => (
          <TouchableOpacity
            key={item.id}
            style={styles.historyCard}
            onPress={() => {
              setInputText(item.source_text || '');
              setSourceLang(item.source_language);
              setTargetLang(item.target_language);
              setTab('translate');
            }}
          >
            <View style={styles.historyLangPair}>
              <Text style={styles.historyLang}>{item.source_language.slice(0, 2).toUpperCase()}</Text>
              <Ionicons name="arrow-forward" size={12} color={Colors.neutral[400]} />
              <Text style={styles.historyLang}>{item.target_language.slice(0, 2).toUpperCase()}</Text>
            </View>
            <View style={styles.historyInfo}>
              <Text style={styles.historyPreview} numberOfLines={2}>{item.preview}</Text>
              <Text style={styles.historyMeta}>
                {item.word_count ? `${item.word_count} words · ` : ''}
                {new Date(item.created_at).toLocaleDateString('en-IN')}
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={Colors.neutral[300]} />
          </TouchableOpacity>
        ))}
      </ScrollView>
    )
  );

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Translator" subtitle="Telugu ↔ English" onBack={() => navigation.goBack()} />

      {/* Tabs */}
      <View style={styles.tabs}>
        {([
          { key: 'translate', label: 'Translate', icon: 'language-outline' },
          { key: 'history',   label: 'History',   icon: 'time-outline'     },
        ] as const).map((t) => (
          <TouchableOpacity
            key={t.key}
            style={[styles.tab, tab === t.key && styles.tabActive]}
            onPress={() => setTab(t.key)}
          >
            <Ionicons name={t.icon} size={16} color={tab === t.key ? Colors.primary[600] : Colors.neutral[400]} />
            <Text style={[styles.tabText, tab === t.key && styles.tabTextActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {tab === 'translate' ? renderTranslateTab() : renderHistoryTab()}
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

  langRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.md },
  langBox: { flex: 1 },
  langBoxLabel: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[500], marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  langSelector: { gap: 6 },
  langChip: { padding: Spacing.sm, borderRadius: BorderRadius.lg, borderWidth: 1.5, borderColor: Colors.border, alignItems: 'center', backgroundColor: Colors.neutral[50] },
  langChipActive: { borderColor: Colors.primary[600], backgroundColor: Colors.primary[50] },
  langChipText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  langChipTextActive: { color: Colors.primary[700], fontWeight: Typography.weights.bold },
  swapBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: Colors.primary[50], justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: Colors.primary[200], marginTop: Spacing.xl },

  inputCard: { marginBottom: Spacing.sm },
  inputCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  inputCardTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.primary[700] },
  textArea: { fontSize: Typography.sizes.base, color: Colors.neutral[900], minHeight: 140, textAlignVertical: 'top', lineHeight: 24 },
  charCount: { fontSize: Typography.sizes.xs, textAlign: 'right', marginTop: Spacing.sm },

  contentTypeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, alignItems: 'center', marginBottom: Spacing.md },
  contentTypeLabel: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  contentChip: { backgroundColor: Colors.neutral[100], paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  contentChipText: { fontSize: Typography.sizes.xs, color: Colors.neutral[600] },

  translateBtn: { marginBottom: Spacing.lg },

  resultCard: { backgroundColor: '#f0f9ff' },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  resultLangBadge: { backgroundColor: Colors.primary[600], paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  resultLangText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  resultText: { fontSize: Typography.sizes.base, color: Colors.neutral[800], lineHeight: 26, marginBottom: Spacing.md },
  resultMeta: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: Spacing.md, borderTopWidth: 1, borderTopColor: Colors.primary[100] },
  resultMetaText: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  copyBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: Colors.primary[600], paddingHorizontal: Spacing.sm, paddingVertical: 6, borderRadius: BorderRadius.full },
  copyBtnText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },

  historyCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.sm, ...Shadows.sm },
  historyLangPair: { width: 56, height: 56, borderRadius: 28, backgroundColor: Colors.primary[50], justifyContent: 'center', alignItems: 'center', gap: 2 },
  historyLang: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.primary[700] },
  historyInfo: { flex: 1 },
  historyPreview: { fontSize: Typography.sizes.sm, color: Colors.neutral[700], lineHeight: 18 },
  historyMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 4 },
});
