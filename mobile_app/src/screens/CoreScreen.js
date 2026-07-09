import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, SectionTitle, Card, Badge } from '../components/Shared';

function credBadge(present) {
  return <Badge label={present ? 'SET' : 'MISSING'} tone={present ? 'ok' : 'error'} />;
}

export default function CoreScreen() {
  const [health, setHealth] = useState(null);
  const [creds, setCreds] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const [h, c] = await Promise.all([api.health(), api.credentialsStatus()]);
      setHealth(h);
      setCreds(c);
    } catch (e) {
      setError(e.message || 'Failed to load core status');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Core" sub="/health · /api/credentials/status" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
        >
          <SectionTitle>Health</SectionTitle>
          <Card>
            <View style={styles.row}>
              <Text style={styles.label}>Status</Text>
              <Badge label={health?.status ?? 'unknown'} tone={health?.status === 'ok' ? 'ok' : 'warn'} />
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Timestamp</Text>
              <Text style={styles.value} numberOfLines={1}>{health?.timestamp ?? '—'}</Text>
            </View>
          </Card>

          <SectionTitle>Credentials</SectionTitle>
          <Card>
            <View style={styles.row}><Text style={styles.label}>Etsy API Key</Text>{credBadge(creds?.etsy?.api_key)}</View>
            <View style={styles.row}><Text style={styles.label}>Etsy Access Token</Text>{credBadge(creds?.etsy?.access_token)}</View>
            <View style={styles.row}><Text style={styles.label}>Etsy Refresh Token</Text>{credBadge(creds?.etsy?.refresh_token)}</View>
            <View style={styles.row}><Text style={styles.label}>Anthropic</Text>{credBadge(creds?.anthropic?.api_key)}</View>
            <View style={styles.row}><Text style={styles.label}>OpenAI</Text>{credBadge(creds?.openai?.api_key)}</View>
            <View style={styles.row}><Text style={styles.label}>SMTP User</Text>{credBadge(creds?.smtp?.user)}</View>
            <View style={styles.row}><Text style={styles.label}>SMTP Password</Text>{credBadge(creds?.smtp?.password)}</View>
            <View style={styles.row}><Text style={styles.label}>Pinterest</Text>{credBadge(creds?.pinterest?.api_key)}</View>
          </Card>

          <SectionTitle>Etsy Live</SectionTitle>
          <Card>
            <View style={styles.row}>
              <Text style={styles.label}>Live</Text>
              <Badge label={creds?.etsy_live ? 'LIVE' : 'OFFLINE'} tone={creds?.etsy_live ? 'ok' : 'error'} />
            </View>
            <View style={styles.row}>
              <Text style={styles.label}>Shop</Text>
              <Text style={styles.value}>{creds?.shop_name ?? '—'}</Text>
            </View>
            {creds?.etsy_live_error ? (
              <Text style={styles.errInline}>{creds.etsy_live_error}</Text>
            ) : null}
          </Card>
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
  errInline: { ...typography.small, color: colors.error, marginTop: spacing.sm },
});
