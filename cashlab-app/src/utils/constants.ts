/**
 * CashLab — Constantes do app
 */

/** API host — para health check / wake-up */
export const API_HOST = __DEV__
  ? 'http://localhost:8000'
  : 'https://app-cashlab.onrender.com';

/** API base URL — ajustar para produção */
export const API_BASE_URL = `${API_HOST}/api/v1`;

/** Categorias do sistema (18 categorias) */
export const SYSTEM_CATEGORIES = [
  'Alimentação',
  'Assinaturas e Serviços Digitais',
  'Automotivo',
  'Combustível',
  'Compras Online',
  'Educação',
  'Estacionamento e Transporte',
  'Farmácia e Saúde',
  'Lazer e Entretenimento',
  'Moradia',
  'Pets',
  'Seguros',
  'Serviços Pessoais (Estética)',
  'Supermercado',
  'Transferências Pessoais',
  'Vestuário',
  'Tarifas Bancárias',
  'Outros',
] as const;

/** Membros da família */
export const FAMILY_MEMBERS = ['LUCAS', 'JURA', 'JOICE'] as const;

/** Bancos suportados */
export const SUPPORTED_BANKS = ['bv', 'itau', 'nubank'] as const;

/** Valores de QUEM válidos */
export const WHO_VALUES = ['LUCAS', 'JURA', 'JOICE', '-', 'PENDENTE'] as const;

/** Tamanhos de espaçamento (escala de 4pt) */
export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
} as const;
