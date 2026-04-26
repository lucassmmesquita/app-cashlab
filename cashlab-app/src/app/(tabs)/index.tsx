/**
 * CashLab — Dashboard (dados reais do backend)
 *
 * Visão consolidada do mês com dados da API.
 * Inclui insights financeiros dinâmicos e tendências.
 */
import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, RefreshControl, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';

import { useMonthNavigation } from '@/hooks/useMonthNavigation';
import { useAppTheme } from '@/hooks/useAppTheme';
import { formatCurrency } from '@/utils/formatters';
import { getCategoryColor, getMemberColor } from '@/utils/colors';

import { DonutChart } from '@/components/charts/DonutChart';
import type { DonutSegment } from '@/components/charts/DonutChart';
import { CategoryLegend } from '@/components/charts/CategoryLegend';
import { SummaryRow } from '@/components/dashboard/SummaryCards';
import { MonthNavigator } from '@/components/dashboard/MonthNavigator';
import { NotificationBell } from '@/components/dashboard/NotificationBell';

import { dashboardService } from '@/services/dashboardService';
import type { DashboardResponse, DashboardInsight } from '@/services/dashboardService';
import type { Alert as AlertType } from '@/types/budget';

// ── Dashboard ─────────────────────────────────────────────────────

export default function DashboardScreen() {
  const { selectedMonth, goToPreviousMonth, goToNextMonth } = useMonthNavigation();
  const { colors, isDark, radius, spacing } = useAppTheme();
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setError(null);
      const result = await dashboardService.get(selectedMonth);
      setData(result);
    } catch (err: any) {
      setError('Não foi possível carregar o dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedMonth]);

  useEffect(() => {
    setLoading(true);
    fetchDashboard();
  }, [fetchDashboard]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchDashboard();
    setRefreshing(false);
  }, [fetchDashboard]);

  // Build data for display
  const totalExpenses = data?.total_card_expenses || '0';
  const totalIncome = data?.total_income || '0';
  const balance = data?.balance || '0';
  const categories = data?.by_category || [];
  const members = data?.by_member || [];
  const insights = data?.insights || [];
  const alerts: AlertType[] = (data?.alerts || []).map(a => ({
    type: a.type as 'critical' | 'warning' | 'info',
    message: a.message,
  }));

  // Build donut segments
  const categorySegments: DonutSegment[] = categories.map((cat) => ({
    label: cat.category_name,
    value: parseFloat(cat.total_amount),
    color: getCategoryColor(cat.category_name, isDark),
    percentage: cat.percentage,
  }));

  return (
    <View style={[styles.container, { backgroundColor: colors.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[styles.scrollContent, { padding: spacing.lg }]}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />
          }
        >
          {/* Header */}
          <View style={styles.headerRow}>
            <Text style={[styles.largeTitle, { color: colors.label }]}>Summary</Text>
            <NotificationBell notifications={alerts} />
          </View>

          {/* Segment control placeholder */}
          <View style={[styles.segmentControl, { backgroundColor: colors.segmentBg, borderRadius: 8 }]}>
            <Text style={[styles.segOption, { color: colors.secondaryLabel }]}>Sem</Text>
            <View style={[styles.segActive, { backgroundColor: colors.segmentActive, borderRadius: 7 }]}>
              <Text style={[styles.segOptionActive, { color: colors.label }]}>Mês</Text>
            </View>
            <Text style={[styles.segOption, { color: colors.secondaryLabel }]}>6 Meses</Text>
            <Text style={[styles.segOption, { color: colors.secondaryLabel }]}>Ano</Text>
          </View>

          {/* Month Navigator */}
          <MonthNavigator
            month={selectedMonth}
            onPrevious={goToPreviousMonth}
            onNext={goToNextMonth}
          />

          {/* Loading */}
          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.blue} />
            </View>
          )}

          {/* Error */}
          {error && !loading && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 20, alignItems: 'center' }]}>
              <Ionicons name="warning-outline" size={32} color={colors.red} />
              <Text style={[styles.errorText, { color: colors.red }]}>{error}</Text>
              <Pressable
                style={({ pressed }) => [styles.retryBtn, { backgroundColor: colors.blue, opacity: pressed ? 0.85 : 1 }]}
                onPress={fetchDashboard}
              >
                <Text style={styles.retryText}>Tentar novamente</Text>
              </Pressable>
            </View>
          )}

          {/* Data */}
          {!loading && data && (
            <>
              {/* Expense total card */}
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                <Text style={[styles.cardLabel, { color: colors.secondaryLabel }]}>Despesa total</Text>
                <Text style={[styles.heroValue, { color: colors.label }]}>
                  {formatCurrency(totalExpenses)}
                </Text>
              </View>

              {/* Summary */}
              <SummaryRow
                totalExpenses={data.total_expenses || totalExpenses}
                totalIncome={totalIncome}
                balance={balance}
              />

              {/* ── Insights Financeiros ── */}
              {insights.length > 0 && (
                <>
                  <View style={styles.sectionHeader}>
                    <Text style={[styles.title2, { color: colors.label }]}>Insights</Text>
                  </View>
                  <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                    {insights.map((insight, index) => {
                      const iconName = insight.type === 'critical' ? 'alert-circle' :
                        insight.type === 'warning' ? 'warning' : 'information-circle';
                      const iconColor = insight.type === 'critical' ? colors.red :
                        insight.type === 'warning' ? colors.orange : colors.blue;
                      return (
                        <View key={index}>
                          {index > 0 && (
                            <View style={[styles.separator, { backgroundColor: colors.separator, marginLeft: 44 }]} />
                          )}
                          <View style={styles.insightRow}>
                            <Ionicons name={iconName as any} size={20} color={iconColor} />
                            <View style={styles.insightBody}>
                              <Text style={[styles.insightTitle, { color: colors.label }]}>{insight.title}</Text>
                              <Text style={[styles.insightMsg, { color: colors.secondaryLabel }]}>{insight.message}</Text>
                            </View>
                          </View>
                        </View>
                      );
                    })}
                  </View>
                </>
              )}

              {/* Donut Chart */}
              {categories.length > 0 && (
                <>
                  <View style={styles.sectionHeader}>
                    <Text style={[styles.title2, { color: colors.label }]}>Gastos por categoria</Text>
                  </View>

                  <View style={[styles.chartCard, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                    <View style={styles.chartContainer}>
                      <DonutChart
                        segments={categorySegments}
                        size={200}
                        strokeWidth={28}
                        centerValue={formatCurrency(totalExpenses)}
                        centerLabel="total"
                      />
                    </View>
                  </View>

                  {/* Category Legend */}
                  <CategoryLegend segments={categorySegments} />
                </>
              )}

              {/* Members */}
              {members.length > 0 && (
                <>
                  <View style={styles.sectionHeader}>
                    <Text style={[styles.title2, { color: colors.label }]}>Gastos por membro</Text>
                  </View>

                  <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                    {members.map((member, index) => {
                      const memberColor = getMemberColor(member.member_name, isDark);
                      return (
                        <View key={member.member_name}>
                          {index > 0 && (
                            <View style={[styles.separator, { backgroundColor: colors.separator, marginLeft: 52 }]} />
                          )}
                          <View style={styles.memberRow}>
                            <View style={[styles.memberAvatar, { backgroundColor: memberColor }]}>
                              <Text style={styles.memberInitial}>{member.member_name[0]}</Text>
                            </View>
                            <View style={styles.memberBody}>
                              <Text style={[styles.memberName, { color: colors.label }]}>{member.member_name}</Text>
                              <Text style={[styles.memberPct, { color: colors.secondaryLabel }]}>
                                {member.percentage.toFixed(1).replace('.', ',')}%
                              </Text>
                            </View>
                            <Text style={[styles.memberValue, { color: colors.label }]}>
                              {formatCurrency(member.total_amount)}
                            </Text>
                          </View>
                        </View>
                      );
                    })}
                  </View>
                </>
              )}

              {/* Empty state */}
              {categories.length === 0 && members.length === 0 && (
                <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 24, alignItems: 'center' }]}>
                  <Ionicons name="receipt-outline" size={48} color={colors.tertiaryLabel} />
                  <Text style={[styles.emptyText, { color: colors.secondaryLabel }]}>
                    Nenhuma transação no mês
                  </Text>
                  <Text style={[styles.emptySubtext, { color: colors.tertiaryLabel }]}>
                    Importe faturas em Cartões para ver o resumo aqui
                  </Text>
                </View>
              )}
            </>
          )}

          {/* Import CTA */}
          <Pressable
            style={({ pressed }) => [
              styles.ctaButton,
              { backgroundColor: colors.blue, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 },
            ]}
          >
            <Text style={styles.ctaText}>Importar fatura</Text>
          </Pressable>

          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scroll: { flex: 1 },
  scrollContent: { gap: 8 },

  // Header
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5 },

  // Segment control
  segmentControl: {
    flexDirection: 'row',
    padding: 2,
    marginBottom: 4,
  },
  segOption: {
    flex: 1,
    textAlign: 'center',
    paddingVertical: 7,
    fontSize: 13,
    fontWeight: '500',
  },
  segActive: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 5,
  },
  segOptionActive: {
    fontSize: 13,
    fontWeight: '600',
  },

  // Cards
  card: { padding: 16 },
  cardLabel: { fontSize: 12, marginBottom: 3 },
  heroValue: { fontSize: 28, fontWeight: '700', letterSpacing: -0.5 },

  // Sections
  sectionHeader: { marginTop: 16, marginBottom: 4 },
  title2: { fontSize: 22, fontWeight: '700', letterSpacing: -0.5 },

  // Chart
  chartCard: { padding: 16, alignItems: 'center' },
  chartContainer: { paddingVertical: 8 },

  // Insights
  insightRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  insightBody: { flex: 1, gap: 2 },
  insightTitle: { fontSize: 14, fontWeight: '600' },
  insightMsg: { fontSize: 13 },

  // Members
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    paddingHorizontal: 16,
  },
  memberAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  memberInitial: { color: '#fff', fontSize: 15, fontWeight: '700' },
  memberBody: { flex: 1, gap: 1 },
  memberName: { fontSize: 15, fontWeight: '500' },
  memberPct: { fontSize: 12 },
  memberValue: { fontSize: 15, fontWeight: '600' },
  separator: { height: 0.5 },

  // Loading
  loadingContainer: { paddingVertical: 60, alignItems: 'center' },

  // Error
  errorText: { fontSize: 15, fontWeight: '500', marginTop: 8 },
  retryBtn: { marginTop: 12, paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
  retryText: { color: '#fff', fontSize: 14, fontWeight: '600' },

  // Empty
  emptyText: { fontSize: 15, marginTop: 12 },
  emptySubtext: { fontSize: 13, textAlign: 'center', marginTop: 4, paddingHorizontal: 24 },

  // CTA
  ctaButton: {
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 16,
  },
  ctaText: { color: '#fff', fontSize: 17, fontWeight: '600' },
});
