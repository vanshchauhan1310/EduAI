import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import TutorHomeScreen from '../screens/student/TutorHomeScreen';
import TutorSessionScreen from '../screens/student/TutorSessionScreen';
import TutorChatScreen from '../screens/student/TutorChatScreen';
import TutorKnowledgeBaseScreen from '../screens/student/TutorKnowledgeBaseScreen';
import { TutorLanguage } from '../types';

export type TutorStackParams = {
  TutorHome: undefined;
  TutorSession: { subject: string; chapter: string; concept: string; mastery: number; language: TutorLanguage };
  TutorChat: undefined;
  TutorKnowledgeBase: { subject?: string; chapter?: string } | undefined;
};

const Stack = createNativeStackNavigator<TutorStackParams>();

export function TutorNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="TutorHome" component={TutorHomeScreen} />
      <Stack.Screen name="TutorSession" component={TutorSessionScreen} />
      <Stack.Screen name="TutorChat" component={TutorChatScreen} />
      <Stack.Screen name="TutorKnowledgeBase" component={TutorKnowledgeBaseScreen} />
    </Stack.Navigator>
  );
}
