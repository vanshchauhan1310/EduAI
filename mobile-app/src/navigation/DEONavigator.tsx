import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import DistrictDashboard from '../screens/deo/DistrictDashboard';
import SchoolHealthMonitor from '../screens/deo/SchoolHealthMonitor';
import DropoutMonitor from '../screens/deo/DropoutMonitor';
import GovernanceInsights from '../screens/deo/GovernanceInsights';
import { CopilotNavigator } from './CopilotNavigator';
import ProfileScreen from '../screens/common/ProfileScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();

export function DEONavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarStyle: { backgroundColor: Colors.white, borderTopColor: Colors.border, height: 60 },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            District: focused ? 'grid' : 'grid-outline',
            'School Health': focused ? 'school' : 'school-outline',
            Dropout: focused ? 'alert-circle' : 'alert-circle-outline',
            Insights: focused ? 'bulb' : 'bulb-outline',
            Copilot: focused ? 'sparkles' : 'sparkles-outline',
            Profile: focused ? 'person-circle' : 'person-circle-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="District" component={DistrictDashboard} />
      <Tab.Screen name="School Health" component={SchoolHealthMonitor} />
      <Tab.Screen name="Dropout" component={DropoutMonitor} />
      <Tab.Screen name="Insights" component={GovernanceInsights} />
      <Tab.Screen name="Copilot" component={CopilotNavigator} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
