import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import DashboardScreen from './src/screens/DashboardScreen';
import ChatScreen      from './src/screens/ChatScreen';
import ListingsScreen  from './src/screens/ListingsScreen';
import { colors }      from './src/theme';

const Tab = createBottomTabNavigator();

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

export default function App() {
  return (
    <NavigationContainer theme={NAV_THEME}>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: {
            backgroundColor: colors.card,
            borderTopColor:  colors.cardBorder,
            borderTopWidth:  1,
            height:          60,
            paddingBottom:   8,
          },
          tabBarActiveTintColor:   colors.gold,
          tabBarInactiveTintColor: colors.textMuted,
          tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
          tabBarIcon: ({ focused, color, size }) => {
            const icons = {
              Dashboard: focused ? 'bar-chart'      : 'bar-chart-outline',
              Chat:      focused ? 'chatbubble'      : 'chatbubble-outline',
              Listings:  focused ? 'pricetags'       : 'pricetags-outline',
            };
            return <Ionicons name={icons[route.name]} size={size} color={color} />;
          },
        })}
      >
        <Tab.Screen name="Dashboard" component={DashboardScreen} />
        <Tab.Screen name="Chat"      component={ChatScreen} />
        <Tab.Screen name="Listings"  component={ListingsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
