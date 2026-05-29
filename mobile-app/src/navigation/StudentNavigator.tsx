import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import AssignmentsScreen from '../screens/student/AssignmentsScreen';
import AttendanceScreen from '../screens/student/AttendanceScreen';
import PerformanceScreen from '../screens/student/PerformanceScreen';
import AIAssistantScreen from '../screens/student/AIAssistantScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

export function StudentNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border, height: 60 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Assignments:  focused ? 'book' : 'book-outline',
            Attendance:   focused ? 'calendar' : 'calendar-outline',
            Performance:  focused ? 'trophy' : 'trophy-outline',
            'AI Tutor':   focused ? 'sparkles' : 'sparkles-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Assignments" component={AssignmentsScreen} />
      <Tab.Screen name="Attendance" component={AttendanceScreen} />
      <Tab.Screen name="Performance" component={PerformanceScreen} />
      <Tab.Screen name="AI Tutor" component={AIAssistantScreen} />
    </Tab.Navigator>
  );
}
