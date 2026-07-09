import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, Card } from '../components/Shared';

export default function ActionCenterScreen() {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.queue('pending');
      setActions(resp.actions ?? []);
    } catch (e) {
      setError(e.message || 'Failed to load action queue');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const approve = (id) => {
    Alert.alert('Approve action', 'Run this staged action now?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Approve', onPress: async () => {
        setBusyId(id);
        try { await api.approveAction(id); await load(); }
        catch (e) { setError(e.message || 'Approve failed'); }
        finally { setBusyId(null); }
      }},
    ]);
  };

  const reject = (id) => {
    Alert.alert('Reject action', 'Discard this staged action?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Reject', style: 'destructive', onPress: async () => {
        setBusyId(id);
        try { await api.rejectAction(id); await load(); }
        catch (e) { setError(e.message || 'Reject failed'); }
        finally { setBusyId(null); }
      }},
    ]);
  };

  return (
    <View style={styles.container}>
      <ScreenHeader title="Action Center" sub="/api/queue · /api/actions" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : actions.length === 0 ? (
        <Empty label="No pending actions awaiting approval" />
      ) : (
        <FlatList
          data={actions}
          keyExtractor={(a) => String(a.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
          renderItem={({ item }) => (
            <Card>
              <Text style={styles.type}>{item.type}</Text>
              <Text style={styles.summary}>{item.summary}</Text>
              <Text style={styles.created}>{item.created_at}</Text>
              <View style={styles.btnRow}>
                <TouchableOpacity
                  style={[styles.btn, styles.approveBtn]}
                  disabled={busyId === item.id}
                  onPress={() => approve(item.id)}
                >
                  <Text style={styles.approveText}>Approve</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btn, styles.rejectBtn]}
                  disabled={busyId === item.id}
                  onPress={() => reject(item.id)}
                >
                  <Text style={styles.rejectText}>Reject</Text>
                </TouchableOpacity>
              </View>
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
  type: { ...typography.label, color: colors.gold },
  summary: { ...typography.body, color: colors.textPrimary, marginTop: 4 },
  created: { ...typography.small, color: colors.textMuted, marginTop: 4 },

  btnRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  btn: { flex: 1, borderRadius: radius.sm, paddingVertical: 8, alignItems: 'center' },
  approveBtn: { backgroundColor: colors.success },
  rejectBtn: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.error },
  approveText: { ...typography.small, color: '#0D1B2A', fontWeight: '700' },
  rejectText: { ...typography.small, color: colors.error, fontWeight: '700' },
});
