import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, KeyboardAvoidingView, Platform, Image,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { useLogin } from '../../hooks/useAuth';
import Button from '../../components/common/Button';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { AuthStackParams } from '../../navigation/AuthNavigator';

type Nav = NativeStackNavigationProp<AuthStackParams>;

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const { mutate: login, isPending, error } = useLogin();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState({ email: false, password: false });

  const emailError = touched.email && !email.includes('@') ? 'Enter a valid email' : '';
  const passwordError = touched.password && password.length < 6 ? 'Minimum 6 characters' : '';
  const canSubmit = email.includes('@') && password.length >= 6;

  const handleLogin = () => {
    setTouched({ email: true, password: true });
    if (!canSubmit) return;
    login({ email, password });
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + Spacing.xl }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Logo & Branding */}
        <View style={styles.brandBlock}>
          <View style={styles.logoCircle}>
            <Ionicons name="school" size={44} color={Colors.white} />
          </View>
          <Text style={styles.appName}>EduAI Platform</Text>
          <Text style={styles.tagline}>AI-Powered Education Governance</Text>
        </View>

        {/* Login Card */}
        <View style={styles.card}>
          <Text style={styles.heading}>Welcome Back</Text>
          <Text style={styles.subheading}>Sign in to continue</Text>

          {/* Email */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>Email Address</Text>
            <View style={[styles.inputWrap, emailError ? styles.inputError : null]}>
              <Ionicons name="mail-outline" size={20} color={Colors.neutral[400]} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                value={email}
                onChangeText={setEmail}
                onBlur={() => setTouched((t) => ({ ...t, email: true }))}
                placeholder="you@edu.gov.in"
                placeholderTextColor={Colors.neutral[400]}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
              />
            </View>
            {emailError ? <Text style={styles.errorText}>{emailError}</Text> : null}
          </View>

          {/* Password */}
          <View style={styles.fieldGroup}>
            <Text style={styles.fieldLabel}>Password</Text>
            <View style={[styles.inputWrap, passwordError ? styles.inputError : null]}>
              <Ionicons name="lock-closed-outline" size={20} color={Colors.neutral[400]} style={styles.inputIcon} />
              <TextInput
                style={[styles.input, styles.inputFlex]}
                value={password}
                onChangeText={setPassword}
                onBlur={() => setTouched((t) => ({ ...t, password: true }))}
                placeholder="••••••••"
                placeholderTextColor={Colors.neutral[400]}
                secureTextEntry={!showPassword}
                autoComplete="password"
              />
              <TouchableOpacity onPress={() => setShowPassword((s) => !s)} style={styles.eyeBtn}>
                <Ionicons
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  size={20}
                  color={Colors.neutral[400]}
                />
              </TouchableOpacity>
            </View>
            {passwordError ? <Text style={styles.errorText}>{passwordError}</Text> : null}
          </View>

          {/* API Error */}
          {error && (
            <View style={styles.apiError}>
              <Ionicons name="alert-circle" size={16} color={Colors.danger} />
              <Text style={styles.apiErrorText}>
                {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Login failed. Please try again.'}
              </Text>
            </View>
          )}

          {/* Forgot Password */}
          <TouchableOpacity
            onPress={() => navigation.navigate('ForgotPassword')}
            style={styles.forgotBtn}
          >
            <Text style={styles.forgotText}>Forgot Password?</Text>
          </TouchableOpacity>

          {/* Sign In */}
          <Button
            title="Sign In"
            onPress={handleLogin}
            loading={isPending}
            disabled={!canSubmit}
            fullWidth
            size="lg"
          />
        </View>

        {/* Footer */}
        <Text style={styles.footer}>
          © 2025 EduAI Governance Platform{'\n'}Secure • Reliable • AI-Powered
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.primary[700] },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing['2xl'],
  },
  brandBlock: {
    alignItems: 'center',
    marginBottom: Spacing['2xl'],
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  appName: {
    fontSize: Typography.sizes['3xl'],
    fontWeight: Typography.weights.bold,
    color: Colors.white,
  },
  tagline: {
    fontSize: Typography.sizes.base,
    color: 'rgba(255,255,255,0.75)',
    marginTop: 4,
  },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 24,
    padding: Spacing.xl,
    ...Shadows.lg,
  },
  heading: {
    fontSize: Typography.sizes['2xl'],
    fontWeight: Typography.weights.bold,
    color: Colors.neutral[900],
  },
  subheading: {
    fontSize: Typography.sizes.base,
    color: Colors.neutral[500],
    marginTop: 4,
    marginBottom: Spacing.xl,
  },
  fieldGroup: { marginBottom: Spacing.base },
  fieldLabel: {
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
  inputError: { borderColor: Colors.danger },
  inputIcon: { marginRight: Spacing.sm },
  input: {
    flex: 1,
    fontSize: Typography.sizes.base,
    color: Colors.neutral[900],
  },
  inputFlex: { flex: 1 },
  eyeBtn: { padding: Spacing.xs },
  errorText: {
    fontSize: Typography.sizes.xs,
    color: Colors.danger,
    marginTop: 4,
  },
  apiError: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef2f2',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    gap: Spacing.sm,
  },
  apiErrorText: { fontSize: Typography.sizes.sm, color: Colors.danger, flex: 1 },
  forgotBtn: { alignSelf: 'flex-end', marginBottom: Spacing.lg },
  forgotText: {
    fontSize: Typography.sizes.sm,
    color: Colors.primary[600],
    fontWeight: Typography.weights.semibold,
  },
  footer: {
    textAlign: 'center',
    color: 'rgba(255,255,255,0.55)',
    fontSize: Typography.sizes.xs,
    marginTop: Spacing.xl,
    lineHeight: 18,
  },
});
