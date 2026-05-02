/**
 * SwipeableRow — iOS-style swipe-to-delete row component.
 *
 * Wraps children in a Swipeable container from react-native-gesture-handler.
 * Swiping left reveals a red "Excluir" action button.
 * Tapping the row itself should trigger edit/detail (handled by parent).
 */
import React, { useRef } from 'react';
import { View, Text, StyleSheet, Pressable, Animated } from 'react-native';
import { Swipeable, RectButton } from 'react-native-gesture-handler';
import Ionicons from '@expo/vector-icons/Ionicons';

interface SwipeableRowProps {
  children: React.ReactNode;
  onDelete: () => void;
  enabled?: boolean;
}

export function SwipeableRow({ children, onDelete, enabled = true }: SwipeableRowProps) {
  const swipeableRef = useRef<Swipeable>(null);

  const renderRightActions = (
    progress: Animated.AnimatedInterpolation<number>,
    _dragX: Animated.AnimatedInterpolation<number>,
  ) => {
    const translateX = progress.interpolate({
      inputRange: [0, 1],
      outputRange: [80, 0],
      extrapolate: 'clamp',
    });

    return (
      <View style={styles.actionsContainer}>
        <Animated.View style={[styles.actionWrapper, { transform: [{ translateX }] }]}>
          <RectButton
            style={styles.deleteAction}
            onPress={() => {
              swipeableRef.current?.close();
              onDelete();
            }}
          >
            <Ionicons name="trash" size={20} color="#fff" />
            <Text style={styles.deleteText}>Excluir</Text>
          </RectButton>
        </Animated.View>
      </View>
    );
  };

  if (!enabled) {
    return <>{children}</>;
  }

  return (
    <Swipeable
      ref={swipeableRef}
      friction={2}
      overshootRight={false}
      rightThreshold={40}
      renderRightActions={renderRightActions}
    >
      {children}
    </Swipeable>
  );
}

const styles = StyleSheet.create({
  actionsContainer: {
    width: 80,
  },
  actionWrapper: {
    flex: 1,
  },
  deleteAction: {
    flex: 1,
    backgroundColor: '#FF3B30',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 4,
  },
  deleteText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
});
