import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import SchoolDashboard from '../screens/hm/SchoolDashboard';
import AttendanceScreen from '../screens/hm/AttendanceScreen';
import StudentMonitor from '../screens/hm/StudentMonitor';
import AssessmentsScreen from '../screens/hm/AssessmentsScreen';
import ParentEngagement from '../screens/hm/ParentEngagement';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

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
            Attendance:  focused ? 'checkbox' : 'checkbox-outline',
            Students:    focused ? 'people' : 'people-outline',
            Assessments: focused ? 'document-text' : 'document-text-outline',
            Parents:     focused ? 'call' : 'call-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={SchoolDashboard} />
      <Tab.Screen name="Attendance" component={AttendanceScreen} />
      <Tab.Screen name="Students" component={StudentMonitor} />
      <Tab.Screen name="Assessments" component={AssessmentsScreen} />
      <Tab.Screen name="Parents" component={ParentEngagement} />
    </Tab.Navigator>
  );
}
