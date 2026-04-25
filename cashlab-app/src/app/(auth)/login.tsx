/**
 * CashLab — Tela de Login (iOS Design System v2)
 *
 * Sem gradientes. iOS systemColors. Face ID / Touch ID.
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import Ionicons from '@expo/vector-icons/Ionicons';

import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/useAuthStore';
import { useSettingsStore } from '@/store/useSettingsStore';
import { useAppTheme } from '@/hooks/useAppTheme';
import { useBiometric } from '@/hooks/useBiometric';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setAuth = useAuthStore((s) => s.setAuth);
  const accessToken = useAuthStore((s) => s.accessToken);
  const biometricEnabled = useSettingsStore((s) => s.biometricEnabled);
  const { colors, spacing, radius } = useAppTheme();
  const { isAvailable: biometricAvailable, authenticate, biometricLabel } = useBiometric();

  // Auto Face ID if enabled and has saved session
  useEffect(() => {
    if (biometricEnabled && biometricAvailable && accessToken) {
      handleBiometricLogin();
    }
  }, [biometricEnabled, biometricAvailable]);

  const handleBiometricLogin = async () => {
    const success = await authenticate();
    if (success) {
      if (Platform.OS !== 'web') {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
      router.replace('/(tabs)');
    }
  };

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      setError('Preencha email e senha');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await authService.login(email.trim(), password);
      await setAuth(response.user, response.access_token, response.refresh_token);

      if (Platform.OS !== 'web') {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }

      router.replace('/(tabs)');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Erro ao fazer login';
      setError(message);

      if (Platform.OS !== 'web') {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = async (provider: 'google' | 'apple') => {
    Alert.alert(
      `Login com ${provider === 'google' ? 'Google' : 'Apple'}`,
      'Configure GOOGLE_CLIENT_ID ou APPLE_BUNDLE_ID no backend para ativar.',
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.bg }]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <SafeAreaView style={styles.safeArea}>
            {/* Logo */}
            <View style={styles.logoSection}>
              <View style={[styles.logoIcon, { backgroundColor: colors.blue }]}>
                <Ionicons name="wallet" size={32} color="#fff" />
              </View>
              <Text style={[styles.appName, { color: colors.label }]}>CashLab</Text>
              <Text style={[styles.tagline, { color: colors.secondaryLabel }]}>
                Controle financeiro familiar
              </Text>
            </View>

            {/* Form */}
            <View style={styles.formSection}>
              {/* Error */}
              {error && (
                <View style={[styles.errorCard, { backgroundColor: colors.surface }]}>
                  <View style={[styles.errorDot, { backgroundColor: colors.red }]} />
                  <Text style={[styles.errorText, { color: colors.red }]}>{error}</Text>
                </View>
              )}

              {/* Inputs — iOS grouped style */}
              <View style={[styles.inputGroup, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                <View style={styles.inputRow}>
                  <Text style={[styles.inputLabel, { color: colors.label }]}>Email</Text>
                  <TextInput
                    style={[styles.input, { color: colors.label }]}
                    placeholder="seu@email.com"
                    placeholderTextColor={colors.tertiaryLabel}
                    value={email}
                    onChangeText={(t) => { setEmail(t); setError(null); }}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    editable={!isLoading}
                  />
                </View>
                <View style={[styles.inputSep, { backgroundColor: colors.separator, marginLeft: spacing.base }]} />
                <View style={styles.inputRow}>
                  <Text style={[styles.inputLabel, { color: colors.label }]}>Senha</Text>
                  <TextInput
                    style={[styles.input, { color: colors.label, flex: 1 }]}
                    placeholder="••••••••"
                    placeholderTextColor={colors.tertiaryLabel}
                    value={password}
                    onChangeText={(t) => { setPassword(t); setError(null); }}
                    secureTextEntry={!showPassword}
                    autoCapitalize="none"
                    editable={!isLoading}
                  />
                  <Pressable onPress={() => setShowPassword(!showPassword)} hitSlop={12}>
                    <Ionicons
                      name={showPassword ? 'eye-off' : 'eye'}
                      size={20}
                      color={colors.tertiaryLabel}
                    />
                  </Pressable>
                </View>
              </View>

              {/* Login button */}
              <Pressable
                style={({ pressed }) => [
                  styles.loginButton,
                  { backgroundColor: colors.blue, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 },
                  isLoading && { opacity: 0.6 },
                ]}
                onPress={handleLogin}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.loginText}>Entrar</Text>
                )}
              </Pressable>

              {/* Face ID button */}
              {biometricAvailable && biometricEnabled && accessToken && (
                <Pressable
                  style={({ pressed }) => [
                    styles.biometricButton,
                    { borderColor: colors.separator, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 },
                  ]}
                  onPress={handleBiometricLogin}
                >
                  <Ionicons
                    name={Platform.OS === 'ios' ? 'scan' : 'finger-print'}
                    size={22}
                    color={colors.blue}
                  />
                  <Text style={[styles.biometricText, { color: colors.blue }]}>
                    Entrar com {biometricLabel}
                  </Text>
                </Pressable>
              )}

              {/* Divider */}
              <View style={styles.divider}>
                <View style={[styles.dividerLine, { backgroundColor: colors.separator }]} />
                <Text style={[styles.dividerText, { color: colors.tertiaryLabel }]}>ou</Text>
                <View style={[styles.dividerLine, { backgroundColor: colors.separator }]} />
              </View>

              {/* Social buttons */}
              <View style={styles.socialRow}>
                <Pressable
                  style={({ pressed }) => [
                    styles.socialButton,
                    { backgroundColor: colors.surface, borderRadius: radius.lg, opacity: pressed ? 0.85 : 1 },
                  ]}
                  onPress={() => handleSocialLogin('google')}
                >
                  <Ionicons name="logo-google" size={20} color="#DB4437" />
                  <Text style={[styles.socialText, { color: colors.label }]}>Google</Text>
                </Pressable>

                {Platform.OS === 'ios' && (
                  <Pressable
                    style={({ pressed }) => [
                      styles.socialButton,
                      { backgroundColor: colors.surface, borderRadius: radius.lg, opacity: pressed ? 0.85 : 1 },
                    ]}
                    onPress={() => handleSocialLogin('apple')}
                  >
                    <Ionicons name="logo-apple" size={20} color={colors.label} />
                    <Text style={[styles.socialText, { color: colors.label }]}>Apple</Text>
                  </Pressable>
                )}
              </View>
            </View>

            {/* Footer */}
            <View style={styles.footer}>
              <Text style={[styles.footerText, { color: colors.secondaryLabel }]}>
                Não tem conta?{' '}
                <Text
                  style={{ color: colors.blue, fontWeight: '600' }}
                  onPress={() => Alert.alert('Registro', 'Em breve')}
                >
                  Criar conta
                </Text>
              </Text>
            </View>
          </SafeAreaView>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  keyboardView: { flex: 1 },
  scrollContent: { flexGrow: 1 },
  safeArea: {
    flex: 1,
    paddingHorizontal: 20,
    justifyContent: 'center',
    gap: 32,
  },

  // Logo
  logoSection: { alignItems: 'center', gap: 8 },
  logoIcon: {
    width: 64,
    height: 64,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 4,
  },
  appName: { fontSize: 34, fontWeight: '800', letterSpacing: -1.5 },
  tagline: { fontSize: 15 },

  // Form
  formSection: { gap: 16 },

  // Error
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 10,
    gap: 10,
  },
  errorDot: { width: 8, height: 8, borderRadius: 4 },
  errorText: { fontSize: 14, fontWeight: '500', flex: 1 },

  // iOS grouped inputs
  inputGroup: { overflow: 'hidden' },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    height: 44,
  },
  inputLabel: {
    fontSize: 15,
    fontWeight: '400',
    width: 60,
  },
  input: {
    flex: 1,
    fontSize: 17,
    height: '100%',
  },
  inputSep: { height: 0.5 },

  // Login button
  loginButton: {
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
  },

  // Biometric button
  biometricButton: {
    height: 50,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
  },
  biometricText: {
    fontSize: 17,
    fontWeight: '600',
  },

  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginVertical: 4,
  },
  dividerLine: { flex: 1, height: 0.5 },
  dividerText: { fontSize: 13 },

  // Social
  socialRow: { flexDirection: 'row', gap: 8 },
  socialButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    height: 44,
  },
  socialText: { fontSize: 15, fontWeight: '500' },

  // Footer
  footer: { alignItems: 'center', paddingVertical: 16 },
  footerText: { fontSize: 15 },
});
