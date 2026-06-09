import React from 'react';
import { View, Text, Image, ActivityIndicator, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing } from '../../theme';

export default function SplashScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.logoCircle}>
        <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
      </View>
      <Text style={styles.appName}>EduAI</Text>
      <Text style={styles.tagline}>AI-Powered Education Governance</Text>
      <ActivityIndicator size="large" color="rgba(255,255,255,0.7)" style={styles.spinner} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary[600],
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing['2xl'],
  },
  logoCircle: {
    width: 108,
    height: 108,
    borderRadius: 54,
    backgroundColor: 'rgba(255,255,255,0.92)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.lg,
    overflow: 'hidden',
  },
  logo: {
    width: '100%',
    height: '100%',
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
