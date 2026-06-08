import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { ActivityIndicator, View } from 'react-native';
import { useAuthStore } from '../store/authStore';
import { AuthNavigator } from './AuthNavigator';
import { DEONavigator } from './DEONavigator';
import { MEONavigator } from './MEONavigator';
import { HMNavigator } from './HMNavigator';
import { TeacherNavigator } from './TeacherNavigator';
import { StudentNavigator } from './StudentNavigator';
import { ParentNavigator } from './ParentNavigator';

function normalizeRole(role: string | undefined | null) {
  if (!role) return null;
  const normalized = role.toString().trim().toUpperCase();
  console.log('🔍 Role normalization:', { input: role, normalized });
  return normalized;
}

function RoleNavigator() {
  const user = useAuthStore((s) => s.user);
  const role = normalizeRole(user?.role);

  console.log('🎯 RoleNavigator render:', { user: user?.email, rawRole: user?.role, normalizedRole: role });

  if (!user) {
    console.log('❌ No user - showing AuthNavigator');
    return <AuthNavigator />;
  }

  const navigatorMap: Record<string, React.ReactNode> = {
    'DEO':     <DEONavigator />,
    'MEO':     <MEONavigator />,
    'HM':      <HMNavigator />,
    'TEACHER': <TeacherNavigator />,
    'STUDENT': <StudentNavigator />,
    'PARENT':  <ParentNavigator />,
  };

  const selectedNavigator = navigatorMap[role ?? ''];
  
  if (!selectedNavigator) {
    console.log('⚠️  Unknown role or no match:', { role, availableRoles: Object.keys(navigatorMap) });
    return <AuthNavigator />;
  }

  console.log('✅ Using navigator for role:', role);
  return selectedNavigator;
}

export function RootNavigator() {
  const { isLoading, loadStoredAuth } = useAuthStore();

  useEffect(() => {
    loadStoredAuth();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#3b82f6" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <RoleNavigator />
    </NavigationContainer>
  );
}
