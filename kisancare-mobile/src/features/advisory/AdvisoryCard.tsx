import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { AdvisoryItem } from '@/types';
import { Button } from '@/components/common/Button';
import { useRouter } from 'expo-router';

type IconName = keyof typeof Ionicons.glyphMap;

interface AdvisoryCardProps {
  advisory: AdvisoryItem;
}

export const AdvisoryCard: React.FC<AdvisoryCardProps> = ({ advisory }) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();

  const getCategoryConfig = (): { icon: IconName; color: string; label: string } => {
    switch (advisory.category) {
      case 'irrigation':
        return { icon: 'water', color: theme.info, label: 'Irrigation' };
      case 'fertilizer':
        return { icon: 'flask', color: theme.primary, label: 'Fertilizer' };
      case 'pest':
        return { icon: 'warning', color: theme.error, label: 'Pest Alert' };
      case 'weather':
        return { icon: 'cloud-outline', color: '#0284C7', label: 'Weather Risk' };
      case 'soil':
        return { icon: 'leaf-outline', color: '#16A34A', label: 'Soil Nutrient' };
      case 'market':
      default:
        return { icon: 'trending-up', color: theme.accent, label: 'Market' };
    }
  };

  const { icon, color, label } = getCategoryConfig();

  const handleAction = () => {
    if (advisory.actionRoute) {
      router.push(advisory.actionRoute as any);
    }
  };

  return (
    <Card style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.categoryRow}>
          <View style={[styles.iconWrapper, { backgroundColor: `${color}18` }]}>
            <Ionicons name={icon} size={18} color={color} />
          </View>
          <Text style={[styles.categoryLabel, { color }]}>{label}</Text>
        </View>
        <Badge
          label={advisory.priority.toUpperCase()}
          variant={
            advisory.priority === 'urgent'
              ? 'error'
              : advisory.priority === 'recommended'
              ? 'warning'
              : 'info'
          }
          size="sm"
        />
      </View>

      <Text style={[styles.title, { color: theme.text }]}>
        {advisory.title}
      </Text>
      <Text style={[styles.description, { color: theme.textSecondary }]}>
        {advisory.description}
      </Text>

      {advisory.source && (
        <Text style={[styles.sourceText, { color: theme.textMuted }]}>
          Source: {advisory.source}
        </Text>
      )}

      <View style={styles.footerRow}>
        <View style={styles.timeGroup}>
          <Ionicons name="time-outline" size={14} color={theme.textMuted} />
          <Text style={[styles.timestamp, { color: theme.textMuted }]}>
            {advisory.timestamp}
          </Text>
        </View>
        {advisory.actionText && advisory.actionRoute ? (
          <Button
            title={advisory.actionText}
            onPress={handleAction}
            size="sm"
            variant="outline"
          />
        ) : null}
      </View>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    marginBottom: Spacing.four,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.two,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconWrapper: {
    width: 28,
    height: 28,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.two,
  },
  categoryLabel: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.bold,
  },
  title: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    marginBottom: Spacing.one,
  },
  description: {
    fontSize: Typography.sizes.sm,
    lineHeight: 20,
    marginBottom: Spacing.two,
  },
  sourceText: {
    fontSize: Typography.sizes.xs,
    fontStyle: 'italic',
    marginBottom: Spacing.three,
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#EBF1EC',
    paddingTop: Spacing.three,
  },
  timeGroup: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timestamp: {
    fontSize: Typography.sizes.xs,
    marginLeft: Spacing.one,
  },
});
