import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import TeacherDashboardScreen from '../screens/teacher/TeacherDashboardScreen';
import AttendanceScreen from '../screens/teacher/AttendanceScreen';
import AssignmentsScreen from '../screens/teacher/AssignmentsScreen';
import AssessmentsListScreen from '../screens/teacher/AssessmentsListScreen';
import AssessmentResultsScreen from '../screens/teacher/AssessmentResultsScreen';
import AIAssistantScreen from '../screens/teacher/AIAssistantScreen';
import ProfileScreen from '../screens/common/ProfileScreen';
import CreateAssessmentScreen from '../screens/teacher/CreateAssessmentScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();
const AssessmentsStack = createNativeStackNavigator();

function AssessmentsStackScreen() {
  return (
    <AssessmentsStack.Navigator
      screenOptions={{
        headerShown: false,
        animationEnabled: true,
      }}
    >
      <AssessmentsStack.Screen name="AssessmentsList" component={AssessmentsListScreen} />
      <AssessmentsStack.Screen name="CreateAssessment" component={CreateAssessmentScreen} options={{ animationEnabled: true }} />
      <AssessmentsStack.Screen name="AssessmentResults" component={AssessmentResultsScreen} options={{ animationEnabled: true }} />
    </AssessmentsStack.Navigator>
  );
}

export function TeacherNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.primary[600],
        tabBarInactiveTintColor: Colors.neutral[400],
        tabBarScrollEnabled: true,
        tabBarStyle: { 
          backgroundColor: Colors.white, 
          borderTopColor: Colors.border, 
          height: 65,
          paddingBottom: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '500',
          marginBottom: 4,
        },
        tabBarIcon: ({ focused, color, size }) => {
          const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
            Dashboard:    focused ? 'grid' : 'grid-outline',
            Attendance:   focused ? 'checkbox' : 'checkbox-outline',
            Assignments:  focused ? 'book' : 'book-outline',
            Assessments:  focused ? 'clipboard' : 'clipboard-outline',
            'AI Assist':  focused ? 'sparkles' : 'sparkles-outline',
            Profile:      focused ? 'person-circle' : 'person-circle-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={TeacherDashboardScreen} options={{ title: 'Dashboard' }} />
      {/* Hidden from the tab bar — reachable via the Dashboard's Quick Actions */}
      <Tab.Screen name="Attendance" component={AttendanceScreen} options={{ title: 'Attendance', tabBarButton: () => null }} />
      <Tab.Screen name="Assignments" component={AssignmentsScreen} options={{ title: 'Assignments', tabBarButton: () => null }} />
      <Tab.Screen
        name="Assessments"
        component={AssessmentsStackScreen}
        options={{ title: 'Assessments' }}
        listeners={({ navigation }) => ({
          tabPress: (e) => {
            // Always land on the assessments list, never wherever the nested stack was last left (e.g. the create wizard)
            e.preventDefault();
            navigation.navigate('Assessments', { screen: 'AssessmentsList' });
          },
        })}
      />
      <Tab.Screen name="AI Assist" component={AIAssistantScreen} options={{ title: 'AI Assist' }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ title: 'Profile' }} />
    </Tab.Navigator>
  );
}
