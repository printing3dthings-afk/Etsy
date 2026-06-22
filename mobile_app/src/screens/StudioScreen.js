import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Empty } from '../components/Shared';

// Studio is an intentional placeholder on the web HUD too — matching, not building ahead of it.
export default function StudioScreen() {
  return (
    <View style={styles.container}>
      <ScreenHeader title="Studio" sub="Coming soon" />
      <View style={styles.center}>
        <Ionicons name="construct-outline" size={40} color={colors.textMuted} />
        <Empty label="Studio (video generation) is not built yet — placeholder on web too" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.xl },
});
