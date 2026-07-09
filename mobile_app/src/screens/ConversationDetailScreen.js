import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { useFocusEffect, useRoute } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty } from '../components/Shared';

export default function ConversationDetailScreen() {
  const route = useRoute();
  const { sessionId } = route.params;
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.conversationDetail(sessionId);
      setMessages(resp.messages ?? []);
    } catch (e) {
      setError(e.message || 'Failed to load conversation');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [sessionId]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Conversation" sub={sessionId} />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : messages.length === 0 ? (
        <Empty label="No messages" />
      ) : (
        <FlatList
          data={messages}
          keyExtractor={(m, i) => String(m.id ?? i)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.agentBubble]}>
              <Text style={styles.role}>{item.role}</Text>
              <Text style={styles.text}>{item.content ?? item.text}</Text>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing.md },
  bubble: { borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.sm, maxWidth: '90%' },
  userBubble: { backgroundColor: colors.userBubble, alignSelf: 'flex-end' },
  agentBubble: { backgroundColor: colors.agentBubble, alignSelf: 'flex-start' },
  role: { ...typography.label, color: colors.textMuted, marginBottom: 4 },
  text: { ...typography.body, color: colors.textPrimary },
});
