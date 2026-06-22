import 'react-native-gesture-handler';
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import { colors } from './src/theme';
import { sectionStackOptions } from './src/navigation/stackOptions';
import DrawerMenuButton from './src/navigation/DrawerMenuButton';

import DashboardScreen from './src/screens/DashboardScreen';
import ChatScreen      from './src/screens/ChatScreen';

import CommandCenterScreen from './src/screens/CommandCenterScreen';
import CoreScreen          from './src/screens/CoreScreen';
import AgentsScreen        from './src/screens/AgentsScreen';

import TasksScreen               from './src/screens/TasksScreen';
import ActionCenterScreen        from './src/screens/ActionCenterScreen';
import CalendarScreen            from './src/screens/CalendarScreen';
import MemoryScreen              from './src/screens/MemoryScreen';
import ConversationsScreen       from './src/screens/ConversationsScreen';
import ConversationDetailScreen  from './src/screens/ConversationDetailScreen';
import KnowledgeBaseScreen       from './src/screens/KnowledgeBaseScreen';
import KbDocScreen               from './src/screens/KbDocScreen';

import ToolsSkillsScreen from './src/screens/ToolsSkillsScreen';
import WorkflowsScreen   from './src/screens/WorkflowsScreen';
import StudioScreen      from './src/screens/StudioScreen';

import ListingsScreen    from './src/screens/ListingsScreen';
import ProductsScreen    from './src/screens/ProductsScreen';
import BrandKitScreen    from './src/screens/BrandKitScreen';
import FilesScreen       from './src/screens/FilesScreen';
import ConnectionsScreen from './src/screens/ConnectionsScreen';
import SecurityScreen    from './src/screens/SecurityScreen';

const Drawer = createDrawerNavigator();
const FrankStack = createNativeStackNavigator();
const KnowledgeStack = createNativeStackNavigator();
const ToolsStack = createNativeStackNavigator();
const ShopStack = createNativeStackNavigator();

const NAV_THEME = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: colors.bg,
    card:       colors.card,
    border:     colors.cardBorder,
    primary:    colors.gold,
    text:       colors.textPrimary,
  },
};

function FrankSection() {
  return (
    <FrankStack.Navigator screenOptions={sectionStackOptions}>
      <FrankStack.Screen name="CommandCenter" component={CommandCenterScreen} options={{ title: 'Command Center', headerLeft: () => <DrawerMenuButton /> }} />
      <FrankStack.Screen name="Core" component={CoreScreen} options={{ title: 'Core' }} />
      <FrankStack.Screen name="Agents" component={AgentsScreen} options={{ title: 'Agents' }} />
    </FrankStack.Navigator>
  );
}

function KnowledgeSection() {
  return (
    <KnowledgeStack.Navigator screenOptions={sectionStackOptions}>
      <KnowledgeStack.Screen name="Tasks" component={TasksScreen} options={{ title: 'Tasks', headerLeft: () => <DrawerMenuButton /> }} />
      <KnowledgeStack.Screen name="ActionCenter" component={ActionCenterScreen} options={{ title: 'Action Center' }} />
      <KnowledgeStack.Screen name="Calendar" component={CalendarScreen} options={{ title: 'Calendar' }} />
      <KnowledgeStack.Screen name="Memory" component={MemoryScreen} options={{ title: 'Memory' }} />
      <KnowledgeStack.Screen name="Conversations" component={ConversationsScreen} options={{ title: 'Conversations' }} />
      <KnowledgeStack.Screen name="ConversationDetail" component={ConversationDetailScreen} options={{ title: 'Conversation' }} />
      <KnowledgeStack.Screen name="KnowledgeBase" component={KnowledgeBaseScreen} options={{ title: 'Knowledge Base' }} />
      <KnowledgeStack.Screen name="KbDoc" component={KbDocScreen} options={{ title: 'Document' }} />
    </KnowledgeStack.Navigator>
  );
}

function ToolsSection() {
  return (
    <ToolsStack.Navigator screenOptions={sectionStackOptions}>
      <ToolsStack.Screen name="ToolsSkills" component={ToolsSkillsScreen} options={{ title: 'Tools & Skills', headerLeft: () => <DrawerMenuButton /> }} />
      <ToolsStack.Screen name="Workflows" component={WorkflowsScreen} options={{ title: 'Workflows' }} />
      <ToolsStack.Screen name="Studio" component={StudioScreen} options={{ title: 'Studio' }} />
    </ToolsStack.Navigator>
  );
}

function ShopSection() {
  return (
    <ShopStack.Navigator screenOptions={sectionStackOptions}>
      <ShopStack.Screen name="Listings" component={ListingsScreen} options={{ title: 'Listings', headerLeft: () => <DrawerMenuButton /> }} />
      <ShopStack.Screen name="Products" component={ProductsScreen} options={{ title: 'Products' }} />
      <ShopStack.Screen name="BrandKit" component={BrandKitScreen} options={{ title: 'Brand Kit' }} />
      <ShopStack.Screen name="Files" component={FilesScreen} options={{ title: 'Files' }} />
      <ShopStack.Screen name="Connections" component={ConnectionsScreen} options={{ title: 'Connections' }} />
      <ShopStack.Screen name="Security" component={SecurityScreen} options={{ title: 'Security' }} />
    </ShopStack.Navigator>
  );
}

const DRAWER_ICONS = {
  Dashboard: 'bar-chart-outline',
  Chat:      'chatbubble-outline',
  Frank:     'sparkles-outline',
  Knowledge: 'book-outline',
  Tools:     'construct-outline',
  Shop:      'storefront-outline',
};

export default function App() {
  return (
    <NavigationContainer theme={NAV_THEME}>
      <StatusBar style="light" />
      <Drawer.Navigator
        screenOptions={({ route }) => ({
          // Dashboard/Chat are leaf screens with no header of their own — the
          // drawer supplies one. The 4 section routes wrap their own
          // Stack.Navigator (via sectionStackOptions), which renders its own
          // header; showing the drawer's header too would double up.
          headerShown: route.name === 'Dashboard' || route.name === 'Chat',
          headerStyle: { backgroundColor: colors.card },
          headerTintColor: colors.textPrimary,
          headerTitleStyle: { color: colors.textPrimary, fontWeight: '700' },
          drawerStyle: { backgroundColor: colors.card, width: 250 },
          drawerActiveTintColor: colors.gold,
          drawerInactiveTintColor: colors.textSecondary,
          drawerActiveBackgroundColor: colors.inputBg,
          drawerLabelStyle: { fontSize: 14, fontWeight: '600' },
          drawerIcon: ({ color, size }) => (
            <Ionicons name={DRAWER_ICONS[route.name]} size={size} color={color} />
          ),
        })}
      >
        <Drawer.Screen name="Dashboard" component={DashboardScreen} />
        <Drawer.Screen name="Chat" component={ChatScreen} />
        <Drawer.Screen name="Frank" component={FrankSection} />
        <Drawer.Screen name="Knowledge" component={KnowledgeSection} />
        <Drawer.Screen name="Tools" component={ToolsSection} />
        <Drawer.Screen name="Shop" component={ShopSection} />
      </Drawer.Navigator>
    </NavigationContainer>
  );
}
