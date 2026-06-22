import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, TextInput, RefreshControl } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty } from '../components/Shared';

export default function ConversationsScreen() {
  const navigation = useNavigation();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');

  const load = useCallback(async (q = '', isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.conversations(q);
      setSessions(resp.sessions ?? resp.results ?? []);
    } catch (e) {
      setError(e.message || 'Failed to load conversations');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(query); }, [load, query]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Conversations" sub="/api/conversations" />
      <View style={styles.searchRow}>
        <TextInput
          style={styles.input}
          placeholder="Search conversations…"
          placeholderTextColor={colors.textMuted}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={() => load(query)}
          returnKeyType="search"
        />
      </View>

      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={() => load(query)} />
      ) : sessions.length === 0 ? (
        <Empty label="No conversations found" />
      ) : (
        <FlatList
          data={sessions}
          keyExtractor={(s) => String(s.session_id ?? s.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(query, true)} tintColor={colors.gold} />}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.row}
              onPress={() => navigation.navigate('ConversationDetail', { sessionId: item.session_id ?? item.id })}
            >
              <View style={{ flex: 1 }}>
                <Text style={styles.title} numberOfLines={1}>{item.session_id ?? item.id}</Text>
                <Text style={styles.sub} numberOfLines={1}>{item.preview ?? item.last_message ?? ''}</Text>
                <Text style={styles.meta}>{item.message_count ?? ''} messages · {item.updated_at ?? item.last_at ?? ''}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  searchRow: { paddingHorizontal: spacing.md, paddingBottom: spacing.sm },
  input: {
    backgroundColor: colors.inputBg, borderRadius: radius.md, borderWidth: 1, borderColor: colors.cardBorder,
    paddingHorizontal: spacing.md, paddingVertical: 10, color: colors.textPrimary, ...typography.body,
  },
  list: { paddingHorizontal: spacing.md, paddingBottom: spacing.md },
  row: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.card, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.cardBorder, padding: spacing.md, marginBottom: spacing.sm,
  },
  title: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  sub: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
  meta: { ...typography.small, color: colors.textMuted, marginTop: 2 },
});
