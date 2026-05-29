import React, { useState, useRef } from 'react';
import {
  View, Text, TextInput, FlatList, StyleSheet,
  TouchableOpacity, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

interface Message { id: string; role: 'user' | 'assistant'; text: string; }

const QUICK_PROMPTS = [
  'Explain fractions simply',
  'Help me write an essay',
  'What is photosynthesis?',
  'Give me practice sums',
];

export default function AIAssistantScreen() {
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'assistant', text: "Hi! I'm your AI Learning Tutor 📚\nAsk me anything — I'll explain it in a simple, easy-to-understand way!" },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef<FlatList>(null);

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { id: Date.now().toString(), role: 'user', text }]);
    setInput('');
    setLoading(true);

    setTimeout(() => {
      const response = `Great question about "${text}"! Here's a simple explanation:\n\n🔹 Step 1: Understand the core concept\n🔹 Step 2: Break it into smaller parts\n🔹 Step 3: Practice with examples\n\n📝 Quick Example:\nIf you're studying fractions, remember: the top number is the numerator (how many parts you have) and the bottom is the denominator (total parts).\n\nWant me to give you 5 practice problems?`;
      setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: 'assistant', text: response }]);
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }, 1000);
  };

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="AI Tutor" subtitle="Your Smart Learning Companion" />

        <View style={styles.quickRow}>
          {QUICK_PROMPTS.map((p) => (
            <TouchableOpacity key={p} style={styles.quickChip} onPress={() => sendMessage(p)}>
              <Text style={styles.quickText}>{p}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.aiBubble]}>
              {item.role === 'assistant' && (
                <View style={styles.aiAvatar}>
                  <Text style={styles.aiAvatarText}>🎓</Text>
                </View>
              )}
              <View style={[styles.content, item.role === 'user' ? styles.userContent : styles.aiContent]}>
                <Text style={[styles.text, item.role === 'user' && styles.userText]}>{item.text}</Text>
              </View>
            </View>
          )}
        />

        {loading && (
          <View style={styles.typing}>
            <Text style={styles.typingText}>Tutor is thinking…</Text>
          </View>
        )}

        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Ask any question..."
            placeholderTextColor={Colors.neutral[400]}
            multiline
          />
          <TouchableOpacity
            style={[styles.sendBtn, !input.trim() && styles.sendBtnOff]}
            onPress={() => sendMessage(input)}
            disabled={!input.trim() || loading}
          >
            <Ionicons name="send" size={20} color={Colors.white} />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  quickRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm, padding: Spacing.sm, backgroundColor: Colors.white, borderBottomWidth: 1, borderBottomColor: Colors.border },
  quickChip: { backgroundColor: '#f0fdf4', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 6, borderWidth: 1, borderColor: '#bbf7d0' },
  quickText: { fontSize: Typography.sizes.xs, color: '#15803d' },
  messageList: { padding: Spacing.base, gap: Spacing.md },
  bubble: { flexDirection: 'row', alignItems: 'flex-end', gap: Spacing.sm },
  userBubble: { justifyContent: 'flex-end' },
  aiBubble: { justifyContent: 'flex-start' },
  aiAvatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#f0fdf4', justifyContent: 'center', alignItems: 'center' },
  aiAvatarText: { fontSize: 16 },
  content: { maxWidth: '78%', borderRadius: BorderRadius.xl, padding: Spacing.md },
  aiContent: { backgroundColor: Colors.white, borderBottomLeftRadius: 4, ...require('../../theme').Shadows.sm },
  userContent: { backgroundColor: Colors.primary[600], borderBottomRightRadius: 4 },
  text: { fontSize: Typography.sizes.sm, color: Colors.neutral[800], lineHeight: 20 },
  userText: { color: Colors.white },
  typing: { paddingHorizontal: Spacing.xl, paddingBottom: Spacing.sm },
  typingText: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontStyle: 'italic' },
  inputBar: { flexDirection: 'row', alignItems: 'flex-end', gap: Spacing.sm, padding: Spacing.sm, backgroundColor: Colors.white, borderTopWidth: 1, borderTopColor: Colors.border },
  input: { flex: 1, backgroundColor: Colors.neutral[50], borderWidth: 1.5, borderColor: Colors.border, borderRadius: BorderRadius.xl, paddingHorizontal: Spacing.md, paddingVertical: Spacing.sm, fontSize: Typography.sizes.base, color: Colors.neutral[900], maxHeight: 120 },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: Colors.success, justifyContent: 'center', alignItems: 'center' },
  sendBtnOff: { backgroundColor: Colors.neutral[300] },
});
