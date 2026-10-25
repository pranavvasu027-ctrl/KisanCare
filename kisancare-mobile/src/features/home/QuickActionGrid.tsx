import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors, BorderRadius, Spacing, Typography, Shadows } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { t } from '@/utils/localization';

type IconName = keyof typeof Ionicons.glyphMap;

interface ActionItem {
  id: string;
  title: string;
  subtitle: string;
  icon: IconName;
  route: string;
  badge?: string;
  accentColor?: string;
}

export const QuickActionGrid: React.FC = () => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();

  const actions: ActionItem[] = [
    {
      id: 'crop-planning',
      title: t('actions.cropPlanning'),
      subtitle: t('actions.cropPlanningDesc'),
      icon: 'calculator-outline',
      route: '/crop-planning',
      accentColor: theme.primary,
    },
    {
      id: 'soil-report',
      title: t('actions.soilReport'),
      subtitle: t('actions.soilReportDesc'),
      icon: 'flask-outline',
      route: '/soil-report',
      accentColor: '#00796B',
    },
    {
      id: 'crop-health',
      title: t('actions.cropHealth'),
      subtitle: t('actions.cropHealthDesc'),
      icon: 'scan-outline',
      route: '/crop-health',
      badge: 'AI Vision',
      accentColor: '#D32F2F',
    },
    {
      id: 'market-prices',
      title: t('actions.marketPrices'),
      subtitle: t('actions.marketPricesDesc'),
      icon: 'trending-up-outline',
      route: '/(tabs)/market',
      accentColor: theme.accent,
    },
  ];

  return (
    <View style={styles.grid}>
      {actions.map((action) => (
        <TouchableOpacity
          key={action.id}
          style={[
            styles.actionCard,
            {
              backgroundColor: theme.surface,
              borderColor: theme.borderLight,
            },
          ]}
          onPress={() => router.push(action.route as any)}
          activeOpacity={0.7}
          accessible={true}
          accessibilityRole="button"
          accessibilityLabel={`${action.title}: ${action.subtitle}`}
        >
          <View style={styles.topRow}>
            <View
              style={[
                styles.iconContainer,
                { backgroundColor: theme.primaryContainer },
              ]}
            >
              <Ionicons
                name={action.icon}
                size={24}
                color={action.accentColor || theme.primary}
              />
            </View>
            {action.badge ? (
              <View
                style={[
                  styles.badgeContainer,
                  { backgroundColor: theme.primarySelected },
                ]}
              >
                <Text
                  style={[styles.badgeText, { color: theme.primaryDark }]}
                >
                  {action.badge}
                </Text>
              </View>
            ) : null}
          </View>

          <Text style={[styles.title, { color: theme.text }]} numberOfLines={1}>
            {action.title}
          </Text>
          <Text
            style={[styles.subtitle, { color: theme.textSecondary }]}
            numberOfLines={2}
          >
            {action.subtitle}
          </Text>

          <View style={styles.footerRow}>
            <Text style={[styles.arrowText, { color: theme.primary }]}>
              Open
            </Text>
            <Ionicons
              name="arrow-forward"
              size={14}
              color={theme.primary}
              style={{ marginLeft: 2 }}
            />
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: Spacing.four,
  },
  actionCard: {
    width: '48%',
    borderRadius: BorderRadius.card,
    padding: Spacing.three,
    marginBottom: Spacing.three,
    borderWidth: 1,
    ...Shadows.card,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: Spacing.two,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeContainer: {
    paddingHorizontal: Spacing.two,
    paddingVertical: 2,
    borderRadius: BorderRadius.pill,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: Typography.weights.bold,
  },
  title: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    marginBottom: 2,
  },
  subtitle: {
    fontSize: Typography.sizes.xs,
    lineHeight: 16,
    minHeight: 32,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.two,
  },
  arrowText: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.semibold,
  },
});
