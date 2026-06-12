import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import MetricCard from '../components/MetricCard';
import { api } from '../api';
import { colors, spacing, typography } from '../theme';

const fmt$ = (n) => `$${Number(n ?? 0).toFixed(2)}`;
const fmtN = (n) => String(n ?? '—');

function Section({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Row({ children }) {
  return <View style={styles.row}>{children}</View>;
}

export default function DashboardScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const m = await api.metrics();
      setData(m);
    } catch (e) {
      setError(e.message || 'Failed to load metrics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  const avgRating = data?.reviews?.avg_rating;
  const stars = avgRating
    ? '★'.repeat(Math.round(avgRating)) + '☆'.repeat(5 - Math.round(avgRating))
    : '—';

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#162033', '#0D1B2A']}
        style={styles.header}
      >
        <Text style={styles.greeting}>{greeting()}, Scott 👋</Text>
        <Text style={styles.date}>{today}</Text>
        {data?.shop?.name && (
          <View style={styles.shopBadge}>
            <Text style={styles.shopBadgeText}>🏪 {data.shop.name}</Text>
          </View>
        )}
      </LinearGradient>

      {loading && !refreshing ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
          <Text style={styles.loadingText}>Loading metrics…</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>⚠ {error}</Text>
          <Text style={styles.retryText} onPress={() => load()}>Tap to retry</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => load(true)}
              tintColor={colors.gold}
            />
          }
        >
          {/* Revenue */}
          <Section title="Revenue">
            <Row>
              <MetricCard
                half
                label="Last 7 days"
                value={fmt$(data?.orders?.revenue_7d)}
                accent
              />
              <MetricCard
                half
                label="Last 30 days"
                value={fmt$(data?.orders?.revenue_30d)}
              />
            </Row>
          </Section>

          {/* Orders */}
          <Section title="Orders">
            <Row>
              <MetricCard
                half
                label="This week"
                value={fmtN(data?.orders?.last_7_days)}
                sub="orders placed"
              />
              <MetricCard
                half
                label="This month"
                value={fmtN(data?.orders?.last_30_days)}
                sub="orders placed"
              />
            </Row>
          </Section>

          {/* Listings */}
          <Section title="Listings">
            <Row>
              <MetricCard
                half
                label="Active"
                value={fmtN(data?.listings?.active_count)}
                sub="live on Etsy"
                accent
              />
              <MetricCard
                half
                label="Drafts"
                value={fmtN(data?.listings?.draft_count)}
                sub="pending review"
              />
            </Row>
            {data?.listings?.draft_count > 0 && (
              <View style={styles.draftAlert}>
                <Text style={styles.draftAlertText}>
                  🔔 {data.listings.draft_count} draft{data.listings.draft_count !== 1 ? 's' : ''} ready for your review in Shop Manager
                </Text>
              </View>
            )}
          </Section>

          {/* Ratings */}
          <Section title="Customer Reviews">
            <Row>
              <MetricCard
                half
                label="Avg rating"
                value={avgRating ? avgRating.toFixed(2) : '—'}
                sub={stars}
                accent={avgRating >= 4.8}
              />
              <MetricCard
                half
                label="5-star %"
                value={data?.reviews?.five_star_pct != null ? `${data.reviews.five_star_pct}%` : '—'}
                sub={`of ${data?.reviews?.recent_sample ?? 0} reviews`}
              />
            </Row>
          </Section>

          {/* Shop */}
          <Section title="All-Time Shop">
            <MetricCard
              label="Total sales"
              value={fmtN(data?.shop?.total_sales)}
              sub="completed transactions"
            />
          </Section>

          {data?.shop?.on_vacation && (
            <View style={styles.vacationBanner}>
              <Text style={styles.vacationText}>
                ⛺ Shop is in Vacation Mode — buyers cannot purchase
              </Text>
            </View>
          )}

          <View style={{ height: spacing.xl }} />
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: {
    paddingTop: 60,
    paddingBottom: spacing.lg,
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  greeting: { ...typography.title, color: colors.textPrimary, marginBottom: 2 },
  date:     { ...typography.body, color: colors.textSecondary },
  shopBadge: {
    alignSelf: 'flex-start',
    marginTop: spacing.sm,
    backgroundColor: '#1B3A68',
    borderRadius: 20,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  shopBadgeText: { ...typography.small, color: colors.gold, fontWeight: '600' },
  scroll: { padding: spacing.md },
  section: { marginBottom: spacing.md },
  sectionTitle: {
    ...typography.label,
    color: colors.textMuted,
    marginBottom: spacing.sm,
  },
  row: { flexDirection: 'row', marginHorizontal: -spacing.xs / 2 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  loadingText: { ...typography.body, color: colors.textSecondary, marginTop: spacing.md },
  errorText:   { ...typography.body, color: colors.error, textAlign: 'center' },
  retryText:   { ...typography.body, color: colors.gold, marginTop: spacing.md },
  draftAlert: {
    backgroundColor: '#1B3A68',
    borderRadius: 10,
    padding: spacing.sm,
    marginTop: spacing.xs,
    borderLeftWidth: 3,
    borderLeftColor: colors.gold,
  },
  draftAlertText: { ...typography.small, color: colors.goldLight, lineHeight: 18 },
  vacationBanner: {
    backgroundColor: '#3A2010',
    borderRadius: 10,
    padding: spacing.md,
    borderLeftWidth: 3,
    borderLeftColor: colors.warning,
    marginBottom: spacing.md,
  },
  vacationText: { ...typography.body, color: colors.warning },
});
