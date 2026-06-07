import React from 'react';
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import { useLogout } from '../../hooks/useAuth';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

export default function HMProfileScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const { mutate: logout, isPending } = useLogout();

  const confirmLogout = () => {
    Alert.alert('Logout', 'Do you want to sign out of the Head Master account?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: () => logout() },
    ]);
  };

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.profileCard}>
          <View style={styles.cover} />
          <View style={styles.avatar}>
            <Ionicons name="school-outline" size={46} color="#d6b354" />
          </View>
          <View style={styles.profileBody}>
            <Text style={styles.name}>{user?.full_name ?? 'Head Master'}</Text>
            <View style={styles.rolePill}>
              <Text style={styles.rolePillText}>Head Master</Text>
            </View>
            <Text style={styles.designation}>Head Master - ZPHS Mandal Center</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          {[
            ['485', 'Students'],
            ['22', 'Teachers'],
            ['8.5 / 10', 'School Score'],
          ].map(([value, label]) => (
            <View key={label} style={styles.profileStat}>
              <Text style={styles.profileStatValue}>{value}</Text>
              <Text style={styles.profileStatLabel}>{label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.cardTitle}>Contact Information</Text>
          {[
            ['mail-outline', user?.email ?? 'headmaster@zphs.edu'],
            ['call-outline', '+91 98765 43217'],
            ['location-outline', 'Mandal Center, Warangal, Telangana'],
            ['calendar-outline', `Employee ID: HM${String(user?.id ?? 2024001).padStart(6, '0')}`],
          ].map(([icon, text]) => (
            <View key={text} style={styles.infoRow}>
              <Ionicons name={icon as any} size={23} color="#687893" />
              <Text style={styles.infoText}>{text}</Text>
            </View>
          ))}
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.cardTitle}>Account</Text>
          <TouchableOpacity style={styles.accountRow} onPress={() => Alert.alert('Profile', 'Profile editing will be available soon.')}>
            <View style={styles.accountIcon}>
              <Ionicons name="create-outline" size={22} color={Colors.primary[600]} />
            </View>
            <View style={styles.accountTextWrap}>
              <Text style={styles.accountTitle}>Edit Profile</Text>
              <Text style={styles.accountSubtitle}>Update contact and school details</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#8a9ab3" />
          </TouchableOpacity>

          <TouchableOpacity style={[styles.accountRow, styles.logoutRow]} onPress={confirmLogout} disabled={isPending}>
            <View style={[styles.accountIcon, styles.logoutIcon]}>
              <Ionicons name="log-out-outline" size={22} color={Colors.danger} />
            </View>
            <View style={styles.accountTextWrap}>
              <Text style={[styles.accountTitle, { color: Colors.danger }]}>{isPending ? 'Logging out...' : 'Logout'}</Text>
              <Text style={styles.accountSubtitle}>Sign out from this device</Text>
            </View>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#edf3ff' },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  profileCard: { backgroundColor: Colors.white, borderRadius: BorderRadius.xl, overflow: 'hidden', marginBottom: Spacing.lg, ...Shadows.sm },
  cover: { height: 104, backgroundColor: '#2b44d9' },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#12244b',
    borderWidth: 5,
    borderColor: Colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: -50,
    marginLeft: Spacing.xl,
  },
  profileBody: { paddingHorizontal: Spacing.xl, paddingTop: Spacing.md, paddingBottom: Spacing.xl },
  name: { color: '#071a3a', fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold },
  rolePill: { alignSelf: 'flex-start', backgroundColor: '#f5eddb', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.md, paddingVertical: 6, marginTop: Spacing.sm },
  rolePillText: { color: '#c29125', fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  designation: { color: '#536784', fontSize: Typography.sizes.base, marginTop: Spacing.lg },
  statsRow: { flexDirection: 'row', gap: Spacing.md, marginBottom: Spacing.lg },
  profileStat: { flex: 1, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.lg, alignItems: 'center', ...Shadows.sm },
  profileStatValue: { color: '#071a3a', fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold },
  profileStatLabel: { color: '#536784', fontSize: Typography.sizes.sm, marginTop: 4, textAlign: 'center' },
  infoCard: { backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.xl, marginBottom: Spacing.lg, ...Shadows.sm },
  cardTitle: { color: '#071a3a', fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, marginBottom: Spacing.lg },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.lg },
  infoText: { flex: 1, color: '#071a3a', fontSize: Typography.sizes.base },
  accountRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, paddingVertical: Spacing.md },
  logoutRow: { borderTopWidth: 1, borderTopColor: Colors.border, marginTop: Spacing.sm },
  accountIcon: { width: 44, height: 44, borderRadius: BorderRadius.lg, backgroundColor: Colors.primary[50], alignItems: 'center', justifyContent: 'center' },
  logoutIcon: { backgroundColor: '#fef2f2' },
  accountTextWrap: { flex: 1 },
  accountTitle: { color: '#071a3a', fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  accountSubtitle: { color: '#536784', fontSize: Typography.sizes.sm, marginTop: 2 },
});
