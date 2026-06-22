import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, SectionList, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty, Card } from '../components/Shared';

export default function FilesScreen() {
  const [groups, setGroups] = useState([]);
  const [emptyReason, setEmptyReason] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.files();
      setGroups(resp.groups ?? []);
      setEmptyReason(resp.empty_reason ?? '');
    } catch (e) {
      setError(e.message || 'Failed to load files');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const sections = groups.map((g) => ({ title: g.label ?? g.root, data: g.files ?? [] }));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Files" sub="/api/files" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : sections.length === 0 ? (
        <Empty label={emptyReason || 'No files found'} />
      ) : (
        <SectionList
          sections={sections}
          keyExtractor={(f) => f.path}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
          renderSectionHeader={({ section }) => <Text style={styles.sectionHeader}>{section.title}</Text>}
          renderItem={({ item }) => (
            <Card>
              <Text style={styles.name} numberOfLines={1}>{item.path}</Text>
              <Text style={styles.meta}>{item.size_human} · {item.modified}{item.is_zip ? ` · ${item.entries?.length ?? 0} entries` : ''}</Text>
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
  sectionHeader: { ...typography.label, color: colors.textMuted, marginTop: spacing.md, marginBottom: spacing.sm },
  name: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  meta: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
});
