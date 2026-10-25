import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, BorderRadius, Spacing, Typography, Shadows } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';

type IconName = keyof typeof Ionicons.glyphMap;

interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
  icon: IconName;
  color?: string;
  subValue?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  icon,
  color,
  subValue,
}) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const accentColor = color || theme.primary;

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.surface,
          borderColor: theme.borderLight,
        },
      ]}
    >
      <View style={styles.headerRow}>
        <View style={[styles.iconContainer, { backgroundColor: theme.primaryContainer }]}>
          <Ionicons name={icon} size={20} color={accentColor} />
        </View>
        <Text style={[styles.label, { color: theme.textSecondary }]} numberOfLines={1}>
          {label}
        </Text>
      </View>
      <View style={styles.valueRow}>
        <Text style={[styles.value, { color: theme.text }]}>
          {value}
          {unit ? <Text style={[styles.unit, { color: theme.textSecondary }]}> {unit}</Text> : null}
        </Text>
      </View>
      {subValue ? (
        <Text style={[styles.subValue, { color: theme.textMuted }]} numberOfLines={1}>
          {subValue}
        </Text>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: BorderRadius.card,
    padding: Spacing.three,
    borderWidth: 1,
    ...Shadows.card,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.two,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.two,
  },
  label: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.medium,
    flexShrink: 1,
  },
  valueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  value: {
    fontSize: Typography.sizes.lg,
    fontWeight: Typography.weights.bold,
  },
  unit: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.normal,
  },
  subValue: {
    fontSize: Typography.sizes.xs,
    marginTop: Spacing.half,
  },
});
