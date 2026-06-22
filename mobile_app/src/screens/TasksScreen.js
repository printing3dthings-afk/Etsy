import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, TextInput, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api';
import { colors, spacing, radius, typography } from '../theme';
import { ScreenHeader, Loading, ErrorRetry, Empty } from '../components/Shared';

export default function TasksScreen() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [text, setText] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const resp = await api.todos();
      setTodos(resp.todos ?? resp ?? []);
    } catch (e) {
      setError(e.message || 'Failed to load tasks');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const addTodo = async () => {
    const t = text.trim();
    if (!t) return;
    setText('');
    try {
      await api.addTodo(t);
      load();
    } catch (e) {
      setError(e.message || 'Failed to add task');
    }
  };

  const toggle = async (id, done) => {
    try {
      await api.toggleTodo(id, !done);
      load();
    } catch (e) {
      setError(e.message || 'Failed to update task');
    }
  };

  const remove = async (id) => {
    try {
      await api.deleteTodo(id);
      load();
    } catch (e) {
      setError(e.message || 'Failed to delete task');
    }
  };

  return (
    <View style={styles.container}>
      <ScreenHeader title="Tasks" sub="/api/todos" />
      <View style={styles.composer}>
        <TextInput
          style={styles.input}
          placeholder="Add a task…"
          placeholderTextColor={colors.textMuted}
          value={text}
          onChangeText={setText}
          onSubmitEditing={addTodo}
          returnKeyType="done"
        />
        <TouchableOpacity style={styles.addBtn} onPress={addTodo}>
          <Ionicons name="add" size={22} color="#0D1B2A" />
        </TouchableOpacity>
      </View>

      {loading && !refreshing ? (
        <Loading />
      ) : error ? (
        <ErrorRetry message={error} onRetry={load} />
      ) : todos.length === 0 ? (
        <Empty label="No tasks yet" />
      ) : (
        <FlatList
          data={todos}
          keyExtractor={(t) => String(t.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />}
          renderItem={({ item }) => (
            <View style={styles.row}>
              <TouchableOpacity style={styles.checkRow} onPress={() => toggle(item.id, item.done)}>
                <Ionicons
                  name={item.done ? 'checkbox' : 'square-outline'}
                  size={22}
                  color={item.done ? colors.success : colors.textMuted}
                />
                <Text style={[styles.text, item.done && styles.textDone]} numberOfLines={2}>{item.text}</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => remove(item.id)}>
                <Ionicons name="trash-outline" size={18} color={colors.error} />
              </TouchableOpacity>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },

  composer: { flexDirection: 'row', padding: spacing.md, gap: spacing.sm },
  input: {
    flex: 1,
    backgroundColor: colors.inputBg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
    color: colors.textPrimary,
    ...typography.body,
  },
  addBtn: {
    width: 44, height: 44, borderRadius: radius.md,
    backgroundColor: colors.gold, alignItems: 'center', justifyContent: 'center',
  },

  list: { paddingHorizontal: spacing.md, paddingBottom: spacing.md },
  row: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.card, borderRadius: radius.md, borderWidth: 1, borderColor: colors.cardBorder,
    padding: spacing.md, marginBottom: spacing.sm,
  },
  checkRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flex: 1, marginRight: spacing.sm },
  text: { ...typography.body, color: colors.textPrimary, flex: 1 },
  textDone: { color: colors.textMuted, textDecorationLine: 'line-through' },
});
