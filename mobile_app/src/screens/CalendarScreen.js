import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, SectionTitle, Card, Badge } from '../components/Shared';

export default function CalendarScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      setData(await api.cadence());
    } catch (e) {
      setError(e.message || 'Failed to load cadence');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Calendar" sub="/api/cadence · /api/todos" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
        >
          <SectionTitle>Due Tasks</SectionTitle>
          {(data?.due_todos ?? []).length === 0 ? (
            <Empty label="Nothing due" />
          ) : (
            data.due_todos.map((t) => (
              <Card key={t.id}>
                <Text style={styles.text}>{t.text}</Text>
                <Text style={styles.sub}>Due {t.due_date}</Text>
              </Card>
            ))
          )}

          <SectionTitle>Tax Deadlines</SectionTitle>
          {(data?.tax_deadlines ?? []).map((d, i) => (
            <Card key={i}>
              <View style={styles.row}>
                <Text style={styles.text}>{d.label ?? d.name}</Text>
                <Badge label={d.date} tone="neutral" />
              </View>
            </Card>
          ))}

          <SectionTitle>Seasonal</SectionTitle>
          {(data?.seasonal ?? []).map((s, i) => (
            <Card key={i}>
              <Text style={styles.text}>{s.label ?? s.name ?? JSON.stringify(s)}</Text>
              {s.update_by ? <Text style={styles.sub}>Update by {s.update_by}</Text> : null}
            </Card>
          ))}

          <SectionTitle>Checklists</SectionTitle>
          {(data?.checklists ?? []).map((c, i) => (
            <Card key={i}>
              <Text style={styles.text}>{c.label ?? c.name ?? JSON.stringify(c)}</Text>
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
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  text: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  sub: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
});
