import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, TextInput } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';

const MOCK_PARENTS = [
  { id: 1, parent_name: 'Ramesh Kumar', student_name: 'Arjun Kumar', phone: '+91 98765 43210', last_contact: '2 days ago', unread: 2 },
  { id: 2, parent_name: 'Sunitha Devi',  student_name: 'Priya Devi',  phone: '+91 87654 32109', last_contact: '1 week ago',  unread: 0 },
  { id: 3, parent_name: 'Vijay Rao',     student_name: 'Venkat Rao',  phone: '+91 76543 21098', last_contact: 'Today',       unread: 1 },
];

export default function ParentEngagement() {
  const insets = useSafeAreaInsets();
  const [broadcastMsg, setBroadcastMsg] = useState('');
  const [showBroadcast, setShowBroadcast] = useState(false);

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Parent Engagement" subtitle={`${MOCK_PARENTS.length} Parents`} />

      {/* Broadcast Banner */}
      {showBroadcast ? (
        <View style={styles.broadcastPanel}>
          <Text style={styles.broadcastTitle}>Broadcast to All Parents</Text>
          <TextInput
            style={styles.broadcastInput}
            value={broadcastMsg}
            onChangeText={setBroadcastMsg}
            placeholder="Type your message..."
            placeholderTextColor={Colors.neutral[400]}
            multiline
            numberOfLines={3}
          />
          <View style={styles.broadcastActions}>
            <Button title="Cancel" variant="ghost" onPress={() => setShowBroadcast(false)} size="sm" />
            <Button title="Send via WhatsApp" onPress={() => setShowBroadcast(false)} size="sm" />
          </View>
        </View>
      ) : (
        <TouchableOpacity style={styles.broadcastBtn} onPress={() => setShowBroadcast(true)}>
          <Ionicons name="megaphone-outline" size={18} color={Colors.white} />
          <Text style={styles.broadcastBtnText}>Broadcast Message to All Parents</Text>
        </TouchableOpacity>
      )}

      <FlatList
        data={MOCK_PARENTS}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.cardRow}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{item.parent_name.charAt(0)}</Text>
              </View>
              <View style={styles.info}>
                <View style={styles.nameRow}>
                  <Text style={styles.parentName}>{item.parent_name}</Text>
                  {item.unread > 0 && (
                    <View style={styles.unreadBadge}>
                      <Text style={styles.unreadText}>{item.unread}</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.studentName}>Ward: {item.student_name}</Text>
                <Text style={styles.lastContact}>Last contact: {item.last_contact}</Text>
              </View>
            </View>

            <View style={styles.actions}>
              <TouchableOpacity style={[styles.actionBtn, { backgroundColor: '#25d366' }]}>
                <Ionicons name="logo-whatsapp" size={16} color={Colors.white} />
                <Text style={styles.actionBtnText}>WhatsApp</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.actionBtn, { backgroundColor: Colors.primary[600] }]}>
                <Ionicons name="call-outline" size={16} color={Colors.white} />
                <Text style={styles.actionBtnText}>Call</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.actionBtn, { backgroundColor: Colors.neutral[200] }]}>
                <Ionicons name="notifications-outline" size={16} color={Colors.neutral[700]} />
                <Text style={[styles.actionBtnText, { color: Colors.neutral[700] }]}>Notify</Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  broadcastBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    backgroundColor: Colors.primary[600],
    margin: Spacing.base,
    padding: Spacing.md,
    borderRadius: BorderRadius.xl,
  },
  broadcastBtnText: { color: Colors.white, fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold },
  broadcastPanel: {
    backgroundColor: Colors.white,
    margin: Spacing.base,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    ...require('../../theme').Shadows.md,
  },
  broadcastTitle: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900], marginBottom: Spacing.sm },
  broadcastInput: {
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    fontSize: Typography.sizes.base,
    color: Colors.neutral[900],
    minHeight: 80,
    textAlignVertical: 'top',
    marginBottom: Spacing.md,
  },
  broadcastActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: Spacing.sm },
  list: { paddingHorizontal: Spacing.base, paddingBottom: Spacing['2xl'], gap: Spacing.sm },
  card: { padding: Spacing.md },
  cardRow: { flexDirection: 'row', gap: Spacing.md, marginBottom: Spacing.md },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.secondary[500],
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: Typography.sizes.xl, fontWeight: Typography.weights.bold, color: Colors.white },
  info: { flex: 1 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  parentName: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  unreadBadge: {
    backgroundColor: Colors.danger,
    borderRadius: 10,
    minWidth: 18,
    height: 18,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  unreadText: { color: Colors.white, fontSize: 10, fontWeight: Typography.weights.bold },
  studentName: { fontSize: Typography.sizes.sm, color: Colors.neutral[600], marginTop: 2 },
  lastContact: { fontSize: Typography.sizes.xs, color: Colors.neutral[400], marginTop: 1 },
  actions: { flexDirection: 'row', gap: Spacing.sm },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    borderRadius: BorderRadius.lg,
  },
  actionBtnText: { color: Colors.white, fontSize: Typography.sizes.xs, fontWeight: Typography.weights.semibold },
});
