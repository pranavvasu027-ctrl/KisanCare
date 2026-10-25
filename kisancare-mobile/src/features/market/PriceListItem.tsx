import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { MarketPriceItem } from '@/types';

interface PriceListItemProps {
  item: MarketPriceItem;
}

export const PriceListItem: React.FC<PriceListItemProps> = ({ item }) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const isUp = item.trend === 'up';
  const isDown = item.trend === 'down';
  const trendColor = isUp ? theme.primary : isDown ? theme.error : theme.textSecondary;
  const trendIcon = isUp ? 'trending-up' : isDown ? 'trending-down' : 'remove';

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.surface,
          borderColor: theme.borderLight,
        },
      ]}
    >
      <View style={styles.leftGroup}>
        <View style={[styles.cropAvatar, { backgroundColor: theme.primaryContainer }]}>
          <Ionicons name="leaf" size={20} color={theme.primary} />
        </View>
        <View style={styles.cropDetails}>
          <Text style={[styles.cropName, { color: theme.text }]}>
            {item.cropName}
            {item.variety ? (
              <Text style={[styles.variety, { color: theme.textSecondary }]}>
                {' '}
                ({item.variety})
              </Text>
            ) : null}
          </Text>
          <Text style={[styles.mandiName, { color: theme.textSecondary }]}>
            {item.marketName}
          </Text>
        </View>
      </View>

      <View style={styles.rightGroup}>
        <Text style={[styles.price, { color: theme.text }]}>
          ₹{item.currentPrice.toLocaleString('en-IN')}
          <Text style={[styles.unit, { color: theme.textSecondary }]}>
            /{item.unit}
          </Text>
        </Text>
        <View style={styles.trendRow}>
          <Ionicons name={trendIcon} size={14} color={trendColor} />
          <Text style={[styles.changeText, { color: trendColor }]}>
            {isUp ? '+' : ''}
            {item.changeAmount} ({item.changePercentage}%)
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderRadius: BorderRadius.card,
    padding: Spacing.four,
    marginBottom: Spacing.three,
    borderWidth: 1,
  },
  leftGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  cropAvatar: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.three,
  },
  cropDetails: {
    flex: 1,
  },
  cropName: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
  },
  variety: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.normal,
  },
  mandiName: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
  rightGroup: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
  },
  unit: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.normal,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  changeText: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.semibold,
    marginLeft: 2,
  },
});
