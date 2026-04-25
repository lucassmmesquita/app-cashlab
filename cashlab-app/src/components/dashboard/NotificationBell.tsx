/**
 * CashLab — NotificationBell (iOS Design System v2)
 *
 * Ícone de sino no header com badge de contagem.
 * Ao tocar, abre modal com lista de notificações agrupadas por tipo.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Modal,
  ScrollView,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';

import { useAppTheme } from '@/hooks/useAppTheme';
import type { Alert as AlertType } from '@/types/budget';

interface NotificationBellProps {
  notifications: AlertType[];
}

const ALERT_CONFIG: Record<string, { icon: string; label: string; colorKey: 'red' | 'orange' | 'green' | 'blue' }> = {
  critical: { icon: 'alert-circle', label: 'Crítico', colorKey: 'red' },
  warning: { icon: 'warning', label: 'Atenção', colorKey: 'orange' },
  info: { icon: 'information-circle', label: 'Info', colorKey: 'green' },
};

export function NotificationBell({ notifications }: NotificationBellProps) {
  const { colors, radius, spacing } = useAppTheme();
  const [visible, setVisible] = useState(false);

  const unreadCount = notifications.length;

  return (
    <>
      {/* ── Bell Icon ──────────────────────────────── */}
      <Pressable
        onPress={() => setVisible(true)}
        style={({ pressed }) => [
          styles.bellButton,
          { opacity: pressed ? 0.6 : 1 },
        ]}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <Ionicons name="notifications-outline" size={24} color={colors.label} />
        {unreadCount > 0 && (
          <View style={[styles.badge, { backgroundColor: colors.red }]}>
            <Text style={styles.badgeText}>
              {unreadCount > 9 ? '9+' : unreadCount}
            </Text>
          </View>
        )}
      </Pressable>

      {/* ── Modal ──────────────────────────────────── */}
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setVisible(false)}
      >
        <View style={[styles.modalContainer, { backgroundColor: colors.bg }]}>
          <SafeAreaView style={{ flex: 1 }} edges={['top']}>
            {/* Modal Header */}
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: colors.label }]}>
                Notificações
              </Text>
              <Pressable
                onPress={() => setVisible(false)}
                style={({ pressed }) => [
                  styles.closeButton,
                  { backgroundColor: colors.segmentBg, opacity: pressed ? 0.6 : 1 },
                ]}
              >
                <Ionicons name="close" size={18} color={colors.secondaryLabel} />
              </Pressable>
            </View>

            {/* Notification List */}
            <ScrollView
              contentContainerStyle={[styles.modalContent, { padding: spacing.lg }]}
              showsVerticalScrollIndicator={false}
            >
              {notifications.length === 0 ? (
                <View style={styles.emptyState}>
                  <View style={[styles.emptyIcon, { backgroundColor: `${colors.green}15` }]}>
                    <Ionicons name="checkmark-circle" size={48} color={colors.green} />
                  </View>
                  <Text style={[styles.emptyTitle, { color: colors.label }]}>
                    Tudo certo!
                  </Text>
                  <Text style={[styles.emptySub, { color: colors.secondaryLabel }]}>
                    Sem notificações no momento.
                  </Text>
                </View>
              ) : (
                <View style={[styles.notifCard, { backgroundColor: colors.surface, borderRadius: radius.lg }]}>
                  {notifications.map((notif, index) => {
                    const config = ALERT_CONFIG[notif.type] || ALERT_CONFIG.info;
                    const dotColor = colors[config.colorKey];

                    return (
                      <View key={index}>
                        {index > 0 && (
                          <View
                            style={[
                              styles.separator,
                              { backgroundColor: colors.separator, marginLeft: 52 },
                            ]}
                          />
                        )}
                        <View style={styles.notifRow}>
                          <View style={[styles.notifIconWrap, { backgroundColor: `${dotColor}15` }]}>
                            <Ionicons
                              name={config.icon as any}
                              size={20}
                              color={dotColor}
                            />
                          </View>
                          <View style={styles.notifBody}>
                            <Text style={[styles.notifLabel, { color: dotColor }]}>
                              {config.label}
                            </Text>
                            <Text style={[styles.notifMessage, { color: colors.label }]}>
                              {notif.message}
                            </Text>
                          </View>
                        </View>
                      </View>
                    );
                  })}
                </View>
              )}

              <View style={{ height: 40 }} />
            </ScrollView>
          </SafeAreaView>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  // Bell
  bellButton: {
    position: 'relative',
    padding: 4,
  },
  badge: {
    position: 'absolute',
    top: 0,
    right: 0,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
    lineHeight: 14,
  },

  // Modal
  modalContainer: { flex: 1 },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  modalTitle: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  closeButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: { gap: 12 },

  // Notification card
  notifCard: { overflow: 'hidden' },
  notifRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 14,
    paddingHorizontal: 16,
  },
  notifIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
  },
  notifBody: { flex: 1, gap: 2 },
  notifLabel: { fontSize: 12, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  notifMessage: { fontSize: 15, fontWeight: '500', lineHeight: 21 },
  separator: { height: 0.5 },

  // Empty state
  emptyState: { alignItems: 'center', paddingVertical: 60, gap: 12 },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  emptyTitle: { fontSize: 20, fontWeight: '700' },
  emptySub: { fontSize: 15 },
});
