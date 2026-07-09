import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Card, Badge } from '../components/Shared';

// Static security posture checklist — mirrors the web's security panel.
const CHECKLIST = [
  { label: '.env not committed to git', ok: true },
  { label: 'APP_SECRET_TOKEN set', ok: true },
  { label: 'Quality gate is code', ok: true },
  { label: 'Staged action queue', ok: true },
  { label: 'Etsy MFA enabled?', ok: null, note: 'Verify in Etsy account settings' },
  { label: 'Outlook 2FA active?', ok: null, note: 'Verify in Outlook account settings' },
  { label: 'Pinterest not integrated yet', ok: null, note: 'No live credential risk' },
  { label: 'No per-IP rate limiting', ok: false, note: 'Consider adding for /api/* routes' },
  { label: 'Token rotation reminder needed', ok: false, note: 'Etsy refresh token expires every 90 days' },
];

function tone(ok) {
  if (ok === true) return 'ok';
  if (ok === false) return 'warn';
  return 'neutral';
}
function label(ok) {
  if (ok === true) return 'OK';
  if (ok === false) return 'ATTENTION';
  return 'CHECK';
}

export default function SecurityScreen() {
  return (
    <View style={styles.container}>
      <ScreenHeader title="Security" sub="Posture checklist" />
      <FlatList
        data={CHECKLIST}
        keyExtractor={(c) => c.label}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <Card>
            <View style={styles.row}>
              <Text style={styles.label} numberOfLines={2}>{item.label}</Text>
              <Badge label={label(item.ok)} tone={tone(item.ok)} />
            </View>
            {item.note ? <Text style={styles.note}>{item.note}</Text> : null}
          </Card>
        )}
        ListFooterComponent={
          <Card>
            <Text style={styles.footerTitle}>Re-authorize Etsy</Text>
            <Text style={styles.footerText}>If any API call returns 401, run: python tools/etsy_oauth.py</Text>
          </Card>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing.md },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: spacing.sm },
  label: { ...typography.body, color: colors.textPrimary, flex: 1 },
  note: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
  footerTitle: { ...typography.body, color: colors.gold, fontWeight: '700' },
  footerText: { ...typography.small, color: colors.textSecondary, marginTop: 4 },
});
