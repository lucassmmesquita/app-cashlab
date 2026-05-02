/**
 * CashLab — Tela Cartões (Gestão de Faturas)
 *
 * v2.1: Wizard onboarding no primeiro acesso + fluxo assistido de importação.
 */
import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, StyleSheet, Pressable, ScrollView, ActivityIndicator,
  Alert, Modal, RefreshControl, TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import * as DocumentPicker from 'expo-document-picker';
import Ionicons from '@expo/vector-icons/Ionicons';

import { useAppTheme } from '@/hooks/useAppTheme';
import { invoiceService } from '@/services/invoiceService';
import { bankService } from '@/services/bankService';
import type { UploadPreview, InvoiceListItem, InvoiceDetail } from '@/services/invoiceService';
import type { BankItem } from '@/services/bankService';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { SwipeableRow } from '@/components/common/SwipeableRow';

type Step = 'idle' | 'uploading' | 'preview' | 'confirming' | 'done';

const BANK_COLOR_OPTIONS = ['#F5A623','#FF6B00','#8A05BE','#007AFF','#34C759','#E63946','#2D3436','#00B894'];

const PARSER_STATUS_MAP: Record<string, { label: string; color: string; emoji: string }> = {
  pending: { label: 'Pendente', color: '#FF9500', emoji: '⏳' },
  processing: { label: 'Processando...', color: '#007AFF', emoji: '⚙️' },
  ready: { label: 'Pronto', color: '#34C759', emoji: '✅' },
  error: { label: 'Erro', color: '#FF3B30', emoji: '❌' },
};

