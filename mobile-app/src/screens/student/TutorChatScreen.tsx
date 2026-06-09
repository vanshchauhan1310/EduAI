import React, { useRef, useState } from 'react';
import {
  View, Text, TextInput, FlatList, StyleSheet,
  TouchableOpacity, KeyboardAvoidingView, Platform, Linking,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Animated, { FadeInUp, FadeIn } from 'react-native-reanimated';
import Header from '../../components/common/Header';
import ConceptImageStrip from '../../components/common/ConceptImageStrip';
import RichAnswer from '../../components/common/RichAnswer';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { TUTOR_LANGUAGES } from '../../constants';
import { useTutorChat } from '../../hooks/useAiTutor';
import { newMessageId, emptyChatGreeting } from '../../services/aiTutorService';
import { ChatMessage, TutorLanguage } from '../../types';

const QUICK_PROMPTS = [
  "What is Ohm's law?",
  'Explain photosynthesis simply',
  'How do I balance chemical equations?',
  'Difference between speed and velocity?',
];

const SOURCE_ICON: Record<string, keyof typeof Ionicons.glyphMap> = { pdf: 'document-text', note: 'create' };

function SourceRow({ source }: { source: { kind: string; concept: string; text: string; score: number } }) {
  return (
    <View style={styles.sourceRow}>
      <Ionicons name={SOURCE_ICON[source.kind] ?? 'document'} size={14} color={Colors.secondary[600]} />
      <View style={styles.sourceTextBlock}>
        <Text style={styles.sourceConcept} numberOfLines={1}>{source.concept} · {Math.round(source.score * 100)}% match</Text>
        <Text style={styles.sourceExcerpt} numberOfLines={3}>{source.text}</Text>
      </View>
    </View>
  );
}

function Bubble({ message, index }: { message: ChatMessage; index: number }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isUser = message.role === 'user';
  const hasSources = !!message.sources?.length;

  return (
    <Animated.View entering={FadeInUp.duration(260).delay(Math.min(index, 4) * 30)}
      style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
      {!isUser && (
        <View style={styles.aiAvatar}>
          <Ionicons name="sparkles" size={15} color={Colors.secondary[600]} />
        </View>
      )}
      <View style={[styles.content, isUser ? styles.userContent : styles.aiContent]}>
        {!isUser && message.detected_topic && (
          <View style={styles.topicChip}>
            <Ionicons name="locate" size={11} color={Colors.secondary[600]} />
            <Text style={styles.topicChipText}>{message.detected_topic}</Text>
          </View>
        )}
        {isUser ? (
          <Text style={styles.userText}>{message.text}</Text>
        ) : (
          <RichAnswer text={message.text} />
        )}

        {!isUser && !!message.images?.length && <ConceptImageStrip images={message.images} />}

        {!isUser && !!message.videos?.length && (
          <View style={styles.videoSection}>
            <Text style={styles.videoSectionTitle}>📹 Related Videos</Text>
            {message.videos.map((video, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.videoCard}
                onPress={() => Linking.openURL(video.url)}
                activeOpacity={0.7}
              >
                <Ionicons name="logo-youtube" size={18} color="#FF0000" />
                <View style={styles.videoCardText}>
                  <Text style={styles.videoCardTitle} numberOfLines={2}>{video.title}</Text>
                  <Text style={styles.videoCardChannel}>{video.channel}</Text>
                </View>
                <Ionicons name="open-outline" size={14} color={Colors.primary[500]} />
              </TouchableOpacity>
            ))}
          </View>
        )}

        {hasSources && (
          <View>
            <TouchableOpacity style={styles.sourcesToggle} onPress={() => setSourcesOpen((v) => !v)} activeOpacity={0.7}>
              <Ionicons name={sourcesOpen ? 'chevron-up' : 'chevron-down'} size={13} color={Colors.neutral[500]} />
              <Text style={styles.sourcesToggleText}>
                {sourcesOpen ? 'Hide' : 'View'} sources ({message.sources!.length})
              </Text>
            </TouchableOpacity>
            {sourcesOpen && (
              <Animated.View entering={FadeIn.duration(180)} style={styles.sourcesList}>
                {message.sources!.map((s, i) => <SourceRow key={i} source={s} />)}
              </Animated.View>
            )}
          </View>
        )}
      </View>
    </Animated.View>
  );
}

