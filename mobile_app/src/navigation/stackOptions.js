import React from 'react';
import ChatHeaderButton from './ChatHeaderButton';
import { colors } from '../theme';

// Shared by every section Stack.Navigator so headers look consistent and
// Chat is reachable via the header-right button from any screen.
export const sectionStackOptions = {
  headerStyle: { backgroundColor: colors.card },
  headerTintColor: colors.textPrimary,
  headerTitleStyle: { color: colors.textPrimary, fontWeight: '700' },
  headerRight: () => <ChatHeaderButton />,
};