export default function ImportScreen() {
  const { colors, radius, spacing } = useAppTheme();

  // Import flow
  const [step, setStep] = useState<Step>('idle');
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState('');
  const [fileUri, setFileUri] = useState('');

  // Bank/month selector (shown after picking PDF)
  const [selectModal, setSelectModal] = useState(false);
  const [selectedBank, setSelectedBank] = useState('auto');
  const now = new Date();
  const [selectedYear, setSelectedYear] = useState(String(now.getFullYear()));
  const [selectedMonth, setSelectedMonth] = useState(String(now.getMonth() + 1).padStart(2, '0'));

  // Data lists
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [banks, setBanks] = useState<BankItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Detail modal (invoice)
  const [detailModal, setDetailModal] = useState(false);
  const [detailData, setDetailData] = useState<InvoiceDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Add bank modal
  const [bankModal, setBankModal] = useState(false);
  const [newBankName, setNewBankName] = useState('');
  const [newBankColor, setNewBankColor] = useState('#007AFF');
  const [newClosingDay, setNewClosingDay] = useState('');
  const [newDueDay, setNewDueDay] = useState('');
  const [bankSaving, setBankSaving] = useState(false);

  // Detail/Edit bank modal
  const [bankDetailBank, setBankDetailBank] = useState<BankItem | null>(null);
  const [bankDetailModal, setBankDetailModal] = useState(false);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState('');
  const [editClosing, setEditClosing] = useState('');
  const [editDue, setEditDue] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [retraining, setRetraining] = useState(false);


  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [inv, bnk] = await Promise.all([invoiceService.list(), bankService.list()]);
      setInvoices(inv);
      setBanks(bnk);
    } catch { /* keep current */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  const MONTHS = ['01','02','03','04','05','06','07','08','09','10','11','12'];
  const MONTH_NAMES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

  // ── Import Flow ──
  const handlePickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: 'application/pdf', copyToCacheDirectory: true });
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      setFileName(asset.name);
      setFileUri(asset.uri);
      setError(null);
      // Show bank/month selector
      setSelectModal(true);
    } catch (err: any) {
      setError(err.message || 'Erro ao selecionar PDF');
    }
  };

  const handleUploadWithParams = async () => {
    setSelectModal(false);
    setStep('uploading');
    setError(null);
    try {
      const refMonth = `${selectedYear}-${selectedMonth}`;
      const data = await invoiceService.upload(fileUri, fileName, selectedBank, refMonth);
      setPreview(data);
      setStep('preview');
    } catch (err: any) {
      let errorMsg = 'Erro ao processar PDF';
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        errorMsg = 'Tempo esgotado. O PDF pode ser muito grande. Tente novamente.';
      } else if (status === 400) {
        errorMsg = detail || 'Arquivo inválido. Verifique se é um PDF válido.';
      } else if (status === 422) {
        errorMsg = detail || 'Não foi possível identificar o banco. Selecione manualmente.';
      } else if (status === 409) {
        errorMsg = detail || 'Esta fatura já foi importada anteriormente.';
      } else if (status === 500) {
        errorMsg = detail || 'Erro interno ao processar o PDF. Tente novamente.';
      } else if (!err.response) {
        errorMsg = 'Sem conexão com o servidor. Verifique sua rede.';
      } else {
        errorMsg = detail || err.message || 'Erro desconhecido';
      }

      setError(errorMsg);
      setStep('idle');
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;
    setStep('confirming');
    try {
      await invoiceService.confirmImport(preview.file_id);
      setStep('done');
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao confirmar');
      setStep('preview');
    }
  };

  const handleReset = () => { setStep('idle'); setPreview(null); setError(null); setFileName(''); setFileUri(''); };

  // ── Invoice Detail ──
  const openDetail = async (id: number) => {
    setDetailLoading(true);
    setDetailModal(true);
    try {
      const data = await invoiceService.getDetail(id);
      setDetailData(data);
    } catch { setDetailData(null); }
    finally { setDetailLoading(false); }
  };

  const handleDeleteInvoice = (id: number) => {
    Alert.alert('Excluir Fatura', 'Tem certeza? As transações associadas também serão removidas.', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Excluir', style: 'destructive', onPress: async () => {
        try { await invoiceService.remove(id); fetchData(); } catch { Alert.alert('Erro', 'Não foi possível excluir'); }
      }},
    ]);
  };

  // ── Bank CRUD ──
  const handleCreateBank = async () => {
    if (!newBankName.trim()) return;
    setBankSaving(true);
    try {
      const cd = newClosingDay ? parseInt(newClosingDay) : undefined;
      const dd = newDueDay ? parseInt(newDueDay) : undefined;
      await bankService.create(newBankName.trim(), newBankColor, cd, dd);
      setBankModal(false);
      setNewBankName(''); setNewClosingDay(''); setNewDueDay('');
      fetchData();
    } catch (err: any) {
      Alert.alert('Erro', err.response?.data?.detail || 'Erro ao criar cartão');
    } finally { setBankSaving(false); }
  };

  const openBankDetail = (bank: BankItem) => {
    setBankDetailBank(bank);
    setEditName(bank.name);
    setEditColor(bank.color);
    setEditClosing(bank.closing_day ? String(bank.closing_day) : '');
    setEditDue(bank.due_day ? String(bank.due_day) : '');
    setBankDetailModal(true);
  };

  const handleUpdateBank = async () => {
    if (!bankDetailBank) return;
    setEditSaving(true);
    try {
      await bankService.update(bankDetailBank.id, {
        name: editName.trim() || undefined,
        color: editColor || undefined,
        closing_day: editClosing ? parseInt(editClosing) : undefined,
        due_day: editDue ? parseInt(editDue) : undefined,
      });
      setBankDetailModal(false);
      fetchData();
    } catch (err: any) {
      Alert.alert('Erro', err.response?.data?.detail || 'Erro ao atualizar');
    } finally { setEditSaving(false); }
  };

  const handleRetrainParser = async () => {
    if (!bankDetailBank) return;
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: 'application/pdf', copyToCacheDirectory: true });
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      setRetraining(true);
      const updated = await bankService.retrain(bankDetailBank.id, asset.uri, asset.name);
      Alert.alert('Sucesso', updated.message || 'Parser treinado com sucesso');
      setBankDetailModal(false);
      fetchData();
    } catch (err: any) {
      Alert.alert('Erro', err.response?.data?.detail || 'Erro ao treinar parser');
    } finally { setRetraining(false); }
  };

  const handleDeleteBank = (id: number, name: string) => {
    Alert.alert('Excluir Cartão', `Remover "${name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Excluir', style: 'destructive', onPress: async () => {
        try { await bankService.remove(id); fetchData(); } catch (err: any) {
          Alert.alert('Erro', err.response?.data?.detail || 'Não foi possível excluir');
        }
      }},
    ]);
  };

  const bankLabel = (b: string) => ({ bv: 'Banco BV', itau: 'Itaú', nubank: 'Nubank' }[b] || b);
  const fmtSize = (b: number | null) => b ? (b > 1024*1024 ? `${(b/1024/1024).toFixed(1)} MB` : `${Math.round(b/1024)} KB`) : '';

  return (
    <GestureHandlerRootView style={[styles.container, { backgroundColor: colors.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <ScrollView contentContainerStyle={[styles.scrollContent, { padding: spacing.lg }]}
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />}
        >
          <Text style={[styles.largeTitle, { color: colors.label }]}>Cartões</Text>

          {error && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
              <View style={styles.errorRow}>
                <View style={[styles.dot, { backgroundColor: colors.red }]} />
                <Text style={[styles.errorText, { color: colors.red }]}>{error}</Text>
              </View>
            </View>
          )}

          {/* ── WIZARD ONBOARDING (nenhum cartão/fatura cadastrado) ── */}
          {step === 'idle' && !loading && invoices.length === 0 && (
            <View style={{ alignItems: 'center', paddingVertical: 40, gap: 16 }}>
              <Ionicons name="card-outline" size={64} color={colors.tertiaryLabel} />
              <Text style={[styles.onboardTitle, { color: colors.label }]}>Bem-vindo ao CashLab!</Text>
              <Text style={[styles.onboardSub, { color: colors.secondaryLabel }]}>
                Importe sua primeira fatura de cartão{'\n'}para começar a controlar seus gastos.
              </Text>
              <Pressable style={({ pressed }) => [styles.importBtn, { backgroundColor: colors.blue, borderRadius: radius.lg, opacity: pressed ? 0.85 : 1, width: '100%' }]}
                onPress={handlePickFile}>
                <Ionicons name="cloud-upload" size={22} color="#fff" />
                <Text style={styles.importBtnText}>Importar Fatura (PDF)</Text>
              </Pressable>
            </View>
          )}

          {/* ── IMPORT FLOW (quando já tem cartões ou está no fluxo) ── */}
          {step === 'idle' && invoices.length > 0 && (
            <Pressable style={({ pressed }) => [styles.importBtn, { backgroundColor: colors.blue, borderRadius: radius.lg, opacity: pressed ? 0.85 : 1 }]}
              onPress={handlePickFile}>
              <Ionicons name="cloud-upload" size={22} color="#fff" />
              <Text style={styles.importBtnText}>Importar Fatura (PDF)</Text>
            </Pressable>
          )}

          {step === 'uploading' && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 32 }]}>
              <ActivityIndicator size="large" color={colors.blue} />
              <Text style={[styles.centerText, { color: colors.label, marginTop: 16 }]}>Processando...</Text>
              <Text style={[styles.centerTextSm, { color: colors.secondaryLabel }]}>{fileName}</Text>
            </View>
          )}

          {step === 'preview' && preview && (
            <>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16 }]}>
                <Text style={[styles.previewBank, { color: colors.label }]}>{bankLabel(preview.bank)}</Text>
                <Text style={[styles.previewSub, { color: colors.secondaryLabel }]}>
                  Cartão final {preview.card_last_digits} · {preview.reference_month}
                </Text>
                <View style={styles.previewStats}>
                  <View style={styles.stat}>
                    <Text style={[styles.statLabel, { color: colors.tertiaryLabel }]}>TOTAL</Text>
                    <Text style={[styles.statValue, { color: colors.red }]}>{formatCurrency(preview.total_amount)}</Text>
                  </View>
                  <View style={styles.stat}>
                    <Text style={[styles.statLabel, { color: colors.tertiaryLabel }]}>TRANSAÇÕES</Text>
                    <Text style={[styles.statValue, { color: colors.label }]}>{preview.transaction_count}</Text>
                  </View>
                </View>
              </View>
              {/* Confirmação — Etapa 3 do wizard: "Deseja importar esta fatura?" */}
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, alignItems: 'center', marginTop: 8 }]}>
                <Text style={[{ fontSize: 16, fontWeight: '600', color: colors.label, textAlign: 'center' }]}>
                  Deseja importar esta fatura?
                </Text>
                <Text style={[{ fontSize: 13, color: colors.secondaryLabel, textAlign: 'center', marginTop: 4 }]}>
                  O cartão e as transações serão criados automaticamente.
                </Text>
              </View>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, maxHeight: 300 }]}>
                <ScrollView nestedScrollEnabled>
                  {preview.transactions.slice(0, 50).map((tx, i) => (
                    <View key={`${tx.description}-${i}`} style={[styles.txRow, i > 0 && { borderTopWidth: 0.5, borderTopColor: colors.separator }]}>
                      <View style={{ flex: 1 }}>
                        <Text style={[styles.txDesc, { color: colors.label }]} numberOfLines={1}>{tx.description}</Text>
                        <Text style={[styles.txDate, { color: colors.secondaryLabel }]}>{tx.date ? formatDate(tx.date) : ''}</Text>
                      </View>
                      <Text style={[styles.txAmt, { color: colors.label }]}>{formatCurrency(tx.amount)}</Text>
                    </View>
                  ))}
                </ScrollView>
              </View>
              <Pressable style={({ pressed }) => [styles.importBtn, { backgroundColor: colors.green, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 }]}
                onPress={handleConfirm}>
                <Ionicons name="checkmark-circle" size={20} color="#fff" />
                <Text style={styles.importBtnText}>Confirmar importação</Text>
              </Pressable>
              <Pressable style={styles.cancelBtn} onPress={handleReset}>
                <Text style={[{ color: colors.red, fontSize: 15 }]}>Cancelar</Text>
              </Pressable>
            </>
          )}

          {step === 'confirming' && (
            <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 32 }]}>
              <ActivityIndicator size="large" color={colors.green} />
              <Text style={[styles.centerText, { color: colors.label, marginTop: 16 }]}>Salvando...</Text>
            </View>
          )}

          {step === 'done' && (
            <>
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 24, alignItems: 'center' }]}>
                <Ionicons name="checkmark-circle" size={48} color={colors.green} />
                <Text style={[styles.doneTitle, { color: colors.label }]}>Importação concluída!</Text>
                <Text style={[styles.centerTextSm, { color: colors.secondaryLabel, marginTop: 4 }]}>
                  Cartão, fatura e transações foram criados automaticamente.
                </Text>
              </View>
              <Pressable style={({ pressed }) => [styles.importBtn, { backgroundColor: colors.blue, borderRadius: radius.xl, opacity: pressed ? 0.85 : 1 }]}
                onPress={handleReset}>
                <Text style={styles.importBtnText}>Importar outra fatura</Text>
              </Pressable>
            </>
          )}

          {/* ── FATURAS IMPORTADAS (só aparece quando tem faturas) ── */}
          {step === 'idle' && invoices.length > 0 && (
            <>
              <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>FATURAS IMPORTADAS</Text>
              {loading && <ActivityIndicator style={{ marginVertical: 12 }} color={colors.blue} />}
              {invoices.map((inv) => (
                <SwipeableRow key={inv.id} onDelete={() => handleDeleteInvoice(inv.id)}>
                  <Pressable
                    style={({ pressed }) => [styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, opacity: pressed ? 0.9 : 1, marginBottom: 8 }]}
                    onPress={() => openDetail(inv.id)}>
                    <View style={styles.invRow}>
                      <View style={[styles.bankDot, { backgroundColor: colors.blue }]} />
                      <View style={{ flex: 1 }}>
                        <Text style={[styles.invTitle, { color: colors.label }]}>
                          {inv.bank_name || 'Cartão'} · {inv.card_last_digits || '****'}
                        </Text>
                        <Text style={[styles.invSub, { color: colors.secondaryLabel }]}>
                          {inv.reference_month} · {inv.transaction_count} transações{inv.file_size ? ` · ${fmtSize(inv.file_size)}` : ''}
                        </Text>
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        <Text style={[styles.invAmount, { color: colors.red }]}>{formatCurrency(inv.total_amount)}</Text>
                        <Text style={[styles.invDate, { color: colors.tertiaryLabel }]}>
                          {inv.created_at ? new Date(inv.created_at).toLocaleDateString('pt-BR') : ''}
                        </Text>
                      </View>
                      <Ionicons name="chevron-forward" size={16} color={colors.tertiaryLabel} style={{ marginLeft: 4 }} />
                    </View>
                  </Pressable>
                </SwipeableRow>
              ))}
            </>
          )}

          {/* ── CARTÕES CADASTRADOS ── */}
          {step === 'idle' && (
            <>
              <View style={[styles.sectionRow, { marginTop: 24 }]}>
                <Text style={[styles.sectionLabel, { color: colors.secondaryLabel, marginTop: 0 }]}>CARTÕES</Text>
                <Pressable onPress={() => setBankModal(true)} hitSlop={12}>
                  <Ionicons name="add-circle" size={22} color={colors.blue} />
                </Pressable>
              </View>
              {loading && <ActivityIndicator style={{ marginVertical: 8 }} color={colors.blue} />}
              <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                {banks.length === 0 && !loading && (
                  <View style={{ padding: 16, alignItems: 'center' }}>
                    <Text style={[styles.invSub, { color: colors.tertiaryLabel }]}>Nenhum cartão cadastrado</Text>
                  </View>
                )}
                {banks.map((b, i) => {
                  const ps = PARSER_STATUS_MAP[b.parser_status] || PARSER_STATUS_MAP.pending;
                  return (
                    <View key={b.id}>
                      {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 52 }]} />}
                      <Pressable style={styles.bankRow} onPress={() => openBankDetail(b)}>
                        <View style={[styles.bankDot, { backgroundColor: b.color }]} />
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.bankName, { color: colors.label }]}>{b.name}</Text>
                          <Text style={[styles.invSub, { color: colors.tertiaryLabel }]}>
                            {b.closing_day ? `Fech. dia ${b.closing_day}` : ''}{b.closing_day && b.due_day ? ' · ' : ''}{b.due_day ? `Venc. dia ${b.due_day}` : ''}
                            {b.invoice_count > 0 ? ` · ${b.invoice_count} fatura(s)` : ''}
                          </Text>
                        </View>
                        <View style={[styles.statusBadge, { backgroundColor: `${ps.color}20` }]}>
                          <Text style={[styles.statusText, { color: ps.color }]}>{ps.emoji} {ps.label}</Text>
                        </View>
                        <Ionicons name="chevron-forward" size={16} color={colors.tertiaryLabel} style={{ marginLeft: 6 }} />
                      </Pressable>
                    </View>
                  );
                })}
              </View>
            </>
          )}

          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>

      {/* ── ADD BANK MODAL ── */}
      <Modal visible={bankModal} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.formModal, { backgroundColor: colors.surface, borderRadius: radius.xl }]}>
            <Text style={[styles.modalTitle, { color: colors.label, marginBottom: 16 }]}>Novo Cartão</Text>
            <TextInput style={[styles.input, { backgroundColor: colors.bg, color: colors.label, borderRadius: radius.md }]}
              placeholder="Nome do cartão (ex: Itaú, BV)" placeholderTextColor={colors.tertiaryLabel}
              value={newBankName} onChangeText={setNewBankName} />
            <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Dia Fechamento</Text>
                <TextInput style={[styles.input, { backgroundColor: colors.bg, color: colors.label, borderRadius: radius.md }]}
                  placeholder="Ex: 03" placeholderTextColor={colors.tertiaryLabel} keyboardType="number-pad"
                  value={newClosingDay} onChangeText={setNewClosingDay} maxLength={2} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Dia Vencimento</Text>
                <TextInput style={[styles.input, { backgroundColor: colors.bg, color: colors.label, borderRadius: radius.md }]}
                  placeholder="Ex: 09" placeholderTextColor={colors.tertiaryLabel} keyboardType="number-pad"
                  value={newDueDay} onChangeText={setNewDueDay} maxLength={2} />
              </View>
            </View>
            <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Cor</Text>
            <View style={styles.colorRow}>
              {BANK_COLOR_OPTIONS.map(c => (
                <Pressable key={c} onPress={() => setNewBankColor(c)}
                  style={[styles.colorOption, { backgroundColor: c, borderWidth: newBankColor === c ? 3 : 0, borderColor: '#fff' }]} />
              ))}
            </View>
            <Text style={[styles.footnote, { color: colors.tertiaryLabel, marginBottom: 16 }]}>
              Após criar, envie um PDF de fatura para treinar o parser.
            </Text>
            <View style={styles.formActions}>
              <Pressable onPress={() => setBankModal(false)} style={styles.cancelBtn}>
                <Text style={[{ color: colors.red, fontSize: 15 }]}>Cancelar</Text>
              </Pressable>
              <Pressable style={[styles.saveBtn, { backgroundColor: colors.blue, borderRadius: radius.md }]}
                onPress={handleCreateBank} disabled={bankSaving}>
                {bankSaving ? <ActivityIndicator size="small" color="#fff" /> :
                  <Text style={{ color: '#fff', fontSize: 15, fontWeight: '600' }}>Criar</Text>}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      {/* ── BANK DETAIL/EDIT MODAL ── */}
      <Modal visible={bankDetailModal} animationType="slide" presentationStyle="pageSheet">
        <View style={[styles.modalContainer, { backgroundColor: colors.bg }]}>
          <SafeAreaView style={{ flex: 1 }} edges={['top']}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.separator }]}>
              <Text style={[styles.modalTitle, { color: colors.label }]}>Detalhes do Cartão</Text>
              <Pressable onPress={() => setBankDetailModal(false)}>
                <Ionicons name="close-circle" size={28} color={colors.secondaryLabel} />
              </Pressable>
            </View>
            {bankDetailBank && (
              <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
                {/* Status do parser */}
                <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, marginBottom: 16, alignItems: 'center' }]}>
                  {(() => { const ps = PARSER_STATUS_MAP[bankDetailBank.parser_status] || PARSER_STATUS_MAP.pending; return (
                    <>
                      <Text style={{ fontSize: 32 }}>{ps.emoji}</Text>
                      <Text style={[styles.bankName, { color: ps.color, marginTop: 4 }]}>{ps.label}</Text>
                      {bankDetailBank.parser_trained_at && (
                        <Text style={[styles.invSub, { color: colors.tertiaryLabel, marginTop: 4 }]}>
                          Último treinamento: {new Date(bankDetailBank.parser_trained_at).toLocaleDateString('pt-BR')}
                        </Text>
                      )}
                      <Text style={[styles.invSub, { color: colors.tertiaryLabel, marginTop: 2 }]}>
                        {bankDetailBank.invoice_count} fatura(s) importada(s)
                      </Text>
                    </>
                  ); })()}
                </View>

                {/* Campos editáveis */}
                <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Nome</Text>
                <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.label, borderRadius: radius.md }]}
                  value={editName} onChangeText={setEditName} editable={!bankDetailBank.has_native_parser} />

                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Dia Fechamento</Text>
                    <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.label, borderRadius: radius.md }]}
                      value={editClosing} onChangeText={setEditClosing} keyboardType="number-pad" maxLength={2} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Dia Vencimento</Text>
                    <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.label, borderRadius: radius.md }]}
                      value={editDue} onChangeText={setEditDue} keyboardType="number-pad" maxLength={2} />
                  </View>
                </View>

                <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Cor</Text>
                <View style={[styles.colorRow, { marginBottom: 24 }]}>
                  {BANK_COLOR_OPTIONS.map(c => (
                    <Pressable key={c} onPress={() => setEditColor(c)}
                      style={[styles.colorOption, { backgroundColor: c, borderWidth: editColor === c ? 3 : 0, borderColor: '#fff' }]} />
                  ))}
                </View>

                {/* Actions */}
                <Pressable style={[styles.actionBtn, { backgroundColor: colors.blue, borderRadius: radius.md }]}
                  onPress={handleUpdateBank} disabled={editSaving}>
                  {editSaving ? <ActivityIndicator size="small" color="#fff" /> :
                    <Text style={styles.actionBtnText}>Salvar Alterações</Text>}
                </Pressable>

                <Pressable style={[styles.actionBtn, { backgroundColor: `${colors.orange}15`, borderRadius: radius.md, marginTop: 12 }]}
                  onPress={handleRetrainParser} disabled={retraining}>
                  {retraining ? <ActivityIndicator size="small" color={colors.orange} /> : (
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                      <Ionicons name="refresh" size={18} color={colors.orange} />
                      <Text style={[styles.actionBtnText, { color: colors.orange }]}>Retreinar Parser (enviar PDF)</Text>
                    </View>
                  )}
                </Pressable>

                {!bankDetailBank.has_native_parser && (
                  <Pressable style={[styles.actionBtn, { backgroundColor: `${colors.red}10`, borderRadius: radius.md, marginTop: 12 }]}
                    onPress={() => { setBankDetailModal(false); handleDeleteBank(bankDetailBank.id, bankDetailBank.name); }}>
                    <Text style={[styles.actionBtnText, { color: colors.red }]}>Excluir Cartão</Text>
                  </Pressable>
                )}

                <View style={{ height: 50 }} />
              </ScrollView>
            )}
          </SafeAreaView>
        </View>
      </Modal>

      {/* ── DETAIL MODAL ── */}
      <Modal visible={detailModal} animationType="slide" presentationStyle="pageSheet">
        <View style={[styles.modalContainer, { backgroundColor: colors.bg }]}>
          <SafeAreaView style={{ flex: 1 }} edges={['top']}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.separator }]}>
              <Text style={[styles.modalTitle, { color: colors.label }]}>Detalhes da Fatura</Text>
              <Pressable onPress={() => { setDetailModal(false); setDetailData(null); }}>
                <Ionicons name="close-circle" size={28} color={colors.secondaryLabel} />
              </Pressable>
            </View>
            {detailLoading && <ActivityIndicator style={{ marginTop: 32 }} size="large" color={colors.blue} />}
            {detailData && (
              <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
                <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16 }]}>
                  <Text style={[styles.detailTitle, { color: colors.label }]}>
                    {detailData.bank_name || 'Cartão'} · final {detailData.card_last_digits}
                  </Text>
                  <View style={styles.detailGrid}>
                    <View style={styles.detailItem}>
                      <Text style={[styles.detailLabel, { color: colors.tertiaryLabel }]}>MÊS</Text>
                      <Text style={[styles.detailValue, { color: colors.label }]}>{detailData.reference_month}</Text>
                    </View>
                    <View style={styles.detailItem}>
                      <Text style={[styles.detailLabel, { color: colors.tertiaryLabel }]}>TOTAL</Text>
                      <Text style={[styles.detailValue, { color: colors.red }]}>{formatCurrency(detailData.total_amount)}</Text>
                    </View>
                    <View style={styles.detailItem}>
                      <Text style={[styles.detailLabel, { color: colors.tertiaryLabel }]}>TRANSAÇÕES</Text>
                      <Text style={[styles.detailValue, { color: colors.label }]}>{detailData.transaction_count}</Text>
                    </View>
                    <View style={styles.detailItem}>
                      <Text style={[styles.detailLabel, { color: colors.tertiaryLabel }]}>TAMANHO</Text>
                      <Text style={[styles.detailValue, { color: colors.label }]}>{fmtSize(detailData.file_size)}</Text>
                    </View>
                    <View style={styles.detailItem}>
                      <Text style={[styles.detailLabel, { color: colors.tertiaryLabel }]}>IMPORTADO</Text>
                      <Text style={[styles.detailValue, { color: colors.label }]}>
                        {detailData.created_at ? new Date(detailData.created_at).toLocaleString('pt-BR') : '-'}
                      </Text>
                    </View>
                    <View style={styles.detailItem}>
                      <Text style={[styles.detailLabel, { color: colors.tertiaryLabel }]}>VENCIMENTO</Text>
                      <Text style={[styles.detailValue, { color: colors.label }]}>
                        {detailData.due_date ? formatDate(detailData.due_date) : '-'}
                      </Text>
                    </View>
                  </View>
                </View>
                <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>
                  TRANSAÇÕES ({detailData.transaction_count})
                </Text>
                <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                  {detailData.transactions.map((tx, i) => (
                    <View key={tx.id}>
                      {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 16 }]} />}
                      <View style={styles.txRow}>
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.txDesc, { color: colors.label }]} numberOfLines={1}>{tx.description}</Text>
                          <Text style={[styles.txDate, { color: colors.secondaryLabel }]}>
                            {formatDate(tx.date)} · {tx.who}{tx.category ? ` · ${tx.category}` : ''}
                          </Text>
                        </View>
                        <Text style={[styles.txAmt, { color: colors.label }]}>{formatCurrency(tx.amount)}</Text>
                      </View>
                    </View>
                  ))}
                </View>
                <View style={{ height: 50 }} />
              </ScrollView>
            )}
          </SafeAreaView>
        </View>
      </Modal>



      {/* ── SELECT BANK + MONTH MODAL ── */}
      <Modal visible={selectModal} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.formModal, { backgroundColor: colors.surface, borderRadius: radius.xl }]}>
            <Text style={[styles.modalTitle, { color: colors.label, marginBottom: 4 }]}>Importar Fatura</Text>
            <Text style={[styles.invSub, { color: colors.secondaryLabel, marginBottom: 16 }]}>{fileName}</Text>

            <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Cartão (apenas com parser pronto)</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }}>
              <View style={{ flexDirection: 'row', gap: 8 }}>
                {banks.filter(b => b.parser_status === 'ready').map(b => (
                  <Pressable key={b.slug}
                    onPress={() => setSelectedBank(b.slug)}
                    style={[styles.chipBtn, {
                      backgroundColor: selectedBank === b.slug ? b.color : `${colors.tertiaryLabel}20`,
                      borderRadius: radius.md,
                    }]}>
                    <Text style={{ color: selectedBank === b.slug ? '#fff' : colors.label, fontSize: 13, fontWeight: '600' }}>
                      {b.name}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </ScrollView>

            <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Mês/Ano de Pagamento</Text>
            <View style={{ flexDirection: 'row', gap: 8, marginBottom: 16 }}>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ flex: 1 }}>
                <View style={{ flexDirection: 'row', gap: 4 }}>
                  {MONTHS.map((m, i) => (
                    <Pressable key={m}
                      onPress={() => setSelectedMonth(m)}
                      style={[styles.chipBtn, {
                        backgroundColor: selectedMonth === m ? colors.blue : `${colors.tertiaryLabel}20`,
                        borderRadius: radius.sm, paddingHorizontal: 10,
                      }]}>
                      <Text style={{ color: selectedMonth === m ? '#fff' : colors.label, fontSize: 12, fontWeight: '600' }}>
                        {MONTH_NAMES[i]}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </ScrollView>
            </View>
            <View style={{ flexDirection: 'row', gap: 8, marginBottom: 20 }}>
              {['2025', '2026'].map(y => (
                <Pressable key={y}
                  onPress={() => setSelectedYear(y)}
                  style={[styles.chipBtn, {
                    backgroundColor: selectedYear === y ? colors.blue : `${colors.tertiaryLabel}20`,
                    borderRadius: radius.sm, flex: 1,
                  }]}>
                  <Text style={{ color: selectedYear === y ? '#fff' : colors.label, fontSize: 14, fontWeight: '600' }}>
                    {y}
                  </Text>
                </Pressable>
              ))}
            </View>

            <View style={styles.formActions}>
              <Pressable onPress={() => { setSelectModal(false); setFileUri(''); setFileName(''); }} style={styles.cancelBtn}>
                <Text style={[{ color: colors.red, fontSize: 15 }]}>Cancelar</Text>
              </Pressable>
              <Pressable style={[styles.saveBtn, { backgroundColor: colors.blue, borderRadius: radius.md }]}
                onPress={handleUploadWithParams}>
                <Text style={{ color: '#fff', fontSize: 15, fontWeight: '600' }}>Processar</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: { gap: 8 },
  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5, marginBottom: 12 },

  card: { overflow: 'hidden' },
  errorRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16, gap: 10 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  errorText: { fontSize: 14, fontWeight: '500', flex: 1 },

  importBtn: { height: 50, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  importBtnText: { color: '#fff', fontSize: 17, fontWeight: '600' },
  cancelBtn: { alignItems: 'center', paddingVertical: 12 },

  centerText: { fontSize: 17, fontWeight: '600', textAlign: 'center' },
  centerTextSm: { fontSize: 13, textAlign: 'center', marginTop: 4 },

  previewBank: { fontSize: 17, fontWeight: '600' },
  previewSub: { fontSize: 13, marginTop: 2 },
  previewStats: { flexDirection: 'row', marginTop: 12, gap: 16 },
  stat: { flex: 1, gap: 2 },
  statLabel: { fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 },
  statValue: { fontSize: 17, fontWeight: '700' },

  txRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  txDesc: { fontSize: 15, fontWeight: '500' },
  txDate: { fontSize: 12, marginTop: 2 },
  txAmt: { fontSize: 15, fontWeight: '600', marginLeft: 8 },

  doneTitle: { fontSize: 22, fontWeight: '700', marginTop: 12 },
  onboardTitle: { fontSize: 24, fontWeight: '700', textAlign: 'center' },
  onboardSub: { fontSize: 15, textAlign: 'center', lineHeight: 22 },

  sectionLabel: { fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1, marginTop: 20, marginBottom: 8, paddingHorizontal: 4 },
  sectionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 4, marginBottom: 8 },

  invRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  invTitle: { fontSize: 15, fontWeight: '600' },
  invSub: { fontSize: 12, marginTop: 2 },
  invAmount: { fontSize: 15, fontWeight: '700' },
  invDate: { fontSize: 11, marginTop: 2 },

  bankRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  bankDot: { width: 28, height: 28, borderRadius: 14, marginRight: 12 },
  bankName: { fontSize: 15, fontWeight: '500', flex: 1 },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  statusText: { fontSize: 11, fontWeight: '600' },
  sep: { height: 0.5 },

  modalContainer: { flex: 1 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 0.5 },
  modalTitle: { fontSize: 20, fontWeight: '700' },

  detailTitle: { fontSize: 18, fontWeight: '700', marginBottom: 12 },
  detailGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  detailItem: { width: '45%', gap: 2 },
  detailLabel: { fontSize: 10, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  detailValue: { fontSize: 15, fontWeight: '600' },

  modalOverlay: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)' },
  formModal: { width: '85%', padding: 24 },
  input: { height: 44, paddingHorizontal: 12, fontSize: 15, marginBottom: 12 },
  colorLabel: { fontSize: 12, fontWeight: '600', marginBottom: 8 },
  colorRow: { flexDirection: 'row', gap: 10, flexWrap: 'wrap', marginBottom: 20 },
  colorOption: { width: 32, height: 32, borderRadius: 16 },
  formActions: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  saveBtn: { paddingHorizontal: 24, paddingVertical: 10 },
  chipBtn: { paddingHorizontal: 14, paddingVertical: 8, alignItems: 'center', justifyContent: 'center' },
  actionBtn: { height: 48, justifyContent: 'center', alignItems: 'center' },
  actionBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  footnote: { fontSize: 13, lineHeight: 18 },
});
