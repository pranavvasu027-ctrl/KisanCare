import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { ScreenContainer } from '@/components/common/ScreenContainer';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import {
  assessSoilNutrients,
  computeNutrientBreakdown,
  SoilNutrientStatus,
} from '@/services/soilService';
import { SoilAssessmentResponse } from '@/types';
import { t } from '@/utils/localization';

export default function SoilReportScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();

  // Soil Nutrient Inputs
  const [nitrogen, setNitrogen] = useState<string>('120');
  const [phosphorus, setPhosphorus] = useState<string>('35');
  const [potassium, setPotassium] = useState<string>('180');
  const [ph, setPh] = useState<string>('6.8');

  // API State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<SoilAssessmentResponse | null>(null);
  const [nutrients, setNutrients] = useState<SoilNutrientStatus[]>([]);

  // Initial assessment on mount
  useEffect(() => {
    handleAssessSoil();
  }, []);

  const handleAssessSoil = async () => {
    const nNum = parseFloat(nitrogen);
    const pNum = parseFloat(phosphorus);
    const kNum = parseFloat(potassium);
    const phNum = parseFloat(ph);

    if (isNaN(nNum) || nNum < 0) {
      setError('Nitrogen (N) must be a positive number.');
      return;
    }
    if (isNaN(pNum) || pNum < 0) {
      setError('Phosphorus (P) must be a positive number.');
      return;
    }
    if (isNaN(kNum) || kNum < 0) {
      setError('Potassium (K) must be a positive number.');
      return;
    }
    if (isNaN(phNum) || phNum < 0 || phNum > 14) {
      setError('Soil pH must be between 0 and 14.');
      return;
    }

    setIsLoading(true);
    setError(null);

    const payload = { n: nNum, p: pNum, k: kNum, ph: phNum };
    setNutrients(computeNutrientBreakdown(payload));

    try {
      const res = await assessSoilNutrients(payload);
      setAssessment(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to evaluate soil nutrients with server.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScreenContainer>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>
          {t('soil.title')}
        </Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          {t('soil.subtitle')}
        </Text>
      </View>

      {/* Input Parameters Form Card */}
      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons name="flask-outline" size={20} color={theme.primary} />
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            Soil Test Parameters
          </Text>
        </View>

        <View style={styles.inputGrid}>
          {/* Nitrogen */}
          <View style={styles.inputCol}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
              {t('soil.nLabel')}
            </Text>
            <TextInput
              style={[
                styles.textInput,
                { backgroundColor: theme.backgroundElement, color: theme.text, borderColor: theme.border },
              ]}
              value={nitrogen}
              onChangeText={setNitrogen}
              keyboardType="numeric"
              placeholder="e.g. 120"
              placeholderTextColor={theme.textSecondary}
            />
          </View>

          {/* Phosphorus */}
          <View style={styles.inputCol}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
              {t('soil.pLabel')}
            </Text>
            <TextInput
              style={[
                styles.textInput,
                { backgroundColor: theme.backgroundElement, color: theme.text, borderColor: theme.border },
              ]}
              value={phosphorus}
              onChangeText={setPhosphorus}
              keyboardType="numeric"
              placeholder="e.g. 35"
              placeholderTextColor={theme.textSecondary}
            />
          </View>

          {/* Potassium */}
          <View style={styles.inputCol}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
              {t('soil.kLabel')}
            </Text>
            <TextInput
              style={[
                styles.textInput,
                { backgroundColor: theme.backgroundElement, color: theme.text, borderColor: theme.border },
              ]}
              value={potassium}
              onChangeText={setPotassium}
              keyboardType="numeric"
              placeholder="e.g. 180"
              placeholderTextColor={theme.textSecondary}
            />
          </View>

          {/* pH */}
          <View style={styles.inputCol}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
              {t('soil.phLabel')}
            </Text>
            <TextInput
              style={[
                styles.textInput,
                { backgroundColor: theme.backgroundElement, color: theme.text, borderColor: theme.border },
              ]}
              value={ph}
              onChangeText={setPh}
              keyboardType="numeric"
              placeholder="e.g. 6.8"
              placeholderTextColor={theme.textSecondary}
            />
          </View>
        </View>

        <Button
          title={isLoading ? t('soil.loading') : t('soil.evaluateBtn')}
          onPress={handleAssessSoil}
          disabled={isLoading}
          icon={isLoading ? undefined : 'analytics-outline'}
          style={{ marginTop: Spacing.four }}
        />
      </Card>

      {/* Loading Indicator */}
      {isLoading && (
        <View style={styles.loadingBox}>
          <ActivityIndicator size="large" color={theme.primary} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            {t('soil.loading')}
          </Text>
        </View>
      )}

      {/* Error Card */}
      {!isLoading && error && (
        <Card variant="flat" style={[styles.errorCard, { borderColor: theme.error }]}>
          <View style={styles.errorRow}>
            <Ionicons name="alert-circle" size={24} color={theme.error} />
            <View style={{ marginLeft: Spacing.two, flex: 1 }}>
              <Text style={[styles.errorTitle, { color: theme.error }]}>Evaluation Error</Text>
              <Text style={[styles.errorMsg, { color: theme.textSecondary }]}>{error}</Text>
            </View>
          </View>
          <Button
            title="Retry Evaluation"
            variant="outline"
            size="sm"
            onPress={handleAssessSoil}
            style={{ marginTop: Spacing.two }}
          />
        </Card>
      )}

      {/* Assessment Outcome */}
      {!isLoading && assessment && (
        <View>
          {/* Provenance Banner */}
          <View style={styles.provenancePill}>
            <Ionicons name="shield-checkmark-outline" size={16} color={theme.primary} />
            <Text style={[styles.provenanceText, { color: theme.textSecondary }]}>
              {t('soil.provenanceNotice')}
            </Text>
          </View>

          {/* Status & Recommendation Card */}
          <Card
            variant={assessment.overall_status === 'Healthy' ? 'accent' : 'elevated'}
            style={styles.card}
          >
            <View style={styles.statusHeader}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.statusSubtitle, { color: theme.textSecondary }]}>
                  {t('soil.statusTitle')}
                </Text>
                <Text style={[styles.statusMain, { color: theme.text }]}>
                  {assessment.overall_status}
                </Text>
              </View>
              <Badge
                label={assessment.overall_status}
                variant={assessment.overall_status === 'Healthy' ? 'success' : 'warning'}
                size="md"
              />
            </View>

            {/* Issues */}
            <View style={{ marginTop: Spacing.three }}>
              <Text style={[styles.sectionSubtitle, { color: theme.textSecondary }]}>
                {t('soil.issuesTitle')}:
              </Text>
              <View style={styles.issuesWrap}>
                {assessment.issues.map((issue, idx) => (
                  <Badge
                    key={idx}
                    label={issue}
                    variant={issue.toLowerCase().includes('optimal') ? 'success' : 'warning'}
                    size="sm"
                  />
                ))}
              </View>
            </View>

            {/* Recommendation */}
            <View style={{ marginTop: Spacing.three }}>
              <Text style={[styles.sectionSubtitle, { color: theme.textSecondary }]}>
                {t('soil.recommendationTitle')}:
              </Text>
              <Text style={[styles.recBody, { color: theme.text }]}>
                {assessment.recommendation}
              </Text>
            </View>
          </Card>

          {/* Nutrient Breakdown Grid */}
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            {t('soil.benchmarksTitle')}
          </Text>

          <Card style={styles.card}>
            {nutrients.map((item, idx) => (
              <View
                key={item.name}
                style={[
                  styles.nutrientRow,
                  idx !== nutrients.length - 1 && { borderBottomColor: theme.borderLight, borderBottomWidth: 1 },
                ]}
              >
                <View style={{ flex: 1 }}>
                  <Text style={[styles.nutrientName, { color: theme.text }]}>
                    {item.name} ({item.chemicalSymbol})
                  </Text>
                  <Text style={[styles.nutrientVal, { color: theme.textSecondary }]}>
                    Value: {item.value} {item.unit} • Benchmark: {item.benchmark}
                  </Text>
                  <Text style={[styles.nutrientDesc, { color: theme.textSecondary }]}>
                    {item.description}
                  </Text>
                </View>
                <Badge
                  label={item.rating}
                  variant={item.rating === 'Optimal' ? 'success' : 'warning'}
                  size="sm"
                />
              </View>
            ))}
          </Card>
        </View>
      )}

      {/* Back button */}
      <Button
        title={t('common.back')}
        onPress={() => router.back()}
        variant="outline"
        icon="arrow-back"
        style={{ marginTop: Spacing.two, marginBottom: Spacing.six }}
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
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.three,
  },
  cardTitle: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    marginLeft: Spacing.two,
  },
  inputGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  inputCol: {
    width: '48%',
    marginBottom: Spacing.three,
  },
  inputLabel: {
    fontSize: Typography.sizes.xs,
    marginBottom: Spacing.one,
    fontWeight: '600',
  },
  textInput: {
    height: 44,
    borderWidth: 1,
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.three,
    fontSize: Typography.sizes.sm,
  },
  loadingBox: {
    padding: Spacing.six,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: Spacing.two,
    fontSize: Typography.sizes.sm,
  },
  errorCard: {
    padding: Spacing.three,
    marginBottom: Spacing.four,
    borderWidth: 1,
  },
  errorRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  errorTitle: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.bold,
  },
  errorMsg: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
  provenancePill: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.two,
    gap: 6,
  },
  provenanceText: {
    fontSize: Typography.sizes.xs,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusSubtitle: {
    fontSize: Typography.sizes.xs,
    textTransform: 'uppercase',
  },
  statusMain: {
    fontSize: Typography.sizes.lg,
    fontWeight: Typography.weights.bold,
    marginTop: 2,
  },
  sectionSubtitle: {
    fontSize: Typography.sizes.xs,
    fontWeight: '600',
    marginBottom: Spacing.one,
  },
  issuesWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.one,
  },
  recBody: {
    fontSize: Typography.sizes.sm,
    lineHeight: 20,
    fontWeight: '500',
  },
  sectionTitle: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    marginBottom: Spacing.two,
  },
  nutrientRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: Spacing.three,
  },
  nutrientName: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.bold,
  },
  nutrientVal: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
  nutrientDesc: {
    fontSize: Typography.sizes.xs,
    marginTop: 4,
    lineHeight: 16,
  },
});
