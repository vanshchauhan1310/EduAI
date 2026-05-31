import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';

const NOTIFICATIONS = [
  ['Class 8B attendance dropped to 82%', 'Attendance Intelligence', '1 hour ago', '#ef4444'],
  ['3 students absent for 5+ consecutive days', 'Dropout Prediction', '3 hours ago', '#ef4444'],
  ['Maths teacher absent - substitute needed', 'Teacher Performance', '8 am today', '#f59e0b'],
  ['Science lab utilization is only 34%', 'School Operations', 'Yesterday', '#06b6d4'],
];

export default function HMNotificationsScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation();

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color="#071a3a" />
        </TouchableOpacity>
        <Text style={styles.title}>Notifications</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {NOTIFICATIONS.map(([title, module, time, color]) => (
          <TouchableOpacity key={title} style={styles.card} activeOpacity={0.84}>
            <View style={[styles.icon, { backgroundColor: `${color}16` }]}>
              <Ionicons name="notifications-outline" size={22} color={color} />
            </View>
            <View style={styles.content}>
              <Text style={styles.notificationTitle}>{title}</Text>
              <Text style={styles.meta}>{module} - {time}</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color="#8a9ab3" />
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#edf3ff' },
  header: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, padding: Spacing.base },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: Colors.white, alignItems: 'center', justifyContent: 'center', ...Shadows.sm },
  title: { color: '#071a3a', fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  card: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, backgroundColor: Colors.white, borderRadius: BorderRadius.xl, padding: Spacing.md, marginBottom: Spacing.md, ...Shadows.sm },
  icon: { width: 48, height: 48, borderRadius: BorderRadius.lg, alignItems: 'center', justifyContent: 'center' },
  content: { flex: 1 },
  notificationTitle: { color: '#071a3a', fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold },
  meta: { color: '#536784', fontSize: Typography.sizes.sm, marginTop: 4 },
});
