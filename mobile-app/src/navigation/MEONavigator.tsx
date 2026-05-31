import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import ClusterMonitor from '../screens/meo/ClusterMonitor';
import AttendanceIntelligence from '../screens/meo/AttendanceIntelligence';
import SchoolPerformance from '../screens/meo/SchoolPerformance';
import TeacherMonitor from '../screens/meo/TeacherMonitor';
import { CopilotNavigator } from './CopilotNavigator';
import ProfileScreen from '../screens/common/ProfileScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

export function MEONavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border, height: 60 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Cluster:     focused ? 'map' : 'map-outline',
            Attendance:  focused ? 'calendar' : 'calendar-outline',
            Performance: focused ? 'stats-chart' : 'stats-chart-outline',
            Teachers:    focused ? 'people' : 'people-outline',
            Copilot:     focused ? 'sparkles' : 'sparkles-outline',
            Profile:     focused ? 'person-circle' : 'person-circle-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Cluster" component={ClusterMonitor} />
      <Tab.Screen name="Attendance" component={AttendanceIntelligence} />
      <Tab.Screen name="Performance" component={SchoolPerformance} />
      <Tab.Screen name="Teachers" component={TeacherMonitor} />
      <Tab.Screen name="Copilot" component={CopilotNavigator} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
