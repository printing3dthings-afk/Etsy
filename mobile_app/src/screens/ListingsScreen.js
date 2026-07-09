import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Linking,
  RefreshControl,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';

const STATES = ['active', 'draft'];

function StateToggle({ value, onChange }) {
  return (
    <View style={styles.toggle}>
      {STATES.map((s) => (
        <TouchableOpacity
          key={s}
          style={[styles.toggleBtn, value === s && styles.toggleBtnActive]}
          onPress={() => onChange(s)}
        >
          <Text style={[styles.toggleText, value === s && styles.toggleTextActive]}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

function ListingCard({ item }) {
  const open = () => Linking.openURL(item.url);

  return (
    <TouchableOpacity style={styles.card} onPress={open} activeOpacity={0.75}>
      {item.thumbnail_url ? (
        <Image source={{ uri: item.thumbnail_url }} style={styles.thumb} />
      ) : (
        <View style={[styles.thumb, styles.thumbPlaceholder]}>
          <Text style={styles.thumbPlaceholderText}>🖼</Text>
        </View>
      )}
      <View style={styles.cardBody}>
        <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
        <View style={styles.meta}>
          <Text style={styles.price}>${item.price?.toFixed(2)}</Text>
          {item.state === 'draft' && (
            <View style={styles.draftBadge}>
              <Text style={styles.draftBadgeText}>DRAFT</Text>
            </View>
          )}
        </View>
        <View style={styles.stats}>
          <Text style={styles.stat}>👁 {item.views ?? 0}</Text>
          <Text style={styles.stat}>♥ {item.num_favorers ?? 0}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

export default function ListingsScreen() {
  const [state, setState] = useState('active');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (s = state, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.listings(s);
      setData(resp.listings ?? []);
    } catch (e) {
      setError(e.message || 'Failed to load listings');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [state]);

  useFocusEffect(useCallback(() => { load(state); }, [state, load]));

  const switchState = (s) => {
    setState(s);
    load(s);
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#162033', '#0D1B2A']} style={styles.header}>
        <Text style={styles.headerTitle}>Listings</Text>
        <StateToggle value={state} onChange={switchState} />
      </LinearGradient>

      {loading && !refreshing ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>⚠ {error}</Text>
          <Text style={styles.retryText} onPress={() => load(state)}>Tap to retry</Text>
        </View>
      ) : data.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>No {state} listings found</Text>
        </View>
      ) : (
        <FlatList
          data={data}
          keyExtractor={(item) => String(item.listing_id)}
          renderItem={({ item }) => <ListingCard item={item} />}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => load(state, true)}
              tintColor={colors.gold}
            />
          }
          ListHeaderComponent={
            <Text style={styles.count}>{data.length} listing{data.length !== 1 ? 's' : ''}</Text>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },

  header: {
    paddingTop: 60,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
    gap: spacing.sm,
  },
  headerTitle: { ...typography.title, color: colors.textPrimary },

  toggle: {
    flexDirection: 'row',
    backgroundColor: colors.card,
    borderRadius: radius.full,
    padding: 3,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  toggleBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: radius.full,
  },
  toggleBtnActive:   { backgroundColor: colors.gold },
  toggleText:        { ...typography.small, color: colors.textSecondary, fontWeight: '600' },
  toggleTextActive:  { color: '#0D1B2A' },

  list:  { padding: spacing.md },
  count: { ...typography.label, color: colors.textMuted, marginBottom: spacing.sm },

  card: {
    flexDirection: 'row',
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    marginBottom: spacing.sm,
    overflow: 'hidden',
  },
  thumb: { width: 90, height: 90 },
  thumbPlaceholder: {
    backgroundColor: colors.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  thumbPlaceholderText: { fontSize: 28 },

  cardBody: {
    flex: 1,
    padding: spacing.sm,
    justifyContent: 'space-between',
  },
  title: { ...typography.body, color: colors.textPrimary, fontWeight: '600', lineHeight: 19 },

  meta:      { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, marginTop: 4 },
  price:     { ...typography.body, color: colors.gold, fontWeight: '700' },
  draftBadge: {
    backgroundColor: '#1B3A68',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  draftBadgeText: { ...typography.label, color: colors.goldLight, fontSize: 9 },

  stats: { flexDirection: 'row', gap: spacing.md, marginTop: 4 },
  stat:  { ...typography.small, color: colors.textSecondary },

  center:    { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  errorText: { ...typography.body, color: colors.error, textAlign: 'center' },
  retryText: { ...typography.body, color: colors.gold, marginTop: spacing.md },
  emptyText: { ...typography.body, color: colors.textMuted },
});
