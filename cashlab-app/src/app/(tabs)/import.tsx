/**
 * CashLab — Tela de Upload de Faturas (iOS Design System v2)
 *
 * Fluxo: Selecionar PDF → Upload → Preview transações → Confirmar
 */
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as DocumentPicker from 'expo-document-picker';
import Ionicons from '@expo/vector-icons/Ionicons';

import { useAppTheme } from '@/hooks/useAppTheme';
import { invoiceService } from '@/services/invoiceService';
import type { UploadPreview, ParsedTransaction } from '@/services/invoiceService';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { BANK_COLORS } from '@/utils/colors';

type Step = 'idle' | 'uploading' | 'preview' | 'confirming' | 'done';

export default function ImportScreen() {
  const { colors, radius, spacing } = useAppTheme();

  const [step, setStep] = useState<Step>('idle');
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    handleReset();
    await new Promise(r => setTimeout(r, 500));
    setRefreshing(false);
  }, []);

  const handlePickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets?.[0]) return;

      const asset = result.assets[0];
      setFileName(asset.name);
      setStep('uploading');
      setError(null);

      const data = await invoiceService.upload(asset.uri, asset.name);
      setPreview(data);
      setStep('preview');
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Erro ao processar PDF';
      setError(message);
      setStep('idle');
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;

    setStep('confirming');
    try {
      await invoiceService.confirmImport(preview.file_id);
      setStep('done');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao confirmar importação');
      setStep('preview');
    }
  };

  const handleReset = () => {
    setStep('idle');
    setPreview(null);
    setError(null);
    setFileName('');
  };

  const bankLabel = (bank: string) => {
    const labels: Record<string, string> = { bv: 'Banco BV', itau: 'Itaú', nubank: 'Nubank' };
    return labels[bank] || bank;
  };

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
          <Text style={[styles.largeTitle, { color: colors.label }]}>Cartões</Text>

          {/* Error */}
          {error && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
              <View style={styles.errorRow}>
                <View style={[styles.dot, { backgroundColor: colors.red }]} />
                <Text style={[styles.errorText, { color: colors.red }]}>{error}</Text>
              </View>
            </View>
          )}

          {/* ── STEP: Idle — Pick file ──────────────── */}
          {step === 'idle' && (
            <>
              <Pressable
                style={({ pressed }) => [
                  styles.uploadCard,
                  { backgroundColor: colors.surface, borderRadius: radius.lg, opacity: pressed ? 0.85 : 1 },
                ]}
                onPress={handlePickFile}
              >
                <View style={[styles.uploadIcon, { backgroundColor: `${colors.blue}15` }]}>
                  <Ionicons name="cloud-upload" size={32} color={colors.blue} />
                </View>
                <Text style={[styles.uploadTitle, { color: colors.label }]}>Importar fatura</Text>
                <Text style={[styles.uploadSub, { color: colors.secondaryLabel }]}>
                  Selecione um PDF de fatura do BV, Itaú ou Nubank
                </Text>
              </Pressable>

              {/* Supported banks */}
              <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>BANCOS SUPORTADOS</Text>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                {[
                  { bank: 'bv', name: 'Banco BV', status: 'Pronto' },
                  { bank: 'itau', name: 'Itaú', status: 'Pronto' },
                  { bank: 'nubank', name: 'Nubank', status: 'Em breve' },
                ].map((item, i) => (
                  <View key={item.bank}>
                    {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 52 }]} />}
                    <View style={styles.bankRow}>
                      <View style={[styles.bankDot, { backgroundColor: BANK_COLORS[item.bank] }]} />
                      <Text style={[styles.bankName, { color: colors.label }]}>{item.name}</Text>
                      <Text
                        style={[
                          styles.bankStatus,
                          { color: item.status === 'Pronto' ? colors.green : colors.tertiaryLabel },
                        ]}
                      >
                        {item.status}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            </>
          )}

          {/* ── STEP: Uploading ────────────────────── */}
          {step === 'uploading' && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 32 }]}>
              <ActivityIndicator size="large" color={colors.blue} />
              <Text style={[styles.uploadingText, { color: colors.label }]}>Processando...</Text>
              <Text style={[styles.uploadingSub, { color: colors.secondaryLabel }]}>{fileName}</Text>
            </View>
          )}

          {/* ── STEP: Preview ─────────────────────── */}
          {step === 'preview' && preview && (
            <>
              {/* Summary card */}
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                <View style={styles.previewHeader}>
                  <View style={[styles.bankBadge, { backgroundColor: BANK_COLORS[preview.bank] || colors.blue }]}>
                    <Ionicons name="card" size={18} color="#fff" />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.previewBank, { color: colors.label }]}>
                      {bankLabel(preview.bank)}
                    </Text>
                    <Text style={[styles.previewSub, { color: colors.secondaryLabel }]}>
                      Cartão final {preview.card_last_digits} · {preview.reference_month}
                    </Text>
                  </View>
                </View>

                <View style={[styles.sep, { backgroundColor: colors.separator }]} />

                <View style={styles.previewStats}>
                  <View style={styles.stat}>
                    <Text style={[styles.statLabel, { color: colors.tertiaryLabel }]}>Total</Text>
                    <Text style={[styles.statValue, { color: colors.red }]}>
                      {formatCurrency(preview.total_amount)}
                    </Text>
                  </View>
                  <View style={styles.stat}>
                    <Text style={[styles.statLabel, { color: colors.tertiaryLabel }]}>Transações</Text>
                    <Text style={[styles.statValue, { color: colors.label }]}>
                      {preview.transaction_count}
                    </Text>
                  </View>
                  {preview.due_date && (
                    <View style={styles.stat}>
                      <Text style={[styles.statLabel, { color: colors.tertiaryLabel }]}>Vencimento</Text>
                      <Text style={[styles.statValue, { color: colors.label }]}>
                        {formatDate(preview.due_date)}
                      </Text>
                    </View>
                  )}
                </View>
              </View>

              {/* Transactions list */}
              <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>
                TRANSAÇÕES ({preview.transaction_count})
              </Text>

              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                {preview.transactions.slice(0, 50).map((tx, i) => (
                  <View key={`${tx.description}-${i}`}>
                    {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 16 }]} />}
                    <View style={styles.txRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={[styles.txDesc, { color: colors.label }]} numberOfLines={1}>
                          {tx.description}
                          {tx.installment_num && tx.installment_total
                            ? ` (${tx.installment_num}/${tx.installment_total})`
                            : ''}
                        </Text>
                        <Text style={[styles.txDate, { color: colors.secondaryLabel }]}>
                          {tx.date ? formatDate(tx.date) : ''}
                          {tx.card_last_digits ? ` · final ${tx.card_last_digits}` : ''}
                        </Text>
                      </View>
                      <Text style={[styles.txAmount, { color: colors.label }]}>
                        {formatCurrency(tx.amount)}
                      </Text>
                    </View>
                  </View>
                ))}
                {preview.transaction_count > 50 && (
                  <View style={styles.moreRow}>
                    <Text style={[styles.moreText, { color: colors.secondaryLabel }]}>
                      +{preview.transaction_count - 50} transações não exibidas
                    </Text>
                  </View>
                )}
              </View>

              {/* Action buttons */}
              <Pressable
                style={({ pressed }) => [
                  styles.ctaButton,
                  { backgroundColor: colors.green, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 },
                ]}
                onPress={handleConfirm}
              >
                <Ionicons name="checkmark-circle" size={20} color="#fff" />
                <Text style={styles.ctaText}>Confirmar importação</Text>
              </Pressable>

              <Pressable style={styles.cancelButton} onPress={handleReset}>
                <Text style={[styles.cancelText, { color: colors.red }]}>Cancelar</Text>
              </Pressable>
            </>
          )}

          {/* ── STEP: Confirming ──────────────────── */}
          {step === 'confirming' && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 32 }]}>
              <ActivityIndicator size="large" color={colors.green} />
              <Text style={[styles.uploadingText, { color: colors.label }]}>Salvando...</Text>
            </View>
          )}

          {/* ── STEP: Done ────────────────────────── */}
          {step === 'done' && preview && (
            <>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 24 }]}>
                <View style={styles.doneContent}>
                  <View style={[styles.doneIcon, { backgroundColor: `${colors.green}15` }]}>
                    <Ionicons name="checkmark-circle" size={48} color={colors.green} />
                  </View>
                  <Text style={[styles.doneTitle, { color: colors.label }]}>Importação concluída!</Text>
                  <Text style={[styles.doneSub, { color: colors.secondaryLabel }]}>
                    {preview.transaction_count} transações do {bankLabel(preview.bank)} importadas.
                  </Text>
                </View>
              </View>

              <Pressable
                style={({ pressed }) => [
                  styles.ctaButton,
                  { backgroundColor: colors.blue, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 },
                ]}
                onPress={handleReset}
              >
                <Text style={styles.ctaText}>Importar outra fatura</Text>
              </Pressable>
            </>
          )}

          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: { gap: 8 },

  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5, marginBottom: 12 },

  // Cards
  card: { overflow: 'hidden' },

  // Error
  errorRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16, gap: 10 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  errorText: { fontSize: 14, fontWeight: '500', flex: 1 },

  // Upload card
  uploadCard: { alignItems: 'center', padding: 32, gap: 12 },
  uploadIcon: { width: 64, height: 64, borderRadius: 32, justifyContent: 'center', alignItems: 'center' },
  uploadTitle: { fontSize: 17, fontWeight: '600' },
  uploadSub: { fontSize: 13, textAlign: 'center', lineHeight: 18 },

  // Section labels
  sectionLabel: {
    fontSize: 11, fontWeight: '600', textTransform: 'uppercase',
    letterSpacing: 1, marginTop: 20, marginBottom: 8, paddingHorizontal: 4,
  },

  // Bank rows
  bankRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  bankDot: { width: 28, height: 28, borderRadius: 14, marginRight: 12 },
  bankName: { fontSize: 15, fontWeight: '500', flex: 1 },
  bankStatus: { fontSize: 13, fontWeight: '500' },
  sep: { height: 0.5 },

  // Uploading
  uploadingText: { fontSize: 17, fontWeight: '600', textAlign: 'center', marginTop: 16 },
  uploadingSub: { fontSize: 13, textAlign: 'center', marginTop: 4 },

  // Preview header
  previewHeader: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  bankBadge: {
    width: 40, height: 40, borderRadius: 12,
    justifyContent: 'center', alignItems: 'center',
  },
  previewBank: { fontSize: 17, fontWeight: '600' },
  previewSub: { fontSize: 13, marginTop: 2 },

  // Stats
  previewStats: { flexDirection: 'row', padding: 16, gap: 16 },
  stat: { flex: 1, gap: 2 },
  statLabel: { fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 },
  statValue: { fontSize: 17, fontWeight: '700' },

  // Transaction rows
  txRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  txDesc: { fontSize: 15, fontWeight: '500' },
  txDate: { fontSize: 12, marginTop: 2 },
  txAmount: { fontSize: 15, fontWeight: '600', marginLeft: 8 },
  moreRow: { padding: 12, paddingHorizontal: 16 },
  moreText: { fontSize: 13, textAlign: 'center' },

  // CTA
  ctaButton: {
    height: 50, flexDirection: 'row', justifyContent: 'center',
    alignItems: 'center', marginTop: 16, gap: 8,
  },
  ctaText: { color: '#fff', fontSize: 17, fontWeight: '600' },
  cancelButton: { alignItems: 'center', paddingVertical: 12 },
  cancelText: { fontSize: 15 },

  // Done
  doneContent: { alignItems: 'center', gap: 8 },
  doneIcon: { width: 80, height: 80, borderRadius: 40, justifyContent: 'center', alignItems: 'center' },
  doneTitle: { fontSize: 22, fontWeight: '700' },
  doneSub: { fontSize: 15, textAlign: 'center' },
});
