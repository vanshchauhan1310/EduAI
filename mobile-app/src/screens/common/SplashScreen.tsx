import React, { useEffect } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, Spacing } from '../../theme';

export default function SplashScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.logoCircle}>
        <Ionicons name="school" size={56} color={Colors.white} />
      </View>
      <Text style={styles.appName}>EduAI Platform</Text>
      <Text style={styles.tagline}>AI-Powered Education Governance</Text>
      <ActivityIndicator size="large" color="rgba(255,255,255,0.7)" style={styles.spinner} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary[700],
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing['2xl'],
  },
  logoCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  appName: {
    fontSize: Typography.sizes['3xl'],
    fontWeight: Typography.weights.bold,
    color: Colors.white,
    marginBottom: Spacing.sm,
  },
  tagline: {
    fontSize: Typography.sizes.base,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
  },
  spinner: {
    marginTop: Spacing['3xl'],
  },
});
