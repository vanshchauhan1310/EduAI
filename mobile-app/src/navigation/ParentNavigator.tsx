import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import AttendanceTracking from '../screens/parent/AttendanceTracking';
import ChildPerformance from '../screens/parent/ChildPerformance';
import NotificationsScreen from '../screens/parent/NotificationsScreen';
import ComplaintsScreen from '../screens/parent/ComplaintsScreen';
import ProfileScreen from '../screens/common/ProfileScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

export function ParentNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border, height: 60 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Attendance:   focused ? 'calendar' : 'calendar-outline',
            Performance:  focused ? 'stats-chart' : 'stats-chart-outline',
            Alerts:       focused ? 'notifications' : 'notifications-outline',
            Complaints:   focused ? 'chatbubbles' : 'chatbubbles-outline',
            Profile:      focused ? 'person-circle' : 'person-circle-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Attendance" component={AttendanceTracking} />
      <Tab.Screen name="Performance" component={ChildPerformance} />
      <Tab.Screen name="Alerts" component={NotificationsScreen} />
      <Tab.Screen name="Complaints" component={ComplaintsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
