import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, SectionTitle, Card } from '../components/Shared';

// Static palette/standards data — mirrors the web's brandkit panel (CLAUDE.md source of truth).
const THEMES = [
  { id: 'DP1026', name: 'Lavender Dreams', primary: '#8666AA', accent: '#C4A8D4', neutral: '#FAF7FF', text: '#2C1A3A' },
  { id: 'DP1027', name: 'Cotton Candy',    primary: '#DE97C6', accent: '#97C6DE', neutral: '#FFF6FC', text: '#2C1A2A' },
  { id: 'DP1028', name: 'Midnight Blue',   primary: '#1B2568', accent: '#7BA7C2', neutral: '#F0F5FF', text: '#0D1525' },
  { id: 'DP1029', name: 'Coral Peach',     primary: '#FD6C49', accent: '#F5B878', neutral: '#FFF8F4', text: '#3A1A0D' },
];

const STANDARDS = [
  'Title ≤ 70 chars, keyword first 40, commas not pipes',
  'Tags: 13 used, ≤ 20 chars each, multi-word',
  'Photos: 10 slots, 2400×2400px, lifestyle hero first',
  'Price endings: .99 / .97 / .49',
  'AI disclosure required on every listing',
  'Digital file limit: 20MB per file',
];

const PRICING = [
  { product: 'DP1026', price: '$14.99', note: '104pg + stickers' },
  { product: 'DP1027', price: '$9.99', note: '90pg' },
  { product: 'DP1028', price: '$12.99', note: '102pg' },
  { product: 'DP1029', price: '$12.99', note: '91pg' },
  { product: 'SVG 5-pack', price: '$9.99', note: '' },
  { product: 'SVG 10+pack', price: '$14.99', note: '' },
];

function Swatch({ hex }) {
  return <View style={[styles.swatch, { backgroundColor: hex }]} />;
}

export default function BrandKitScreen() {
  return (
    <View style={styles.container}>
      <ScreenHeader title="Brand Kit" sub="Themes, standards, pricing" />
      <ScrollView contentContainerStyle={styles.scroll}>
        <SectionTitle>Color Themes</SectionTitle>
        {THEMES.map((t) => (
          <Card key={t.id}>
            <Text style={styles.themeName}>{t.id} — {t.name}</Text>
            <View style={styles.swatchRow}>
              <Swatch hex={t.primary} /><Swatch hex={t.accent} /><Swatch hex={t.neutral} /><Swatch hex={t.text} />
            </View>
          </Card>
        ))}

        <SectionTitle>Listing Standards</SectionTitle>
        <Card>
          {STANDARDS.map((s, i) => <Text key={i} style={styles.bullet}>• {s}</Text>)}
        </Card>

        <SectionTitle>Pricing Tiers</SectionTitle>
        <Card>
          {PRICING.map((p, i) => (
            <View key={i} style={styles.priceRow}>
              <Text style={styles.priceProduct}>{p.product}{p.note ? ` (${p.note})` : ''}</Text>
              <Text style={styles.priceValue}>{p.price}</Text>
            </View>
          ))}
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: spacing.md },
  themeName: { ...typography.body, color: colors.textPrimary, fontWeight: '700', marginBottom: spacing.sm },
  swatchRow: { flexDirection: 'row', gap: spacing.sm },
  swatch: { width: 36, height: 36, borderRadius: 8, borderWidth: 1, borderColor: colors.cardBorder },
  bullet: { ...typography.body, color: colors.textSecondary, marginBottom: 4 },
  priceRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  priceProduct: { ...typography.body, color: colors.textPrimary },
  priceValue: { ...typography.body, color: colors.gold, fontWeight: '700' },
});
