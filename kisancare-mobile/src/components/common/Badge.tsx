import React from 'react';
import { View, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

interface BadgeProps {
  label: string;
  variant?: 'success' | 'warning' | 'info' | 'error' | 'neutral';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'success',
  size = 'md',
}) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const getColors = (): { bg: string; text: string } => {
    switch (variant) {
      case 'warning':
        return { bg: theme.warningLight, text: theme.warning };
      case 'info':
        return { bg: theme.infoLight, text: theme.info };
      case 'error':
        return { bg: theme.errorLight, text: theme.error };
      case 'neutral':
        return {
          bg: colorScheme === 'dark' ? '#2A362C' : '#E8EDE9',
          text: theme.textSecondary,
        };
      case 'success':
      default:
        return { bg: theme.successLight, text: theme.success };
    }
  };

  const { bg, text } = getColors();

  const isSmall = size === 'sm';
  const containerStyle: ViewStyle = {
    backgroundColor: bg,
    paddingHorizontal: isSmall ? Spacing.two : Spacing.three,
    paddingVertical: isSmall ? Spacing.half : Spacing.one,
  };

  const textStyle: TextStyle = {
    color: text,
    fontSize: isSmall ? Typography.sizes.xs : Typography.sizes.sm,
  };

  return (
    <View style={[styles.badge, containerStyle]}>
      <Text style={[styles.text, textStyle]}>{label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    borderRadius: BorderRadius.pill,
    alignSelf: 'flex-start',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontWeight: Typography.weights.semibold,
  },
});
