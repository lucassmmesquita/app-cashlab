/**
 * CashLab — Summary Cards (iOS Design System v2)
 * Sem gradientes. Cores sólidas do tema.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { formatCurrency } from '@/utils/formatters';
import { useAppTheme } from '@/hooks/useAppTheme';

interface SummaryRowProps {
  totalExpenses: string;
  totalIncome: string;
  balance: string;
}

export function SummaryRow({ totalExpenses, totalIncome, balance }: SummaryRowProps) {
  const { colors, radius } = useAppTheme();
  const balanceNum = parseFloat(balance);
  const isPositive = balanceNum >= 0;

  return (
    <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
      <View style={styles.resultRow}>
        <Text style={[styles.resultLabel, { color: colors.secondaryLabel }]}>Resultado do mês</Text>
        <Text style={[styles.heroValue, { color: isPositive ? colors.green : colors.red }]}>
          {isPositive ? '' : '–'}{formatCurrency(Math.abs(balanceNum))}
        </Text>
      </View>

      <View style={[styles.separator, { backgroundColor: colors.separator }]} />

      <View style={styles.breakdownRow}>
        <View style={styles.breakdownItem}>
          <Text style={[styles.breakdownLabel, { color: colors.tertiaryLabel }]}>Receita</Text>
          <Text style={[styles.breakdownValue, { color: colors.green }]}>
            {formatCurrency(totalIncome)}
          </Text>
        </View>
        <View style={styles.breakdownItem}>
          <Text style={[styles.breakdownLabel, { color: colors.tertiaryLabel }]}>Cartões</Text>
          <Text style={[styles.breakdownValue, { color: colors.red }]}>
            –{formatCurrency(totalExpenses)}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
  resultRow: { marginBottom: 12 },
  resultLabel: { fontSize: 12, marginBottom: 3 },
  heroValue: { fontSize: 34, fontWeight: '700', letterSpacing: -1 },
  separator: { height: 0.5, marginVertical: 12 },
  breakdownRow: { flexDirection: 'row', gap: 20 },
  breakdownItem: { gap: 2 },
  breakdownLabel: { fontSize: 12 },
  breakdownValue: { fontSize: 15, fontWeight: '600' },
});
