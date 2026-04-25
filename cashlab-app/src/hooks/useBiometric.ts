/**
 * CashLab — Biometric authentication hook (Face ID / Touch ID)
 *
 * Usa expo-local-authentication para autenticação biométrica.
 * O usuário habilita em Configurações → Segurança.
 */
import { useState, useEffect, useCallback } from 'react';
import { Platform } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';

export interface BiometricInfo {
  isAvailable: boolean;
  biometricType: 'face-id' | 'touch-id' | 'fingerprint' | null;
}

export function useBiometric() {
  const [info, setInfo] = useState<BiometricInfo>({
    isAvailable: false,
    biometricType: null,
  });

  useEffect(() => {
    checkBiometric();
  }, []);

  const checkBiometric = async () => {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();

      if (!compatible || !enrolled) {
        setInfo({ isAvailable: false, biometricType: null });
        return;
      }

      const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
      let biometricType: BiometricInfo['biometricType'] = null;

      if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        biometricType = 'face-id';
      } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        biometricType = Platform.OS === 'ios' ? 'touch-id' : 'fingerprint';
      }

      setInfo({ isAvailable: true, biometricType });
    } catch {
      setInfo({ isAvailable: false, biometricType: null });
    }
  };

  const authenticate = useCallback(async (): Promise<boolean> => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Desbloquear CashLab',
        fallbackLabel: 'Usar senha',
        disableDeviceFallback: false,
        cancelLabel: 'Cancelar',
      });
      return result.success;
    } catch {
      return false;
    }
  }, []);

  /** Label amigável para UI */
  const biometricLabel = info.biometricType === 'face-id'
    ? 'Face ID'
    : info.biometricType === 'touch-id'
    ? 'Touch ID'
    : info.biometricType === 'fingerprint'
    ? 'Impressão digital'
    : 'Biometria';

  return {
    ...info,
    authenticate,
    biometricLabel,
  };
}
