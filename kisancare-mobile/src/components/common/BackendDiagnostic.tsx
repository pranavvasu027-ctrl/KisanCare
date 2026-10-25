import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { checkBackendHealth, HealthCheckResult } from '@/services/healthService';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { ApiError } from '@/services/apiError';

export const BackendDiagnostic: React.FC = () => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const {
    data: health,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<HealthCheckResult, ApiError>({
    queryKey: ['backend-health'],
    queryFn: checkBackendHealth,
    retry: 1,
  });

  const getStatusBadge = () => {
    if (isLoading || isFetching) {
      return <Badge label="Connecting..." variant="info" size="sm" />;
    }
    if (isError) {
      if (error?.isTimeout) {
        return <Badge label="Request Timed Out" variant="error" size="sm" />;
      }
      if (error?.isNetworkError) {
        return <Badge label="Unreachable" variant="error" size="sm" />;
      }
      return <Badge label="Server Error" variant="warning" size="sm" />;
    }
    if (health?.isHealthy) {
      return <Badge label="Connected" variant="success" size="sm" />;
    }
    return <Badge label="Degraded" variant="warning" size="sm" />;
  };

  return (
    <Card variant="outlined" style={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.titleGroup}>
          <View style={[styles.iconCircle, { backgroundColor: theme.primaryContainer }]}>
            <Ionicons name="server-outline" size={18} color={theme.primary} />
          </View>
          <Text style={[styles.title, { color: theme.text }]}>
            Backend Connectivity
          </Text>
        </View>
        {getStatusBadge()}
      </View>

      <View style={styles.infoGrid}>
        <View style={styles.infoRow}>
          <Text style={[styles.label, { color: theme.textSecondary }]}>
            Active Base URL:
          </Text>
          <Text style={[styles.val, { color: theme.text }]} numberOfLines={1}>
            {health?.baseUrl || 'Auto-detecting...'}
          </Text>
        </View>

        {health && (
          <>
            <View style={styles.infoRow}>
              <Text style={[styles.label, { color: theme.textSecondary }]}>
                Backend Service:
              </Text>
              <Text style={[styles.val, { color: theme.text }]}>
                {health.serviceName}
              </Text>
            </View>

            <View style={styles.infoRow}>
              <Text style={[styles.label, { color: theme.textSecondary }]}>
                Roundtrip Latency:
              </Text>
              <Text style={[styles.val, { color: theme.primary, fontWeight: '700' }]}>
                {health.latencyMs} ms
              </Text>
            </View>

            {health.copilotModel && (
              <View style={styles.infoRow}>
                <Text style={[styles.label, { color: theme.textSecondary }]}>
                  AI Copilot Engine:
                </Text>
                <Text style={[styles.val, { color: theme.text }]}>
                  {health.copilotModel} ({health.copilotReady ? 'Ready' : 'Unconfigured'})
                </Text>
              </View>
            )}
          </>
        )}

        {isError && (
          <View style={[styles.errorBox, { backgroundColor: theme.errorLight }]}>
            <Ionicons name="alert-circle" size={16} color={theme.error} />
            <Text style={[styles.errorText, { color: theme.error }]}>
              {error?.userFriendlyMessage || 'Connection failed'}
            </Text>
          </View>
        )}
      </View>

      <Button
        title={isFetching ? 'Pinging Server...' : 'Test Connection'}
        onPress={() => refetch()}
        variant="secondary"
        size="sm"
        icon="refresh"
        loading={isFetching}
        style={styles.retryButton}
      />
    </Card>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: Spacing.four,
    marginBottom: Spacing.four,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.three,
  },
  titleGroup: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconCircle: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.two,
  },
  title: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.bold,
  },
  infoGrid: {
    marginBottom: Spacing.three,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 3,
  },
  label: {
    fontSize: Typography.sizes.xs,
  },
  val: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.medium,
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.two,
    borderRadius: BorderRadius.sm,
    marginTop: Spacing.two,
  },
  errorText: {
    fontSize: Typography.sizes.xs,
    marginLeft: Spacing.one,
    flex: 1,
  },
  retryButton: {
    marginTop: Spacing.one,
  },
});
