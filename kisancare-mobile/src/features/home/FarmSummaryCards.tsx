import React from 'react';
import { View, StyleSheet } from 'react-native';
import { MetricCard } from '@/components/common/MetricCard';
import { Spacing } from '@/constants/theme';
import { t } from '@/utils/localization';

interface FarmSummaryCardsProps {
  totalAcres?: number;
  currentCrop?: string;
  sowingDate?: string;
  growthStage?: string;
  expectedHarvest?: string;
}

export const FarmSummaryCards: React.FC<FarmSummaryCardsProps> = ({
  totalAcres = 5.2,
  currentCrop = 'Soybean & Onion',
  sowingDate = '15 Jan 2026',
  growthStage = 'Pod Development',
  expectedHarvest = '25 Apr 2026',
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.row}>
        <MetricCard
          icon="map-outline"
          label={t('dashboard.totalArea')}
          value={totalAcres.toString()}
          unit={t('dashboard.acres')}
          subValue="2 Registered Fields"
        />
        <View style={styles.gap} />
        <MetricCard
          icon="leaf-outline"
          label={t('dashboard.activeCrop')}
          value={currentCrop}
          subValue={growthStage}
        />
      </View>

      <View style={[styles.row, styles.secondRow]}>
        <MetricCard
          icon="calendar-outline"
          label={t('dashboard.sowingDate')}
          value={sowingDate}
          subValue="98 Days Elapsed"
        />
        <View style={styles.gap} />
        <MetricCard
          icon="time-outline"
          label={t('dashboard.expectedHarvest')}
          value={expectedHarvest}
          subValue="Est. 88 Quintals"
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: Spacing.four,
  },
  row: {
    flexDirection: 'row',
  },
  secondRow: {
    marginTop: Spacing.three,
  },
  gap: {
    width: Spacing.three,
  },
});
