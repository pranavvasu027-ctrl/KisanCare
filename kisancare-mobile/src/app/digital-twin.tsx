import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { ScreenContainer } from '@/components/common/ScreenContainer';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { fetchFarms } from '@/services/farmService';
import { apiClient } from '@/services/apiClient';

export default function DigitalTwinScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();

  const { data: farmsData } = useQuery({
    queryKey: ['farms'],
    queryFn: fetchFarms,
  });

  const activeFarm = farmsData?.farms?.[0];
  const farmId = activeFarm?.id || 'F001';
  const farmName = activeFarm?.name || 'Takli Bu Farm';
  const cropName = activeFarm?.activeCrop || 'Cotton';

  const { data: dtData, isLoading, refetch } = useQuery({
    queryKey: ['digital-twin', farmId],
    queryFn: () => apiClient.get<any>(`/api/v1/digital-twin/${farmId}`),
  });

  const healthScore = dtData?.healthScore ?? 88;
  const soilMoisture = Math.round((dtData?.state?.soil_moisture ?? 0.45) * 100);
  const temp = dtData?.climate?.temperature ?? 28;
  const condition = dtData?.climate?.weather_condition ?? 'Sunny';

  const phenologyStages = [
    { name: 'Sowing & Germination', days: 'Day 1-10', status: 'Completed', active: false },
    { name: 'Vegetative Growth', days: 'Day 11-45', status: 'Completed', active: false },
    { name: 'Flowering & Boll/Pod Set', days: 'Day 46-75', status: 'Active Stage', active: true },
    { name: 'Boll Maturation / Filling', days: 'Day 76-110', status: 'Upcoming', active: false },
    { name: 'Harvest Window', days: 'Day 111-140', status: 'Upcoming', active: false },
  ];

  return (
    <ScreenContainer onRefresh={refetch}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>
          Farm Digital Twin Simulator
        </Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          Real-time biophysical simulation of crop phenology, root-zone depletion, and water stress
        </Text>
      </View>

      {/* Field Vigor & Health Status */}
      <Card variant="accent" style={styles.card}>
        <View style={styles.statusRow}>
          <View>
            <Text style={[styles.fieldName, { color: theme.text }]}>
              {farmName} • {cropName}
            </Text>
            <Text style={[styles.metaText, { color: theme.textSecondary }]}>
              {activeFarm?.location || 'Akola, Maharashtra'} • {activeFarm?.areaAcres || 5.2} Acres
            </Text>
          </View>
          <Badge label={`Vigor: ${healthScore}%`} variant="success" />
        </View>

        <View style={[styles.divider, { backgroundColor: theme.borderLight }]} />

        <View style={styles.metricsRow}>
          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
              Soil Moisture
            </Text>
            <Text style={[styles.metricVal, { color: theme.primary }]}>
              {soilMoisture}%
            </Text>
            <Text style={[styles.metricHint, { color: theme.textMuted }]}>
              Field Capacity: 75%
            </Text>
          </View>

          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
              Water Stress (CWSI)
            </Text>
            <Text style={[styles.metricVal, { color: theme.success }]}>
              0.16
            </Text>
            <Text style={[styles.metricHint, { color: theme.textMuted }]}>
              Safe Range &lt; 0.35
            </Text>
          </View>

          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
              Simulated Temp
            </Text>
            <Text style={[styles.metricVal, { color: theme.text }]}>
              {Math.round(temp)}°C
            </Text>
            <Text style={[styles.metricHint, { color: theme.textMuted }]}>
              {condition}
            </Text>
          </View>
        </View>
      </Card>

      {/* Crop Phenology Stage Progress */}
      <Text style={[styles.sectionTitle, { color: theme.text }]}>
        Phenology Progress ({cropName})
      </Text>
      <Card variant="outlined" style={styles.card}>
        {phenologyStages.map((stage, idx) => (
          <View key={stage.name} style={styles.timelineRow}>
            <View style={styles.timelineIndicator}>
              <View
                style={[
                  styles.circle,
                  {
                    backgroundColor: stage.active
                      ? theme.primary
                      : stage.status === 'Completed'
                      ? theme.success
                      : theme.border,
                  },
                ]}
              >
                {stage.status === 'Completed' && (
                  <Ionicons name="checkmark" size={12} color="#FFFFFF" />
                )}
                {stage.active && <View style={styles.innerDot} />}
              </View>
              {idx < phenologyStages.length - 1 && (
                <View
                  style={[
                    styles.line,
                    {
                      backgroundColor:
                        stage.status === 'Completed' ? theme.success : theme.borderLight,
                    },
                  ]}
                />
              )}
            </View>
            <View style={styles.timelineContent}>
              <View style={styles.timelineHeader}>
                <Text style={[styles.stageName, { color: theme.text }]}>
                  {stage.name}
                </Text>
                <Badge
                  label={stage.status}
                  variant={stage.active ? 'info' : stage.status === 'Completed' ? 'success' : 'neutral'}
                  size="sm"
                />
              </View>
              <Text style={[styles.stageDays, { color: theme.textSecondary }]}>
                {stage.days}
              </Text>
            </View>
          </View>
        ))}
      </Card>

      <Button
        title="Return to My Farm"
        onPress={() => router.back()}
        variant="outline"
        icon="arrow-back"
        style={{ marginTop: Spacing.four }}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingVertical: Spacing.three,
  },
  title: {
    fontSize: Typography.sizes.xl,
    fontWeight: Typography.weights.bold,
  },
  subtitle: {
    fontSize: Typography.sizes.sm,
    marginTop: 4,
    lineHeight: 18,
  },
  card: {
    marginBottom: Spacing.four,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  fieldName: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
  },
  metaText: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
  divider: {
    height: 1,
    marginVertical: Spacing.three,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricItem: {
    flex: 1,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 11,
    marginBottom: 4,
  },
  metricVal: {
    fontSize: Typography.sizes.lg,
    fontWeight: Typography.weights.bold,
  },
  metricHint: {
    fontSize: 9,
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    marginBottom: Spacing.two,
  },
  timelineRow: {
    flexDirection: 'row',
    minHeight: 52,
  },
  timelineIndicator: {
    alignItems: 'center',
    width: 24,
    marginRight: Spacing.three,
  },
  circle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  innerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FFFFFF',
  },
  line: {
    width: 2,
    flex: 1,
    marginVertical: 2,
  },
  timelineContent: {
    flex: 1,
    paddingBottom: Spacing.three,
  },
  timelineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stageName: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.semibold,
  },
  stageDays: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
});
