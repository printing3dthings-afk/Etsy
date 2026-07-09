import React from 'react';
import { TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';

// Pinned to every stack's header so Chat (and therefore voice) is always one
// tap away, regardless of which of the 4 nav sections the user is in.
export default function ChatHeaderButton() {
  const navigation = useNavigation();
  return (
    <TouchableOpacity
      onPress={() => navigation.navigate('Chat')}
      style={{ paddingHorizontal: 12, paddingVertical: 6 }}
    >
      <Ionicons name="chatbubble-ellipses" size={22} color={colors.gold} />
    </TouchableOpacity>
  );
}
