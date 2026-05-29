import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: keyof typeof Ionicons.glyphMap;
  iconColor?: string;
  trend?: { value: number; label: string };
  style?: ViewStyle;
  accent?: string;
}

export default function StatsCard({
  label, value, icon, iconColor, trend, style, accent,
}: StatsCardProps) {
  const accentColor = accent ?? Colors.primary[600];
  const trendUp = trend && trend.value >= 0;

  return (
    <View style={[styles.card, style]}>
      <View style={[styles.accentBar, { backgroundColor: accentColor }]} />
      <View style={styles.content}>
        <View style={styles.top}>
          {icon && (
            <View style={[styles.iconWrap, { backgroundColor: `${accentColor}18` }]}>
              <Ionicons name={icon} size={20} color={iconColor ?? accentColor} />
            </View>
          )}
          <Text style={styles.label} numberOfLines={2}>{label}</Text>
        </View>
        <Text style={styles.value}>{value}</Text>
        {trend && (
          <View style={styles.trendRow}>
            <Ionicons
              name={trendUp ? 'trending-up' : 'trending-down'}
              size={14}
              color={trendUp ? Colors.success : Colors.danger}
            />
            <Text style={[styles.trendText, { color: trendUp ? Colors.success : Colors.danger }]}>
              {trend.value > 0 ? '+' : ''}{trend.value}% {trend.label}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    ...Shadows.md,
    flexDirection: 'row',
    overflow: 'hidden',
    flex: 1,
  },
  accentBar: {
    width: 4,
  },
  content: {
    flex: 1,
    padding: Spacing.md,
  },
  top: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: BorderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.sm,
  },
  label: {
    flex: 1,
    fontSize: Typography.sizes.sm,
    color: Colors.neutral[500],
    fontWeight: Typography.weights.medium,
  },
  value: {
    fontSize: Typography.sizes['2xl'],
    fontWeight: Typography.weights.bold,
    color: Colors.neutral[900],
    marginTop: 2,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.xs,
    gap: 4,
  },
  trendText: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.medium,
  },
});
