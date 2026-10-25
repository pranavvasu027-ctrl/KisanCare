import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Colors, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { WeatherData } from '@/types';
import { t } from '@/utils/localization';

interface WeatherCardProps {
  weather?: WeatherData;
  onPress?: () => void;
}

const defaultWeather: WeatherData = {
  temperature: 28,
  condition: 'Partly Cloudy',
  humidity: 64,
  windSpeed: 12,
  rainfallMm: 0,
  location: 'Pune, Maharashtra',
  riskLevel: 'low',
  riskMessage: 'Optimal weather for field operations',
};

export const WeatherCard: React.FC<WeatherCardProps> = ({
  weather = defaultWeather,
  onPress,
}) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  return (
    <Card onPress={onPress} style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.locationContainer}>
          <Ionicons name="location-sharp" size={16} color={theme.primary} />
          <Text style={[styles.locationText, { color: theme.textSecondary }]}>
            {weather.location}
          </Text>
        </View>
        <Badge
          label={t('dashboard.weatherRisk')}
          variant={weather.riskLevel === 'high' ? 'error' : weather.riskLevel === 'moderate' ? 'warning' : 'success'}
          size="sm"
        />
      </View>

      <View style={styles.mainWeatherRow}>
        <View style={styles.tempGroup}>
          <Text style={[styles.tempText, { color: theme.text }]}>
            {weather.temperature}°C
          </Text>
          <Text style={[styles.conditionText, { color: theme.textSecondary }]}>
            {weather.condition}
          </Text>
        </View>
        <View style={[styles.weatherIconCircle, { backgroundColor: theme.primaryContainer }]}>
          <Ionicons name="partly-sunny" size={36} color={theme.primary} />
        </View>
      </View>

      <View style={[styles.metricsRow, { borderColor: theme.borderLight }]}>
        <View style={styles.metricItem}>
          <Ionicons name="water-outline" size={16} color={theme.info} />
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
            {t('dashboard.humidity')}:
          </Text>
          <Text style={[styles.metricValue, { color: theme.text }]}>
            {weather.humidity}%
          </Text>
        </View>

        <View style={styles.metricDivider} />

        <View style={styles.metricItem}>
          <Ionicons name="speedometer-outline" size={16} color={theme.accent} />
          <Text style={[styles.metricLabel, { color: theme.textSecondary }]}>
            {t('dashboard.wind')}:
          </Text>
          <Text style={[styles.metricValue, { color: theme.text }]}>
            {weather.windSpeed} km/h
          </Text>
        </View>
      </View>

      <View style={[styles.advisoryBanner, { backgroundColor: theme.primaryContainer }]}>
        <Ionicons name="information-circle-outline" size={16} color={theme.primary} />
        <Text style={[styles.advisoryText, { color: theme.primaryDark }]} numberOfLines={1}>
          {weather.riskMessage}
        </Text>
      </View>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    paddingVertical: Spacing.four,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.three,
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  locationText: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.medium,
    marginLeft: Spacing.one,
  },
  mainWeatherRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: Spacing.one,
  },
  tempGroup: {
    justifyContent: 'center',
  },
  tempText: {
    fontSize: 34,
    fontWeight: Typography.weights.bold,
    letterSpacing: -1,
  },
  conditionText: {
    fontSize: Typography.sizes.md,
    marginTop: Spacing.half,
  },
  weatherIconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    paddingTop: Spacing.three,
    marginTop: Spacing.three,
  },
  metricItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: Typography.sizes.xs,
    marginLeft: Spacing.one,
    marginRight: Spacing.half,
  },
  metricValue: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.bold,
  },
  metricDivider: {
    width: 1,
    height: 16,
    backgroundColor: '#E0EAE1',
  },
  advisoryBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 8,
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.two,
    marginTop: Spacing.three,
  },
  advisoryText: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.medium,
    marginLeft: Spacing.two,
    flex: 1,
  },
});
