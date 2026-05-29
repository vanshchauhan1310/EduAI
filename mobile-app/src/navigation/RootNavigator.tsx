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

function RoleNavigator() {
  const user = useAuthStore((s) => s.user);

  if (!user) return <AuthNavigator />;

  switch (user.role) {
    case 'DEO':     return <DEONavigator />;
    case 'MEO':     return <MEONavigator />;
    case 'HM':      return <HMNavigator />;
    case 'TEACHER': return <TeacherNavigator />;
    case 'STUDENT': return <StudentNavigator />;
    case 'PARENT':  return <ParentNavigator />;
    default:        return <AuthNavigator />;
  }
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
