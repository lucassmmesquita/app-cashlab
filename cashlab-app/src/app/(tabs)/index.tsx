/**
 * CashLab — Dashboard (iOS Design System v2)
 *
 * Visão consolidada do mês. iOS grouped cards. Sem gradientes.
 * Dados mock baseados na spec real (BV + Itaú Abril/2026).
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
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

import type { CategoryBreakdown, MemberBreakdown, Alert as AlertType } from '@/types/budget';

// ── Mock Data ─────────────────────────────────────────────────────

const MOCK_CATEGORIES: CategoryBreakdown[] = [
  { category_name: 'Alimentação', total_amount: '3245.80', percentage: 14.2, transaction_count: 28 },
  { category_name: 'Supermercado', total_amount: '2890.50', percentage: 12.6, transaction_count: 15 },
  { category_name: 'Assinaturas e Serviços Digitais', total_amount: '2180.40', percentage: 9.5, transaction_count: 12 },
  { category_name: 'Combustível', total_amount: '1950.00', percentage: 8.5, transaction_count: 18 },
  { category_name: 'Automotivo', total_amount: '1800.00', percentage: 7.8, transaction_count: 4 },
  { category_name: 'Farmácia e Saúde', total_amount: '1520.30', percentage: 6.6, transaction_count: 10 },
  { category_name: 'Compras Online', total_amount: '1450.00', percentage: 6.3, transaction_count: 8 },
  { category_name: 'Serviços Pessoais (Estética)', total_amount: '1280.00', percentage: 5.6, transaction_count: 6 },
  { category_name: 'Lazer e Entretenimento', total_amount: '1150.73', percentage: 5.0, transaction_count: 9 },
  { category_name: 'Educação', total_amount: '980.00', percentage: 4.3, transaction_count: 3 },
  { category_name: 'Vestuário', total_amount: '890.50', percentage: 3.9, transaction_count: 7 },
  { category_name: 'Moradia', total_amount: '750.00', percentage: 3.3, transaction_count: 2 },
  { category_name: 'Tarifas Bancárias', total_amount: '445.50', percentage: 1.9, transaction_count: 4 },
  { category_name: 'Outros', total_amount: '400.00', percentage: 1.7, transaction_count: 5 },
];

const MOCK_MEMBERS: MemberBreakdown[] = [
  { member_name: 'LUCAS', total_amount: '14520.80', percentage: 63.3 },
  { member_name: 'JURA', total_amount: '6412.93', percentage: 28.0 },
  { member_name: 'JOICE', total_amount: '2000.00', percentage: 8.7 },
];

const MOCK_ALERTS: AlertType[] = [
  { type: 'critical', message: 'Limite do BV está 99,88% utilizado. Evite novas compras.' },
  { type: 'warning', message: 'Alimentação ultrapassou o orçamento em R$ 245,80 (+8,2%)' },
  { type: 'info', message: '3 faturas importadas este mês (BV, Itaú 8001, Itaú 9825)' },
];

const MOCK_TOTAL_EXPENSES = '22933.73';
const MOCK_TOTAL_INCOME = '28500.00';
const MOCK_BALANCE = '5566.27';

// ── Dashboard ─────────────────────────────────────────────────────

export default function DashboardScreen() {
  const { selectedMonth, goToPreviousMonth, goToNextMonth } = useMonthNavigation();
  const { colors, isDark, radius, spacing } = useAppTheme();

  // Build donut segments
  const categorySegments: DonutSegment[] = MOCK_CATEGORIES.map((cat) => ({
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
        >
          {/* Header */}
          <View style={styles.headerRow}>
            <Text style={[styles.largeTitle, { color: colors.label }]}>Summary</Text>
            <NotificationBell notifications={MOCK_ALERTS} />
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

          {/* Expense total card */}
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <Text style={[styles.cardLabel, { color: colors.secondaryLabel }]}>Despesa total</Text>
            <Text style={[styles.heroValue, { color: colors.label }]}>
              R$ 22.933,73
            </Text>
          </View>

          {/* Summary */}
          <SummaryRow
            totalExpenses={MOCK_TOTAL_EXPENSES}
            totalIncome={MOCK_TOTAL_INCOME}
            balance={MOCK_BALANCE}
          />



          {/* Donut Chart */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.title2, { color: colors.label }]}>Gastos por categoria</Text>
          </View>

          <View style={[styles.chartCard, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.chartContainer}>
              <DonutChart
                segments={categorySegments}
                size={200}
                strokeWidth={28}
                centerValue={formatCurrency(MOCK_TOTAL_EXPENSES)}
                centerLabel="total"
              />
            </View>
          </View>

          {/* Category Legend */}
          <CategoryLegend segments={categorySegments} />

          {/* Members */}
          <View style={styles.sectionHeader}>
            <Text style={[styles.title2, { color: colors.label }]}>Gastos por membro</Text>
          </View>

          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            {MOCK_MEMBERS.map((member, index) => {
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

  // CTA
  ctaButton: {
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 16,
  },
  ctaText: { color: '#fff', fontSize: 17, fontWeight: '600' },
});
