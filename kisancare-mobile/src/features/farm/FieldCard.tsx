import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { FieldItem } from '@/types';
import { useRouter } from 'expo-router';

interface FieldCardProps {
  field: FieldItem;
  onDigitalTwinPress?: () => void;
}

export const FieldCard: React.FC<FieldCardProps> = ({
  field,
  onDigitalTwinPress,
}) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();

  const handleTwin = () => {
    if (onDigitalTwinPress) {
      onDigitalTwinPress();
    } else {
      router.push('/digital-twin');
    }
  };

  return (
    <Card style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.titleGroup}>
          <Text style={[styles.fieldName, { color: theme.text }]}>
            {field.name}
          </Text>
          <Text style={[styles.cropText, { color: theme.textSecondary }]}>
            {field.crop} • {field.acres} Acres
          </Text>
        </View>
        <Badge
          label={`Health: ${field.healthScore}%`}
          variant={field.healthScore >= 80 ? 'success' : 'warning'}
        />
      </View>

      <View style={[styles.metricsContainer, { backgroundColor: theme.backgroundElement }]}>
        <View style={styles.metricItem}>
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
            Stage
          </Text>
          <Text style={[styles.metricVal, { color: theme.text }]}>
            {field.growthStage}
          </Text>
        </View>

        <View style={styles.metricDivider} />

        <View style={styles.metricItem}>
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
            Soil Moisture
          </Text>
          <Text style={[styles.metricVal, { color: theme.primary }]}>
            {field.soilMoisturePct}%
          </Text>
        </View>

        <View style={styles.metricDivider} />

        <View style={styles.metricItem}>
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
            Est. Harvest
          </Text>
          <Text style={[styles.metricVal, { color: theme.text }]}>
            {field.expectedHarvest}
          </Text>
        </View>
      </View>

      <View style={styles.actionRow}>
        <Button
          title="Digital Twin Simulation"
          onPress={handleTwin}
          variant="secondary"
          size="sm"
          icon="analytics-outline"
          style={{ flex: 1 }}
        />
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
    alignItems: 'flex-start',
    marginBottom: Spacing.three,
  },
  titleGroup: {
    flex: 1,
    paddingRight: Spacing.two,
  },
  fieldName: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
  },
  cropText: {
    fontSize: Typography.sizes.sm,
    marginTop: 2,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.three,
    marginVertical: Spacing.two,
  },
  metricItem: {
    alignItems: 'center',
    flex: 1,
  },
  metricLabel: {
    fontSize: 11,
    marginBottom: 4,
  },
  metricVal: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.bold,
  },
  metricDivider: {
    width: 1,
    height: '80%',
    backgroundColor: '#D1DDD3',
    alignSelf: 'center',
  },
  actionRow: {
    marginTop: Spacing.three,
  },
});
