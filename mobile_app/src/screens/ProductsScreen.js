import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { colors, spacing, typography } from '../theme';
import { ScreenHeader, Card } from '../components/Shared';

// Static catalog data — mirrors the web's brandkit "products" panel (CLAUDE.md source of truth).
const PRODUCTS = [
  { id: 'DP1026', name: 'Ultimate Life Planner', theme: 'Lavender Dreams', price: 14.99, pages: 104, note: '+ sticker pack' },
  { id: 'DP1027', name: 'Student & School Planner', theme: 'Cotton Candy', price: 9.99, pages: 90, note: '' },
  { id: 'DP1028', name: 'Budget & Finance Planner', theme: 'Midnight Blue', price: 12.99, pages: 102, note: '' },
  { id: 'DP1029', name: 'Fitness & Wellness Planner', theme: 'Coral Peach', price: 12.99, pages: 91, note: '' },
];

export default function ProductsScreen() {
  return (
    <View style={styles.container}>
      <ScreenHeader title="Products" sub="Product catalog" />
      <FlatList
        data={PRODUCTS}
        keyExtractor={(p) => p.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <Card>
            <View style={styles.row}>
              <Text style={styles.id}>{item.id}</Text>
              <Text style={styles.price}>${item.price.toFixed(2)}</Text>
            </View>
            <Text style={styles.name}>{item.name}</Text>
            <Text style={styles.sub}>{item.theme} · {item.pages} pages{item.note ? ` ${item.note}` : ''}</Text>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  list: { padding: spacing.md },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  id: { ...typography.label, color: colors.gold },
  price: { ...typography.body, color: colors.gold, fontWeight: '700' },
  name: { ...typography.body, color: colors.textPrimary, fontWeight: '700', marginTop: 4 },
  sub: { ...typography.small, color: colors.textSecondary, marginTop: 2 },
});
