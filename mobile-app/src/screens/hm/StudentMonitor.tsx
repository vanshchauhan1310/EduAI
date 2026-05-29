import React, { useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput, TouchableOpacity, RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import Header from '../../components/common/Header';
import Card from '../../components/common/Card';
import RiskBadge from '../../components/common/RiskBadge';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import EmptyState from '../../components/common/EmptyState';
import { useAuthStore } from '../../store/authStore';
import { Colors, Typography, Spacing, BorderRadius } from '../../theme';
import { RiskLevel } from '../../types';

export default function StudentMonitor() {
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['students', user?.school_id, page],
    queryFn: async () => {
      const res = await api.get('/students', {
        params: { school_id: user?.school_id, page, page_size: 20 },
      });
      return res.data;
    },
  });

  const students = (data?.items ?? []).filter((s: any) =>
    s.full_name.toLowerCase().includes(search.toLowerCase()) ||
    s.admission_no.includes(search)
  );

  if (isLoading) return <LoadingSpinner fullScreen message="Loading students..." />;

  return (
    <View style={[styles.flex, { paddingBottom: insets.bottom }]}>
      <Header title="Student Monitor" subtitle={`${data?.total ?? 0} Students`} />

      <View style={styles.searchBar}>
        <Ionicons name="search-outline" size={18} color={Colors.neutral[400]} />
        <TextInput
          style={styles.searchInput}
          value={search}
          onChangeText={setSearch}
          placeholder="Search by name or admission no..."
          placeholderTextColor={Colors.neutral[400]}
        />
        {search ? (
          <TouchableOpacity onPress={() => setSearch('')}>
            <Ionicons name="close-circle" size={18} color={Colors.neutral[400]} />
          </TouchableOpacity>
        ) : null}
      </View>

      {students.length === 0 ? (
        <EmptyState icon="people-outline" title="No students found" />
      ) : (
        <FlatList
          data={students}
          keyExtractor={(item: any) => String(item.id)}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
          renderItem={({ item }) => (
            <Card style={styles.card}>
              <View style={styles.cardRow}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{item.full_name?.charAt(0)}</Text>
                </View>
                <View style={styles.info}>
                  <Text style={styles.name}>{item.full_name}</Text>
                  <Text style={styles.meta}>
                    Class {item.current_class}{item.section ? `-${item.section}` : ''} • {item.admission_no}
                  </Text>
                </View>
                <RiskBadge level={item.risk_level as RiskLevel} size="sm" />
              </View>
              {item.dropout_risk_score != null && item.risk_level !== 'LOW' && (
                <View style={styles.riskRow}>
                  <View style={styles.riskBarBg}>
                    <View style={[styles.riskBarFill, {
                      width: `${Math.round(item.dropout_risk_score * 100)}%` as any,
                      backgroundColor: item.dropout_risk_score >= 0.65 ? Colors.danger : Colors.warning,
                    }]} />
                  </View>
                  <Text style={styles.riskPct}>{Math.round(item.dropout_risk_score * 100)}% risk</Text>
                </View>
              )}
              <View style={styles.cardFooter}>
                <Text style={styles.gender}>{item.gender} • {item.academic_year}</Text>
                <TouchableOpacity style={styles.viewBtn}>
                  <Text style={styles.viewText}>View Profile</Text>
                </TouchableOpacity>
              </View>
            </Card>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.background },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    margin: Spacing.base,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  searchInput: { flex: 1, fontSize: Typography.sizes.base, color: Colors.neutral[900] },
  list: { paddingHorizontal: Spacing.base, paddingBottom: Spacing['2xl'], gap: Spacing.sm },
  card: { padding: Spacing.md },
  cardRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, marginBottom: Spacing.sm },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primary[100],
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.bold, color: Colors.primary[700] },
  info: { flex: 1 },
  name: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.semibold, color: Colors.neutral[900] },
  meta: { fontSize: Typography.sizes.xs, color: Colors.neutral[500], marginTop: 2 },
  riskRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  riskBarBg: { flex: 1, height: 5, backgroundColor: Colors.neutral[100], borderRadius: 3, overflow: 'hidden' },
  riskBarFill: { height: '100%', borderRadius: 3 },
  riskPct: { fontSize: Typography.sizes.xs, color: Colors.neutral[600], fontWeight: Typography.weights.bold },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: Spacing.sm, borderTopWidth: 1, borderTopColor: Colors.neutral[100] },
  gender: { fontSize: Typography.sizes.xs, color: Colors.neutral[400] },
  viewBtn: {},
  viewText: { fontSize: Typography.sizes.sm, color: Colors.primary[600], fontWeight: Typography.weights.medium },
});