export default function TutorChatScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<ChatMessage[]>([emptyChatGreeting()]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState<TutorLanguage>('english');
  const listRef = useRef<FlatList>(null);
  const chatMutation = useTutorChat();

  const scrollToEnd = () => setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);

  const sendMessage = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || chatMutation.isPending) return;

    const userMsg: ChatMessage = { id: newMessageId(), role: 'user', text: trimmed };
    const history = [...messages, userMsg]
      .slice(-8)
      .map((m) => ({ role: m.role, content: m.text }));

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    scrollToEnd();

    chatMutation.mutate(
      { question: trimmed, language, history },
      {
        onSuccess: (res) => {
          setMessages((prev) => [...prev, {
            id: newMessageId(), role: 'assistant', text: res.answer,
            detected_topic: res.detected_topic, sources: res.sources, images: res.images, videos: res.videos,
          }]);
          scrollToEnd();
        },
        onError: () => {
          setMessages((prev) => [...prev, {
            id: newMessageId(), role: 'assistant',
            text: "Sorry, I couldn't reach the tutor service just now. Please try again in a moment.",
          }]);
          scrollToEnd();
        },
      },
    );
  };

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}>
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="Ask a doubt" subtitle="RAG-grounded · answers from your syllabus" onBack={() => navigation.goBack()} />

        <View style={styles.langRow}>
          {TUTOR_LANGUAGES.map((l) => {
            const active = l.value === language;
            return (
              <TouchableOpacity key={l.value} onPress={() => setLanguage(l.value)} activeOpacity={0.85}
                style={[styles.langPill, active && styles.langPillActive]}>
                <Text style={[styles.langPillText, active && styles.langPillTextActive]}>{l.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {messages.length <= 1 && (
          <View style={styles.quickRow}>
            {QUICK_PROMPTS.map((p) => (
              <TouchableOpacity key={p} style={styles.quickChip} onPress={() => sendMessage(p)}>
                <Text style={styles.quickText}>{p}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={scrollToEnd}
          renderItem={({ item, index }) => <Bubble message={item} index={index} />}
        />

        {chatMutation.isPending && (
          <View style={styles.typing}>
            <View style={styles.typingDots}>
              <View style={styles.typingDot} /><View style={styles.typingDot} /><View style={styles.typingDot} />
            </View>
            <Text style={styles.typingText}>Searching your textbook & thinking…</Text>
          </View>
        )}

        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Ask any question from your syllabus…"
            placeholderTextColor={Colors.neutral[400]}
            multiline
          />
          <TouchableOpacity
            style={[styles.sendBtn, !input.trim() && styles.sendBtnOff]}
            onPress={() => sendMessage(input)}
            disabled={!input.trim() || chatMutation.isPending}
          >
            <Ionicons name="send" size={19} color={Colors.white} />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },

  langRow: { flexDirection: 'row', gap: Spacing.sm, padding: Spacing.sm, paddingBottom: 0 },
  langPill: { backgroundColor: Colors.white, borderRadius: BorderRadius.full, paddingHorizontal: Spacing.md, paddingVertical: 6, borderWidth: 1.5, borderColor: Colors.border },
  langPillActive: { backgroundColor: Colors.secondary[600], borderColor: Colors.secondary[600] },
  langPillText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  langPillTextActive: { color: Colors.white },

  quickRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, padding: Spacing.sm },
  quickChip: { backgroundColor: Colors.white, borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 6, borderWidth: 1, borderColor: Colors.border },
  quickText: { fontSize: Typography.sizes.xs, color: Colors.secondary[600] },

  messageList: { padding: Spacing.base, gap: Spacing.md },
  bubble: { flexDirection: 'row', alignItems: 'flex-end', gap: Spacing.sm },
  userBubble: { justifyContent: 'flex-end' },
  aiBubble: { justifyContent: 'flex-start' },
  aiAvatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: `${Colors.secondary[600]}16`, justifyContent: 'center', alignItems: 'center' },
  content: { maxWidth: '80%', borderRadius: BorderRadius.xl, padding: Spacing.md, gap: Spacing.xs },
  aiContent: { backgroundColor: Colors.white, borderBottomLeftRadius: 4, ...Shadows.sm },
  userContent: { backgroundColor: Colors.primary[600], borderBottomRightRadius: 4 },
  userText: { fontSize: Typography.sizes.sm, color: Colors.white, lineHeight: 20 },

  topicChip: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', backgroundColor: `${Colors.secondary[600]}12`, borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm - 2, paddingVertical: 2 },
  topicChipText: { fontSize: Typography.sizes.xs - 1, fontWeight: Typography.weights.semibold, color: Colors.secondary[600] },

  sourcesToggle: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  sourcesToggleText: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], fontWeight: Typography.weights.medium },
  sourcesList: { gap: Spacing.xs, marginTop: Spacing.xs, paddingTop: Spacing.xs, borderTopWidth: 1, borderTopColor: Colors.neutral[100] },
  sourceRow: { flexDirection: 'row', gap: Spacing.xs, alignItems: 'flex-start' },
  sourceTextBlock: { flex: 1 },
  sourceConcept: { fontSize: Typography.sizes.xs - 1, fontWeight: Typography.weights.semibold, color: Colors.neutral[700] },
  sourceExcerpt: { fontSize: Typography.sizes.xs - 1, color: Colors.neutral[500], lineHeight: 15, marginTop: 1 },

  videoSection: { marginTop: Spacing.sm, gap: Spacing.xs },
  videoSectionTitle: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, color: Colors.neutral[700] },
  videoCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, backgroundColor: Colors.neutral[50], borderRadius: BorderRadius.md, padding: Spacing.sm, borderWidth: 1, borderColor: Colors.neutral[100] },
  videoCardText: { flex: 1 },
  videoCardTitle: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold, color: Colors.neutral[800] },
  videoCardChannel: { fontSize: Typography.sizes.xs - 1, color: Colors.neutral[500] },

  typing: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, paddingHorizontal: Spacing.xl, paddingBottom: Spacing.sm },
  typingDots: { flexDirection: 'row', gap: 3 },
  typingDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.secondary[500] },
  typingText: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontStyle: 'italic' },

  inputBar: { flexDirection: 'row', alignItems: 'flex-end', gap: Spacing.sm, padding: Spacing.sm, backgroundColor: Colors.white, borderTopWidth: 1, borderTopColor: Colors.border },
  input: { flex: 1, backgroundColor: Colors.neutral[50], borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.xl, paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm, fontSize: Typography.sizes.base, color: Colors.neutral[900], maxHeight: 120 },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: Colors.secondary[600], justifyContent: 'center', alignItems: 'center' },
  sendBtnOff: { backgroundColor: Colors.neutral[300] },
});
