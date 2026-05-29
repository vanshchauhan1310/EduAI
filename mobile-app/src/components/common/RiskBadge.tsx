import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { RiskLevel } from '../../types';
import { Typography, BorderRadius, Spacing } from '../../theme';

const RISK_STYLES: Record<RiskLevel, { bg: string; text: string; dot: string }> = {
  LOW:      { bg: '#dcfce7', text: '#166534', dot: '#22c55e' },
  MEDIUM:   { bg: '#fef9c3', text: '#854d0e', dot: '#eab308' },
  HIGH:     { bg: '#ffedd5', text: '#9a3412', dot: '#f97316' },
  CRITICAL: { bg: '#fee2e2', text: '#991b1b', dot: '#ef4444' },
};

const LABELS: Record<RiskLevel, string> = {
  LOW: 'Low Risk', MEDIUM: 'Medium Risk', HIGH: 'High Risk', CRITICAL: 'Critical',
};

interface RiskBadgeProps {
  level: RiskLevel;
  showDot?: boolean;
  size?: 'sm' | 'md';
}

export default function RiskBadge({ level, showDot = true, size = 'md' }: RiskBadgeProps) {
  const style = RISK_STYLES[level];
  const isSmall = size === 'sm';

  return (
    <View style={[
      styles.badge,
      { backgroundColor: style.bg },
      isSmall && styles.badgeSm,
    ]}>
      {showDot && <View style={[styles.dot, { backgroundColor: style.dot }, isSmall && styles.dotSm]} />}
      <Text style={[styles.text, { color: style.text }, isSmall && styles.textSm]}>
        {LABELS[level]}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    alignSelf: 'flex-start',
    gap: 5,
  },
  badgeSm: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  dotSm: { width: 5, height: 5 },
  text: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.semibold,
  },
  textSm: { fontSize: Typography.sizes.xs },
});
