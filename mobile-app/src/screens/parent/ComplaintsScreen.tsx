import React, { useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput, TouchableOpacity, Modal,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Button from '../../components/common/Button';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import dayjs from 'dayjs';

type ComplaintStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED';

interface Complaint {
  id: number;
  subject: string;
  description: string;
  status: ComplaintStatus;
  date: string;
  response?: string;
}

const STATUS_CONFIG: Record<ComplaintStatus, { color: string; icon: string }> = {
  OPEN:        { color: Colors.warning, icon: 'time-outline' },
  IN_PROGRESS: { color: Colors.primary[600], icon: 'sync-outline' },
  RESOLVED:    { color: Colors.success, icon: 'checkmark-circle-outline' },
};

const MOCK_COMPLAINTS: Complaint[] = [
  { id: 1, subject: 'Drinking water not available',  description: 'School drinking water tap is broken since 3 days.', status: 'RESOLVED',    date: '2025-05-10', response: 'Issue has been resolved. Plumber visited on 13-May.' },
  { id: 2, subject: 'Bus delay issue',               description: 'School bus is regularly 30 minutes late causing anxiety.', status: 'IN_PROGRESS', date: '2025-05-20' },
  { id: 3, subject: 'Extra fees collected',          description: 'Teacher collected extra fees for notebook that should be free.', status: 'OPEN', date: '2025-05-27' },
];

export default function ComplaintsScreen() {
  const insets = useSafeAreaInsets();
  const [complaints, setComplaints] = useState<Complaint[]>(MOCK_COMPLAINTS);
  const [showModal, setShowModal] = useState(false);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = () => {
    if (!subject.trim() || !description.trim()) return;
    setComplaints((prev) => [
      {
        id: Date.now(),
        subject: subject.trim(),
        description: description.trim(),
        status: 'OPEN',
        date: dayjs().format('YYYY-MM-DD'),
      },
      ...prev,
    ]);
    setSubject('');
    setDescription('');
    setShowModal(false);
  };

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Complaints & Feedback"
        subtitle={`${complaints.filter((c) => c.status === 'OPEN').length} open`}
        rightAction={{ icon: 'add-circle-outline', onPress: () => setShowModal(true) }}
      />

      <FlatList
        data={complaints}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => {
          const cfg = STATUS_CONFIG[item.status];
          return (
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <View style={[styles.statusBadge, { backgroundColor: `${cfg.color}18` }]}>
                  <Ionicons name={cfg.icon as any} size={14} color={cfg.color} />
                  <Text style={[styles.statusText, { color: cfg.color }]}>{item.status.replace('_', ' ')}</Text>
                </View>
                <Text style={styles.date}>{dayjs(item.date).format('DD MMM YYYY')}</Text>
              </View>
              <Text style={styles.subject}>{item.subject}</Text>
              <Text style={styles.description} numberOfLines={2}>{item.description}</Text>
              {item.response && (
                <View style={styles.responseBox}>
                  <Ionicons name="chatbubble-ellipses-outline" size={14} color={Colors.success} />
                  <Text style={styles.responseText}>{item.response}</Text>
                </View>
              )}
            </View>
          );
        }}
      />

      {/* New Complaint Modal */}
      <Modal visible={showModal} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Submit Complaint / Feedback</Text>

            <Text style={styles.fieldLabel}>Subject</Text>
            <TextInput
              style={styles.fieldInput}
              value={subject}
              onChangeText={setSubject}
              placeholder="Brief subject of complaint"
              placeholderTextColor={Colors.neutral[400]}
            />

            <Text style={styles.fieldLabel}>Description</Text>
            <TextInput
              style={[styles.fieldInput, styles.textArea]}
              value={description}
              onChangeText={setDescription}
              placeholder="Describe the issue in detail..."
              placeholderTextColor={Colors.neutral[400]}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />

            <View style={styles.modalActions}>
              <Button title="Cancel" variant="outline" onPress={() => setShowModal(false)} size="md" style={styles.cancelBtn} />
              <Button title="Submit" onPress={handleSubmit} disabled={!subject.trim() || !description.trim()} size="md" style={styles.submitBtn} />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  list: { padding: Spacing.base, gap: Spacing.sm },
  card: {
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    ...require('../../theme').Shadows.sm,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.full },
  statusText: { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold },
  date: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  subject: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: 4 },
  description: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], lineHeight: 18, marginBottom: Spacing.sm },
  responseBox: {
    flexDirection: 'row',
    gap: Spacing.sm,
    backgroundColor: '#f0fdf4',
    borderRadius: BorderRadius.lg,
    padding: Spacing.sm,
    alignItems: 'flex-start',
  },
  responseText: { flex: 1, fontSize: Typography.sizes.xs, color: '#166534', lineHeight: 16 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: Colors.white, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: Spacing.xl },
  modalTitle: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.lg },
  fieldLabel: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: Colors.neutral[700], marginBottom: Spacing.xs },
  fieldInput: {
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    fontSize: Typography.sizes.base,
    color: Colors.neutral[900],
    marginBottom: Spacing.md,
    backgroundColor: Colors.neutral[50],
  },
  textArea: { minHeight: 100, textAlignVertical: 'top' },
  modalActions: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  cancelBtn: { flex: 1 },
  submitBtn: { flex: 1 },
});
