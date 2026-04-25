/**
 * CashLab — Alerts (iOS Design System v2)
 * Dot 8px + texto. Sem backgrounds coloridos.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAppTheme } from '@/hooks/useAppTheme';
import type { Alert as AlertType } from '@/types/budget';

interface DashboardAlertsProps {
  alerts: AlertType[];
}

export function DashboardAlerts({ alerts }: DashboardAlertsProps) {
  const { colors, radius } = useAppTheme();

  if (alerts.length === 0) return null;

  const alertColor = (type: string) => {
    switch (type) {
      case 'critical': return colors.red;
      case 'warning': return colors.orange;
      case 'info': return colors.green;
      default: return colors.gray;
    }
  };

  return (
    <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
      {alerts.map((alert, index) => (
        <View key={index}>
          {index > 0 && (
            <View style={[styles.separator, { backgroundColor: colors.separator, marginLeft: 26 }]} />
          )}
          <View style={styles.alertRow}>
            <View style={[styles.dot, { backgroundColor: alertColor(alert.type) }]} />
            <View style={styles.textContainer}>
              <Text style={[styles.alertText, { color: colors.label }]}>{alert.message}</Text>
            </View>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { overflow: 'hidden' },
  alertRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 12,
    paddingHorizontal: 16,
  },
  dot: { width: 8, height: 8, borderRadius: 4, marginTop: 5, flexShrink: 0 },
  textContainer: { flex: 1 },
  alertText: { fontSize: 14, fontWeight: '500', lineHeight: 20 },
  separator: { height: 0.5 },
});
