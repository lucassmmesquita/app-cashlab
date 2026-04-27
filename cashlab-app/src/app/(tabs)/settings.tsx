/**
 * CashLab — Settings (iOS Design System v2)
 *
 * Seções: Aparência (tema), Segurança (Face ID), Bancos (CRUD + parser), Conta (logout).
 * v2.0: Cadastro de bancos migrado da tela Cartões para cá.
 */
import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable, Switch, Alert, Platform, RefreshControl, Modal, TextInput, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScrollView } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';

import { useAuthStore } from '@/store/useAuthStore';
import { useSettingsStore } from '@/store/useSettingsStore';
import { useAppTheme } from '@/hooks/useAppTheme';
import { useBiometric } from '@/hooks/useBiometric';
import { bankService } from '@/services/bankService';
import type { BankItem } from '@/services/bankService';

type ThemeMode = 'system' | 'light' | 'dark';

const BANK_COLOR_OPTIONS = ['#F5A623','#FF6B00','#8A05BE','#007AFF','#34C759','#E63946','#2D3436','#00B894'];

const PARSER_STATUS_MAP: Record<string, { label: string; color: string; emoji: string }> = {
  pending: { label: 'Pendente', color: '#FF9500', emoji: '⏳' },
  processing: { label: 'Processando...', color: '#007AFF', emoji: '⚙️' },
  ready: { label: 'Pronto', color: '#34C759', emoji: '✅' },
  error: { label: 'Erro', color: '#FF3B30', emoji: '❌' },
};

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

  // Banks state
  const [banks, setBanks] = useState<BankItem[]>([]);
  const [banksLoading, setBanksLoading] = useState(false);

  // Add bank modal
  const [bankModal, setBankModal] = useState(false);
  const [newBankName, setNewBankName] = useState('');
  const [newBankColor, setNewBankColor] = useState('#007AFF');
  const [newClosingDay, setNewClosingDay] = useState('');
  const [newDueDay, setNewDueDay] = useState('');
  const [bankSaving, setBankSaving] = useState(false);

  // Detail/Edit bank modal
  const [detailBank, setDetailBank] = useState<BankItem | null>(null);
  const [detailModal, setDetailModal] = useState(false);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState('');
  const [editClosing, setEditClosing] = useState('');
  const [editDue, setEditDue] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [retraining, setRetraining] = useState(false);

  const fetchBanks = useCallback(async () => {
    setBanksLoading(true);
    try {
      const data = await bankService.list();
      setBanks(data);
    } catch { /* keep current */ }
    finally { setBanksLoading(false); }
  }, []);

  useEffect(() => { fetchBanks(); }, [fetchBanks]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchBanks();
    setRefreshing(false);
  }, [fetchBanks]);

  const handleLogout = () => {
    Alert.alert('Sair', 'Deseja sair da conta?', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Sair', style: 'destructive', onPress: () => { clearAuth(); router.replace('/(auth)/login'); } },
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
      fetchBanks();
    } catch (err: any) {
      Alert.alert('Erro', err.response?.data?.detail || 'Erro ao criar banco');
    } finally { setBankSaving(false); }
  };

  const openBankDetail = (bank: BankItem) => {
    setDetailBank(bank);
    setEditName(bank.name);
    setEditColor(bank.color);
    setEditClosing(bank.closing_day ? String(bank.closing_day) : '');
    setEditDue(bank.due_day ? String(bank.due_day) : '');
    setDetailModal(true);
  };

  const handleUpdateBank = async () => {
    if (!detailBank) return;
    setEditSaving(true);
    try {
      await bankService.update(detailBank.id, {
        name: editName.trim() || undefined,
        color: editColor || undefined,
        closing_day: editClosing ? parseInt(editClosing) : undefined,
        due_day: editDue ? parseInt(editDue) : undefined,
      });
      setDetailModal(false);
      fetchBanks();
    } catch (err: any) {
      Alert.alert('Erro', err.response?.data?.detail || 'Erro ao atualizar');
    } finally { setEditSaving(false); }
  };

  const handleRetrainParser = async () => {
    if (!detailBank) return;
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: 'application/pdf', copyToCacheDirectory: true });
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      setRetraining(true);
      const updated = await bankService.retrain(detailBank.id, asset.uri, asset.name);
      Alert.alert('Sucesso', updated.message || 'Parser treinado com sucesso');
      setDetailModal(false);
      fetchBanks();
    } catch (err: any) {
      Alert.alert('Erro', err.response?.data?.detail || 'Erro ao treinar parser');
    } finally { setRetraining(false); }
  };

  const handleDeleteBank = (id: number, name: string) => {
    Alert.alert('Excluir Banco', `Remover "${name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Excluir', style: 'destructive', onPress: async () => {
        try { await bankService.remove(id); fetchBanks(); } catch (err: any) {
          Alert.alert('Erro', err.response?.data?.detail || 'Não foi possível excluir');
        }
      }},
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
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.blue} />}
        >
          <Text style={[styles.largeTitle, { color: colors.label }]}>Settings</Text>

          {/* ── Conta ── */}
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

          {/* ── Aparência ── */}
          <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>APARÊNCIA</Text>
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.rowSimple}>
              <Text style={[styles.rowTitle, { color: colors.label }]}>Tema</Text>
            </View>
            <View style={[styles.segmentControl, { backgroundColor: colors.segmentBg, borderRadius: 8, marginHorizontal: 16, marginBottom: 16 }]}>
              {themeOptions.map((opt) => (
                <Pressable
                  key={opt.value}
                  style={[styles.segOption, themeMode === opt.value && [styles.segActive, { backgroundColor: colors.segmentActive, borderRadius: 7 }]]}
                  onPress={() => setThemeMode(opt.value)}
                >
                  <Text style={[styles.segText, { color: themeMode === opt.value ? colors.label : colors.secondaryLabel }, themeMode === opt.value && { fontWeight: '600' }]}>
                    {opt.label}
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>

          {/* ── Segurança ── */}
          <Text style={[styles.sectionLabel, { color: colors.secondaryLabel }]}>SEGURANÇA</Text>
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.switchRow}>
              <View style={styles.switchRowLeft}>
                <Ionicons name={Platform.OS === 'ios' ? 'scan' : 'finger-print'} size={22} color={colors.blue} style={{ marginRight: 12 }} />
                <Text style={[styles.rowTitle, { color: colors.label }]}>{biometricLabel}</Text>
              </View>
              <Switch
                value={biometricEnabled}
                onValueChange={(val) => {
                  if (!biometricAvailable) { Alert.alert(`${biometricLabel} indisponível`, `Configure ${biometricLabel} nas configurações do seu dispositivo primeiro.`); return; }
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

          {/* ── BANCOS (migrado de Cartões) ── */}
          <View style={[styles.sectionRow, { marginTop: 24 }]}>
            <Text style={[styles.sectionLabel, { color: colors.secondaryLabel, marginTop: 0 }]}>BANCOS</Text>
            <Pressable onPress={() => setBankModal(true)} hitSlop={12}>
              <Ionicons name="add-circle" size={22} color={colors.blue} />
            </Pressable>
          </View>
          {banksLoading && <ActivityIndicator style={{ marginVertical: 8 }} color={colors.blue} />}
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            {banks.map((b, i) => {
              const ps = PARSER_STATUS_MAP[b.parser_status] || PARSER_STATUS_MAP.pending;
              return (
                <View key={b.id}>
                  {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 52 }]} />}
                  <Pressable style={styles.bankRow} onPress={() => openBankDetail(b)}>
                    <View style={[styles.bankDot, { backgroundColor: b.color }]} />
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.bankName, { color: colors.label }]}>{b.name}</Text>
                      <Text style={[styles.rowSub, { color: colors.tertiaryLabel }]}>
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

          {/* ── Ação ── */}
          <View style={{ marginTop: 24 }}>
            <Pressable style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]} onPress={handleLogout}>
              <View style={[styles.rowSimple, { justifyContent: 'center' }]}>
                <Text style={[styles.rowTitle, { color: colors.red, textAlign: 'center' }]}>Sair da conta</Text>
              </View>
            </Pressable>
          </View>

          <Text style={[styles.footer, { color: colors.tertiaryLabel }]}>CashLab v2.0.0 · Abril 2026</Text>
          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>

      {/* ── ADD BANK MODAL ── */}
      <Modal visible={bankModal} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.formModal, { backgroundColor: colors.surface, borderRadius: radius.xl }]}>
            <Text style={[styles.modalTitle, { color: colors.label, marginBottom: 16 }]}>Novo Banco</Text>
            <TextInput style={[styles.input, { backgroundColor: colors.bg, color: colors.label, borderRadius: radius.md }]}
              placeholder="Nome do banco" placeholderTextColor={colors.tertiaryLabel}
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
      <Modal visible={detailModal} animationType="slide" presentationStyle="pageSheet">
        <View style={[styles.container, { backgroundColor: colors.bg }]}>
          <SafeAreaView style={{ flex: 1 }} edges={['top']}>
            <View style={[styles.modalHeader, { borderBottomColor: colors.separator }]}>
              <Text style={[styles.modalTitle, { color: colors.label }]}>Detalhes do Banco</Text>
              <Pressable onPress={() => setDetailModal(false)}>
                <Ionicons name="close-circle" size={28} color={colors.secondaryLabel} />
              </Pressable>
            </View>
            {detailBank && (
              <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
                {/* Status do parser */}
                <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg, padding: 16, marginBottom: 16, alignItems: 'center' }]}>
                  {(() => { const ps = PARSER_STATUS_MAP[detailBank.parser_status] || PARSER_STATUS_MAP.pending; return (
                    <>
                      <Text style={{ fontSize: 32 }}>{ps.emoji}</Text>
                      <Text style={[styles.bankName, { color: ps.color, marginTop: 4 }]}>{ps.label}</Text>
                      {detailBank.parser_trained_at && (
                        <Text style={[styles.rowSub, { color: colors.tertiaryLabel, marginTop: 4 }]}>
                          Último treinamento: {new Date(detailBank.parser_trained_at).toLocaleDateString('pt-BR')}
                        </Text>
                      )}
                      <Text style={[styles.rowSub, { color: colors.tertiaryLabel, marginTop: 2 }]}>
                        {detailBank.invoice_count} fatura(s) importada(s)
                      </Text>
                    </>
                  ); })()}
                </View>

                {/* Campos editáveis */}
                <Text style={[styles.colorLabel, { color: colors.secondaryLabel }]}>Nome</Text>
                <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.label, borderRadius: radius.md }]}
                  value={editName} onChangeText={setEditName} editable={!detailBank.has_native_parser} />

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

                {!detailBank.has_native_parser && (
                  <Pressable style={[styles.actionBtn, { backgroundColor: `${colors.red}10`, borderRadius: radius.md, marginTop: 12 }]}
                    onPress={() => { setDetailModal(false); handleDeleteBank(detailBank.id, detailBank.name); }}>
                    <Text style={[styles.actionBtnText, { color: colors.red }]}>Excluir Banco</Text>
                  </Pressable>
                )}

                <View style={{ height: 50 }} />
              </ScrollView>
            )}
          </SafeAreaView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: { gap: 0 },
  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5, marginBottom: 24 },
  sectionLabel: { fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1, marginTop: 24, marginBottom: 8, paddingHorizontal: 4 },
  sectionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 4, marginBottom: 8 },
  card: { overflow: 'hidden', marginBottom: 0 },
  row: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  rowSimple: { padding: 12, paddingHorizontal: 16 },
  rowBody: { flex: 1, gap: 1 },
  rowTitle: { fontSize: 17, fontWeight: '400' },
  rowSub: { fontSize: 13 },
  avatar: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: '700' },
  segmentControl: { flexDirection: 'row', padding: 2 },
  segOption: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingVertical: 7 },
  segActive: {},
  segText: { fontSize: 13, fontWeight: '500' },
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 12, paddingHorizontal: 16 },
  switchRowLeft: { flexDirection: 'row', alignItems: 'center' },
  footnote: { fontSize: 13, lineHeight: 18 },
  footer: { textAlign: 'center', fontSize: 11, marginTop: 32 },
  // Banks
  bankRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16 },
  bankDot: { width: 28, height: 28, borderRadius: 14, marginRight: 12 },
  bankName: { fontSize: 15, fontWeight: '500' },
  statusBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  statusText: { fontSize: 11, fontWeight: '600' },
  sep: { height: 0.5 },
  // Modals
  modalOverlay: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)' },
  formModal: { width: '85%', padding: 24 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 0.5 },
  modalTitle: { fontSize: 20, fontWeight: '700' },
  input: { height: 44, paddingHorizontal: 12, fontSize: 15, marginBottom: 12 },
  colorLabel: { fontSize: 12, fontWeight: '600', marginBottom: 8 },
  colorRow: { flexDirection: 'row', gap: 10, flexWrap: 'wrap', marginBottom: 20 },
  colorOption: { width: 32, height: 32, borderRadius: 16 },
  formActions: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cancelBtn: { alignItems: 'center', paddingVertical: 12 },
  saveBtn: { paddingHorizontal: 24, paddingVertical: 10 },
  actionBtn: { height: 48, justifyContent: 'center', alignItems: 'center' },
  actionBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
});
