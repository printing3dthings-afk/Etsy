import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, SectionTitle, Card } from '../components/Shared';

export default function MemoryScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      setData(await api.memory());
    } catch (e) {
      setError(e.message || 'Failed to load memory');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Memory" sub="/api/memory" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
        >
          <View style={styles.statsGrid}>
            <Card style={styles.statCard}>
              <Text style={styles.statValue}>{data?.total_sessions ?? 0}</Text>
              <Text style={styles.statLabel}>Sessions</Text>
            </Card>
            <Card style={styles.statCard}>
              <Text style={styles.statValue}>{data?.total_messages ?? 0}</Text>
              <Text style={styles.statLabel}>Messages</Text>
            </Card>
            <Card style={styles.statCard}>
              <Text style={styles.statValue}>{data?.kb_doc_count ?? 0}</Text>
              <Text style={styles.statLabel}>KB Docs</Text>
            </Card>
            <Card style={styles.statCard}>
              <Text style={styles.statValue}>{data?.learnings_count ?? 0}</Text>
              <Text style={styles.statLabel}>Learnings</Text>
            </Card>
          </View>

          <Card>
            <Text style={styles.sub}>Oldest: {data?.oldest_at ?? '—'}</Text>
            <Text style={styles.sub}>Newest: {data?.newest_at ?? '—'}</Text>
          </Card>

          <SectionTitle>Recent Learnings</SectionTitle>
          {(data?.learnings ?? []).length === 0 ? (
            <Empty label="No learnings recorded yet" />
          ) : (
            data.learnings.map((l, i) => (
              <Card key={i}>
                <Text style={styles.text}>{typeof l === 'string' ? l : (l.text ?? JSON.stringify(l))}</Text>
              </Card>
            ))
          )}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: spacing.md },

  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginBottom: spacing.sm },
  statCard: { width: '47%', alignItems: 'center' },
  statValue: { ...typography.hero, color: colors.gold, fontSize: 24 },
  statLabel: { ...typography.small, color: colors.textSecondary, marginTop: 2 },

  sub: { ...typography.small, color: colors.textSecondary },
  text: { ...typography.body, color: colors.textPrimary },
});
