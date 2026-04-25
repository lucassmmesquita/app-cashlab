/**
 * CashLab — Settings (iOS Design System v2)
 *
 * Seções: Aparência (tema), Segurança (Face ID), Conta (logout).
 * iOS grouped table style.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Pressable, Switch, Alert, Platform, RefreshControl } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScrollView } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';

import { useAuthStore } from '@/store/useAuthStore';
import { useSettingsStore } from '@/store/useSettingsStore';
import { useAppTheme } from '@/hooks/useAppTheme';
import { useBiometric } from '@/hooks/useBiometric';

type ThemeMode = 'system' | 'light' | 'dark';

export default function SettingsScreen() {
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const { colors, radius, spacing } = useAppTheme();

  const themeMode = useSettingsStore((s) => s.themeMode);
  const setThemeMode = useSettingsStore((s) => s.setThemeMode);
  const biometricEnabled = useSettingsStore((s) => s.biometricEnabled);
  const setBiometricEnabled = useSettingsStore((s) => s.setBiometricEnabled);

  const { isAvailable: biometricAvailable, biometricLabel } = useBiometric();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await new Promise(r => setTimeout(r, 500));
    setRefreshing(false);
  }, []);

  const handleLogout = () => {
    Alert.alert('Sair', 'Deseja sair da conta?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Sair',
        style: 'destructive',
        onPress: () => {
          clearAuth();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  const themeOptions: { value: ThemeMode; label: string }[] = [
    { value: 'system', label: 'Sistema' },
    { value: 'light', label: 'Claro' },
    { value: 'dark', label: 'Escuro' },
  ];

  return (
    <View style={[styles.container, { backgroundColor: colors.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <ScrollView
          contentContainerStyle={[styles.scrollContent, { padding: spacing.lg }]}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />
          }
        >
          <Text style={[styles.largeTitle, { color: colors.label }]}>Settings</Text>

          {/* ── Conta ─────────────────────────────────── */}
          {user && (
            <>
              <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>CONTA</Text>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                <View style={styles.row}>
                  <View style={[styles.avatar, { backgroundColor: colors.green }]}>
                    <Text style={styles.avatarText}>{user.name?.[0]?.toUpperCase() || 'U'}</Text>
                  </View>
                  <View style={styles.rowBody}>
                    <Text style={[styles.rowTitle, { color: colors.label }]}>{user.name}</Text>
                    <Text style={[styles.rowSub, { color: colors.secondaryLabel }]}>{user.email}</Text>
                  </View>
                </View>
              </View>
            </>
          )}

          {/* ── Aparência ─────────────────────────────── */}
          <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>APARÊNCIA</Text>
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.rowSimple}>
              <Text style={[styles.rowTitle, { color: colors.label }]}>Tema</Text>
            </View>
            <View style={[styles.segmentControl, { backgroundColor: colors.segmentBg, borderRadius: 8, marginHorizontal: 16, marginBottom: 16 }]}>
              {themeOptions.map((opt) => (
                <Pressable
                  key={opt.value}
                  style={[
                    styles.segOption,
                    themeMode === opt.value && [styles.segActive, { backgroundColor: colors.segmentActive, borderRadius: 7 }],
                  ]}
                  onPress={() => setThemeMode(opt.value)}
                >
                  <Text
                    style={[
                      styles.segText,
                      { color: themeMode === opt.value ? colors.label : colors.secondaryLabel },
                      themeMode === opt.value && { fontWeight: '600' },
                    ]}
                  >
                    {opt.label}
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>

          {/* ── Segurança ─────────────────────────────── */}
          <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>SEGURANÇA</Text>
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.switchRow}>
              <View style={styles.switchRowLeft}>
                <Ionicons
                  name={Platform.OS === 'ios' ? 'scan' : 'finger-print'}
                  size={22}
                  color={colors.blue}
                  style={{ marginRight: 12 }}
                />
                <Text style={[styles.rowTitle, { color: colors.label }]}>{biometricLabel}</Text>
              </View>
              <Switch
                value={biometricEnabled}
                onValueChange={(val) => {
                  if (!biometricAvailable) {
                    Alert.alert(
                      `${biometricLabel} indisponível`,
                      `Configure ${biometricLabel} nas configurações do seu dispositivo primeiro.`,
                    );
                    return;
                  }
                  setBiometricEnabled(val);
                }}
                trackColor={{ false: colors.segmentBg, true: colors.green }}
                ios_backgroundColor={colors.segmentBg}
              />
            </View>
            <Text style={[styles.footnote, { color: colors.secondaryLabel, paddingHorizontal: 16, paddingBottom: 12 }]}>
              Use {biometricLabel} para desbloquear o app rapidamente sem digitar sua senha.
            </Text>
          </View>

          {/* ── Ação ─────────────────────────────────── */}
          <View style={{ marginTop: 24 }}>
            <Pressable
              style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}
              onPress={handleLogout}
            >
              <View style={[styles.rowSimple, { justifyContent: 'center' }]}>
                <Text style={[styles.rowTitle, { color: colors.red, textAlign: 'center' }]}>Sair da conta</Text>
              </View>
            </Pressable>
          </View>

          <Text style={[styles.footer, { color: colors.tertiaryLabel }]}>
            CashLab v1.0.0 · Abril 2026
          </Text>

          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: { gap: 0 },

  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5, marginBottom: 24 },

  // Section labels
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 24,
    marginBottom: 8,
    paddingHorizontal: 4,
  },

  // Card
  card: { overflow: 'hidden', marginBottom: 0 },

  // Rows
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    paddingHorizontal: 16,
  },
  rowSimple: {
    padding: 12,
    paddingHorizontal: 16,
  },
  rowBody: { flex: 1, gap: 1 },
  rowTitle: { fontSize: 17, fontWeight: '400' },
  rowSub: { fontSize: 13 },

  // Avatar
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: '700' },

  // Segment control
  segmentControl: {
    flexDirection: 'row',
    padding: 2,
  },
  segOption: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 7,
  },
  segActive: {},
  segText: { fontSize: 13, fontWeight: '500' },

  // Switch row
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    paddingHorizontal: 16,
  },
  switchRowLeft: { flexDirection: 'row', alignItems: 'center' },

  // Footnote
  footnote: { fontSize: 13, lineHeight: 18 },

  // Footer
  footer: {
    textAlign: 'center',
    fontSize: 11,
    marginTop: 32,
  },
});
