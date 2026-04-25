/**
 * CashLab — Paleta de cores por categoria e membro
 *
 * Alinhado ao Design System v2 (iOS systemColors).
 * Ref: docs/CASHLAB_DESIGN_SYSTEM_v2.html → seção "Categorias" e "Membros"
 */

/** Cores por membro da família (design system v2) */
export const MEMBER_COLORS: Record<string, { light: string; dark: string }> = {
  LUCAS:   { light: '#34C759', dark: '#30D158' },  // systemGreen
  JURA:    { light: '#FF9500', dark: '#FF9F0A' },  // systemOrange
  JOICE:   { light: '#FF2D55', dark: '#FF375F' },  // systemPink
  '-':     { light: '#8E8E93', dark: '#8E8E93' },  // systemGray
  PENDENTE:{ light: '#FF9500', dark: '#FF9F0A' },  // systemOrange
};

/** Cores por categoria (design system v2) */
export const CATEGORY_COLORS: Record<string, { light: string; dark: string }> = {
  'Alimentação':                    { light: '#FF9500', dark: '#FF9F0A' },  // systemOrange
  'Supermercado':                   { light: '#34C759', dark: '#30D158' },  // systemGreen
  'Assinaturas e Serviços Digitais':{ light: '#5856D6', dark: '#5E5CE6' },  // systemIndigo
  'Automotivo':                     { light: '#8E8E93', dark: '#8E8E93' },  // systemGray
  'Combustível':                    { light: '#FF9500', dark: '#FF9F0A' },  // systemOrange
  'Compras Online':                 { light: '#AF52DE', dark: '#BF5AF2' },  // systemPurple
  'Educação':                       { light: '#007AFF', dark: '#0A84FF' },  // systemBlue
  'Estacionamento e Transporte':    { light: '#5AC8FA', dark: '#64D2FF' },  // systemTeal
  'Farmácia e Saúde':               { light: '#FF2D55', dark: '#FF375F' },  // systemPink
  'Lazer e Entretenimento':         { light: '#FF9500', dark: '#FF9F0A' },  // systemOrange
  'Moradia':                        { light: '#34C759', dark: '#30D158' },  // systemGreen
  'Pets':                           { light: '#FFCC00', dark: '#FFD60A' },  // systemYellow
  'Seguros':                        { light: '#5AC8FA', dark: '#64D2FF' },  // systemTeal
  'Serviços Pessoais (Estética)':   { light: '#AF52DE', dark: '#BF5AF2' },  // systemPurple
  'Transferências Pessoais':        { light: '#007AFF', dark: '#0A84FF' },  // systemBlue
  'Vestuário':                      { light: '#FF2D55', dark: '#FF375F' },  // systemPink
  'Tarifas Bancárias':              { light: '#8E8E93', dark: '#8E8E93' },  // systemGray
  'Outros':                         { light: '#8E8E93', dark: '#8E8E93' },  // systemGray
};

/** Helper: pega a cor correta pro tema */
export function getCategoryColor(name: string, isDark: boolean): string {
  const entry = CATEGORY_COLORS[name];
  if (!entry) return isDark ? '#8E8E93' : '#8E8E93';
  return isDark ? entry.dark : entry.light;
}

export function getMemberColor(name: string, isDark: boolean): string {
  const entry = MEMBER_COLORS[name];
  if (!entry) return isDark ? '#8E8E93' : '#8E8E93';
  return isDark ? entry.dark : entry.light;
}

/** Cores por banco */
export const BANK_COLORS: Record<string, string> = {
  bv: '#00A651',
  itau: '#003399',
  nubank: '#820AD1',
};
