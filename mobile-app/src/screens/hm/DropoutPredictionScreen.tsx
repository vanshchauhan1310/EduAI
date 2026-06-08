/**
 * DropoutPredictionScreen — HM Portal for Class-Wise Dropout Prediction
 *
 * UI/UX Flow:
 *   1. INITIAL STATE: Class selector + Predict button (full visible area)
 *   2. PREDICTING: Loading spinner over class panel
 *   3. RESULTS: Class panel collapses, results take full screen
 *      - Summary cards at top
 *      - Scrollable student list below
 *      - "Change Class" button in header to go back
 *   4. DETAIL OVERLAY: Tap student → modal with full details
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Animated,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useQueryClient } from '@tanstack/react-query';
import { dropoutService, PredictByClassResponse, ClassPredictionStudent } from '../../services/dropoutService';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius, Shadows } from '../../theme';
import { RISK_COLORS, CLASS_GRADES } from '../../constants';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

// ─── Utility ──────────────────────────────────────────────────

function getRiskColor(level?: string): string {
  const normalized = (level || '').toUpperCase();
  if (normalized === 'CRITICAL') return '#dc2626';
  if (normalized === 'HIGH') return '#f97316';
  if (normalized === 'MEDIUM') return '#d97706';
  if (normalized === 'LOW') return '#16a34a';
  return '#8090aa';
}

function getRiskBg(level?: string): string {
  const normalized = (level || '').toUpperCase();
  if (normalized === 'CRITICAL') return '#fef2f2';
  if (normalized === 'HIGH') return '#fff7ed';
  if (normalized === 'MEDIUM') return '#fefce8';
  if (normalized === 'LOW') return '#f0fdf4';
  return '#f8fafc';
}

// ─── Components ───────────────────────────────────────────────

function RiskBadge({ level, compact = false }: { level: string; compact?: boolean }) {
  return (
    <View style={[riskBadgeStyles.badge, { backgroundColor: getRiskBg(level) }, compact && riskBadgeStyles.compact]}>
      <View style={[riskBadgeStyles.dot, { backgroundColor: getRiskColor(level) }, compact && riskBadgeStyles.dotCompact]} />
      <Text style={[riskBadgeStyles.text, { color: getRiskColor(level) }, compact && riskBadgeStyles.textCompact]}>
        {level}
      </Text>
    </View>
  );
}

const riskBadgeStyles = StyleSheet.create({
  badge: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20, gap: 6 },
  compact: { paddingHorizontal: 8, paddingVertical: 2, gap: 4 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  dotCompact: { width: 5, height: 5, borderRadius: 3 },
  text: { fontSize: 12, fontWeight: '600' },
  textCompact: { fontSize: 10 },
});

// ─── Main Screen ──────────────────────────────────────────────

export default function DropoutPredictionScreen() {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const [selectedStudent, setSelectedStudent] = useState<ClassPredictionStudent | null>(null);

  // Screen state
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [predicting, setPredicting] = useState(false);
  const [classResults, setClassResults] = useState<PredictByClassResponse | null>(null);

  const detailRecommendations = selectedStudent
    ? selectedStudent.recommendations?.length > 0
      ? selectedStudent.recommendations
      : selectedStudent.recommendation
        ? [selectedStudent.recommendation]
        : []
    : [];

  // Animated panel height for smooth transitions
  const panelHeight = useRef(new Animated.Value(350)).current;
  const resultsOpacity = useRef(new Animated.Value(0)).current;

  // ── Animate panel collapse on results ──
  useEffect(() => {
    if (classResults) {
      Animated.parallel([
        Animated.timing(panelHeight, {
          toValue: 0,
          duration: 300,
          useNativeDriver: false,
        }),
        Animated.timing(resultsOpacity, {
          toValue: 1,
          duration: 400,
          useNativeDriver: false,
        }),
      ]).start();
    } else {
      panelHeight.setValue(350);
      resultsOpacity.setValue(0);
    }
  }, [classResults, panelHeight, resultsOpacity]);

  // ── Run Class-Wise Prediction ──
  const handleClassPrediction = useCallback(async () => {
    if (!selectedClass) {
      Alert.alert('Select Class', 'Please select a class to run predictions.');
      return;
    }
    try {
      setPredicting(true);
      const result = await dropoutService.predictByClass(selectedClass);
      setClassResults(result);
    } catch (error: any) {
      Alert.alert('Prediction Failed', error?.response?.data?.detail || error?.message || 'Failed to run predictions');
    } finally {
      setPredicting(false);
    }
  }, [selectedClass]);

  // ── Change Class (go back to selector) ──
  const handleChangeClass = useCallback(() => {
    setClassResults(null);
    setSelectedClass(null);
    setSelectedStudent(null);
  }, []);

  // ── Reset All ──
  const handleReset = useCallback(() => {
    handleChangeClass();
  }, [handleChangeClass]);

  // ── Render ──
  return (
    <View style={[styles.flex, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color="#071a3a" />
        </TouchableOpacity>
        <View style={styles.headerIconWrap}>
          <Ionicons name="warning-outline" size={24} color="#ef4444" />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.headerTitle}>Dropout Prediction</Text>
          <Text style={styles.headerSubtitle}>
            {classResults ? `Class ${selectedClass} Analysis` : 'ML-powered risk analysis'}
          </Text>
        </View>
        {classResults ? (
          <TouchableOpacity style={styles.changeClassBtn} onPress={handleChangeClass}>
            <Ionicons name="repeat-outline" size={18} color="#2f6df6" />
            <Text style={styles.changeClassText}>Class</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Animated Class Selection Panel - collapses on results */}
      <Animated.View style={[styles.classPanel, { height: panelHeight, overflow: 'hidden' }]}>
        <Text style={styles.classPanelTitle}>Select Class</Text>

        <View style={styles.classGrid}>
          {CLASS_GRADES.map((cls) => (
            <TouchableOpacity
              key={cls.value}
              style={[
                styles.classBtn,
                selectedClass === cls.value && styles.classBtnActive,
              ]}
              onPress={() => setSelectedClass(cls.value)}
            >
              <Text style={[
                styles.classBtnText,
                selectedClass === cls.value && styles.classBtnTextActive,
              ]}>
                {cls.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[
            styles.runClassBtn,
            (!selectedClass || predicting) && styles.runClassBtnDisabled,
          ]}
          onPress={handleClassPrediction}
          disabled={!selectedClass || predicting}
        >
          {predicting ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Ionicons name="play-circle-outline" size={22} color="#fff" />
          )}
          <Text style={styles.runClassBtnText}>
            {predicting ? 'Running ML Model...' : `Predict Class ${selectedClass || ''}`}
          </Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Loading overlay shown during prediction */}
      {predicting && !classResults && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#2f6df6" />
          <Text style={styles.loadingText}>Analyzing students in Class {selectedClass}...</Text>
        </View>
      )}

      {/* Results Section - takes full remaining height after header */}
      <Animated.View style={[styles.resultsContainer, { opacity: resultsOpacity }]}>
        {classResults && (
          <View style={styles.resultsInner}>
            {/* Summary Strip */}
            <View style={styles.summaryStrip}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{classResults.total_students}</Text>
                <Text style={styles.summaryLabel}>Total</Text>
              </View>
              <View style={[styles.summaryItem, styles.summaryCritical]}>
                <Text style={[styles.summaryValue, { color: '#dc2626' }]}>{classResults.critical_risk_count}</Text>
                <Text style={styles.summaryLabel}>Critical</Text>
              </View>
              <View style={[styles.summaryItem, styles.summaryHigh]}>
                <Text style={[styles.summaryValue, { color: '#f97316' }]}>{classResults.high_risk_count}</Text>
                <Text style={styles.summaryLabel}>High</Text>
              </View>
              <View style={[styles.summaryItem, styles.summaryMedium]}>
                <Text style={[styles.summaryValue, { color: '#d97706' }]}>{classResults.medium_risk_count}</Text>
                <Text style={styles.summaryLabel}>Medium</Text>
              </View>
              <View style={[styles.summaryItem, styles.summaryLow]}>
                <Text style={[styles.summaryValue, { color: '#16a34a' }]}>{classResults.low_risk_count}</Text>
                <Text style={styles.summaryLabel}>Low</Text>
              </View>
            </View>

            {/* Student List Header */}
            <View style={styles.listHeader}>
              <Text style={styles.sectionTitle}>Students</Text>
              <Text style={styles.sectionCount}>{classResults.total_students} students · Class {selectedClass}</Text>
            </View>

            {/* Scrollable Student Cards - takes remaining space */}
            <ScrollView
              style={styles.studentScroll}
              contentContainerStyle={styles.studentScrollContent}
              showsVerticalScrollIndicator={true}
            >
              {classResults.students.map((student, index) => (
                <TouchableOpacity
                  key={student.student_id || index}
                  style={styles.studentCard}
                  onPress={() => setSelectedStudent(student)}
                  activeOpacity={0.7}
                >
                  <View style={[styles.studentAvatar, { backgroundColor: getRiskBg(student.risk_level) }]}>
                    <Text style={[styles.avatarText, { color: getRiskColor(student.risk_level) }]}>
                      {student.student_name?.charAt(0) || '?'}
                    </Text>
                  </View>

                  <View style={styles.studentInfo}>
                    <Text style={styles.studentName} numberOfLines={1}>{student.student_name}</Text>
                    <Text style={styles.studentMeta}>
                      {student.gender} · Age {student.age} · {student.admission_no}
                    </Text>
                    <View style={styles.featureTags}>
                      <View style={styles.tag}><Text style={styles.tagText}>📊 {student.attendance_pct}%</Text></View>
                      <View style={styles.tag}><Text style={styles.tagText}>📝 {student.avg_marks}</Text></View>
                      {student.previous_failures > 0 && (
                        <View style={[styles.tag, { backgroundColor: '#fef2f2' }]}>
                          <Text style={[styles.tagText, { color: '#dc2626' }]}>⚠️ {student.previous_failures} fails</Text>
                        </View>
                      )}
                    </View>
                  </View>

                  <View style={styles.studentRight}>
                    <RiskBadge level={student.risk_level} compact />
                    <View style={styles.probRow}>
                      <View style={styles.probTrack}>
                        <View style={[styles.probFill, {
                          width: `${Math.min(student.dropout_probability || 0, 100)}%`,
                          backgroundColor: getRiskColor(student.risk_level)
                        }]} />
                      </View>
                      <Text style={[styles.probText, { color: getRiskColor(student.risk_level) }]}>
                        {Math.round(student.dropout_probability || 0)}%
                      </Text>
                    </View>
                  </View>
                </TouchableOpacity>
              ))}

              {/* End of list spacer */}
              <View style={{ height: 40 }} />
            </ScrollView>
          </View>
        )}

        {/* Empty State (before prediction) - visible when classPanel expands and no results yet */}
        {!classResults && !predicting && (
          <View style={styles.emptyState}>
            <View style={styles.emptyIconWrap}>
              <Ionicons name="analytics-outline" size={64} color="#2f6df6" />
            </View>
            <Text style={styles.emptyTitle}>Dropout Risk Prediction</Text>
            <Text style={styles.emptySubtitle}>
              Select a class above and tap "Predict" to identify at-risk students
              using ML analysis of attendance, grades, and demographics.
            </Text>
          </View>
        )}
      </Animated.View>

      {/* Student Detail Overlay */}
      {selectedStudent && (
        <View style={styles.detailOverlay}>
          <View style={styles.detailCard}>
            {/* Detail Header */}
            <View style={styles.detailHeader}>
              <View style={styles.detailTitleRow}>
                <View style={[styles.detailAvatar, { backgroundColor: getRiskBg(selectedStudent.risk_level) }]}>
                  <Text style={[styles.detailAvatarText, { color: getRiskColor(selectedStudent.risk_level) }]}>
                    {selectedStudent.student_name?.charAt(0) || '?'}
                  </Text>
                </View>
                <View style={styles.detailTitleInfo}>
                  <Text style={styles.detailTitle}>{selectedStudent.student_name}</Text>
                  <Text style={styles.detailSubtitle}>{selectedStudent.admission_no} · Class {selectedStudent.current_class}</Text>
                </View>
              </View>
              <TouchableOpacity onPress={() => setSelectedStudent(null)}>
                <Ionicons name="close-circle" size={28} color="#8a9ab3" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} style={styles.detailScroll}>
              {/* Risk Summary */}
              <View style={styles.detailRiskCard}>
                <View style={styles.detailRiskRow}>
                  <RiskBadge level={selectedStudent.risk_level} />
                  <Text style={[styles.detailProbValue, { color: getRiskColor(selectedStudent.risk_level) }]}>
                    {Math.round(selectedStudent.dropout_probability || 0)}% risk
                  </Text>
                </View>
                {/* Mini progress bar */}
                <View style={styles.detailProbLargeTrack}>
                  <View style={[styles.detailProbLargeFill, {
                    width: `${Math.min(selectedStudent.dropout_probability || 0, 100)}%`,
                    backgroundColor: getRiskColor(selectedStudent.risk_level)
                  }]} />
                </View>
              </View>

              {/* Student Details */}
              <View style={styles.detailSection}>
                <View style={styles.detailSectionHeader}>
                  <Ionicons name="person-outline" size={16} color="#2f6df6" />
                  <Text style={styles.detailSectionTitle}>Student Details</Text>
                </View>
                <View style={styles.detailRow}><Text style={styles.detailLabel}>Gender</Text><Text style={styles.detailValue}>{selectedStudent.gender}</Text></View>
                <View style={styles.detailRow}><Text style={styles.detailLabel}>Age</Text><Text style={styles.detailValue}>{selectedStudent.age} years</Text></View>
                <View style={styles.detailRow}><Text style={styles.detailLabel}>Class</Text><Text style={styles.detailValue}>Class {selectedStudent.current_class}</Text></View>
              </View>

              {/* Academic Info */}
              <View style={styles.detailSection}>
                <View style={styles.detailSectionHeader}>
                  <Ionicons name="school-outline" size={16} color="#09b981" />
                  <Text style={styles.detailSectionTitle}>Academic Performance</Text>
                </View>
                <View style={styles.detailRow}><Text style={styles.detailLabel}>Attendance</Text><Text style={styles.detailValue}>{selectedStudent.attendance_pct}%</Text></View>
                <View style={styles.detailRow}><Text style={styles.detailLabel}>Avg. Marks</Text><Text style={styles.detailValue}>{selectedStudent.avg_marks}</Text></View>
                <View style={styles.detailRow}><Text style={styles.detailLabel}>Previous Failures</Text><Text style={styles.detailValue}>{selectedStudent.previous_failures}</Text></View>
              </View>

              {/* Recommendation */}
              {detailRecommendations.length > 0 && (
                <View style={styles.detailSection}>
                  <View style={styles.detailSectionHeader}>
                    <Ionicons name="bulb-outline" size={16} color="#d6a72f" />
                    <Text style={styles.detailSectionTitle}>Recommended Actions</Text>
                  </View>
                  {detailRecommendations.map((item, index) => (
                    <View key={index} style={styles.recommendationRow}>
                      <Text style={styles.recommendationBullet}>•</Text>
                      <Text style={styles.detailRecommendation}>{item}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Intervention level tip */}
              {selectedStudent.risk_level?.toUpperCase() === 'CRITICAL' && (
                <View style={[styles.detailAlert, { backgroundColor: '#fef2f2', borderColor: '#fecaca' }]}>
                  <Ionicons name="alert-circle" size={18} color="#dc2626" />
                  <Text style={[styles.detailAlertText, { color: '#991b1b' }]}>
                    Immediate intervention required. Contact guardian within 24 hours.
                  </Text>
                </View>
              )}
              {selectedStudent.risk_level?.toUpperCase() === 'HIGH' && (
                <View style={[styles.detailAlert, { backgroundColor: '#fff7ed', borderColor: '#fed7aa' }]}>
                  <Ionicons name="warning-outline" size={18} color="#f97316" />
                  <Text style={[styles.detailAlertText, { color: '#9a3412' }]}>
                    Schedule counselling session and assign a mentor.
                  </Text>
                </View>
              )}
            </ScrollView>
          </View>
        </View>
      )}
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#f0f4ff' },

  // ── Header ──
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e8edf5',
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: '#f5f7fb',
    alignItems: 'center', justifyContent: 'center',
  },
  changeClassBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#eff6ff',
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1, borderColor: '#dbeafe',
  },
  changeClassText: { color: '#2f6df6', fontSize: 12, fontWeight: '600' },
  headerIconWrap: {
    width: 40, height: 40, borderRadius: 10,
    backgroundColor: '#fef2f2',
    alignItems: 'center', justifyContent: 'center',
  },
  headerText: { flex: 1 },
  headerTitle: { color: '#071a3a', fontSize: 18, fontWeight: '700' },
  headerSubtitle: { color: '#536784', fontSize: 12, marginTop: 2 },

  // ── Animated Class Selection Panel ──
  classPanel: {
    paddingHorizontal: 16,
    paddingTop: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e8edf5',
  },
  classPanelTitle: {
    color: '#071a3a',
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 12,
  },
  classGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  classBtn: {
    width: '23%',
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#f5f7fb',
    borderWidth: 1,
    borderColor: '#e8edf5',
    alignItems: 'center',
  },
  classBtnActive: {
    backgroundColor: '#2f6df6',
    borderColor: '#2f6df6',
  },
  classBtnText: {
    color: '#536784',
    fontSize: 13,
    fontWeight: '600',
  },
  classBtnTextActive: {
    color: '#fff',
  },
  runClassBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#16a34a',
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 16,
  },
  runClassBtnDisabled: {
    backgroundColor: '#9ca3af',
    opacity: 0.7,
  },
  runClassBtnText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },

  // ── Loading overlay ──
  loadingOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f4ff',
    paddingBottom: 60,
  },
  loadingText: {
    color: '#536784',
    fontSize: 14,
    marginTop: 16,
  },

  // ── Results Container (takes remaining space) ──
  resultsContainer: {
    flex: 1,
    backgroundColor: '#f0f4ff',
  },
  resultsInner: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },

  // ── Summary Strip ──
  summaryStrip: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e8edf5',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
    borderRightWidth: 1,
    borderRightColor: '#eef2f7',
  },
  summaryCritical: {},
  summaryHigh: {},
  summaryMedium: {},
  summaryLow: { borderRightWidth: 0 },
  summaryValue: { fontSize: 20, fontWeight: '700', color: '#071a3a' },
  summaryLabel: { fontSize: 10, color: '#8090aa', marginTop: 2, textTransform: 'uppercase', letterSpacing: 0.3 },

  // ── Student List ──
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
  },
  sectionTitle: { color: '#071a3a', fontSize: 16, fontWeight: '700' },
  sectionCount: { color: '#8090aa', fontSize: 12 },

  studentScroll: {
    flex: 1,
    paddingHorizontal: 16,
  },
  studentScrollContent: {
    paddingTop: 4,
    paddingBottom: 20,
  },

  // ── Student Card ──
  studentCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#eef2f7',
    ...Shadows.sm,
  },
  studentAvatar: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { fontSize: 16, fontWeight: '700' },
  studentInfo: { flex: 1 },
  studentName: { color: '#071a3a', fontSize: 14, fontWeight: '600' },
  studentMeta: { color: '#8090aa', fontSize: 11, marginTop: 1 },
  featureTags: { flexDirection: 'row', gap: 4, marginTop: 4, flexWrap: 'wrap' },
  tag: { backgroundColor: '#f5f7fb', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  tagText: { fontSize: 9, color: '#536784' },
  studentRight: { alignItems: 'flex-end', gap: 4 },
  probRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  probTrack: { width: 40, height: 4, borderRadius: 2, backgroundColor: '#eef2f7', overflow: 'hidden' },
  probFill: { height: 4, borderRadius: 2 },
  probText: { fontSize: 10, fontWeight: '700', width: 32, textAlign: 'right' },

  // ── Empty State ──
  emptyState: { alignItems: 'center', paddingVertical: 40, paddingHorizontal: 20 },
  emptyIconWrap: {
    width: 90, height: 90, borderRadius: 45,
    backgroundColor: '#eff6ff',
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 20,
  },
  emptyTitle: { color: '#071a3a', fontSize: 20, fontWeight: '700', textAlign: 'center' },
  emptySubtitle: { color: '#536784', fontSize: 13, textAlign: 'center', marginTop: 8, lineHeight: 18 },

  // ── Detail Overlay ──
  detailOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'flex-end',
    zIndex: 100,
  },
  detailCard: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: 30,
    maxHeight: SCREEN_HEIGHT * 0.75,
  },
  detailScroll: { maxHeight: SCREEN_HEIGHT * 0.55, marginTop: 12 },
  detailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  detailTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  detailAvatar: {
    width: 44, height: 44, borderRadius: 22,
    alignItems: 'center', justifyContent: 'center',
  },
  detailAvatarText: { fontSize: 18, fontWeight: '700' },
  detailTitleInfo: { flex: 1 },
  detailTitle: { color: '#071a3a', fontSize: 18, fontWeight: '700' },
  detailSubtitle: { color: '#8090aa', fontSize: 12, marginTop: 2 },

  // Risk Card
  detailRiskCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
  },
  detailRiskRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 },
  detailProbValue: { fontSize: 20, fontWeight: '800' },
  detailProbLargeTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: '#eef2f7',
    overflow: 'hidden',
  },
  detailProbLargeFill: {
    height: 8,
    borderRadius: 4,
  },

  // Detail Sections
  detailSection: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  detailSectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 },
  detailSectionTitle: { color: '#071a3a', fontSize: 13, fontWeight: '700' },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 5,
    borderBottomWidth: 1,
    borderBottomColor: '#eef2f7',
  },
  detailLabel: { color: '#6b7fa3', fontSize: 13 },
  detailValue: { color: '#071a3a', fontSize: 13, fontWeight: '500' },
  detailRecommendation: { color: '#334155', fontSize: 14, lineHeight: 22 },
  recommendationRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginBottom: 8 },
  recommendationBullet: { color: '#d6a72f', fontSize: 18, lineHeight: 22, width: 16 },

  // Alert banner in detail
  detailAlert: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 10,
  },
  detailAlertText: { flex: 1, fontSize: 13, lineHeight: 18 },
});