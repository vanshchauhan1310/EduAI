import React from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { CopilotStackParams } from '../../navigation/CopilotNavigator';

type Nav = NativeStackNavigationProp<CopilotStackParams>;

interface FeatureCard {
  title: string;
  subtitle: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  screen: keyof CopilotStackParams;
  metric: string;
  roles?: string[];
  requiresMandal?: boolean;
}

const FEATURES: FeatureCard[] = [
  {
    title: 'Circular Intelligence',
    subtitle: 'PDF summaries, action items, deadlines, compliance notes',
    icon: 'document-text-outline',
    color: '#2563eb',
    screen: 'Circular',
    metric: 'PDF',
  },
  {
    title: 'Telugu-English Desk',
    subtitle: 'Formal translation for notices, circulars, reports, and letters',
    icon: 'language-outline',
    color: '#d97706',
    screen: 'Translation',
    metric: '2',
  },
  {
    title: 'School Health Analyzer',
    subtitle: 'Mandal cluster health comparison and AI recommendations',
    icon: 'bandage-outline',
    color: '#1d4ed8',
    screen: 'SchoolHealthAnalyzer',
    metric: 'MEO',
    roles: ['MEO'],
    requiresMandal: true,
  },
  {
    title: 'MEO Report Generator',
    subtitle: 'Template-based Early Warning, Teacher Vacancy, Governance Communications & Cluster Briefings with PDF/DOCX export',
    icon: 'document-text-outline',
    color: '#0891b2',
    screen: 'MEOCopilotHome',
    metric: '4',
    roles: ['MEO'],
    requiresMandal: true,
  },
  {
    title: 'District Intelligence Briefing',
    subtitle: 'AI-powered daily district intelligence covering attendance, risks, teacher deployment and governance actions',
    icon: 'analytics-outline',
    color: '#dc2626',
    screen: 'DEODistrictIntelligence',
    metric: 'AI',
    roles: ['DEO'],
  },
  {
    title: 'Mandal Performance Analyzer',
    subtitle: 'Compare mandal performance metrics, rankings, and AI insights across the district',
    icon: 'bar-chart-outline',
    color: '#f97316',
    screen: 'DEOMandalPerformance',
    metric: 'DEO',
    roles: ['DEO'],
  },
  {
    title: 'District Risk Monitor',
    subtitle: 'Identify district-level risks, hotspot schools, and escalation recommendations',
    icon: 'warning-outline',
    color: '#dc2626',
    screen: 'DEORiskMonitor',
    metric: 'DEO',
    roles: ['DEO'],
  },
  {
    title: 'Teacher Rationalization',
    subtitle: 'Optimize teacher allocation with surplus/deficit analysis and AI deployment recommendations',
    icon: 'people-outline',
    color: '#059669',
    screen: 'DEOTeacherRationalization',
    metric: 'DEO',
    roles: ['DEO'],
  },
  {
    title: 'Governance Communication',
    subtitle: 'Generate official district circulars, notices, and directives using AI with 8+ templates',
    icon: 'megaphone-outline',
    color: '#7c3aed',
    screen: 'DEOGovernanceCommunication',
    metric: '8',
    roles: ['DEO'],
  },
];

const ROLE_SUMMARY: Record<string, string> = {
  HM: 'School administration workspace',
  MEO: 'Mandal operations workspace',
  DEO: 'District governance workspace',
};

function FeatureTile({ feature, onPress }: { feature: FeatureCard; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.tile} onPress={onPress} activeOpacity={0.9}>
      <View style={styles.tileTop}>
        <View style={[styles.tileIcon, { backgroundColor: `${feature.color}14` }]}>
          <Ionicons name={feature.icon} size={24} color={feature.color} />
        </View>
        <View style={[styles.metricPill, { borderColor: `${feature.color}33` }]}>
          <Text style={[styles.metricText, { color: feature.color }]}>{feature.metric}</Text>
        </View>
      </View>
      <Text style={styles.tileTitle}>{feature.title}</Text>
      <Text style={styles.tileSubtitle}>{feature.subtitle}</Text>
      <View style={styles.tileAction}>
        <Text style={[styles.tileActionText, { color: feature.color }]}>Open workspace</Text>
        <Ionicons name="arrow-forward" size={16} color={feature.color} />
      </View>
    </TouchableOpacity>
  );
}

