import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, SectionTitle, Card, Badge } from '../components/Shared';

function statusTone(status) {
  if (status === 'ok' || status === 'running' || status === 'healthy') return 'ok';
  if (status === 'not_built') return 'neutral';
  if (status === 'error' || status === 'down') return 'error';
  return 'warn';
}

export default function CommandCenterScreen() {
  const [health, setHealth] = useState(null);
  const [queue, setQueue] = useState([]);
  const [agents, setAgents] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const [h, q, a] = await Promise.all([api.health(), api.queue('pending'), api.agentsStatus()]);
      setHealth(h);
      setQueue(q.actions ?? []);
      setAgents(a);
    } catch (e) {
      setError(e.message || 'Failed to load command center');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Command Center" sub="/health · /api/queue · /api/agents/status" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
        >
          <SectionTitle>System Health</SectionTitle>
          <Card>
            <View style={styles.row}>
              <Text style={styles.label}>Status</Text>
              <Badge label={health?.status ?? 'unknown'} tone={health?.status === 'ok' ? 'ok' : 'warn'} />
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Build</Text>
              <Text style={styles.value}>{health?.build ?? '—'}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Persistent</Text>
              <Text style={styles.value}>{String(health?.persistent ?? '—')}</Text>
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Files Volume</Text>
              <Text style={styles.value}>{String(health?.files_volume ?? '—')}</Text>
            </View>
          </Card>

          <SectionTitle>Live Intelligence Feed ({queue.length} pending)</SectionTitle>
          {queue.length === 0 ? (
            <Empty label="No pending actions" />
          ) : (
            queue.slice(0, 10).map((a) => (
              <Card key={a.id}>
                <Text style={styles.cardTitle}>{a.type}</Text>
                <Text style={styles.cardSub} numberOfLines={2}>{a.summary}</Text>
              </Card>
            ))
          )}

          <SectionTitle>Active Agents ({agents?.running_count ?? 0}/{agents?.total_count ?? 0} running)</SectionTitle>
          {(agents?.agents ?? []).map((ag) => (
            <Card key={ag.name} style={styles.agentRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>{ag.label}</Text>
                <Text style={styles.cardSub} numberOfLines={1}>{ag.detail}</Text>
              </View>
              <Badge label={ag.status} tone={statusTone(ag.status)} />
            </Card>
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: spacing.md },

  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 4 },
  label: { ...typography.body, color: colors.textSecondary },
  value: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },

  cardTitle: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  cardSub:   { ...typography.small, color: colors.textSecondary, marginTop: 2 },

  agentRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
});
