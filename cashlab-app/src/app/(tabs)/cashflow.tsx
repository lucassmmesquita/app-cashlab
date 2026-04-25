/**
 * CashLab — Tela de Fluxo de Caixa com CRUD de Receitas e Despesas
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Modal, TextInput, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useMonthNavigation } from '@/hooks/useMonthNavigation';
import { useAppTheme } from '@/hooks/useAppTheme';
import { MonthNavigator } from '@/components/dashboard/MonthNavigator';
import { formatCurrency } from '@/utils/formatters';
import { BANK_COLORS } from '@/utils/colors';
import api from '@/services/api';

interface IncomeItem { id: number; source: string; amount: number; type: string; note: string; }
interface ExpenseItem { id: number; description: string; amount: number; category: string; note: string; }
interface CardInvoice { id: number; reference_month: string; due_date: string | null; total_amount: string; card_id: number; bank?: string; }

// Fallback data used when API returns empty
const FALLBACK_INCOMES: IncomeItem[] = [
  { id: -1, source: 'iRede CLT', amount: 6700, type: 'CLT', note: 'Salário registrado' },
  { id: -2, source: 'iRede PJ', amount: 17500, type: 'PJ', note: 'Pró-labore / nota fiscal' },
  { id: -3, source: 'Totalis', amount: 2000, type: 'PJ/Extra', note: 'Receita adicional' },
];
const FALLBACK_EXPENSES: ExpenseItem[] = [
  { id: -1, description: 'Aluguel + Cond + Água + Gás', amount: 4645.50, category: 'Moradia', note: 'Valor conjunto informado' },
  { id: -2, description: 'Financiamento do carro', amount: 1650.42, category: 'Automotivo', note: 'Parcela 06 de 36' },
  { id: -3, description: 'Energia elétrica (média)', amount: 800, category: 'Moradia', note: 'Média mensal' },
  { id: -4, description: 'Ajuda Pais da Joice', amount: 500, category: 'Família', note: 'Transferência mensal' },
  { id: -5, description: 'Ajuda Pais do Lucas', amount: 500, category: 'Família', note: 'Transferência mensal' },
];

type ModalMode = 'add' | 'edit';
type ModalType = 'income' | 'expense';

export default function CashFlowScreen() {
  const { selectedMonth, goToPreviousMonth, goToNextMonth } = useMonthNavigation();
  const { colors, radius, spacing } = useAppTheme();

  const [incomes, setIncomes] = useState<IncomeItem[]>(FALLBACK_INCOMES);
  const [expenses, setExpenses] = useState<ExpenseItem[]>(FALLBACK_EXPENSES);
  const [invoices, setInvoices] = useState<CardInvoice[]>([]);
  const [loading, setLoading] = useState(false);

  // Modal state
  const [modalVisible, setModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>('add');
  const [modalType, setModalType] = useState<ModalType>('income');
  const [editId, setEditId] = useState<number | null>(null);
  const [formName, setFormName] = useState('');
  const [formType, setFormType] = useState('');
  const [formAmount, setFormAmount] = useState('');
  const [formNote, setFormNote] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [incRes, expRes, invRes] = await Promise.all([
        api.get('/incomes'),
        api.get('/fixed-expenses'),
        api.get('/invoices'),
      ]);
      const incData = incRes.data?.data || [];
      const expData = expRes.data?.data || [];
      const invData = invRes.data?.data || [];
      setIncomes(incData.length > 0 ? incData : FALLBACK_INCOMES);
      setExpenses(expData.length > 0 ? expData : FALLBACK_EXPENSES);
      setInvoices(invData);
    } catch {
      // keep current/fallback data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Totals
  const totalIncome = incomes.reduce((s, i) => s + i.amount, 0);
  const totalFixed = expenses.reduce((s, e) => s + e.amount, 0);
  const totalCards = invoices.reduce((s, inv) => s + parseFloat(inv.total_amount || '0'), 0);
  const totalExpenses = totalFixed + totalCards;
  const balance = totalIncome - totalExpenses;
  const isDeficit = balance < 0;
  const pctCompromised = totalIncome > 0 ? ((totalExpenses / totalIncome) * 100).toFixed(1) : '0';

  // Modal helpers
  const openAddModal = (type: ModalType) => {
    setModalMode('add'); setModalType(type); setEditId(null);
    setFormName(''); setFormType(''); setFormAmount(''); setFormNote('');
    setModalVisible(true);
  };

  const openEditModal = (type: ModalType, item: any) => {
    setModalMode('edit'); setModalType(type); setEditId(item.id);
    setFormName(type === 'income' ? item.source : item.description);
    setFormType(type === 'income' ? item.type : item.category);
    setFormAmount(String(item.amount));
    setFormNote(item.note || '');
    setModalVisible(true);
  };

  const handleSave = async () => {
    if (!formName.trim() || !formAmount.trim()) {
      Alert.alert('Erro', 'Preencha nome e valor'); return;
    }
    setSaving(true);
    try {
      if (modalType === 'income') {
        const payload = { source: formName, type: formType || 'Outro', amount: parseFloat(formAmount), note: formNote };
        if (modalMode === 'add') {
          const res = await api.post('/incomes', payload);
          setIncomes(prev => {
            const real = prev.filter(i => i.id > 0);
            return [...real, res.data.data];
          });
        } else {
          const res = await api.put(`/incomes/${editId}`, payload);
          setIncomes(prev => prev.map(i => i.id === editId ? res.data.data : i));
        }
      } else {
        const payload = { description: formName, category: formType || 'Outro', amount: parseFloat(formAmount), note: formNote };
        if (modalMode === 'add') {
          const res = await api.post('/fixed-expenses', payload);
          setExpenses(prev => {
            const real = prev.filter(e => e.id > 0);
            return [...real, res.data.data];
          });
        } else {
          const res = await api.put(`/fixed-expenses/${editId}`, payload);
          setExpenses(prev => prev.map(e => e.id === editId ? res.data.data : e));
        }
      }
      setModalVisible(false);
      fetchData();
    } catch {
      Alert.alert('Erro', 'Não foi possível salvar');
    } finally { setSaving(false); }
  };

  const handleDelete = (type: ModalType, id: number, name: string) => {
    Alert.alert('Excluir', `Deseja excluir "${name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Excluir', style: 'destructive', onPress: async () => {
        try {
          if (type === 'income') {
            await api.delete(`/incomes/${id}`);
            setIncomes(prev => prev.filter(i => i.id !== id));
          } else {
            await api.delete(`/fixed-expenses/${id}`);
            setExpenses(prev => prev.filter(e => e.id !== id));
          }
        } catch { Alert.alert('Erro', 'Não foi possível excluir'); }
      }},
    ]);
  };

  const SectionHeader = ({ title, icon, onAdd }: { title: string; icon: string; onAdd: () => void }) => (
    <View style={styles.sectionHeader}>
      <Ionicons name={icon as any} size={18} color={colors.blue} />
      <Text style={[styles.sectionTitle, { color: colors.label }]}>{title}</Text>
      <View style={{ flex: 1 }} />
      <TouchableOpacity onPress={onAdd} style={[styles.addBtn, { backgroundColor: `${colors.blue}15` }]}>
        <Ionicons name="add" size={20} color={colors.blue} />
      </TouchableOpacity>
    </View>
  );

  const StaticSectionHeader = ({ title, icon }: { title: string; icon: string }) => (
    <View style={styles.sectionHeader}>
      <Ionicons name={icon as any} size={18} color={colors.blue} />
      <Text style={[styles.sectionTitle, { color: colors.label }]}>{title}</Text>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <ScrollView contentContainerStyle={[styles.scrollContent, { padding: spacing.lg }]} showsVerticalScrollIndicator={false}>
          <Text style={[styles.largeTitle, { color: colors.label }]}>Fluxo de Caixa</Text>
          <MonthNavigator month={selectedMonth} onPrevious={goToPreviousMonth} onNext={goToNextMonth} />

          {loading && <ActivityIndicator style={{ marginVertical: 12 }} color={colors.blue} />}

          {/* Result card */}
          <View style={[styles.resultCard, {
            backgroundColor: isDeficit ? `${colors.red}10` : `${colors.green}10`,
            borderRadius: radius.lg,
            borderColor: isDeficit ? `${colors.red}30` : `${colors.green}30`,
            borderWidth: 1,
          }]}>
            <Text style={[styles.resultLabel, { color: colors.secondaryLabel }]}>SOBRA / DÉFICIT DO MÊS</Text>
            <Text style={[styles.resultValue, { color: isDeficit ? colors.red : colors.green }]}>{formatCurrency(balance)}</Text>
            <Text style={[styles.resultNote, { color: colors.secondaryLabel }]}>{pctCompromised}% da receita comprometida</Text>
          </View>

          {/* Summary bars */}
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={[styles.sumLabel, { color: colors.tertiaryLabel }]}>Receitas</Text>
                <Text style={[styles.sumValue, { color: colors.green }]}>{formatCurrency(totalIncome)}</Text>
              </View>
              <View style={[styles.sumDivider, { backgroundColor: colors.separator }]} />
              <View style={styles.summaryItem}>
                <Text style={[styles.sumLabel, { color: colors.tertiaryLabel }]}>Saídas</Text>
                <Text style={[styles.sumValue, { color: colors.red }]}>{formatCurrency(totalExpenses)}</Text>
              </View>
            </View>
            <View style={[styles.progressBg, { backgroundColor: colors.segmentBg }]}>
              <View style={[styles.progressFill, {
                backgroundColor: isDeficit ? colors.red : colors.green,
                width: `${Math.min((totalExpenses / totalIncome) * 100, 100)}%`,
              }]} />
            </View>
          </View>

          {/* Receitas */}
          <SectionHeader title="Receitas Mensais" icon="arrow-down-circle" onAdd={() => openAddModal('income')} />
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            {incomes.map((item, i) => (
              <View key={item.id}>
                {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 16 }]} />}
                <TouchableOpacity style={styles.lineRow} onPress={() => openEditModal('income', item)} onLongPress={() => item.id > 0 && handleDelete('income', item.id, item.source)}>
                  <View style={styles.lineBody}>
                    <Text style={[styles.lineTitle, { color: colors.label }]}>{item.source}</Text>
                    <Text style={[styles.lineNote, { color: colors.tertiaryLabel }]}>{item.type} · {item.note}</Text>
                  </View>
                  <Text style={[styles.lineAmount, { color: colors.green }]}>{formatCurrency(item.amount)}</Text>
                  <View style={styles.rowActions}>
                    <TouchableOpacity onPress={() => openEditModal('income', item)} hitSlop={{top:8,bottom:8,left:8,right:8}}>
                      <Ionicons name="pencil" size={16} color={colors.tertiaryLabel} />
                    </TouchableOpacity>
                    {item.id > 0 && (
                      <TouchableOpacity onPress={() => handleDelete('income', item.id, item.source)} hitSlop={{top:8,bottom:8,left:8,right:8}}>
                        <Ionicons name="trash-outline" size={16} color={colors.red} />
                      </TouchableOpacity>
                    )}
                  </View>
                </TouchableOpacity>
              </View>
            ))}
            <View style={[styles.sep, { backgroundColor: colors.separator }]} />
            <View style={[styles.totalRow, { backgroundColor: `${colors.green}08` }]}>
              <Text style={[styles.totalLabel, { color: colors.label }]}>Total Receitas Brutas</Text>
              <Text style={[styles.totalValue, { color: colors.green }]}>{formatCurrency(totalIncome)}</Text>
            </View>
          </View>

          {/* Despesas Fixas */}
          <SectionHeader title="Despesas Fixas Mensais" icon="arrow-up-circle" onAdd={() => openAddModal('expense')} />
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            {expenses.map((item, i) => (
              <View key={item.id}>
                {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 16 }]} />}
                <TouchableOpacity style={styles.lineRow} onPress={() => openEditModal('expense', item)} onLongPress={() => item.id > 0 && handleDelete('expense', item.id, item.description)}>
                  <View style={styles.lineBody}>
                    <Text style={[styles.lineTitle, { color: colors.label }]}>{item.description}</Text>
                    <Text style={[styles.lineNote, { color: colors.tertiaryLabel }]}>{item.category} · {item.note}</Text>
                  </View>
                  <Text style={[styles.lineAmount, { color: colors.label }]}>-{formatCurrency(item.amount)}</Text>
                  <View style={styles.rowActions}>
                    <TouchableOpacity onPress={() => openEditModal('expense', item)} hitSlop={{top:8,bottom:8,left:8,right:8}}>
                      <Ionicons name="pencil" size={16} color={colors.tertiaryLabel} />
                    </TouchableOpacity>
                    {item.id > 0 && (
                      <TouchableOpacity onPress={() => handleDelete('expense', item.id, item.description)} hitSlop={{top:8,bottom:8,left:8,right:8}}>
                        <Ionicons name="trash-outline" size={16} color={colors.red} />
                      </TouchableOpacity>
                    )}
                  </View>
                </TouchableOpacity>
              </View>
            ))}
            <View style={[styles.sep, { backgroundColor: colors.separator }]} />
            <View style={[styles.totalRow, { backgroundColor: `${colors.red}08` }]}>
              <Text style={[styles.totalLabel, { color: colors.label }]}>Total Despesas Fixas</Text>
              <Text style={[styles.totalValue, { color: colors.red }]}>-{formatCurrency(totalFixed)}</Text>
            </View>
          </View>

          {/* Faturas de Cartão */}
          <StaticSectionHeader title="Faturas de Cartão" icon="card" />
          <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            {invoices.length === 0 ? (
              <View style={{ padding: 20, alignItems: 'center' }}>
                <Text style={[styles.lineNote, { color: colors.tertiaryLabel }]}>Nenhuma fatura importada</Text>
                <Text style={[styles.lineNote, { color: colors.tertiaryLabel, marginTop: 4 }]}>Vá em Cartões para importar PDFs</Text>
              </View>
            ) : (
              invoices.map((inv, i) => (
                <View key={inv.id}>
                  {i > 0 && <View style={[styles.sep, { backgroundColor: colors.separator, marginLeft: 52 }]} />}
                  <View style={styles.lineRow}>
                    <View style={[styles.bankDot, { backgroundColor: BANK_COLORS[inv.bank || 'bv'] || colors.blue }]} />
                    <View style={styles.lineBody}>
                      <Text style={[styles.lineTitle, { color: colors.label }]}>Fatura {inv.reference_month}</Text>
                      <Text style={[styles.lineNote, { color: colors.tertiaryLabel }]}>
                        {inv.due_date ? `Vencimento ${inv.due_date.split('-').reverse().join('/')}` : 'Sem vencimento'}
                      </Text>
                    </View>
                    <Text style={[styles.lineAmount, { color: colors.label }]}>-{formatCurrency(inv.total_amount)}</Text>
                  </View>
                </View>
              ))
            )}
            {invoices.length > 0 && (
              <>
                <View style={[styles.sep, { backgroundColor: colors.separator }]} />
                <View style={[styles.totalRow, { backgroundColor: `${colors.red}08` }]}>
                  <Text style={[styles.totalLabel, { color: colors.label }]}>Total Faturas do Mês</Text>
                  <Text style={[styles.totalValue, { color: colors.red }]}>-{formatCurrency(totalCards)}</Text>
                </View>
              </>
            )}
          </View>

          <View style={{ height: 100 }} />
        </ScrollView>
      </SafeAreaView>

      {/* CRUD Modal */}
      <Modal visible={modalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: colors.label }]}>
                {modalMode === 'add' ? 'Adicionar' : 'Editar'} {modalType === 'income' ? 'Receita' : 'Despesa'}
              </Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close-circle" size={28} color={colors.tertiaryLabel} />
              </TouchableOpacity>
            </View>

            <Text style={[styles.fieldLabel, { color: colors.secondaryLabel }]}>Nome</Text>
            <TextInput style={[styles.input, { color: colors.label, backgroundColor: colors.bg, borderColor: colors.separator }]}
              value={formName} onChangeText={setFormName} placeholder={modalType === 'income' ? 'Ex: Salário CLT' : 'Ex: Aluguel'}
              placeholderTextColor={colors.tertiaryLabel} />

            <Text style={[styles.fieldLabel, { color: colors.secondaryLabel }]}>Tipo / Categoria</Text>
            <TextInput style={[styles.input, { color: colors.label, backgroundColor: colors.bg, borderColor: colors.separator }]}
              value={formType} onChangeText={setFormType} placeholder={modalType === 'income' ? 'CLT, PJ, Benefício...' : 'Moradia, Família...'}
              placeholderTextColor={colors.tertiaryLabel} />

            <Text style={[styles.fieldLabel, { color: colors.secondaryLabel }]}>Valor (R$)</Text>
            <TextInput style={[styles.input, { color: colors.label, backgroundColor: colors.bg, borderColor: colors.separator }]}
              value={formAmount} onChangeText={setFormAmount} placeholder="0.00"
              placeholderTextColor={colors.tertiaryLabel} keyboardType="decimal-pad" />

            <Text style={[styles.fieldLabel, { color: colors.secondaryLabel }]}>Observação</Text>
            <TextInput style={[styles.input, { color: colors.label, backgroundColor: colors.bg, borderColor: colors.separator }]}
              value={formNote} onChangeText={setFormNote} placeholder="Opcional"
              placeholderTextColor={colors.tertiaryLabel} />

            <TouchableOpacity
              style={[styles.saveBtn, { backgroundColor: modalType === 'income' ? colors.green : colors.blue }]}
              onPress={handleSave} disabled={saving}>
              {saving ? <ActivityIndicator color="#fff" /> :
                <Text style={styles.saveBtnText}>{modalMode === 'add' ? 'Adicionar' : 'Salvar'}</Text>}
            </TouchableOpacity>
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
  largeTitle: { fontSize: 34, fontWeight: '700', letterSpacing: -1.5, marginBottom: 4 },
  resultCard: { padding: 20, alignItems: 'center', gap: 4 },
  resultLabel: { fontSize: 11, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase' },
  resultValue: { fontSize: 32, fontWeight: '800', letterSpacing: -1 },
  resultNote: { fontSize: 13, marginTop: 4 },
  card: { overflow: 'hidden' },
  summaryRow: { flexDirection: 'row', padding: 16, gap: 16, alignItems: 'center' },
  summaryItem: { flex: 1, gap: 2 },
  sumLabel: { fontSize: 11, fontWeight: '600', letterSpacing: 0.5, textTransform: 'uppercase' },
  sumValue: { fontSize: 20, fontWeight: '700' },
  sumDivider: { width: 1, height: 36 },
  progressBg: { height: 6, borderRadius: 3, marginHorizontal: 16, marginBottom: 16 },
  progressFill: { height: 6, borderRadius: 3 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 20, marginBottom: 6 },
  sectionTitle: { fontSize: 18, fontWeight: '700' },
  addBtn: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  lineRow: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingHorizontal: 16, gap: 12 },
  lineBody: { flex: 1, gap: 2 },
  lineTitle: { fontSize: 15, fontWeight: '500' },
  lineNote: { fontSize: 12 },
  lineAmount: { fontSize: 15, fontWeight: '600', flexShrink: 0 },
  rowActions: { flexDirection: 'row', gap: 12, marginLeft: 4 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', padding: 14, paddingHorizontal: 16 },
  totalLabel: { fontSize: 15, fontWeight: '700' },
  totalValue: { fontSize: 17, fontWeight: '700' },
  bankDot: { width: 28, height: 28, borderRadius: 14, flexShrink: 0 },
  sep: { height: 0.5 },
  // Modal
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { padding: 24, paddingBottom: 40 },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  modalTitle: { fontSize: 20, fontWeight: '700' },
  fieldLabel: { fontSize: 13, fontWeight: '600', marginBottom: 6, marginTop: 12 },
  input: { height: 44, borderWidth: 1, borderRadius: 10, paddingHorizontal: 14, fontSize: 16 },
  saveBtn: { height: 48, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginTop: 24 },
  saveBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
