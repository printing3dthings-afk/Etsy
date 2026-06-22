import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, Card, Badge } from '../components/Shared';

export default function WorkflowsScreen() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [runningId, setRunningId] = useState(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.workflows();
      setWorkflows(resp.workflows ?? []);
    } catch (e) {
      setError(e.message || 'Failed to load workflows');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const run = (wf) => {
    Alert.alert(
      wf.requires_approval ? 'Stage workflow' : 'Run workflow',
      wf.requires_approval
        ? `"${wf.name}" requires approval. It will be staged to the Action Center.`
        : `Run "${wf.name}" now?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: wf.requires_approval ? 'Stage' : 'Run', onPress: async () => {
          setRunningId(wf.id);
          try {
            const resp = await api.runWorkflow(wf.id);
            Alert.alert('Done', resp.staged ? 'Staged for approval in the Action Center.' : 'Workflow completed.');
          } catch (e) {
            Alert.alert('Error', e.message || 'Workflow run failed');
          } finally {
            setRunningId(null);
          }
        }},
      ]
    );
  };

  return (
    <View style={styles.container}>
      <ScreenHeader title="Workflows" sub="/api/workflows" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : workflows.length === 0 ? (
        <Empty label="No workflows available" />
      ) : (
        <FlatList
          data={workflows}
          keyExtractor={(w) => w.id}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
          renderItem={({ item }) => (
            <Card>
              <View style={styles.headerRow}>
                <Text style={styles.name}>{item.name}</Text>
                {item.requires_approval ? <Badge label="Approval" tone="warn" /> : null}
                {item.long_running ? <Badge label="Long" tone="neutral" /> : null}
              </View>
              <Text style={styles.desc}>{item.description}</Text>
              <TouchableOpacity
                style={styles.runBtn}
                disabled={runningId === item.id}
                onPress={() => run(item)}
              >
                <Text style={styles.runText}>{runningId === item.id ? 'Running…' : 'Run'}</Text>
              </TouchableOpacity>
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
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flexWrap: 'wrap' },
  name: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  desc: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
  runBtn: {
    marginTop: spacing.sm, backgroundColor: colors.gold, borderRadius: radius.sm,
    paddingVertical: 8, alignItems: 'center',
  },
  runText: { ...typography.small, color: '#0D1B2A', fontWeight: '700' },
});
