import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { useMyCareerRecommendations, useGenerateCareerRecommendations } from '../../hooks/useCareer';
import {
  CareerStreamRecommendation,
  CareerPath,
  CareerSkillCourse,
  CareerScholarship,
} from '../../types';

const SECTOR_STYLES: Record<string, { icon: keyof typeof Ionicons.glyphMap; tint: string }> = {
  BFSI: { icon: 'cash', tint: Colors.success },
  IT: { icon: 'laptop', tint: Colors.primary[600] },
  Pharma: { icon: 'medkit', tint: Colors.danger },
  Manufacturing: { icon: 'construct', tint: Colors.warning },
  Education: { icon: 'school', tint: Colors.secondary[600] },
  'Public Service': { icon: 'business', tint: Colors.neutral[600] },
};

function sectorStyle(sector: string) {
  return SECTOR_STYLES[sector] || { icon: 'briefcase', tint: Colors.secondary[600] };
}

export default function CareerRecommenderScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const { data, isLoading, isError } = useMyCareerRecommendations();
  const { mutate: generate, isPending: isGenerating } = useGenerateCareerRecommendations();

  const handleGenerate = () => {
    generate(undefined, {
      onError: (error: any) => {
        alert(`Could not generate recommendations: ${error.response?.data?.detail || error.message}`);
      },
    });
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading your career profile..." />;
  }

  if (isGenerating) {
    return <LoadingSpinner fullScreen message="Analysing your aptitude, interests and academic record…" />;
  }

  const surveyCompleted = !!data?.survey_completed;
  const recommendation = data?.recommendation;

  return (
    <View style={[styles.flex]}>
      <Header
        title="Career & Skill Recommender"
        subtitle="AI-matched paths based on you"
        onBack={() => navigation.goBack()}
      />

      <ScrollView
        style={styles.flex}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + Spacing.xl }]}
        showsVerticalScrollIndicator={false}
      >
        {!surveyCompleted && (
          <Card style={styles.ctaCard}>
            <View style={[styles.ctaIconWrap, { backgroundColor: Colors.secondary[600] + '16' }]}>
              <Ionicons name="compass" size={28} color={Colors.secondary[600]} />
            </View>
            <Text style={styles.ctaTitle}>Discover Your Path</Text>
            <Text style={styles.ctaText}>
              Take a quick 2-minute survey about your interests and working style. We'll combine
              your answers with your real academic record and attendance to suggest streams,
              careers, skill courses and scholarships matched just for you.
            </Text>
            <Button
              title="Take the Career Survey"
              onPress={() => navigation.navigate('CareerSurvey')}
              size="lg"
              fullWidth
              style={styles.ctaBtn}
            />
          </Card>
        )}

        {surveyCompleted && !recommendation && (
          <Card style={styles.ctaCard}>
            <View style={[styles.ctaIconWrap, { backgroundColor: Colors.primary[600] + '16' }]}>
              <Ionicons name="rocket" size={28} color={Colors.primary[600]} />
            </View>
            <Text style={styles.ctaTitle}>Ready to Discover My Path</Text>
            <Text style={styles.ctaText}>
              Your survey is saved. Tap below and our AI will analyse your interests, subject-wise
              performance and attendance to build your personalised career profile.
            </Text>
            <Button
              title="Discover My Path"
              onPress={handleGenerate}
              size="lg"
              fullWidth
              style={styles.ctaBtn}
            />
            <TouchableOpacity onPress={() => navigation.navigate('CareerSurvey')} style={styles.retakeLink}>
              <Text style={styles.retakeLinkText}>Retake the survey</Text>
            </TouchableOpacity>
          </Card>
        )}

        {isError && (
          <Card style={styles.ctaCard}>
            <Ionicons name="alert-circle-outline" size={48} color={Colors.danger} />
            <Text style={styles.ctaTitle}>Couldn't load your profile</Text>
            <Text style={styles.ctaText}>Please check your connection and try again.</Text>
          </Card>
        )}

        {recommendation && (
          <>
            {/* Profile summary — uses the established AI-insight visual language */}
            <Card style={styles.aiSummaryCard} padding="lg">
              <View style={styles.aiCardHeader}>
                <View style={[styles.aiIconWrap, { backgroundColor: Colors.secondary[600] + '16' }]}>
                  <Ionicons name="sparkles" size={20} color={Colors.secondary[600]} />
                </View>
                <View style={[styles.aiTagPill, { backgroundColor: Colors.secondary[600] + '16' }]}>
                  <Text style={[styles.aiTagText, { color: Colors.secondary[600] }]}>Your Profile</Text>
                </View>
              </View>
              <Text style={styles.aiCardTitle}>AI-Personalised Summary</Text>
              <Text style={styles.aiCardText}>{recommendation.summary}</Text>
              {data?.generated_at && (
                <Text style={styles.generatedAt}>
                  Generated {new Date(data.generated_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                </Text>
              )}
            </Card>

            {/* Recommended streams */}
            <Text style={styles.sectionTitle}>Recommended Streams</Text>
            <Card style={styles.sectionCard}>
              {recommendation.recommended_streams.map((stream: CareerStreamRecommendation, idx: number) => (
                <View key={idx} style={[styles.streamRow, idx !== recommendation.recommended_streams.length - 1 && styles.rowDivider]}>
                  <View style={styles.streamHeaderRow}>
                    <Text style={styles.streamName}>{stream.stream}</Text>
                    <Text style={styles.streamMatch}>{stream.match_percent}% match</Text>
                  </View>
                  <View style={styles.matchBarBg}>
                    <View
                      style={[
                        styles.matchBarFill,
                        { width: `${stream.match_percent}%`, backgroundColor: stream.match_percent >= 75 ? Colors.success : stream.match_percent >= 50 ? Colors.primary[600] : Colors.warning },
                      ]}
                    />
                  </View>
                  <Text style={styles.streamWhy}>{stream.why}</Text>
                </View>
              ))}
            </Card>

            {/* Career pathways */}
            <Text style={styles.sectionTitle}>Career Pathways</Text>
            <View style={styles.pathList}>
              {recommendation.career_paths.map((path: CareerPath, idx: number) => {
                const sStyle = sectorStyle(path.sector);
                return (
                  <Card key={idx} style={styles.pathCard} padding="md">
                    <View style={styles.pathHeaderRow}>
                      <View style={[styles.pathIconWrap, { backgroundColor: sStyle.tint + '16' }]}>
                        <Ionicons name={sStyle.icon} size={20} color={sStyle.tint} />
                      </View>
                      <View style={[styles.sectorPill, { backgroundColor: sStyle.tint + '16' }]}>
                        <Text style={[styles.sectorPillText, { color: sStyle.tint }]}>{path.sector}</Text>
                      </View>
                    </View>
                    <Text style={styles.pathTitle}>{path.title}</Text>
                    <Text style={styles.pathDescription}>{path.description}</Text>
                  </Card>
                );
              })}
            </View>

            {/* Skill courses */}
            <Text style={styles.sectionTitle}>Skill Courses & Certifications</Text>
            <Card style={styles.sectionCard} padding="none">
              {recommendation.skill_courses.map((course: CareerSkillCourse, idx: number) => (
                <View key={idx} style={[styles.listRow, idx !== recommendation.skill_courses.length - 1 && styles.rowDivider]}>
                  <View style={[styles.listIconWrap, { backgroundColor: Colors.primary[600] + '16' }]}>
                    <Ionicons name="school" size={18} color={Colors.primary[600]} />
                  </View>
                  <View style={styles.listInfo}>
                    <Text style={styles.listTitle}>{course.name}</Text>
                    <Text style={styles.listMeta}>{course.provider} • {course.duration}</Text>
                  </View>
                </View>
              ))}
            </Card>

            {/* Scholarships */}
            <Text style={styles.sectionTitle}>Scholarships & Support</Text>
            <Card style={styles.sectionCard} padding="none">
              {recommendation.scholarships.map((scholarship: CareerScholarship, idx: number) => (
                <View key={idx} style={[styles.scholarshipRow, idx !== recommendation.scholarships.length - 1 && styles.rowDivider]}>
                  <View style={styles.listHeaderRow}>
                    <View style={[styles.listIconWrap, { backgroundColor: Colors.success + '16' }]}>
                      <Ionicons name="ribbon" size={18} color={Colors.success} />
                    </View>
                    <Text style={styles.listTitle}>{scholarship.name}</Text>
                  </View>
                  <Text style={styles.scholarshipDetail}><Text style={styles.scholarshipLabel}>Eligibility: </Text>{scholarship.eligibility}</Text>
                  <Text style={styles.scholarshipDetail}><Text style={styles.scholarshipLabel}>How to apply: </Text>{scholarship.how_to_apply}</Text>
                </View>
              ))}
            </Card>

            <View style={styles.actionsRow}>
              <Button
                title="Retake Survey"
                onPress={() => navigation.navigate('CareerSurvey')}
                variant="outline"
                style={styles.actionBtn}
              />
              <Button
                title="Regenerate"
                onPress={handleGenerate}
                style={styles.actionBtn}
              />
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  scrollContent: { padding: Spacing.base, paddingTop: Spacing.lg },

  ctaCard: { alignItems: 'center', padding: Spacing.xl, marginBottom: Spacing.xl },
  ctaIconWrap: { width: 60, height: 60, borderRadius: BorderRadius.xl, justifyContent: 'center', alignItems: 'center', marginBottom: Spacing.md },
  ctaTitle: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900], textAlign: 'center', marginBottom: Spacing.sm },
  ctaText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], textAlign: 'center', lineHeight: 21 },
  ctaBtn: { marginTop: Spacing.lg },
  retakeLink: { marginTop: Spacing.md },
  retakeLinkText: { fontSize: Typography.sizes.sm, color: Colors.secondary[600], fontWeight: Typography.weights.semibold },

  sectionTitle: { fontSize: Typography.sizes.md, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.md },
  sectionCard: { marginBottom: Spacing.xl },
  rowDivider: { borderBottomWidth: 1, borderBottomColor: Colors.neutral[100] },

  // AI summary card — mirrors StudentDashboardScreen's aiCard visual language
  aiSummaryCard: { ...Shadows.sm, marginBottom: Spacing.xl },
  aiCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.md },
  aiIconWrap: { width: 40, height: 40, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  aiTagPill: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  aiTagText: { fontSize: 10, fontWeight: Typography.weights.bold, textTransform: 'uppercase', letterSpacing: 0.5 },
  aiCardTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.xs },
  aiCardText: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20 },
  generatedAt: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: Spacing.md },

  streamRow: { paddingVertical: Spacing.md },
  streamHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  streamName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  streamMatch: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.bold, color: Colors.primary[600] },
  matchBarBg: { height: 8, backgroundColor: Colors.neutral[100], borderRadius: 4, overflow: 'hidden', marginBottom: Spacing.sm },
  matchBarFill: { height: '100%', borderRadius: 4 },
  streamWhy: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20 },

  pathList: { gap: Spacing.sm, marginBottom: Spacing.xl },
  pathCard: {},
  pathHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  pathIconWrap: { width: 40, height: 40, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  sectorPill: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  sectorPillText: { fontSize: 10, fontWeight: Typography.weights.bold, textTransform: 'uppercase', letterSpacing: 0.5 },
  pathTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.xs },
  pathDescription: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], lineHeight: 20 },

  listRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.md },
  listIconWrap: { width: 38, height: 38, borderRadius: BorderRadius.lg, justifyContent: 'center', alignItems: 'center' },
  listInfo: { flex: 1 },
  listTitle: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  listMeta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },

  scholarshipRow: { paddingVertical: Spacing.md, paddingHorizontal: Spacing.md, gap: Spacing.xs },
  listHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.xs },
  scholarshipDetail: { fontSize: Typography.sizes.xs, color: Colors.neutral[600], lineHeight: 18, marginLeft: 50 },
  scholarshipLabel: { fontWeight: Typography.weights.semibold, color: Colors.neutral[700] },

  actionsRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  actionBtn: { flex: 1 },
});
