import React, { useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, Defs, LinearGradient, Stop } from 'react-native-svg';
import Animated, {
  useSharedValue, useAnimatedProps, withTiming, Easing,
} from 'react-native-reanimated';
import { Colors, Typography } from '../../theme';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface MasteryRingProps {
  value: number;            // 0-100
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  gradientId?: string;      // unique id when multiple rings render on one screen
  trackColor?: string;
}

/**
 * Gradient circular progress ring used as the AI Tutor's signature visual —
 * an indigo→violet sweep (the feature's accent identity) that animates in on mount.
 */
export default function MasteryRing({
  value, size = 120, strokeWidth = 12, label, sublabel,
  gradientId = 'masteryGradient', trackColor,
}: MasteryRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, value));

  const progress = useSharedValue(0);
  useEffect(() => {
    progress.value = withTiming(clamped, { duration: 900, easing: Easing.out(Easing.cubic) });
  }, [clamped]);

  const animatedProps = useAnimatedProps(() => ({
    strokeDashoffset: circumference - (progress.value / 100) * circumference,
  }));

  return (
    <View style={styles.container}>
      <Svg width={size} height={size}>
        <Defs>
          <LinearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor={Colors.secondary[500]} />
            <Stop offset="100%" stopColor={Colors.primary[600]} />
          </LinearGradient>
        </Defs>
        <Circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={trackColor ?? 'rgba(255,255,255,0.25)'}
          strokeWidth={strokeWidth}
          fill="none"
        />
        <AnimatedCircle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={`${circumference} ${circumference}`}
          animatedProps={animatedProps}
          strokeLinecap="round"
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      <View style={[styles.center, { width: size, height: size }]}>
        <Text style={[styles.value, { fontSize: size * 0.26 }]}>{Math.round(clamped)}</Text>
        {label ? <Text style={styles.label}>{label}</Text> : null}
        {sublabel ? <Text style={styles.sublabel}>{sublabel}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { position: 'relative', justifyContent: 'center', alignItems: 'center' },
  center: { position: 'absolute', justifyContent: 'center', alignItems: 'center' },
  value: { fontWeight: Typography.weights.bold, color: Colors.white },
  label: { fontSize: Typography.sizes.xs, color: 'rgba(255,255,255,0.85)', marginTop: 2, fontWeight: Typography.weights.semibold },
  sublabel: { fontSize: Typography.sizes.xs - 1, color: 'rgba(255,255,255,0.65)' },
});
