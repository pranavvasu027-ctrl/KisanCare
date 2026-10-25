import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import { fetchFarms } from '@/services/farmService';
import { fetchLiveAdvisories } from '@/services/advisoryService';
import { getStoredProfile } from '@/services/profileService';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

const botAvatar = require('../../../assets/images/ui/bot_avatar.png');

export default function HomeScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const profile = getStoredProfile();
  const { data: farmsData } = useQuery({
    queryKey: ['farms'],
    queryFn: fetchFarms,
  });

  const { data: advisoriesBundle } = useQuery({
    queryKey: ['live-advisories'],
    queryFn: () => fetchLiveAdvisories(),
  });

  const liveWeather = advisoriesBundle?.weatherSummary;
  const tempDisplay = liveWeather?.temperature ? `${Math.round(liveWeather.temperature)}°C` : '31°C';
  const conditionDisplay = liveWeather?.condition || 'Sunny';
  const humidityDisplay = liveWeather?.humidity ? `${Math.round(liveWeather.humidity)}%` : '35%';
  const windDisplay = liveWeather?.windSpeed ? `${Math.round(liveWeather.windSpeed)} km/h` : '10 km/h';

  const activeFarm = farmsData?.farms?.[0];
  const activeCropName = activeFarm?.activeCrop || 'Cotton';
  const totalAcres = farmsData?.farms?.reduce((acc, f) => acc + f.areaAcres, 0) || 5.2;

  let daysSinceSowing = '45 days';
  if (activeFarm?.sowingDate) {
    const sown = new Date(activeFarm.sowingDate);
    const now = new Date();
    const diff = Math.floor((now.getTime() - sown.getTime()) / (1000 * 60 * 60 * 24));
    if (diff > 0 && diff < 365) {
      daysSinceSowing = `${diff} days`;
    }
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      <StatusBar style="dark" />

      {/* Top Header: Farmer Greeting, Location & Notification Bell */}
      <View style={styles.topHeader}>
        <View style={styles.userProfileRow}>
          <TouchableOpacity
            onPress={() => router.push('/profile')}
            activeOpacity={0.8}
            style={styles.avatarWrapper}
          >
            <Image
              source={require('../../../assets/images/ui/farmer_avatar.png')}
              style={styles.avatarImage}
            />
            <View style={styles.onlineBadge} />
          </TouchableOpacity>

          <View style={styles.greetingTextContainer}>
            <Text style={styles.greetingSub}>Good Morning,</Text>
            <Text style={styles.greetingName}>{profile.fullName || 'Farmer'}!</Text>
            <View style={styles.locationRow}>
              <Ionicons name="location-sharp" size={13} color="#16A34A" />
              <Text style={styles.locationText}>
                {profile.village || 'Pimpalgaon'}, {profile.district || 'Jalna'}
              </Text>
            </View>
          </View>
        </View>

        <TouchableOpacity
          style={styles.notificationButton}
          onPress={() => router.push('/(tabs)/advisory')}
          activeOpacity={0.7}
        >
          <Ionicons name="notifications-outline" size={22} color="#1F2937" />
          <View style={styles.notificationBadge} />
        </TouchableOpacity>
      </View>

      {/* Weather Card (Dark Slate / Navy Banner matching UIs.png) */}
      <TouchableOpacity
        style={styles.weatherCard}
        onPress={() => router.push('/(tabs)/advisory')}
        activeOpacity={0.9}
      >
        <View style={styles.weatherLeft}>
          <Ionicons
            name={conditionDisplay.toLowerCase().includes('rain') ? 'rainy' : conditionDisplay.toLowerCase().includes('cloud') ? 'partly-sunny' : 'sunny'}
            size={38}
            color="#FBBF24"
          />
          <View style={styles.weatherTempContainer}>
            <Text style={styles.weatherTemp}>{tempDisplay}</Text>
            <Text style={styles.weatherCondition}>{conditionDisplay}</Text>
          </View>
        </View>

        <View style={styles.weatherDivider} />

        <View style={styles.weatherRight}>
          <View style={styles.weatherMetricItem}>
            <Text style={styles.weatherMetricLabel}>Rain</Text>
            <Text style={styles.weatherMetricValue}>20%</Text>
          </View>
          <View style={styles.weatherMetricItem}>
            <Text style={styles.weatherMetricLabel}>Humidity</Text>
            <Text style={styles.weatherMetricValue}>{humidityDisplay}</Text>
          </View>
          <View style={styles.weatherMetricItem}>
            <Text style={styles.weatherMetricLabel}>Wind</Text>
            <Text style={styles.weatherMetricValue}>{windDisplay}</Text>
          </View>
        </View>
      </TouchableOpacity>

      {/* Farm Overview Card (2x2 Matrix matching UIs.png) */}
      <View style={styles.farmSummaryCard}>
        <View style={styles.summaryRow}>
          {/* Total Area */}
          <View style={styles.summaryItem}>
            <View style={[styles.summaryIconBox, { backgroundColor: '#E8F5E9' }]}>
              <Ionicons name="leaf-outline" size={20} color="#16A34A" />
            </View>
            <View>
              <Text style={styles.summaryValue}>{totalAcres} acres</Text>
              <Text style={styles.summaryLabel}>Total Area</Text>
            </View>
          </View>

          {/* Current Crop */}
          <View style={styles.summaryItem}>
            <View style={[styles.summaryIconBox, { backgroundColor: '#E8F5E9' }]}>
              <Ionicons name="flower-outline" size={20} color="#16A34A" />
            </View>
            <View>
              <Text style={styles.summaryValue}>{activeCropName}</Text>
              <Text style={styles.summaryLabel}>Current Crop</Text>
            </View>
          </View>
        </View>

        <View style={styles.summaryHorizontalDivider} />

        <View style={styles.summaryRow}>
          {/* Since Sowing */}
          <View style={styles.summaryItem}>
            <View style={[styles.summaryIconBox, { backgroundColor: '#E0F2FE' }]}>
              <Ionicons name="calendar-outline" size={20} color="#0284C7" />
            </View>
            <View>
              <Text style={styles.summaryValue}>{daysSinceSowing}</Text>
              <Text style={styles.summaryLabel}>Since Sowing</Text>
            </View>
          </View>

          {/* Expected Harvest */}
          <View style={styles.summaryItem}>
            <View style={[styles.summaryIconBox, { backgroundColor: '#F0FDF4' }]}>
              <Ionicons name="bar-chart-outline" size={20} color="#16A34A" />
            </View>
            <View>
              <Text style={styles.summaryValue}>Nov 2024</Text>
              <Text style={styles.summaryLabel}>Expected Harvest</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Section: Primary Feature Tiles (Scope 2, 3, 4, 5) */}
      <View style={styles.sectionHeaderRow}>
        <Text style={styles.sectionTitle}>Primary Features</Text>
      </View>

      <View style={styles.quickActionGrid}>
        {/* 1. Crop Planning (Crop Recommendation) */}
        <TouchableOpacity
          style={styles.actionTile}
          onPress={() => router.push('/crop-planning')}
          activeOpacity={0.8}
        >
          <View style={[styles.actionIconBox, { backgroundColor: '#E8F5E9' }]}>
            <Ionicons name="calendar" size={26} color="#16A34A" />
          </View>
          <Text style={styles.actionTileTitle}>Crop Planning</Text>
        </TouchableOpacity>

        {/* 2. Crop Health (Disease & Pest Detection) */}
        <TouchableOpacity
          style={styles.actionTile}
          onPress={() => router.push('/crop-health')}
          activeOpacity={0.8}
        >
          <View style={[styles.actionIconBox, { backgroundColor: '#FEE2E2' }]}>
            <Ionicons name="scan-outline" size={26} color="#DC2626" />
          </View>
          <Text style={styles.actionTileTitle}>Crop Health</Text>
        </TouchableOpacity>

        {/* 3. Market Prices (Market Intelligence) */}
        <TouchableOpacity
          style={styles.actionTile}
          onPress={() => router.push('/(tabs)/market')}
          activeOpacity={0.8}
        >
          <View style={[styles.actionIconBox, { backgroundColor: '#DCFCE7' }]}>
            <Ionicons name="trending-up" size={26} color="#16A34A" />
          </View>
          <Text style={styles.actionTileTitle}>Market Prices</Text>
        </TouchableOpacity>

        {/* 4. Equipment Rental (Equipment Rental Marketplace) */}
        <TouchableOpacity
          style={styles.actionTile}
          onPress={() => router.push('/rentals')}
          activeOpacity={0.8}
        >
          <View style={[styles.actionIconBox, { backgroundColor: '#FEF3C7' }]}>
            <Ionicons name="construct" size={26} color="#D97706" />
          </View>
          <Text style={styles.actionTileTitle}>Equipment</Text>
        </TouchableOpacity>
      </View>

      {/* Feature 6: AI Chatbot Hero Card Connecting All 4 Services */}
      <TouchableOpacity
        style={styles.copilotBannerCard}
        onPress={() => router.push('/chatbot')}
        activeOpacity={0.88}
      >
        <Image source={botAvatar} style={styles.copilotBannerAvatar} />
        <View style={styles.copilotBannerContent}>
          <View style={styles.copilotHeaderBadgeRow}>
            <Text style={styles.copilotBannerTitle}>Ask KisanCare AI</Text>
            <View style={styles.copilotLivePill}>
              <View style={styles.copilotLiveDot} />
              <Text style={styles.copilotLiveText}>AI Copilot</Text>
            </View>
          </View>
          <Text style={styles.copilotBannerSub}>
            Ask about crops, leaf pests, mandi rates & rentals
          </Text>
        </View>
        <Ionicons name="chevron-forward" size={18} color="#16A34A" />
      </TouchableOpacity>

      {/* Feature 1 Supporting Navigation: My Farm & Satellite Field Parcels */}
      <View style={styles.cardRow}>
        <TouchableOpacity
          style={[styles.secondaryNavCard, { flex: 1 }]}
          onPress={() => router.push('/(tabs)/farm')}
          activeOpacity={0.85}
        >
          <View style={styles.navCardIconRow}>
            <Ionicons name="map" size={20} color="#16A34A" />
            <Ionicons name="chevron-forward" size={16} color="#9CA3AF" />
          </View>
          <Text style={styles.navCardTitle}>My Farm & Field Parcels</Text>
          <Text style={styles.navCardSub}>
            {totalAcres.toFixed(1)} acres • {farmsData?.farms?.length || 3} parcels • Soil moisture & phenology
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAF8',
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingTop: 52,
    paddingBottom: 32,
  },
  topHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 18,
  },
  userProfileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarWrapper: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    position: 'relative',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  avatarImage: {
    width: '100%',
    height: '100%',
    borderRadius: 24,
  },
  onlineBadge: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#22C55E',
    borderWidth: 2,
    borderColor: '#FFFFFF',
    position: 'absolute',
    bottom: 0,
    right: 0,
  },
  greetingTextContainer: {
    marginLeft: 12,
  },
  greetingSub: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  greetingName: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  locationText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
    marginLeft: 3,
  },
  notificationButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    position: 'relative',
  },
  notificationBadge: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
    position: 'absolute',
    top: 9,
    right: 11,
  },
  weatherCard: {
    backgroundColor: '#1C2A39',
    borderRadius: 20,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 3,
  },
  weatherLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  weatherTempContainer: {
    justifyContent: 'center',
  },
  weatherTemp: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  weatherCondition: {
    fontSize: 12,
    color: '#94A3B8',
    fontWeight: '500',
  },
  weatherDivider: {
    width: 1,
    height: 38,
    backgroundColor: '#334155',
  },
  weatherRight: {
    justifyContent: 'center',
    gap: 3,
  },
  weatherMetricItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 14,
  },
  weatherMetricLabel: {
    fontSize: 12,
    color: '#94A3B8',
  },
  weatherMetricValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#F8FAFC',
  },
  farmSummaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 1,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  summaryHorizontalDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 10,
  },
  summaryItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  summaryIconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1E293B',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
  sectionHeaderRow: {
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  quickActionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 20,
  },
  actionTile: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    paddingVertical: 16,
    paddingHorizontal: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  actionIconBox: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  actionTileTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
    textAlign: 'center',
  },
  cardRow: {
    flexDirection: 'row',
    gap: 12,
  },
  secondaryNavCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  navCardIconRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  navCardTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
  },
  navCardSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  copilotBannerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 14,
    borderWidth: 1.5,
    borderColor: '#DCFCE7',
    marginBottom: 14,
    shadowColor: '#16A34A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 5,
    elevation: 2,
  },
  copilotBannerAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#E8F5E9',
    marginRight: 12,
  },
  copilotBannerContent: {
    flex: 1,
  },
  copilotHeaderBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  copilotBannerTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  copilotLivePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  copilotLiveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#16A34A',
    marginRight: 4,
  },
  copilotLiveText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#16A34A',
  },
  copilotBannerSub: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
});
