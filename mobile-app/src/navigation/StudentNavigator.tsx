import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import StudentDashboardScreen from '../screens/student/StudentDashboardScreen';
import AssignmentsScreen from '../screens/student/AssignmentsScreen';
import AttendanceScreen from '../screens/student/AttendanceScreen';
import PerformanceScreen from '../screens/student/PerformanceScreen';
import AIAssistantScreen from '../screens/student/AIAssistantScreen';
import ProfileScreen from '../screens/common/ProfileScreen';
import StudentAssessmentScreen from '../screens/student/StudentAssessmentScreen';
import StudentAssessmentFeedbackScreen from '../screens/student/StudentAssessmentFeedbackScreen';
import CareerRecommenderScreen from '../screens/student/CareerRecommenderScreen';
import CareerSurveyScreen from '../screens/student/CareerSurveyScreen';
import { Colors } from '../theme';

const Tab = createBottomTabNavigator();
const AssessmentsStack = createNativeStackNavigator();
const CareerStack = createNativeStackNavigator();

function AssessmentsStackScreen() {
  return (
    <AssessmentsStack.Navigator
      screenOptions={{
        headerShown: false,
        animationEnabled: true,
      }}
    >
      <AssessmentsStack.Screen name="FeedbackHome" component={StudentAssessmentFeedbackScreen} />
      <AssessmentsStack.Screen
        name="TakeAssessment"
        component={StudentAssessmentScreen}
        options={{ animationEnabled: true }}
      />
    </AssessmentsStack.Navigator>
  );
}

function CareerStackScreen() {
  return (
    <CareerStack.Navigator screenOptions={{ headerShown: false }}>
      <CareerStack.Screen name="CareerHome" component={CareerRecommenderScreen} />
      <CareerStack.Screen name="CareerSurvey" component={CareerSurveyScreen} />
    </CareerStack.Navigator>
  );
}

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
            Dashboard:    focused ? 'grid' : 'grid-outline',
            Assignments:  focused ? 'book' : 'book-outline',
            Attendance:   focused ? 'calendar' : 'calendar-outline',
            Performance:  focused ? 'trophy' : 'trophy-outline',
            Career:       focused ? 'compass' : 'compass-outline',
            Assessments:  focused ? 'clipboard' : 'clipboard-outline',
            'AI Tutor':   focused ? 'sparkles' : 'sparkles-outline',
            Profile:      focused ? 'person-circle' : 'person-circle-outline',
          };
          return <Ionicons name={icons[route.name] ?? 'apps'} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={StudentDashboardScreen} options={{ title: 'Dashboard' }} />
      {/* Hidden from the tab bar — reachable via the Dashboard's Quick Insights cards */}
      <Tab.Screen name="Assignments" component={AssignmentsScreen} options={{ tabBarButton: () => null }} />
      <Tab.Screen name="Attendance" component={AttendanceScreen} options={{ tabBarButton: () => null }} />
      <Tab.Screen name="Performance" component={PerformanceScreen} options={{ tabBarButton: () => null }} />
      <Tab.Screen name="Career" component={CareerStackScreen} options={{ tabBarButton: () => null }} />
      <Tab.Screen name="Assessments" component={AssessmentsStackScreen} />
      <Tab.Screen name="AI Tutor" component={AIAssistantScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
