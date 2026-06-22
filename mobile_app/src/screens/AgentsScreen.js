import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, Card, Badge } from '../components/Shared';

function statusTone(status) {
  if (status === 'ok' || status === 'running' || status === 'healthy') return 'ok';
  if (status === 'not_built') return 'neutral';
  if (status === 'error' || status === 'down') return 'error';
  return 'warn';
}

export default function AgentsScreen() {
  const [agents, setAgents] = useState([]);
  const [counts, setCounts] = useState({ running_count: 0, total_count: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.agentsStatus();
      setAgents(resp.agents ?? []);
      setCounts({ running_count: resp.running_count, total_count: resp.total_count });
    } catch (e) {
      setError(e.message || 'Failed to load agents');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Agents" sub={`/api/agents/status · ${counts.running_count}/${counts.total_count} running`} />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : agents.length === 0 ? (
        <Empty label="No agents registered" />
      ) : (
        <FlatList
          data={agents}
          keyExtractor={(a) => a.name}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
          renderItem={({ item }) => (
            <Card>
              <View style={styles.headerRow}>
                <Text style={styles.title}>{item.label}</Text>
                <Badge label={item.status} tone={statusTone(item.status)} />
              </View>
              <Text style={styles.detail}>{item.detail}</Text>
              {item.updated_at ? <Text style={styles.updated}>Updated {item.updated_at}</Text> : null}
            </Card>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing.md },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { ...typography.body, color: colors.textPrimary, fontWeight: '700', flex: 1, marginRight: spacing.sm },
  detail: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
  updated: { ...typography.small, color: colors.textMuted, marginTop: 4 },
});
