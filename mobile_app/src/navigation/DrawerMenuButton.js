import React from 'react';
import { TouchableOpacity } from 'react-native';
import { useNavigation, DrawerActions } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';

// The first screen of a nested section Stack doesn't get the Drawer's
// auto-injected hamburger (that only happens for direct Drawer.Screen
// children) — this wires one in manually via the parent Drawer navigator.
export default function DrawerMenuButton() {
  const navigation = useNavigation();
  return (
    <TouchableOpacity
      onPress={() => navigation.dispatch(DrawerActions.toggleDrawer())}
      style={{ paddingHorizontal: 12, paddingVertical: 6 }}
    >
      <Ionicons name="menu" size={24} color={colors.textPrimary} />
    </TouchableOpacity>
  );
}
