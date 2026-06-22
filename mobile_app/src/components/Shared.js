import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../theme';

export function ScreenHeader({ title, sub }) {
  return (
    <LinearGradient colors={['#162033', '#0D1B2A']} style={styles.header}>
      <Text style={styles.headerTitle}>{title}</Text>
      {sub ? <Text style={styles.headerSub}>{sub}</Text> : null}
    </LinearGradient>
  );
}

export function Loading({ label = 'Loading…' }) {
  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color={colors.gold} />
      <Text style={styles.loadingText}>{label}</Text>
    </View>
  );
}

export function ErrorRetry({ message, onRetry }) {
  return (
    <View style={styles.center}>
      <Text style={styles.errorText}>⚠ {message}</Text>
      <Text style={styles.retryText} onPress={onRetry}>Tap to retry</Text>
    </View>
  );
}

export function Empty({ label }) {
  return (
    <View style={styles.center}>
      <Text style={styles.emptyText}>{label}</Text>
    </View>
  );
}

export function SectionTitle({ children }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

export function Card({ children, style }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Badge({ label, tone = 'neutral' }) {
  const palette = {
    ok:      { bg: '#15331F', fg: colors.success },
    warn:    { bg: '#3A2010', fg: colors.warning },
    error:   { bg: '#3A1414', fg: colors.error },
    neutral: { bg: colors.navy, fg: colors.textSecondary },
  }[tone];
  return (
    <View style={[styles.badge, { backgroundColor: palette.bg }]}>
      <Text style={[styles.badgeText, { color: palette.fg }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingTop: 16,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  headerTitle: { ...typography.title, color: colors.textPrimary },
  headerSub:   { ...typography.small, color: colors.textSecondary, marginTop: 2 },

  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  loadingText: { ...typography.body, color: colors.textSecondary, marginTop: spacing.md },
  errorText:   { ...typography.body, color: colors.error, textAlign: 'center' },
  retryText:   { ...typography.body, color: colors.gold, marginTop: spacing.md },
  emptyText:   { ...typography.body, color: colors.textMuted },

  sectionTitle: { ...typography.label, color: colors.textMuted, marginBottom: spacing.sm, marginTop: spacing.md },

  card: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },

  badge: { borderRadius: radius.full, paddingHorizontal: spacing.sm, paddingVertical: 3, alignSelf: 'flex-start' },
  badgeText: { ...typography.small, fontWeight: '700' },
});
