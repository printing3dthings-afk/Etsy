import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useFocusEffect, useRoute } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry } from '../components/Shared';

export default function KbDocScreen() {
  const route = useRoute();
  const { filename } = route.params;
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.kbDoc(filename);
      setContent(resp.content ?? '');
    } catch (e) {
      setError(e.message || 'Failed to load document');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filename]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title={filename} />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
        >
          <Text style={styles.text}>{content}</Text>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: spacing.md },
  text: { ...typography.body, color: colors.textPrimary, lineHeight: 21 },
});
