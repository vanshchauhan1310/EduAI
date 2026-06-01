import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import SchoolDashboard from '../screens/hm/SchoolDashboard';
import StudentMonitor from '../screens/hm/StudentMonitor';
import HMProfileScreen from '../screens/hm/HMProfileScreen';
import HMModuleScreen from '../screens/hm/HMModuleScreen';
import HMNotificationsScreen from '../screens/hm/HMNotificationsScreen';
import { CopilotNavigator } from './CopilotNavigator';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function HMDashboardStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HMDashboardHome" component={SchoolDashboard} />
      <Stack.Screen name="AttendanceIntelligence" component={HMModuleScreen} />
      <Stack.Screen name="DropoutPrediction" component={HMModuleScreen} />
      <Stack.Screen name="TeacherPerformance" component={HMModuleScreen} />
      <Stack.Screen name="StudentLearning" component={HMModuleScreen} />
      <Stack.Screen name="SchoolHealthModule" component={HMModuleScreen} />
      <Stack.Screen name="SchoolOperations" component={HMModuleScreen} />
      <Stack.Screen name="HMNotifications" component={HMNotificationsScreen} />
    </Stack.Navigator>
  );
}

export function HMNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border, height: 60 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Dashboard:   focused ? 'home' : 'home-outline',
            Students:    focused ? 'people' : 'people-outline',
            Copilot:     focused ? 'sparkles' : 'sparkles-outline',
            Profile:     focused ? 'person-circle' : 'person-circle-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={HMDashboardStack} />
      <Tab.Screen name="Students" component={StudentMonitor} />
      <Tab.Screen name="Copilot" component={CopilotNavigator} />
      <Tab.Screen name="Profile" component={HMProfileScreen} />
    </Tab.Navigator>
  );
}
