import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { Colors, Typography } from '../../theme';

interface AttendanceDonutProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export default function AttendanceDonut({
  percentage, size = 100, strokeWidth = 10, label,
}: AttendanceDonutProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, percentage));
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const color =
    progress >= 85 ? Colors.success :
    progress >= 75 ? Colors.warning :
    Colors.danger;

  return (
    <View style={styles.container}>
      <Svg width={size} height={size}>
        {/* Track */}
        <Circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={Colors.neutral[100]}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress */}
        <Circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      <View style={[styles.center, { width: size, height: size }]}>
        <Text style={[styles.pct, { color }]}>{progress.toFixed(0)}%</Text>
        {label && <Text style={styles.label}>{label}</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { position: 'relative', justifyContent: 'center', alignItems: 'center' },
  center: { position: 'absolute', justifyContent: 'center', alignItems: 'center' },
  pct: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold },
  label: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 1 },
});
