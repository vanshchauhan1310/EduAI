import React, { useState, useRef } from 'react';
import {
  View, Text, TextInput, FlatList, StyleSheet,
  TouchableOpacity, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
}

const QUICK_PROMPTS = [
  'Create a quiz for Class 7 Maths Chapter 5',
  'How to improve student engagement?',
  'Suggest activities for weak students',
  'Generate lesson plan for fractions',
];

const MOCK_RESPONSES: Record<string, string> = {
  default: "I'm your AI Teaching Assistant! I can help you create lesson plans, quizzes, and teaching strategies tailored to your class. Ask me anything!",
};

export default function AIAssistantScreen() {
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<Message[]>([
    { id: '0', role: 'assistant', text: MOCK_RESPONSES.default },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef<FlatList>(null);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const response = `Great question! Here's a tailored suggestion for "${text}":\n\n✅ Use real-world examples relevant to students' lives\n✅ Break complex topics into 10-minute micro-lessons\n✅ Apply formative assessment every 15 minutes\n✅ Use peer teaching for slower learners\n\nWould you like me to create a detailed lesson plan?`;
      setMessages((prev) => [...prev, { id: (Date.now() + 1).toString(), role: 'assistant', text: response }]);
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }, 1200);
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={0}
    >
      <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
        <Header title="AI Teaching Assistant" subtitle="Powered by GPT-4o" />

        {/* Quick Prompts */}
        <View style={styles.quickRow}>
          {QUICK_PROMPTS.map((p) => (
            <TouchableOpacity key={p} style={styles.quickChip} onPress={() => sendMessage(p)}>
              <Text style={styles.quickText}>{p}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Messages */}
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
                  <Text style={styles.aiAvatarText}>🤖</Text>
                </View>
              )}
              <View style={[styles.bubbleContent, item.role === 'user' ? styles.userContent : styles.aiContent]}>
                <Text style={[styles.bubbleText, item.role === 'user' && styles.userText]}>
                  {item.text}
                </Text>
              </View>
            </View>
          )}
        />

        {loading && (
          <View style={styles.typingIndicator}>
            <Text style={styles.typingText}>AI is typing…</Text>
          </View>
        )}

        {/* Input Bar */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Ask anything about teaching..."
            placeholderTextColor={Colors.neutral[400]}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[styles.sendBtn, !input.trim() && styles.sendBtnDisabled]}
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
  quickRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
    padding: Spacing.sm,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  quickChip: {
    backgroundColor: Colors.primary[50],
    borderRadius: BorderRadius.full,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: Colors.primary[100],
  },
  quickText: { fontSize: Typography.sizes.xs, color: Colors.primary[700] },
  messageList: { padding: Spacing.base, gap: Spacing.md },
  bubble: { flexDirection: 'row', alignItems: 'flex-end', gap: Spacing.sm },
  userBubble: { justifyContent: 'flex-end' },
  aiBubble: { justifyContent: 'flex-start' },
  aiAvatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: Colors.primary[100], justifyContent: 'center', alignItems: 'center' },
  aiAvatarText: { fontSize: 16 },
  bubbleContent: {
    maxWidth: '78%',
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
  },
  aiContent: { backgroundColor: Colors.white, borderBottomLeftRadius: 4, ...require('../../theme').Shadows.sm },
  userContent: { backgroundColor: Colors.primary[600], borderBottomRightRadius: 4 },
  bubbleText: { fontSize: Typography.sizes.sm, color: Colors.neutral[800], lineHeight: 20 },
  userText: { color: Colors.white },
  typingIndicator: { paddingHorizontal: Spacing.xl, paddingBottom: Spacing.sm },
  typingText: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], fontStyle: 'italic' },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: Spacing.sm,
    padding: Spacing.sm,
    backgroundColor: Colors.white,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.neutral[50],
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    fontSize: Typography.sizes.base,
    color: Colors.neutral[900],
    maxHeight: 120,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary[600],
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendBtnDisabled: { backgroundColor: Colors.neutral[300] },
});
