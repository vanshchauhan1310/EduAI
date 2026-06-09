import React, { useState } from 'react';
import { View, StyleSheet, ViewStyle, LayoutChangeEvent } from 'react-native';
import Svg, { Rect, Defs, LinearGradient, Stop } from 'react-native-svg';
import { BorderRadius } from '../../theme';

let nextId = 0;

interface GradientPanelProps {
  children?: React.ReactNode;
  colors: [string, string];
  style?: ViewStyle;
  radius?: number;
  angle?: 'diagonal' | 'horizontal' | 'vertical';
}

/**
 * Renders a gradient-filled panel using react-native-svg (already a dependency —
 * keeps the bundle lean rather than adding expo-linear-gradient). Used for the AI
 * Tutor's signature gradient hero banners, CTA cards and celebration panels.
 */
export default function GradientPanel({ children, colors, style, radius = BorderRadius.xl, angle = 'diagonal' }: GradientPanelProps) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [id] = useState(() => `gp-${nextId++}`);
  const [x2, y2] = angle === 'horizontal' ? ['100%', '0%'] : angle === 'vertical' ? ['0%', '100%'] : ['100%', '100%'];

  const onLayout = (e: LayoutChangeEvent) => {
    const { width, height } = e.nativeEvent.layout;
    setSize({ width, height });
  };

  return (
    <View style={[styles.container, { borderRadius: radius }, style]} onLayout={onLayout}>
      {size.width > 0 && (
        <Svg width={size.width} height={size.height} style={StyleSheet.absoluteFill}>
          <Defs>
            <LinearGradient id={id} x1="0%" y1="0%" x2={x2} y2={y2}>
              <Stop offset="0%" stopColor={colors[0]} />
              <Stop offset="100%" stopColor={colors[1]} />
            </LinearGradient>
          </Defs>
          <Rect x={0} y={0} width={size.width} height={size.height} fill={`url(#${id})`} />
        </Svg>
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { overflow: 'hidden' },
});
