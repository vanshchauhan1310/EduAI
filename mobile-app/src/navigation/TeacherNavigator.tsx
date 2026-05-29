import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import AttendanceScreen from '../screens/teacher/AttendanceScreen';
import AssignmentsScreen from '../screens/teacher/AssignmentsScreen';
import GradingScreen from '../screens/teacher/GradingScreen';
import AIAssistantScreen from '../screens/teacher/AIAssistantScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

export function TeacherNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border, height: 60 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Attendance:   focused ? 'checkbox' : 'checkbox-outline',
            Assignments:  focused ? 'book' : 'book-outline',
            Grading:      focused ? 'ribbon' : 'ribbon-outline',
            'AI Assist':  focused ? 'sparkles' : 'sparkles-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Attendance" component={AttendanceScreen} />
      <Tab.Screen name="Assignments" component={AssignmentsScreen} />
      <Tab.Screen name="Grading" component={GradingScreen} />
      <Tab.Screen name="AI Assist" component={AIAssistantScreen} />
    </Tab.Navigator>
  );
}
