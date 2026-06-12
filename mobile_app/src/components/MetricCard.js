import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, radius, typography } from '../theme';

export default function MetricCard({ label, value, sub, accent = false, half = false }) {
  return (
    <View style={[styles.wrapper, half && styles.half]}>
      <LinearGradient
        colors={accent ? ['#1B3A68', '#0D2744'] : ['#1A2D45', '#162033']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.card}
      >
        <Text style={styles.label}>{label}</Text>
        <Text style={[styles.value, accent && styles.valueAccent]}>{value}</Text>
        {sub ? <Text style={styles.sub}>{sub}</Text> : null}
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: spacing.sm,
    borderRadius: radius.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  half: {
    flex: 1,
    marginHorizontal: spacing.xs / 2,
  },
  card: {
    padding: spacing.md,
    minHeight: 88,
    justifyContent: 'space-between',
  },
  label: {
    ...typography.label,
    color: colors.textMuted,
    marginBottom: spacing.xs,
  },
  value: {
    ...typography.hero,
    color: colors.textPrimary,
  },
  valueAccent: {
    color: colors.gold,
  },
  sub: {
    ...typography.small,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
});
