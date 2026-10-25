import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function AdvisoryScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const [activeFilter, setActiveFilter] = useState<'current' | '14days' | 'season'>('current');

  return (
    <View style={styles.screenWrapper}>
      {/* Top Header matching Screen 4 of UIs.png */}
      <View style={styles.topHeader}>
        <View style={styles.headerTitleRow}>
          <Ionicons name="bulb" size={22} color="#16A34A" />
          <Text style={styles.headerTitle}>AI Recommendations</Text>
        </View>

        <TouchableOpacity style={styles.searchButton} activeOpacity={0.7}>
          <Ionicons name="search" size={20} color="#1F2937" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Filter Pills: Current Advisory | Next 14 Days | Season Plan */}
        <View style={styles.filterPillRow}>
          <TouchableOpacity
            style={[
              styles.filterPill,
              activeFilter === 'current' && styles.filterPillActive,
            ]}
            onPress={() => setActiveFilter('current')}
          >
            <Text
              style={[
                styles.filterPillText,
                activeFilter === 'current' && styles.filterPillTextActive,
              ]}
            >
              Current Advisory
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.filterPill,
              activeFilter === '14days' && styles.filterPillActive,
            ]}
            onPress={() => setActiveFilter('14days')}
          >
            <Text
              style={[
                styles.filterPillText,
                activeFilter === '14days' && styles.filterPillTextActive,
              ]}
            >
              Next 14 Days
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.filterPill,
              activeFilter === 'season' && styles.filterPillActive,
            ]}
            onPress={() => setActiveFilter('season')}
          >
            <Text
              style={[
                styles.filterPillText,
                activeFilter === 'season' && styles.filterPillTextActive,
              ]}
            >
              Season Plan
            </Text>
          </TouchableOpacity>
        </View>

        {/* Hero Card: Recommended Action matching Screen 4 */}
        <TouchableOpacity
          style={styles.heroActionCard}
          onPress={() => router.push('/crop-health')}
          activeOpacity={0.88}
        >
          <View style={styles.heroActionTop}>
            <View style={styles.leafIconBadge}>
              <Ionicons name="leaf" size={20} color="#16A34A" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.heroCategoryLabel}>Recommended Action</Text>
              <Text style={styles.heroActionHeadline}>
                Apply first top dressing of urea for soybean
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color="#16A34A" />
          </View>

          <View style={styles.heroDivider} />

          <View style={styles.metricsRow}>
            <View>
              <Text style={styles.metricBenefitLabel}>Expected Benefit</Text>
              <Text style={styles.metricBenefitValue}>+18%</Text>
              <Text style={styles.metricBenefitSub}>Better yield potential</Text>
            </View>

            <View style={styles.confidenceCol}>
              <Text style={styles.confidenceLabel}>Confidence</Text>
              <Text style={styles.confidenceValue}>82%</Text>
              <View style={styles.progressBarTrack}>
                <View style={[styles.progressBarFill, { width: '82%' }]} />
              </View>
            </View>
          </View>
        </TouchableOpacity>

        {/* Informational Context Banner */}
        <View style={styles.infoBanner}>
          <Ionicons name="shield-checkmark" size={18} color="#EA580C" />
          <Text style={styles.infoBannerText}>
            Based on current soil condition, weather forecast and crop stage.
          </Text>
        </View>

        {/* AI Copilot Interactive Banner (Scope 6) */}
        <TouchableOpacity
          style={styles.copilotPromptBanner}
          onPress={() => router.push('/chatbot')}
          activeOpacity={0.88}
        >
          <Ionicons name="chatbubble-ellipses" size={20} color="#16A34A" />
          <Text style={styles.copilotPromptText}>
            Have questions? Ask KisanCare AI Copilot →
          </Text>
        </TouchableOpacity>

        {/* Action List Cards matching Screen 4 */}
        <View style={styles.actionList}>
          {/* 1. Irrigation */}
          <TouchableOpacity
            style={styles.actionItemCard}
            onPress={() => router.push('/crop-planning')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionItemIconBox, { backgroundColor: '#E0F2FE' }]}>
              <Ionicons name="water" size={22} color="#0284C7" />
            </View>
            <View style={styles.actionItemContent}>
              <Text style={styles.actionItemTitle}>Irrigation</Text>
              <Text style={styles.actionItemSubtitle}>Irrigate in next 3-4 days</Text>
            </View>
            <View style={[styles.priorityBadge, { backgroundColor: '#FEF9C3' }]}>
              <Text style={[styles.priorityBadgeText, { color: '#CA8A04' }]}>Medium</Text>
            </View>
          </TouchableOpacity>

          {/* 2. Pest Monitoring */}
          <TouchableOpacity
            style={styles.actionItemCard}
            onPress={() => router.push('/crop-health')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionItemIconBox, { backgroundColor: '#DCFCE7' }]}>
              <Ionicons name="bug" size={22} color="#16A34A" />
            </View>
            <View style={styles.actionItemContent}>
              <Text style={styles.actionItemTitle}>Pest Monitoring</Text>
              <Text style={styles.actionItemSubtitle}>Low risk at present</Text>
            </View>
            <View style={[styles.priorityBadge, { backgroundColor: '#DCFCE7' }]}>
              <Text style={[styles.priorityBadgeText, { color: '#16A34A' }]}>Low</Text>
            </View>
          </TouchableOpacity>

          {/* 3. Market Insight */}
          <TouchableOpacity
            style={styles.actionItemCard}
            onPress={() => router.push('/(tabs)/market')}
            activeOpacity={0.8}
          >
            <View style={[styles.actionItemIconBox, { backgroundColor: '#FFEDD5' }]}>
              <Ionicons name="trending-up" size={22} color="#EA580C" />
            </View>
            <View style={styles.actionItemContent}>
              <Text style={styles.actionItemTitle}>Market Insight</Text>
              <Text style={styles.actionItemSubtitle}>
                Soybean prices likely to increase by 8-12%
              </Text>
            </View>
            <View style={[styles.priorityBadge, { backgroundColor: '#FFEDD5' }]}>
              <Text style={[styles.priorityBadgeText, { color: '#EA580C' }]}>High</Text>
            </View>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screenWrapper: {
    flex: 1,
    backgroundColor: '#F8FAF8',
  },
  topHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 54,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
  },
  searchButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },
  filterPillRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  filterPill: {
    paddingVertical: 7,
    paddingHorizontal: 14,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  filterPillActive: {
    backgroundColor: '#16A34A',
    borderColor: '#16A34A',
  },
  filterPillText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  filterPillTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  heroActionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 14,
  },
  heroActionTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  leafIconBadge: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroCategoryLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  heroActionHeadline: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1E293B',
    marginTop: 2,
  },
  heroDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 14,
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  metricBenefitLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  metricBenefitValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#16A34A',
    marginTop: 2,
  },
  metricBenefitSub: {
    fontSize: 11,
    color: '#64748B',
  },
  confidenceCol: {
    width: 100,
  },
  confidenceLabel: {
    fontSize: 11,
    color: '#64748B',
    textAlign: 'right',
  },
  confidenceValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#16A34A',
    textAlign: 'right',
    marginTop: 2,
  },
  progressBarTrack: {
    height: 6,
    backgroundColor: '#E2E8F0',
    borderRadius: 3,
    marginTop: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#16A34A',
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFF7ED',
    borderRadius: 14,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FFEDD5',
  },
  infoBannerText: {
    flex: 1,
    fontSize: 12,
    color: '#C2410C',
    lineHeight: 18,
  },
  copilotPromptBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#F0FDF4',
    borderRadius: 14,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  copilotPromptText: {
    flex: 1,
    fontSize: 13,
    fontWeight: '700',
    color: '#16A34A',
  },
  actionList: {
    gap: 10,
  },
  actionItemCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  actionItemIconBox: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionItemContent: {
    flex: 1,
  },
  actionItemTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  actionItemSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  priorityBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
});
