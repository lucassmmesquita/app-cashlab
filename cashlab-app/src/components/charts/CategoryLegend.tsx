/**
 * CashLab — Category Legend (iOS style)
 */
import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import type { DonutSegment } from './DonutChart';
import { formatCurrency } from '@/utils/formatters';
import { useAppTheme } from '@/hooks/useAppTheme';

interface CategoryLegendProps {
  segments: DonutSegment[];
  onPressItem?: (segment: DonutSegment) => void;
}

export function CategoryLegend({ segments, onPressItem }: CategoryLegendProps) {
  const { colors, radius } = useAppTheme();

  return (
    <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
      {segments.map((seg, index) => (
        <View key={`${seg.label}-${index}`}>
          {index > 0 && (
            <View style={[styles.separator, { backgroundColor: colors.separator, marginLeft: 52 }]} />
          )}
          <Pressable
            style={styles.row}
            onPress={() => onPressItem?.(seg)}
          >
            <View style={[styles.iconBg, { backgroundColor: `${seg.color}1A` }]}>
              <View style={[styles.dot, { backgroundColor: seg.color }]} />
            </View>
            <View style={styles.body}>
              <Text style={[styles.label, { color: colors.label }]} numberOfLines={1}>{seg.label}</Text>
              <Text style={[styles.sub, { color: colors.secondaryLabel }]}>
                {seg.percentage.toFixed(1).replace('.', ',')}%
              </Text>
            </View>
            <Text style={[styles.value, { color: colors.label }]}>{formatCurrency(seg.value)}</Text>
          </Pressable>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { overflow: 'hidden' },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    paddingHorizontal: 16,
  },
  iconBg: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  dot: { width: 10, height: 10, borderRadius: 3 },
  body: { flex: 1, gap: 1 },
  label: { fontSize: 15, fontWeight: '500' },
  sub: { fontSize: 12 },
  value: { fontSize: 15, fontWeight: '600', marginLeft: 8 },
  separator: { height: 0.5 },
});
