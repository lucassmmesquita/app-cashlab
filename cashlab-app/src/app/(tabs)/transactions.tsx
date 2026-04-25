/**
 * CashLab — Tela de Transações (conectada à API real)
 *
 * Lista transações importadas dos PDFs/screenshots, agrupadas por data.
 * Filtros por banco, membro e busca.
 * Botão "+" para importar print de transações semanais.
 */
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, Pressable, TextInput,
  Modal, TouchableOpacity, ActivityIndicator, Alert, Platform, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as ImagePicker from 'expo-image-picker';

import { useAppTheme } from '@/hooks/useAppTheme';
import { useMonthNavigation } from '@/hooks/useMonthNavigation';
import { MonthNavigator } from '@/components/dashboard/MonthNavigator';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { getCategoryColor, getMemberColor, BANK_COLORS } from '@/utils/colors';
import api from '@/services/api';

interface Transaction {
  id: number;
  date: string;
  description: string;
  amount: string;
  category: string;
  subcategory: string | null;
  who: string;
  bank: string;
  card: string;
  installment: string | null;
  location: string | null;
}

type FilterType = 'all' | 'BV' | 'ITAU';
type MemberFilter = 'all' | 'LUCAS' | 'JURA' | 'JOICE';

type ImportStep = 'idle' | 'uploading' | 'preview' | 'confirming';
interface ImportPreview {
  file_id: string;
  transaction_count: number;
  total_amount: number;
  transactions: { date: string; description: string; amount: number; card_last_digits?: string }[];
}

