import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Keyboard,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { WS_URL, APP_TOKEN } from '../config';
import { colors, spacing, radius, typography } from '../theme';

const SUGGESTIONS = [
  "What should I focus on today?",
  "How are my listings performing?",
  "What's the next product I should launch?",
  "Run a quick catalog audit",
  "How can I improve my SS1001 listing?",
];

function Bubble({ role, content, streaming }) {
  const isUser = role === 'user';
  return (
    <View style={[styles.bubbleRow, isUser && styles.bubbleRowUser]}>
      {!isUser && (
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>CEO</Text>
        </View>
      )}
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAgent]}>
        <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>
          {content}
          {streaming && <Text style={styles.cursor}>▊</Text>}
        </Text>
      </View>
    </View>
  );
}

export default function ChatScreen() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hey Scott 👋 I'm your CEO Agent — I know your shop, your products, and the standards we hold. What do you need?",
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsError, setWsError] = useState('');

  const wsRef = useRef(null);
  const listRef = useRef(null);
  const streamingIdxRef = useRef(-1);

  const scrollToBottom = () => {
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 50);
  };

  const connectWS = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_URL}/ws/chat?token=${APP_TOKEN}`);
    wsRef.current = ws;

    ws.onopen = () => setWsError('');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'chunk') {
        setMessages((prev) => {
          const next = [...prev];
          const idx = streamingIdxRef.current;
          if (idx >= 0 && next[idx]) {
            next[idx] = { ...next[idx], content: next[idx].content + data.content };
          }
          return next;
        });
        scrollToBottom();
      } else if (data.type === 'done') {
        setIsStreaming(false);
        streamingIdxRef.current = -1;
        scrollToBottom();
      } else if (data.type === 'error') {
        setIsStreaming(false);
        streamingIdxRef.current = -1;
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `⚠ Error: ${data.content}` },
        ]);
      }
    };

    ws.onerror = () => setWsError('Connection error — check server URL in config.js');
    ws.onclose = () => {};
  }, []);

  useEffect(() => {
    connectWS();
    return () => wsRef.current?.close();
  }, [connectWS]);

  const send = useCallback(() => {
    const text = input.trim();
    if (!text || isStreaming) return;

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWS();
      setTimeout(() => send(), 500);
      return;
    }

    Keyboard.dismiss();
    setInput('');

    const userMsg = { role: 'user', content: text };
    const agentMsg = { role: 'assistant', content: '' };

    setMessages((prev) => {
      const next = [...prev, userMsg, agentMsg];
      streamingIdxRef.current = next.length - 1;
      return next;
    });

    setIsStreaming(true);
    wsRef.current.send(JSON.stringify({ message: text }));
    scrollToBottom();
  }, [input, isStreaming, connectWS]);

  const useSuggestion = (text) => {
    setInput(text);
  };

  const renderItem = ({ item, index }) => (
    <Bubble
      role={item.role}
      content={item.content}
      streaming={isStreaming && index === streamingIdxRef.current}
    />
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      {/* Header */}
      <LinearGradient colors={['#162033', '#0D1B2A']} style={styles.header}>
        <View style={styles.headerInner}>
          <View style={styles.headerAvatar}>
            <Text style={styles.headerAvatarText}>🧠</Text>
          </View>
          <View>
            <Text style={styles.headerTitle}>CEO Agent</Text>
            <Text style={styles.headerSub}>
              {isStreaming ? 'Thinking…' : wsError || 'OnBrandCraftz HQ'}
            </Text>
          </View>
          {isStreaming && (
            <ActivityIndicator color={colors.gold} size="small" style={{ marginLeft: 'auto' }} />
          )}
        </View>
      </LinearGradient>

      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderItem}
        contentContainerStyle={styles.messages}
        onContentSizeChange={scrollToBottom}
        showsVerticalScrollIndicator={false}
      />

      {/* Suggestions (only when not streaming and last message was agent) */}
      {!isStreaming && messages.length < 3 && (
        <View style={styles.suggestions}>
          <Text style={styles.suggestionsLabel}>Quick questions</Text>
          {SUGGESTIONS.map((s) => (
            <TouchableOpacity key={s} style={styles.chip} onPress={() => useSuggestion(s)}>
              <Text style={styles.chipText}>{s}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Input */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask the CEO Agent…"
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={500}
          returnKeyType="send"
          onSubmitEditing={send}
          editable={!isStreaming}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || isStreaming) && styles.sendBtnDisabled]}
          onPress={send}
          disabled={!input.trim() || isStreaming}
        >
          <Text style={styles.sendIcon}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },

  header: {
    paddingTop: 60,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  headerInner:    { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  headerAvatar:   {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: colors.navy,
    alignItems: 'center', justifyContent: 'center',
  },
  headerAvatarText: { fontSize: 20 },
  headerTitle:  { ...typography.heading, color: colors.textPrimary },
  headerSub:    { ...typography.small, color: colors.textSecondary },

  messages: { padding: spacing.md, paddingBottom: spacing.sm },

  bubbleRow:     { flexDirection: 'row', marginBottom: spacing.sm, alignItems: 'flex-end' },
  bubbleRowUser: { justifyContent: 'flex-end' },

  avatar: {
    width: 30, height: 30, borderRadius: 15,
    backgroundColor: colors.navy,
    alignItems: 'center', justifyContent: 'center',
    marginRight: spacing.xs,
  },
  avatarText: { ...typography.label, color: colors.gold },

  bubble: {
    maxWidth: '80%',
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  bubbleUser:  {
    backgroundColor: colors.userBubble,
    borderBottomRightRadius: 4,
  },
  bubbleAgent: {
    backgroundColor: colors.agentBubble,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  bubbleText: {
    ...typography.body,
    color: colors.textPrimary,
    lineHeight: 22,
  },
  bubbleTextUser: { color: colors.textPrimary },
  cursor: { color: colors.gold, opacity: 0.8 },

  suggestions: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
  },
  suggestionsLabel: {
    ...typography.label, color: colors.textMuted, marginBottom: spacing.xs,
  },
  chip: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: 7,
    marginBottom: spacing.xs,
    alignSelf: 'flex-start',
  },
  chipText: { ...typography.small, color: colors.textSecondary },

  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: spacing.sm,
    paddingBottom: Platform.OS === 'ios' ? spacing.xl : spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.cardBorder,
    backgroundColor: colors.bg,
    gap: spacing.sm,
  },
  input: {
    flex: 1,
    backgroundColor: colors.inputBg,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
    color: colors.textPrimary,
    ...typography.body,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  sendBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: colors.gold,
    alignItems: 'center', justifyContent: 'center',
  },
  sendBtnDisabled: { backgroundColor: colors.cardBorder },
  sendIcon: { color: '#0D1B2A', fontSize: 20, fontWeight: '700' },
});
