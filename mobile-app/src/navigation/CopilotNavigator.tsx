import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import AdminCopilotHomeScreen from '../screens/copilot/AdminCopilotHomeScreen';
import CircularSummarizerScreen from '../screens/copilot/CircularSummarizerScreen';
import LetterGeneratorScreen from '../screens/copilot/LetterGeneratorScreen';
import ReportGeneratorScreen from '../screens/copilot/ReportGeneratorScreen';
import TranslationScreen from '../screens/copilot/TranslationScreen';
import SchoolHealthAnalyzerScreen from '../screens/copilot/SchoolHealthAnalyzerScreen';
import {
  EarlyWarningAssistantScreen,
  TeacherVacancyAssistantScreen,
  GovernanceCommunicationAssistantScreen,
  ClusterGovernanceBriefingScreen,
  MEOCopilotHomeScreen,
  MEOReportFormScreen,
  MEOReportHistoryScreen,
  MEOReportDetailScreen,
} from '../screens/copilot/MEOCopilotAssistantScreens';
import {
  DistrictIntelligenceScreen,
  MandalPerformanceScreen,
  DistrictRiskScreen,
  TeacherRationalizationScreen,
  GovernanceCommunicationScreen,
} from '../screens/copilot/DEOCopilotScreens';

export type CopilotStackParams = {
  CopilotHome:     undefined;
  Circular:        undefined;
  LetterGenerator: undefined;
  Report:          undefined;
  Translation:     undefined;
  SchoolHealthAnalyzer: undefined;
  EarlyWarningAssistant: undefined;
  TeacherVacancyAssistant: undefined;
  GovernanceCommunicationAssistant: undefined;
  ClusterGovernanceBriefing: undefined;
  MEOCopilotHome:  undefined;
  MEOReportForm:   { template: any };
  MEOReportHistory: undefined;
  MEOReportDetail: { reportId: number };
  DEODistrictIntelligence: undefined;
  DEOMandalPerformance: undefined;
  DEORiskMonitor: undefined;
  DEOTeacherRationalization: undefined;
  DEOGovernanceCommunication: undefined;
};

const Stack = createNativeStackNavigator<CopilotStackParams>();

export function CopilotNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CopilotHome"     component={AdminCopilotHomeScreen} />
      <Stack.Screen name="Circular"        component={CircularSummarizerScreen} />
      <Stack.Screen name="LetterGenerator" component={LetterGeneratorScreen} />
      <Stack.Screen name="Report"          component={ReportGeneratorScreen} />
      <Stack.Screen name="Translation"     component={TranslationScreen} />
      <Stack.Screen name="SchoolHealthAnalyzer" component={SchoolHealthAnalyzerScreen} />
      <Stack.Screen name="EarlyWarningAssistant" component={EarlyWarningAssistantScreen} />
      <Stack.Screen name="TeacherVacancyAssistant" component={TeacherVacancyAssistantScreen} />
      <Stack.Screen name="GovernanceCommunicationAssistant" component={GovernanceCommunicationAssistantScreen} />
      <Stack.Screen name="ClusterGovernanceBriefing" component={ClusterGovernanceBriefingScreen} />
      <Stack.Screen name="MEOCopilotHome"   component={MEOCopilotHomeScreen} />
      <Stack.Screen name="MEOReportForm"    component={MEOReportFormScreen} />
      <Stack.Screen name="MEOReportHistory"  component={MEOReportHistoryScreen} />
      <Stack.Screen name="MEOReportDetail"   component={MEOReportDetailScreen} />
      <Stack.Screen name="DEODistrictIntelligence" component={DistrictIntelligenceScreen} />
      <Stack.Screen name="DEOMandalPerformance" component={MandalPerformanceScreen} />
      <Stack.Screen name="DEORiskMonitor" component={DistrictRiskScreen} />
      <Stack.Screen name="DEOTeacherRationalization" component={TeacherRationalizationScreen} />
      <Stack.Screen name="DEOGovernanceCommunication" component={GovernanceCommunicationScreen} />
    </Stack.Navigator>
  );
}