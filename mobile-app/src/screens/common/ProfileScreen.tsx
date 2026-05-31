import React from 'react';
import { Alert, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import { useLogout } from '../../hooks/useAuth';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

const ROLE_LABELS: Record<string, string> = {
  DEO: 'District Education Officer',
  MEO: 'Mandal Education Officer',
  HM: 'Head Master',
  TEACHER: 'Teacher',
  STUDENT: 'Student',
  PARENT: 'Parent',
};

const ROLE_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  DEO: 'business',
  MEO: 'map',
  HM: 'school',
  TEACHER: 'people',
  STUDENT: 'book',
  PARENT: 'person',
};

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const { mutate: logout, isPending } = useLogout();

  const roleLabel = user ? ROLE_LABELS[user.role] ?? user.role : 'User';
  const roleIcon = user ? ROLE_ICONS[user.role] ?? 'person' : 'person';

  const confirmLogout = () => {
    Alert.alert('Logout', `Do you want to sign out of the ${roleLabel} account?`, [
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
            <Ionicons name={roleIcon} size={46} color="#d6b354" />
          </View>
          <View style={styles.profileBody}>
            <Text style={styles.name}>{user?.full_name ?? 'EduAI User'}</Text>
            <View style={styles.rolePill}>
              <Text style={styles.rolePillText}>{roleLabel}</Text>
            </View>
            <Text style={styles.designation}>{user?.email ?? 'No email available'}</Text>
          </View>
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.cardTitle}>Contact Information</Text>
          {[
            ['mail-outline', user?.email ?? 'Not available'],
            ['person-outline', `User ID: ${user?.id ?? 'N/A'}`],
            ['ribbon-outline', `Role: ${roleLabel}`],
            ['school-outline', `School ID: ${user?.school_id ?? 'N/A'}`],
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
              <Text style={styles.accountSubtitle}>Update your profile information</Text>
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
