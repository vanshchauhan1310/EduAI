import React, { useState } from 'react';
import {
  View, Text, TextInput, StyleSheet,
  KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useForgotPassword } from '../../hooks/useAuth';
import Button from '../../components/common/Button';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

export default function ForgotPasswordScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();
  const { mutate: forgotPassword, isPending, isSuccess, error } = useForgotPassword();

  const [email, setEmail] = useState('');

  const handleSubmit = () => {
    if (email.includes('@')) {
      forgotPassword(email);
    }
  };

  if (isSuccess) {
    return (
      <View style={[styles.flex, { paddingTop: insets.top }]}>
        <View style={styles.successCard}>
          <View style={styles.successIcon}>
            <Ionicons name="checkmark-circle" size={56} color={Colors.success} />
          </View>
          <Text style={styles.successTitle}>Check Your Email</Text>
          <Text style={styles.successBody}>
            A password reset link has been sent to {email}. Please check your inbox and spam folder.
          </Text>
          <Button title="Back to Login" onPress={() => navigation.goBack()} fullWidth size="lg" />
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + Spacing.xl }]}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <View style={styles.iconCircle}>
            <Ionicons name="key-outline" size={36} color={Colors.white} />
          </View>
          <Text style={styles.title}>Forgot Password?</Text>
          <Text style={styles.subtitle}>
            Enter your registered email address and we'll send you a reset link.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.label}>Email Address</Text>
          <View style={styles.inputWrap}>
            <Ionicons name="mail-outline" size={20} color={Colors.neutral[400]} style={styles.icon} />
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="you@edu.gov.in"
              placeholderTextColor={Colors.neutral[400]}
              keyboardType="email-address"
              autoCapitalize="none"
            />
          </View>

          {error && (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle" size={16} color={Colors.danger} />
              <Text style={styles.errorText}>Something went wrong. Please try again.</Text>
            </View>
          )}

          <Button
            title="Send Reset Link"
            onPress={handleSubmit}
            loading={isPending}
            disabled={!email.includes('@')}
            fullWidth
            size="lg"
            style={{ marginTop: Spacing.lg }}
          />

          <Button
            title="Back to Login"
            onPress={() => navigation.goBack()}
            variant="ghost"
            fullWidth
            size="md"
            style={{ marginTop: Spacing.sm }}
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.primary[700] },
  scroll: { flexGrow: 1, paddingHorizontal: Spacing.base, paddingBottom: Spacing['2xl'] },
  header: { alignItems: 'center', marginBottom: Spacing['2xl'] },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  title: { fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.white },
  subtitle: {
    fontSize: Typography.sizes.base,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
    marginTop: Spacing.sm,
    lineHeight: 22,
    paddingHorizontal: Spacing.lg,
  },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 24,
    padding: Spacing.xl,
    ...Shadows.lg,
  },
  label: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.semibold,
    color: Colors.neutral[700],
    marginBottom: Spacing.xs,
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: Colors.neutral[200],
    borderRadius: BorderRadius.lg,
    backgroundColor: Colors.neutral[50],
    paddingHorizontal: Spacing.md,
    height: 52,
  },
  icon: { marginRight: Spacing.sm },
  input: { flex: 1, fontSize: Typography.sizes.base, color: Colors.neutral[900] },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: '#fef2f2',
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    marginTop: Spacing.md,
  },
  errorText: { fontSize: Typography.sizes.sm, color: Colors.danger, flex: 1 },
  successCard: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing['2xl'],
    backgroundColor: Colors.white,
    margin: Spacing.xl,
    borderRadius: 24,
    ...Shadows.lg,
  },
  successIcon: { marginBottom: Spacing.lg },
  successTitle: {
    fontSize: Typography.sizes['2xl'],
    fontWeight: Typography.weights.bold,
    color: Colors.neutral[900],
    marginBottom: Spacing.md,
    textAlign: 'center',
  },
  successBody: {
    fontSize: Typography.sizes.base,
    color: Colors.neutral[500],
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: Spacing.xl,
  },
});