export default function TransactionsScreen() {
  const { colors, isDark, radius, spacing } = useAppTheme();
  const { selectedMonth, goToPreviousMonth, goToNextMonth } = useMonthNavigation();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [bankFilter, setBankFilter] = useState<FilterType>('all');
  const [memberFilter, setMemberFilter] = useState<MemberFilter>('all');
  const [search, setSearch] = useState('');

  // Screenshot import state
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importStep, setImportStep] = useState<ImportStep>('idle');
  const [importPreview, setImportPreview] = useState<ImportPreview | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { month: selectedMonth };
      if (bankFilter !== 'all') params.bank = bankFilter.toLowerCase();
      if (memberFilter !== 'all') params.member = memberFilter;
      if (search.trim()) params.search = search.trim();

      const res = await api.get('/transactions', { params });
      setTransactions(res.data?.data || []);
    } catch {
      // keep empty
    } finally {
      setLoading(false);
    }
  }, [selectedMonth, bankFilter, memberFilter, search]);

  useEffect(() => { fetchTransactions(); }, [fetchTransactions]);

  // Group by date
  const grouped = useMemo(() => {
    const map: Record<string, Transaction[]> = {};
    for (const tx of transactions) {
      if (!map[tx.date]) map[tx.date] = [];
      map[tx.date].push(tx);
    }
    return Object.entries(map).sort(([a], [b]) => b.localeCompare(a));
  }, [transactions]);

  const totalAmount = transactions.reduce((sum, t) => sum + parseFloat(t.amount), 0);

  // Screenshot import handlers
  const handlePickImage = async () => {
    try {
      // Request permission
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permissão necessária', 'Precisamos de acesso à sua fototeca para importar prints.');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.9,
      });
      if (result.canceled || !result.assets?.[0]) return;

      const asset = result.assets[0];
      setImportStep('uploading');
      setImportError(null);

      const formData = new FormData();
      const fileName = asset.fileName || `screenshot_${Date.now()}.jpg`;
      if (Platform.OS === 'web') {
        const response = await fetch(asset.uri);
        const blob = await response.blob();
        formData.append('file', blob, fileName);
      } else {
        formData.append('file', {
          uri: asset.uri,
          name: fileName,
          type: asset.mimeType || 'image/jpeg',
        } as any);
      }

      const res = await api.post('/transactions/import-screenshot', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      });

      setImportPreview(res.data.data);
      setImportStep('preview');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Erro ao processar imagem';
      setImportError(msg);
      setImportStep('idle');
    }
  };

  const handleConfirmImport = async () => {
    if (!importPreview) return;
    setImportStep('confirming');
    try {
      await api.post(`/transactions/import-screenshot/${importPreview.file_id}/confirm`);
      setImportModalVisible(false);
      setImportStep('idle');
      setImportPreview(null);
      Alert.alert('Sucesso', `${importPreview.transaction_count} transações importadas!`);
      fetchTransactions();
    } catch (err: any) {
      setImportError(err.response?.data?.detail || 'Erro ao confirmar');
      setImportStep('preview');
    }
  };

  const resetImport = () => {
    setImportStep('idle');
    setImportPreview(null);
    setImportError(null);
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <ScrollView
          contentContainerStyle={[styles.scrollContent, { padding: spacing.lg }]}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={async () => { setRefreshing(true); await fetchTransactions(); setRefreshing(false); }}
              tintColor={colors.blue}
            />
          }
        >
          {/* Header with + button */}
          <View style={styles.headerRow}>
            <Text style={[styles.largeTitle, { color: colors.label }]}>Transações</Text>
            <TouchableOpacity
              style={[styles.addButton, { backgroundColor: colors.blue }]}
              onPress={() => { resetImport(); setImportModalVisible(true); }}
            >
              <Ionicons name="add" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {/* Month Navigator */}
          <MonthNavigator month={selectedMonth} onPrevious={goToPreviousMonth} onNext={goToNextMonth} />

          {/* Search */}
          <View style={[styles.searchBox, { backgroundColor: colors.segmentBg, borderRadius: 10 }]}>
            <Ionicons name="search" size={18} color={colors.tertiaryLabel} />
            <TextInput
              style={[styles.searchInput, { color: colors.label }]}
              placeholder="Buscar transação..."
              placeholderTextColor={colors.tertiaryLabel}
              value={search}
              onChangeText={setSearch}
            />
            {search.length > 0 && (
              <Pressable onPress={() => setSearch('')}>
                <Ionicons name="close-circle" size={18} color={colors.tertiaryLabel} />
              </Pressable>
            )}
          </View>

          {/* Filter chips */}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
            {(['all', 'BV', 'ITAU'] as FilterType[]).map(f => (
              <Pressable key={f} onPress={() => setBankFilter(f)}
                style={[styles.chip, {
                  backgroundColor: bankFilter === f ? colors.blue : colors.segmentBg,
                  borderRadius: 20,
                }]}>
                {f !== 'all' && <View style={[styles.chipDot, { backgroundColor: BANK_COLORS[f.toLowerCase()] || colors.gray }]} />}
                <Text style={[styles.chipText, { color: bankFilter === f ? '#fff' : colors.label }]}>
                  {f === 'all' ? 'Todos' : f === 'ITAU' ? 'Itaú' : f}
                </Text>
              </Pressable>
            ))}
            <View style={styles.chipSpacer} />
            {(['all', 'LUCAS', 'JOICE'] as MemberFilter[]).map(f => (
              <Pressable key={f} onPress={() => setMemberFilter(f)}
                style={[styles.chip, {
                  backgroundColor: memberFilter === f ? colors.blue : colors.segmentBg,
                  borderRadius: 20,
                }]}>
                <Text style={[styles.chipText, { color: memberFilter === f ? '#fff' : colors.label }]}>
                  {f === 'all' ? 'Todos' : f}
                </Text>
              </Pressable>
            ))}
          </ScrollView>

          {/* Summary bar */}
          <View style={[styles.summaryBar, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View>
              <Text style={[styles.summaryLabel, { color: colors.tertiaryLabel }]}>TRANSAÇÕES</Text>
              <Text style={[styles.summaryValue, { color: colors.label }]}>{transactions.length}</Text>
            </View>
            <View style={[styles.summaryDivider, { backgroundColor: colors.separator }]} />
            <View style={{ flex: 1, alignItems: 'flex-end' }}>
              <Text style={[styles.summaryLabel, { color: colors.tertiaryLabel }]}>TOTAL</Text>
              <Text style={[styles.summaryValue, { color: colors.red }]}>
                {formatCurrency(totalAmount.toFixed(2))}
              </Text>
            </View>
          </View>

          {loading && <ActivityIndicator style={{ marginVertical: 20 }} color={colors.blue} />}

          {/* Transaction list grouped by date */}
          {grouped.map(([date, txs]) => (
            <View key={date}>
              <Text style={[styles.dateHeader, { color: colors.secondaryLabel }]}>
                {formatDate(date)}
              </Text>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                {txs.map((tx, i) => {
                  const catColor = getCategoryColor(tx.category, isDark);
                  const memberColor = getMemberColor(tx.who, isDark);
                  return (
                    <View key={tx.id}>
                      {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 52 }]} />}
                      <View style={styles.txRow}>
                        <View style={[styles.catDot, { backgroundColor: catColor }]} />
                        <View style={styles.txBody}>
                          <Text style={[styles.txDesc, { color: colors.label }]} numberOfLines={1}>{tx.description}</Text>
                          <View style={styles.txMeta}>
                            <Text style={[styles.txCategory, { color: colors.secondaryLabel }]}>{tx.category}</Text>
                            {tx.installment && (
                              <View style={[styles.installBadge, { backgroundColor: `${colors.blue}15` }]}>
                                <Text style={[styles.installText, { color: colors.blue }]}>{tx.installment}</Text>
                              </View>
                            )}
                          </View>
                        </View>
                        <View style={styles.txRight}>
                          <Text style={[styles.txAmount, { color: colors.label }]}>
                            -{formatCurrency(Math.abs(parseFloat(tx.amount)).toFixed(2))}
                          </Text>
                          <View style={styles.txTags}>
                            <View style={[styles.memberTag, { backgroundColor: `${memberColor}20` }]}>
                              <Text style={[styles.memberTagText, { color: memberColor }]}>{tx.who}</Text>
                            </View>
                          </View>
                        </View>
                      </View>
                    </View>
                  );
                })}
              </View>
            </View>
          ))}

          {!loading && transactions.length === 0 && (
            <View style={styles.emptyState}>
              <Ionicons name="receipt-outline" size={48} color={colors.tertiaryLabel} />
              <Text style={[styles.emptyText, { color: colors.secondaryLabel }]}>
                Nenhuma transação encontrada
              </Text>
              <Text style={[styles.emptySubtext, { color: colors.tertiaryLabel }]}>
                Importe faturas em Cartões ou use o botão + para importar prints
              </Text>
            </View>
          )}

          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>

      {/* Screenshot Import Modal */}
      <Modal visible={importModalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: colors.label }]}>Importar Transações</Text>
              <TouchableOpacity onPress={() => setImportModalVisible(false)}>
                <Ionicons name="close-circle" size={28} color={colors.tertiaryLabel} />
              </TouchableOpacity>
            </View>

            {importError && (
              <View style={[styles.errorBox, { backgroundColor: `${colors.red}10` }]}>
                <Text style={[styles.errorText, { color: colors.red }]}>{importError}</Text>
              </View>
            )}

            {importStep === 'idle' && (
              <TouchableOpacity
                style={[styles.uploadArea, { borderColor: colors.separator, backgroundColor: `${colors.blue}05` }]}
                onPress={handlePickImage}
              >
                <Ionicons name="image-outline" size={48} color={colors.blue} />
                <Text style={[styles.uploadTitle, { color: colors.label }]}>Selecionar print</Text>
                <Text style={[styles.uploadSub, { color: colors.secondaryLabel }]}>
                  Escolha um screenshot das transações semanais do cartão
                </Text>
              </TouchableOpacity>
            )}

            {importStep === 'uploading' && (
              <View style={styles.loadingBox}>
                <ActivityIndicator size="large" color={colors.blue} />
                <Text style={[styles.loadingText, { color: colors.label }]}>Processando com IA...</Text>
                <Text style={[styles.loadingSub, { color: colors.secondaryLabel }]}>Isso pode levar alguns segundos</Text>
              </View>
            )}

            {importStep === 'preview' && importPreview && (
              <ScrollView style={{ maxHeight: 400 }}>
                <Text style={[styles.previewSummary, { color: colors.label }]}>
                  {importPreview.transaction_count} transações • Total: {formatCurrency(importPreview.total_amount)}
                </Text>
                {importPreview.transactions.map((tx, i) => (
                  <View key={i} style={[styles.previewRow, { borderBottomColor: colors.separator }]}>
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.previewDesc, { color: colors.label }]}>{tx.description}</Text>
                      <Text style={[styles.previewDate, { color: colors.secondaryLabel }]}>{tx.date}</Text>
                    </View>
                    <Text style={[styles.previewAmount, { color: colors.red }]}>
                      -{formatCurrency(tx.amount)}
                    </Text>
                  </View>
                ))}
                <TouchableOpacity
                  style={[styles.confirmBtn, { backgroundColor: colors.green }]}
                  onPress={handleConfirmImport}
                >
                  <Text style={styles.confirmBtnText}>Confirmar importação</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.cancelBtn} onPress={resetImport}>
                  <Text style={[styles.cancelBtnText, { color: colors.red }]}>Cancelar</Text>
                </TouchableOpacity>
              </ScrollView>
            )}

            {importStep === 'confirming' && (
              <View style={styles.loadingBox}>
                <ActivityIndicator size="large" color={colors.green} />
                <Text style={[styles.loadingText, { color: colors.label }]}>Salvando...</Text>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: { gap: 8 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5 },
  addButton: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
  searchBox: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 10, gap: 8 },
  searchInput: { flex: 1, fontSize: 16, padding: 0 },
  chipRow: { flexDirection: 'row', marginVertical: 4, flexGrow: 0 },
  chip: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 7, marginRight: 8, gap: 6 },
  chipDot: { width: 8, height: 8, borderRadius: 4 },
  chipText: { fontSize: 13, fontWeight: '600' },
  chipSpacer: { width: 4 },
  summaryBar: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 16 },
  summaryLabel: { fontSize: 11, fontWeight: '600', letterSpacing: 0.5 },
  summaryValue: { fontSize: 20, fontWeight: '700', marginTop: 2 },
  summaryDivider: { width: 1, height: 36 },
  dateHeader: { fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 16, marginBottom: 6, paddingHorizontal: 4 },
  card: { overflow: 'hidden' },
  txRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16, gap: 12 },
  catDot: { width: 10, height: 10, borderRadius: 5, flexShrink: 0, marginTop: 2 },
  txBody: { flex: 1, gap: 3 },
  txDesc: { fontSize: 15, fontWeight: '500' },
  txMeta: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  txCategory: { fontSize: 12 },
  installBadge: { paddingHorizontal: 6, paddingVertical: 1, borderRadius: 4 },
  installText: { fontSize: 11, fontWeight: '600' },
  txRight: { alignItems: 'flex-end', gap: 4, flexShrink: 0 },
  txAmount: { fontSize: 15, fontWeight: '600' },
  txTags: { flexDirection: 'row', gap: 4 },
  memberTag: { paddingHorizontal: 6, paddingVertical: 1, borderRadius: 4 },
  memberTagText: { fontSize: 10, fontWeight: '700' },
  sep: { height: 0.5 },
  emptyState: { alignItems: 'center', paddingVertical: 60, gap: 12 },
  emptyText: { fontSize: 15 },
  emptySubtext: { fontSize: 13, textAlign: 'center', paddingHorizontal: 40 },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { padding: 24, paddingBottom: 40, maxHeight: '80%' },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  modalTitle: { fontSize: 20, fontWeight: '700' },
  errorBox: { padding: 12, borderRadius: 8, marginBottom: 12 },
  errorText: { fontSize: 14 },
  uploadArea: { borderWidth: 2, borderStyle: 'dashed', borderRadius: 16, padding: 40, alignItems: 'center', gap: 8 },
  uploadTitle: { fontSize: 17, fontWeight: '600', marginTop: 8 },
  uploadSub: { fontSize: 13, textAlign: 'center' },
  loadingBox: { alignItems: 'center', padding: 40, gap: 12 },
  loadingText: { fontSize: 17, fontWeight: '600' },
  loadingSub: { fontSize: 13 },
  previewSummary: { fontSize: 15, fontWeight: '600', marginBottom: 12 },
  previewRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 0.5 },
  previewDesc: { fontSize: 14, fontWeight: '500' },
  previewDate: { fontSize: 12, marginTop: 2 },
  previewAmount: { fontSize: 14, fontWeight: '600' },
  confirmBtn: { height: 48, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginTop: 20 },
  confirmBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  cancelBtn: { alignItems: 'center', paddingVertical: 12 },
  cancelBtnText: { fontSize: 15 },
});
