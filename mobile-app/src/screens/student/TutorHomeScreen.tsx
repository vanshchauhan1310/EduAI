import React, { useMemo, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import StatsCard from '../../components/common/StatsCard';
import GradientPanel from '../../components/common/GradientPanel';
import MasteryRing from '../../components/common/MasteryRing';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { TUTOR_CURRICULUM, TUTOR_LANGUAGES, PASS_THRESHOLD } from '../../constants';
import { useConceptMastery, useRecentConcepts } from '../../hooks/useAiTutor';
import { MasteryLevel, TutorLanguage } from '../../types';

const LEVEL_STYLE: Record<MasteryLevel, { color: string; tint: string }> = {
  Beginner: { color: '#f59e0b', tint: '#fef3c7' },
  Intermediate: { color: Colors.primary[600], tint: Colors.primary[100] },
  Advanced: { color: Colors.success, tint: '#dcfce7' },
};

function levelFor(mastery: number): MasteryLevel {
  if (mastery <= 40) return 'Beginner';
  if (mastery <= 70) return 'Intermediate';
  return 'Advanced';
}

export default function TutorHomeScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();

  const subjects = Object.keys(TUTOR_CURRICULUM);
  const [subject, setSubject] = useState(subjects[0]);
  const chapters = Object.keys(TUTOR_CURRICULUM[subject].chapters);
  const [chapter, setChapter] = useState(chapters[0]);
  const concepts = TUTOR_CURRICULUM[subject].chapters[chapter];
  const [concept, setConcept] = useState(concepts[0]);
  const [language, setLanguage] = useState<TutorLanguage>('english');

  // Selecting a subject resets its chapter/concept to the first available.
  const onSelectSubject = (s: string) => {
    setSubject(s);
    const firstChapter = Object.keys(TUTOR_CURRICULUM[s].chapters)[0];
    setChapter(firstChapter);
    setConcept(TUTOR_CURRICULUM[s].chapters[firstChapter][0]);
  };
  const onSelectChapter = (c: string) => {
    setChapter(c);
    setConcept(TUTOR_CURRICULUM[subject].chapters[c][0]);
  };

  const masteryQuery = useConceptMastery(subject, concept);
  const recentQuery = useRecentConcepts(4);
  const mastery = masteryQuery.data?.mastery ?? 0;
  const level = levelFor(mastery);
  const levelStyle = LEVEL_STYLE[level];

  const recent = recentQuery.data ?? [];
  const continueItem = recent[0];

  const goGenerate = () => navigation.navigate('TutorSession', { subject, chapter, concept, mastery, language });
  const goChat = () => navigation.navigate('TutorChat');
  const goStudyMaterial = () => navigation.navigate('TutorKnowledgeBase', { subject, chapter });

  const greeting = useMemo(() => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  }, []);

  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      <ScrollView
        style={styles.flex}
        contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + Spacing['2xl'] }]}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Gradient hero ──────────────────────────────────────────── */}
        <GradientPanel colors={[Colors.secondary[500], Colors.primary[600]]} style={styles.hero} radius={BorderRadius['2xl']}>
          <View style={styles.heroTop}>
            <View style={styles.heroTextBlock}>
              <View style={styles.heroBadge}>
                <Ionicons name="sparkles" size={14} color={Colors.white} />
                <Text style={styles.heroBadgeText}>AI Tutor</Text>
              </View>
              <Text style={styles.heroGreeting}>{greeting} 👋</Text>
              <Text style={styles.heroTitle}>Ready for today's{'\n'}learning sprint?</Text>
              <View style={[styles.levelPill, { backgroundColor: 'rgba(255,255,255,0.18)' }]}>
                <View style={[styles.levelDot, { backgroundColor: levelStyle.color }]} />
                <Text style={styles.levelPillText}>{level} · {concept}</Text>
              </View>
            </View>
            <MasteryRing value={mastery} size={104} strokeWidth={10} label="mastery" gradientId="homeRing" trackColor="rgba(255,255,255,0.22)" />
          </View>

          {continueItem && (
            <TouchableOpacity
              style={styles.continueRow}
              activeOpacity={0.85}
              onPress={() => navigation.navigate('TutorSession', {
                subject: continueItem.subject, chapter: continueItem.chapter,
                concept: continueItem.concept, mastery: continueItem.mastery, language,
              })}
            >
              <Ionicons name="play-circle" size={22} color={Colors.white} />
              <Text style={styles.continueText} numberOfLines={1}>
                Continue: <Text style={styles.continueBold}>{continueItem.concept}</Text> ({Math.round(continueItem.mastery)}% mastered)
              </Text>
              <Ionicons name="chevron-forward" size={18} color="rgba(255,255,255,0.8)" />
            </TouchableOpacity>
          )}
        </GradientPanel>

        {/* ── Quick stats ────────────────────────────────────────────── */}
        <View style={styles.statsRow}>
          <StatsCard label="Mastery" value={`${Math.round(mastery)}/100`} icon="trending-up" accent={Colors.secondary[600]} />
          <StatsCard label="Level" value={level} icon="ribbon" accent={levelStyle.color} />
          <StatsCard label="Pass mark" value={`${PASS_THRESHOLD}%`} icon="flag" accent={Colors.primary[600]} />
        </View>

        {/* ── Subject / chapter / concept picker ─────────────────────── */}
        <Text style={styles.sectionTitle}>What would you like to study?</Text>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          {subjects.map((s) => {
            const active = s === subject;
            return (
              <TouchableOpacity key={s} onPress={() => onSelectSubject(s)} activeOpacity={0.85}
                style={[styles.subjectChip, active && styles.subjectChipActive]}>
                <View style={[styles.subjectIconWrap, { backgroundColor: active ? 'rgba(255,255,255,0.2)' : `${Colors.primary[600]}14` }]}>
                  <Ionicons name={TUTOR_CURRICULUM[s].icon as any} size={18} color={active ? Colors.white : Colors.primary[600]} />
                </View>
                <Text style={[styles.subjectChipText, active && styles.subjectChipTextActive]}>{s}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          {chapters.map((c) => {
            const active = c === chapter;
            return (
              <TouchableOpacity key={c} onPress={() => onSelectChapter(c)} activeOpacity={0.85}
                style={[styles.chapterChip, active && styles.chapterChipActive]}>
                <Text style={[styles.chapterChipText, active && styles.chapterChipTextActive]} numberOfLines={1}>{c}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        <Card padding="sm" style={styles.conceptCard}>
          {concepts.map((c, i) => {
            const active = c === concept;
            return (
              <TouchableOpacity key={c} onPress={() => setConcept(c)} activeOpacity={0.7}
                style={[styles.conceptRow, i < concepts.length - 1 && styles.conceptRowDivider]}>
                <View style={[styles.radio, active && styles.radioActive]}>
                  {active && <View style={styles.radioDot} />}
                </View>
                <Text style={[styles.conceptText, active && styles.conceptTextActive]}>{c}</Text>
                {active && <Ionicons name="checkmark-circle" size={18} color={Colors.secondary[600]} />}
              </TouchableOpacity>
            );
          })}
        </Card>

        {/* ── Language ───────────────────────────────────────────────── */}
        <Text style={styles.sectionTitle}>Lesson language</Text>
        <View style={styles.langRow}>
          {TUTOR_LANGUAGES.map((l) => {
            const active = l.value === language;
            return (
              <TouchableOpacity key={l.value} onPress={() => setLanguage(l.value)} activeOpacity={0.85}
                style={[styles.langPill, active && styles.langPillActive]}>
                <Text style={[styles.langPillText, active && styles.langPillTextActive]}>{l.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* ── My Study Material ──────────────────────────────────────── */}
        <TouchableOpacity activeOpacity={0.85} onPress={goStudyMaterial}>
          <Card style={styles.materialCard}>
            <View style={[styles.materialIconWrap]}>
              <Ionicons name="library" size={22} color={Colors.secondary[600]} />
            </View>
            <View style={styles.materialTextBlock}>
              <Text style={styles.materialTitle}>My Study Material</Text>
              <Text style={styles.materialDesc}>Upload your textbook chapter or notes (PDF or scan) so lessons & quizzes are grounded in exactly what your school teaches.</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={Colors.neutral[400]} />
          </Card>
        </TouchableOpacity>

        {/* ── CTAs ───────────────────────────────────────────────────── */}
        <View style={styles.ctaRow}>
          <Button title="✨ Generate my lesson" onPress={goGenerate} size="lg" fullWidth style={styles.ctaPrimary} />
        </View>
        <Button title="💬 Ask a doubt" onPress={goChat} variant="outline" size="lg" fullWidth />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: Spacing.base, gap: Spacing.lg },

  hero: { padding: Spacing.lg, gap: Spacing.md },
  heroTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: Spacing.md },
  heroTextBlock: { flex: 1, gap: Spacing.xs },
  heroBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', backgroundColor: 'rgba(255,255,255,0.18)', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 3 },
  heroBadgeText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, letterSpacing: 0.5 },
  heroGreeting: { color: 'rgba(255,255,255,0.85)', fontSize: Typography.sizes.sm, fontWeight: Typography.weights.medium },
  heroTitle: { color: Colors.white, fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, lineHeight: 26 },
  levelPill: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start', borderRadius: BorderRadius.full, paddingHorizontal: Spacing.sm, paddingVertical: 4, marginTop: 2 },
  levelDot: { width: 8, height: 8, borderRadius: 4 },
  levelPillText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },

  continueRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, backgroundColor: 'rgba(255,255,255,0.14)', borderRadius: BorderRadius.lg, padding: Spacing.sm, marginTop: Spacing.xs },
  continueText: { flex: 1, color: 'rgba(255,255,255,0.92)', fontSize: Typography.sizes.sm },
  continueBold: { fontWeight: Typography.weights.bold, color: Colors.white },

  statsRow: { flexDirection: 'row', gap: Spacing.sm },

  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[800], marginTop: Spacing.xs },

  chipRow: { gap: Spacing.sm, paddingVertical: 2 },
  subjectChip: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs, backgroundColor: Colors.white, borderRadius: BorderRadius.full, paddingVertical: Spacing.xs, paddingHorizontal: Spacing.md, borderWidth: 1.5, borderColor: Colors.border },
  subjectChipActive: { backgroundColor: Colors.secondary[600], borderColor: Colors.secondary[600] },
  subjectIconWrap: { width: 28, height: 28, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  subjectChipText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700] },
  subjectChipTextActive: { color: Colors.white },

  chapterChip: { backgroundColor: Colors.white, borderRadius: BorderRadius.lg, paddingVertical: Spacing.xs + 2, paddingHorizontal: Spacing.md, borderWidth: 1, borderColor: Colors.border, maxWidth: 220 },
  chapterChipActive: { backgroundColor: Colors.primary[50], borderColor: Colors.primary[400] },
  chapterChipText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600] },
  chapterChipTextActive: { color: Colors.primary[700], fontWeight: Typography.weights.semibold },

  conceptCard: { gap: 0 },
  conceptRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, paddingVertical: Spacing.sm + 2, paddingHorizontal: Spacing.xs },
  conceptRowDivider: { borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },
  radio: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: Colors.neutral[300], justifyContent: 'center', alignItems: 'center' },
  radioActive: { borderColor: Colors.secondary[600] },
  radioDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: Colors.secondary[600] },
  conceptText: { flex: 1, fontSize: Typography.sizes.sm, color: Colors.neutral[700] },
  conceptTextActive: { color: Colors.neutral[900], fontWeight: Typography.weights.semibold },

  langRow: { flexDirection: 'row', gap: Spacing.sm },
  langPill: { flex: 1, alignItems: 'center', backgroundColor: Colors.white, borderRadius: BorderRadius.lg, paddingVertical: Spacing.sm, borderWidth: 1.5, borderColor: Colors.border },
  langPillActive: { backgroundColor: Colors.primary[600], borderColor: Colors.primary[600] },
  langPillText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[600] },
  langPillTextActive: { color: Colors.white },

  materialCard: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  materialIconWrap: { width: 44, height: 44, borderRadius: BorderRadius.lg, backgroundColor: `${Colors.secondary[600]}16`, justifyContent: 'center', alignItems: 'center' },
  materialTextBlock: { flex: 1, gap: 2 },
  materialTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  materialDesc: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], lineHeight: 17 },

  ctaRow: { marginTop: Spacing.xs },
  ctaPrimary: { backgroundColor: Colors.secondary[600] },
});
