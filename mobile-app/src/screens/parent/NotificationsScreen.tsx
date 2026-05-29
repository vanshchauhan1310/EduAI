import React from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import Header from '../../components/common/Header';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { QUERY_KEYS } from '../../constants';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

const TYPE_ICONS: Record<string, { icon: string; color: string }> = {
  ATTENDANCE_ALERT: { icon: 'calendar',           color: Colors.warning },
  DROPOUT_RISK:     { icon: 'alert-circle',        color: Colors.danger },
  GENERAL:          { icon: 'notifications',        color: Colors.primary[600] },
  EXAM:             { icon: 'document-text',        color: Colors.secondary[500] },
};

export default function NotificationsScreen() {
  const insets = useSafeAreaInsets();
  const queryClient = useQueryClient();

  const { data = [], isLoading } = useQuery<any[]>({
    queryKey: [QUERY_KEYS.NOTIFICATIONS],
    queryFn: async () => {
      const res = await api.get('/notifications');
      return res.data;
    },
  });

  const { mutate: markRead } = useMutation({
    mutationFn: (id: number) => api.post(`/notifications/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.NOTIFICATIONS] }),
  });

  if (isLoading) return <LoadingSpinner fullScreen message="Loading notifications..." />;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header
        title="Notifications"
        subtitle={`${data.filter((n) => !n.is_read).length} unread`}
      />

      {data.length === 0 ? (
        <EmptyState icon="notifications-off-outline" title="No Notifications" description="You're all caught up!" />
      ) : (
        <FlatList
          data={data}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => {
            const typeConfig = TYPE_ICONS[item.notification_type ?? 'GENERAL'] ?? TYPE_ICONS.GENERAL;
            return (
              <TouchableOpacity
                style={[styles.notifCard, !item.is_read && styles.unreadCard]}
                onPress={() => !item.is_read && markRead(item.id)}
                activeOpacity={0.8}
              >
                {!item.is_read && <View style={styles.unreadDot} />}
                <View style={[styles.iconWrap, { backgroundColor: `${typeConfig.color}18` }]}>
                  <Ionicons name={typeConfig.icon as any} size={22} color={typeConfig.color} />
                </View>
                <View style={styles.content}>
                  <Text style={[styles.title, !item.is_read && styles.unreadTitle]}>{item.title}</Text>
                  <Text style={styles.body} numberOfLines={2}>{item.body}</Text>
                  <Text style={styles.time}>{dayjs(item.created_at).fromNow()}</Text>
                </View>
              </TouchableOpacity>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  list: { padding: Spacing.base, gap: 8 },
  notifCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.white,
    borderRadius: BorderRadius.xl,
    padding: Spacing.md,
    gap: Spacing.md,
    ...require('../../theme').Shadows.sm,
    position: 'relative',
  },
  unreadCard: { backgroundColor: Colors.primary[50] },
  unreadDot: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary[600],
  },
  iconWrap: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  content: { flex: 1 },
  title: { fontSize: Typography.sizes.base, color: Colors.neutral[700], marginBottom: 3 },
  unreadTitle: { fontWeight: Typography.weights.bold, color: Colors.neutral[900] },
  body: { fontSize: Typography.sizes.sm, color: Colors.neutral[500], lineHeight: 18, marginBottom: 4 },
  time: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
});
