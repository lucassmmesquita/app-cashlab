/**
 * CashLab — Navegação de meses (iOS style)
 */
import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { formatReferenceMonth } from '@/utils/formatters';
import { useAppTheme } from '@/hooks/useAppTheme';

interface MonthNavigatorProps {
  month: string;
  onPrevious: () => void;
  onNext: () => void;
}

export function MonthNavigator({ month, onPrevious, onNext }: MonthNavigatorProps) {
  const { colors } = useAppTheme();

  return (
    <View style={styles.container}>
      <Pressable onPress={onPrevious} hitSlop={12}>
        <Ionicons name="chevron-back" size={22} color={colors.blue} />
      </Pressable>
      <Text style={[styles.monthText, { color: colors.label }]}>
        {formatReferenceMonth(month)}
      </Text>
      <Pressable onPress={onNext} hitSlop={12}>
        <Ionicons name="chevron-forward" size={22} color={colors.blue} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  monthText: {
    fontSize: 17,
    fontWeight: '600',
  },
});
