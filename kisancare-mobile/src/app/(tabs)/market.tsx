import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  Image,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
  SUPPORTED_MARKET_COMMODITIES,
  SupportedCommodity,
  fetchMarketPrice,
  MarketPriceResponse,
} from '@/services/marketService';

const { width } = Dimensions.get('window');

export default function MarketScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const [activeTab, setActiveTab] = useState<'trends' | 'sell_wait' | 'mandis'>('trends');
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1M' | '3M' | '6M' | '1Y'>('3M');
  const [selectedCommodity, setSelectedCommodity] = useState<SupportedCommodity>(
    SUPPORTED_MARKET_COMMODITIES[0]
  );

  const [marketPriceData, setMarketPriceData] = useState<MarketPriceResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    loadPriceForCommodity(selectedCommodity);
  }, [selectedCommodity]);

  const loadPriceForCommodity = async (comm: SupportedCommodity) => {
    setIsLoading(true);
    setApiError(null);
    try {
      const res = await fetchMarketPrice({
        crop: comm.cropKey,
        market: comm.marketKey,
        date: comm.defaultDate,
      });
      setMarketPriceData(res);
    } catch (err: any) {
      setApiError(err?.message || 'Could not fetch market price prediction.');
      setMarketPriceData(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.screenWrapper}>
      {/* Top Header matching UIs.png */}
      <View style={styles.topHeader}>
        <View style={styles.headerTitleRow}>
          <Text style={styles.headerTitle}>Market Prices</Text>
        </View>

        {/* State Selector Pill */}
        <TouchableOpacity style={styles.stateSelectorPill} activeOpacity={0.8}>
          <Ionicons name="location" size={13} color="#16A34A" />
          <Text style={styles.stateSelectorText}>Maharashtra</Text>
          <Ionicons name="chevron-down" size={13} color="#16A34A" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Segmented Toggle Pills: Price Trends | Sell vs Wait | Nearby Mandis */}
        <View style={styles.togglePillContainer}>
          <TouchableOpacity
            style={[
              styles.togglePill,
              activeTab === 'trends' && styles.togglePillActive,
            ]}
            onPress={() => setActiveTab('trends')}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                activeTab === 'trends' && styles.togglePillTextActive,
              ]}
            >
              Price Trends
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.togglePill,
              activeTab === 'sell_wait' && styles.togglePillActive,
            ]}
            onPress={() => setActiveTab('sell_wait')}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                activeTab === 'sell_wait' && styles.togglePillTextActive,
              ]}
            >
              Sell vs Wait
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.togglePill,
              activeTab === 'mandis' && styles.togglePillActive,
            ]}
            onPress={() => setActiveTab('mandis')}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                activeTab === 'mandis' && styles.togglePillTextActive,
              ]}
            >
              Nearby Mandis
            </Text>
          </TouchableOpacity>
        </View>

        {/* Price Trend Chart Card matching Screen 7 */}
        <View style={styles.chartCard}>
          {/* Chart Header */}
          <View style={styles.chartHeaderRow}>
            <View>
              <Text style={styles.chartCropTitle}>
                {selectedCommodity.name} Price Intelligence
              </Text>
              <Text style={styles.chartUnitSubtitle}>
                {selectedCommodity.marketName} • (₹/Quintal)
              </Text>
            </View>

            {/* Timeframe Buttons: 1M | 3M | 6M | 1Y */}
            <View style={styles.timeframePillRow}>
              {(['1M', '3M', '6M', '1Y'] as const).map((tf) => (
                <TouchableOpacity
                  key={tf}
                  style={[
                    styles.timeframeButton,
                    selectedTimeframe === tf && styles.timeframeButtonActive,
                  ]}
                  onPress={() => setSelectedTimeframe(tf)}
                >
                  <Text
                    style={[
                      styles.timeframeButtonText,
                      selectedTimeframe === tf && styles.timeframeButtonTextActive,
                    ]}
                  >
                    {tf}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Current Highlight Badge */}
          {isLoading ? (
            <View style={{ paddingVertical: 20, alignItems: 'center' }}>
              <ActivityIndicator size="small" color="#16A34A" />
              <Text style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>
                Querying XGBoost price model...
              </Text>
            </View>
          ) : marketPriceData ? (
            <View>
              <View style={styles.priceHighlightRow}>
                <View style={styles.priceHighlightBadge}>
                  <Text style={styles.priceHighlightText}>
                    ₹{marketPriceData.current_price?.toLocaleString('en-IN') ?? '—'}
                  </Text>
                  <Text style={styles.priceDateText}>
                    • Observed ({marketPriceData.target_date})
                  </Text>
                </View>
                <View style={styles.trendIndicatorPill}>
                  <Ionicons
                    name={marketPriceData.trend === 'Up' ? 'arrow-up' : 'arrow-forward'}
                    size={12}
                    color="#16A34A"
                  />
                  <Text style={styles.trendIndicatorText}>
                    7d Forecast: ₹{typeof marketPriceData.forecast_7d === 'number' ? marketPriceData.forecast_7d.toFixed(0) : marketPriceData.forecast_7d}
                  </Text>
                </View>
              </View>

              <View style={styles.provenancePill}>
                <Text style={styles.provenancePillText}>
                  Source: Agmarknet APMC • Model: {marketPriceData.model_type}
                </Text>
              </View>
            </View>
          ) : (
            <View style={styles.apiErrorBox}>
              <Ionicons name="alert-circle-outline" size={16} color="#DC2626" />
              <Text style={styles.apiErrorText}>
                {apiError || 'Historical Agmarknet data unavailable for this date.'}
              </Text>
              <TouchableOpacity
                onPress={() => loadPriceForCommodity(selectedCommodity)}
                style={styles.retryButton}
                activeOpacity={0.8}
              >
                <Ionicons name="refresh" size={12} color="#16A34A" />
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* SVG / Vector Stylized Price Line Graph */}
          <View style={styles.chartVisualArea}>
            {/* Horizontal Grid lines */}
            <View style={styles.gridLineRow}>
              <Text style={styles.gridLabel}>3,000</Text>
              <View style={styles.gridDashedLine} />
            </View>
            <View style={styles.gridLineRow}>
              <Text style={styles.gridLabel}>2,000</Text>
              <View style={styles.gridDashedLine} />
            </View>
            <View style={styles.gridLineRow}>
              <Text style={styles.gridLabel}>1,500</Text>
              <View style={styles.gridDashedLine} />
            </View>
            <View style={styles.gridLineRow}>
              <Text style={styles.gridLabel}>1,000</Text>
              <View style={styles.gridDashedLine} />
            </View>

            {/* Simulated Trend Curve */}
            <View style={styles.curveSimulationContainer}>
              <View style={styles.trendBarCluster}>
                <View style={[styles.trendBar, { height: 42 }]} />
                <View style={[styles.trendBar, { height: 58 }]} />
                <View style={[styles.trendBar, { height: 66 }]} />
                <View style={[styles.trendBar, { height: 80 }]} />
                <View style={[styles.trendBar, styles.trendBarLatest, { height: 104 }]} />
              </View>
            </View>

            {/* X-Axis Months */}
            <View style={styles.xAxisRow}>
              <Text style={styles.xAxisLabel}>Jul</Text>
              <Text style={styles.xAxisLabel}>Aug</Text>
              <Text style={styles.xAxisLabel}>Sep</Text>
              <Text style={styles.xAxisLabel}>Oct</Text>
              <Text style={[styles.xAxisLabel, styles.xAxisLabelActive]}>Nov</Text>
            </View>
          </View>

          {/* Mandi & Distance Tag */}
          <View style={styles.mandiLocationBar}>
            <Ionicons name="storefront-outline" size={14} color="#16A34A" />
            <Text style={styles.mandiLocationText}>
              Market: {selectedCommodity.marketName} (Trained XGBoost)
            </Text>
          </View>
        </View>

        {/* Commodity Prices List Header */}
        <View style={styles.listHeaderRow}>
          <Text style={styles.listHeaderTitle}>APMC Mandi Quotations</Text>
          <Text style={styles.listHeaderSub}>Trained model commodities</Text>
        </View>

        {/* Commodity Price Items matching Screen 7 in UIs.png */}
        <View style={styles.commodityList}>
          {SUPPORTED_MARKET_COMMODITIES.map((c) => {
            const isSelected = selectedCommodity.id === c.id;
            return (
              <TouchableOpacity
                key={c.id}
                style={[
                  styles.commodityRow,
                  isSelected && styles.commodityRowSelected,
                ]}
                onPress={() => setSelectedCommodity(c)}
                activeOpacity={0.75}
              >
                <Image source={c.image} style={styles.commodityThumb} />

                <View style={styles.commodityInfo}>
                  <Text style={styles.commodityName}>{c.name}</Text>
                  <Text style={styles.commodityVariety}>{c.marketName}</Text>
                </View>

                <View style={styles.commodityPriceCol}>
                  <Text style={styles.commodityPriceValue}>
                    {isSelected && marketPriceData
                      ? `₹${marketPriceData.current_price}`
                      : 'View Rate'}
                  </Text>
                  <View style={styles.commodityTrendBadge}>
                    <Ionicons name="sparkles" size={12} color="#16A34A" />
                    <Text style={styles.commodityChangeText}>XGBoost</Text>
                  </View>
                </View>

                <Ionicons name="chevron-forward" size={16} color="#CBD5E1" />
              </TouchableOpacity>
            );
          })}
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
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
  },
  stateSelectorPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  stateSelectorText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
  },
  togglePillContainer: {
    flexDirection: 'row',
    backgroundColor: '#E5E7EB',
    borderRadius: 24,
    padding: 3,
    marginBottom: 16,
  },
  togglePill: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 22,
  },
  togglePillActive: {
    backgroundColor: '#16A34A',
  },
  togglePillText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4B5563',
  },
  togglePillTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  chartCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
    marginBottom: 20,
  },
  chartHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  chartCropTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#111827',
  },
  chartUnitSubtitle: {
    fontSize: 12,
    color: '#64748B',
  },
  timeframePillRow: {
    flexDirection: 'row',
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    padding: 2,
    gap: 2,
  },
  timeframeButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  timeframeButtonActive: {
    backgroundColor: '#16A34A',
  },
  timeframeButtonText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
  },
  timeframeButtonTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  priceHighlightRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  priceHighlightBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  priceHighlightText: {
    fontSize: 22,
    fontWeight: '800',
    color: '#111827',
  },
  priceDateText: {
    fontSize: 12,
    color: '#64748B',
  },
  trendIndicatorPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  trendIndicatorText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  chartVisualArea: {
    height: 140,
    justifyContent: 'space-between',
    position: 'relative',
    marginBottom: 12,
  },
  gridLineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gridLabel: {
    fontSize: 10,
    color: '#94A3B8',
    width: 34,
  },
  gridDashedLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#F1F5F9',
  },
  curveSimulationContainer: {
    position: 'absolute',
    left: 44,
    right: 8,
    bottom: 22,
    top: 10,
    justifyContent: 'flex-end',
  },
  trendBarCluster: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
  },
  trendBar: {
    width: 28,
    backgroundColor: '#BBF7D0',
    borderTopLeftRadius: 6,
    borderTopRightRadius: 6,
  },
  trendBarLatest: {
    backgroundColor: '#16A34A',
  },
  xAxisRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingLeft: 44,
    paddingRight: 12,
    marginTop: 4,
  },
  xAxisLabel: {
    fontSize: 11,
    color: '#94A3B8',
    fontWeight: '500',
  },
  xAxisLabelActive: {
    color: '#16A34A',
    fontWeight: '700',
  },
  mandiLocationBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F8FAFC',
    padding: 8,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  mandiLocationText: {
    fontSize: 12,
    color: '#475569',
    fontWeight: '500',
  },
  listHeaderRow: {
    marginBottom: 10,
  },
  listHeaderTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  listHeaderSub: {
    fontSize: 12,
    color: '#64748B',
  },
  commodityList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  commodityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  commodityRowSelected: {
    backgroundColor: '#F0FDF4',
  },
  commodityThumb: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginRight: 12,
  },
  commodityInfo: {
    flex: 1,
  },
  commodityName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  commodityVariety: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 1,
  },
  commodityPriceCol: {
    alignItems: 'flex-end',
    marginRight: 8,
  },
  commodityPriceValue: {
    fontSize: 14,
    fontWeight: '800',
    color: '#1E293B',
  },
  commodityTrendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    marginTop: 2,
  },
  commodityChangeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  provenancePill: {
    marginTop: 6,
    backgroundColor: '#F0FDF4',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  provenancePillText: {
    fontSize: 10,
    color: '#16A34A',
    fontWeight: '600',
  },
  apiErrorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FEE2E2',
    padding: 8,
    borderRadius: 8,
    marginTop: 8,
  },
  apiErrorText: {
    fontSize: 11,
    color: '#DC2626',
    flex: 1,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  retryButtonText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#16A34A',
  },
});
