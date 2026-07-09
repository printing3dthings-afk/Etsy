import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, SectionTitle, Card, Badge } from '../components/Shared';

function credBadge(present) {
  return <Badge label={present ? 'CONNECTED' : 'NOT CONNECTED'} tone={present ? 'ok' : 'error'} />;
}

export default function ConnectionsScreen() {
  const [creds, setCreds] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      setCreds(await api.credentialsStatus());
    } catch (e) {
      setError(e.message || 'Failed to load connections');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <View style={styles.container}>
      <ScreenHeader title="Connections" sub="/api/credentials/status" />
      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
        >
          <Card>
            <View style={styles.row}><Text style={styles.label}>Etsy</Text>{credBadge(creds?.etsy?.access_token)}</View>
            <View style={styles.row}><Text style={styles.label}>Anthropic</Text>{credBadge(creds?.anthropic?.api_key)}</View>
            <View style={styles.row}><Text style={styles.label}>OpenAI</Text>{credBadge(creds?.openai?.api_key)}</View>
            <View style={styles.row}><Text style={styles.label}>SMTP (Outlook)</Text>{credBadge(creds?.smtp?.user)}</View>
            <View style={styles.row}><Text style={styles.label}>Pinterest</Text>{credBadge(creds?.pinterest?.api_key)}</View>
          </Card>

          <SectionTitle>Platform Connections Roadmap</SectionTitle>
          <Card>
            <Text style={styles.bullet}>• Etsy — live, OAuth-connected (re-run etsy_oauth.py every 90 days)</Text>
            <Text style={styles.bullet}>• Pinterest — Rich Pins active, API v5 posting available</Text>
            <Text style={styles.bullet}>• TikTok — not API-integrated, manual posting only</Text>
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
  bullet: { ...typography.body, color: colors.textSecondary, marginBottom: 4 },
});