export default function AdminCopilotHomeScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<Nav>();
  const user = useAuthStore((s) => s.user);
  const role = user?.role ?? 'ADMIN';
  const roleSummary = ROLE_SUMMARY[role] ?? 'Administration workspace';

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <StatusBar barStyle="light-content" backgroundColor="#101827" />

      <View style={[styles.header, { paddingTop: insets.top + Spacing.md }]}>
        <View style={styles.headerTop}>
          <View style={styles.brandMark}>
            <Ionicons name="sparkles" size={22} color={Colors.white} />
          </View>
          <View style={styles.userBlock}>
            <Text style={styles.kicker}>Admin Copilot</Text>
            <Text style={styles.userName} numberOfLines={1}>{user?.full_name ?? 'Education Officer'}</Text>
          </View>
          <View style={styles.roleBadge}>
            <Text style={styles.roleBadgeText}>{role}</Text>
          </View>
        </View>

        <Text style={styles.headline}>AI command center for education governance</Text>
        <Text style={styles.subhead}>{roleSummary} powered by AI.</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Workspaces</Text>
          <Text style={styles.sectionMeta}>HM, MEO, DEO ready</Text>
        </View>

        {FEATURES.filter((feature) => (!feature.roles || feature.roles.includes(role)) && (!feature.requiresMandal || !!user?.mandal_id)).map((feature) => (
          <FeatureTile
            key={feature.screen}
            feature={feature}
            onPress={() => navigation.navigate(feature.screen as any)}
          />
        ))}

        <View style={styles.auditBand}>
          <Ionicons name="shield-checkmark-outline" size={20} color={Colors.neutral[700]} />
          <View style={styles.auditTextWrap}>
            <Text style={styles.auditTitle}>Review before issuing</Text>
            <Text style={styles.auditCopy}>Generated content is stored in history and should be approved by the responsible officer.</Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#f5f7fb' },
  header: {
    backgroundColor: '#101827',
    paddingHorizontal: Spacing.base,
    paddingBottom: Spacing.xl,
  },
  headerTop: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.lg },
  brandMark: {
    width: 44,
    height: 44,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563eb',
  },
  userBlock: { flex: 1 },
  kicker: { fontSize: Typography.sizes.xs, color: '#9fb4d4', fontWeight: Typography.weights.semibold, textTransform: 'uppercase' },
  userName: { fontSize: Typography.sizes.md, color: Colors.white, fontWeight: Typography.weights.bold, marginTop: 2 },
  roleBadge: {
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
  },
  roleBadgeText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  headline: { fontSize: Typography.sizes['2xl'], color: Colors.white, fontWeight: Typography.weights.bold, lineHeight: 30 },
  subhead: { color: '#b8c5d9', fontSize: Typography.sizes.sm, marginTop: Spacing.sm, lineHeight: 20 },
  scroll: { padding: Spacing.base, paddingBottom: Spacing['3xl'] },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  sectionTitle: { fontSize: Typography.sizes.lg, color: Colors.neutral[900], fontWeight: Typography.weights.bold },
  sectionMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], fontWeight: Typography.weights.semibold },
  tile: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: '#e8edf5',
    ...Shadows.sm,
  },
  tileTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  tileIcon: { width: 48, height: 48, borderRadius: BorderRadius.md, alignItems: 'center', justifyContent: 'center' },
  metricPill: { borderWidth: 1, borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 4 },
  metricText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  tileTitle: { fontSize: Typography.sizes.lg, color: Colors.neutral[900], fontWeight: Typography.weights.bold },
  tileSubtitle: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20, marginTop: 4 },
  tileAction: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: Spacing.md },
  tileActionText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  auditBand: {
    flexDirection: 'row',
    gap: Spacing.md,
    backgroundColor: '#eef2f7',
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: '#dde5ef',
  },
  auditTextWrap: { flex: 1 },
  auditTitle: { color: Colors.neutral[900], fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold },
  auditCopy: { color: Colors.neutral[600], fontSize: Typography.sizes.xs, lineHeight: 18, marginTop: 2 },
});
