/**
 * CashLab — Donut Chart (SVG puro, theme-aware)
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';
import { useAppTheme } from '@/hooks/useAppTheme';

export interface DonutSegment {
  label: string;
  value: number;
  color: string;
  percentage: number;
}

interface DonutChartProps {
  segments: DonutSegment[];
  size?: number;
  strokeWidth?: number;
  centerLabel?: string;
  centerValue?: string;
}

export function DonutChart({
  segments,
  size = 200,
  strokeWidth = 28,
  centerLabel,
  centerValue,
}: DonutChartProps) {
  const { colors } = useAppTheme();
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  let cumulativePercent = 0;
  const arcs = segments.map((seg) => {
    const startPercent = cumulativePercent;
    cumulativePercent += seg.percentage;
    return {
      ...seg,
      dashArray: `${(seg.percentage / 100) * circumference} ${circumference}`,
      dashOffset: -((startPercent / 100) * circumference),
    };
  });

  return (
    <View style={styles.container}>
      <Svg width={size} height={size}>
        {/* Background ring */}
        <Circle
          cx={center}
          cy={center}
          r={radius}
          stroke={colors.segmentBg}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Segments */}
        <G rotation={-90} origin={`${center}, ${center}`}>
          {arcs.map((arc, index) => (
            <Circle
              key={`${arc.label}-${index}`}
              cx={center}
              cy={center}
              r={radius}
              stroke={arc.color}
              strokeWidth={strokeWidth}
              fill="none"
              strokeDasharray={arc.dashArray}
              strokeDashoffset={arc.dashOffset}
              strokeLinecap="butt"
            />
          ))}
        </G>
      </Svg>
      {(centerLabel || centerValue) && (
        <View style={[styles.centerText, { width: size, height: size }]}>
          {centerValue && (
            <Text style={[styles.centerValue, { color: colors.label }]}>{centerValue}</Text>
          )}
          {centerLabel && (
            <Text style={[styles.centerLabel, { color: colors.secondaryLabel }]}>{centerLabel}</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center' },
  centerText: { position: 'absolute', justifyContent: 'center', alignItems: 'center' },
  centerValue: { fontSize: 20, fontWeight: '700', letterSpacing: -0.5 },
  centerLabel: { fontSize: 12, marginTop: 2 },
});
