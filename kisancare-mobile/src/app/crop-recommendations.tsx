import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getCropAgronomicInfo } from '@/constants/cropsData';
import { CropRecommendationItem } from '@/types';

export default function RecommendedForYouScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{
    farmId?: string;
    farmName?: string;
    farmLocation?: string;
    district?: string;
    season?: string;
    dateStr?: string;
    recommendationsJson?: string;
    status?: string;
    dataSource?: string;
  }>();

  const farmId = params.farmId || '';
  const farmName = params.farmName || 'Your Farm';
  const district = params.district || 'AKOLA';
  const season = params.season || 'Kharif';
  const dateStr = params.dateStr || '25 Oct 2026';

  // Parse recommendations safely
  const recommendations: CropRecommendationItem[] = React.useMemo(() => {
    try {
      if (params.recommendationsJson) {
        return JSON.parse(params.recommendationsJson);
      }
    } catch {
      // Fallback
    }
    return [];
  }, [params.recommendationsJson]);

  const getSuitabilityText = (rank: number, score: number): string => {
    if (rank === 1) return 'Best match for your farm';
    if (rank === 2) return 'Suitable for current conditions';
    if (rank === 3) return 'Good option';
    return 'Alternative viable option';
  };

  const handleSelectCrop = (cropItem: CropRecommendationItem) => {
    router.push({
      pathname: '/crop-details',
      params: {
        cropName: cropItem.crop,
        farmId,
        farmName,
        district,
        season,
        dateStr,
        rank: cropItem.rank.toString(),
        score: cropItem.predicted_area_frequency.toString(),
        isRecommended: 'true',
      },
    });
  };

  return (
    <View style={[styles.rootContainer, { paddingTop: insets.top, backgroundColor: '#FFFFFF' }]}>
      {/* 1. Top Header: Back Arrow & Centered Leaf Logo */}
      <View style={styles.headerBar}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          accessibilityLabel="Go back"
          accessibilityRole="button"
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
        >
          <Ionicons name="arrow-back" size={26} color="#1A1A1A" />
        </TouchableOpacity>

        <View style={styles.logoContainer}>
          <Image
            source={require('@/assets/images/ui/kisancare_leaf_logo.png')}
            style={styles.headerLeafLogo}
            resizeMode="contain"
          />
        </View>

        <View style={styles.headerRightSpacer} />
      </View>

      {/* 2. Main Title */}
      <View style={styles.titleSection}>
        <Text style={styles.mainHeading}>Recommended for You</Text>
        <Text style={styles.subHeading}>
          {farmName} • {district} ({season} {dateStr.split(' ')[2] || '2026'})
        </Text>
      </View>

      <ScrollView
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 32 }]}
        showsVerticalScrollIndicator={false}
      >
        {recommendations.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons name="leaf-outline" size={56} color="#A5D6A7" />
            <Text style={styles.emptyTitle}>No Recommendations Available</Text>
            <Text style={styles.emptyDescription}>
              No crops meet the climatic or seasonal constraints for {district} in {season} season.
            </Text>
            <TouchableOpacity style={styles.retryButton} onPress={() => router.back()}>
              <Text style={styles.retryButtonText}>Adjust Farm or Season</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.cardsList}>
            {recommendations.map((item) => {
              const cropInfo = getCropAgronomicInfo(item.crop);
              const suitability = getSuitabilityText(item.rank, item.predicted_area_frequency);

              return (
                <TouchableOpacity
                  key={`${item.crop}-${item.rank}`}
                  style={styles.cropCard}
                  onPress={() => handleSelectCrop(item)}
                  activeOpacity={0.8}
                  accessibilityRole="button"
                  accessibilityLabel={`Select ${cropInfo.name}`}
                >
                  {/* Left: Rounded Crop Image */}
                  <Image
                    source={cropInfo.thumbImage}
                    style={styles.cropThumb}
                    resizeMode="cover"
                  />

                  {/* Middle: Name & Suitability Explanation */}
                  <View style={styles.cropDetails}>
                    <Text style={styles.cropName}>{cropInfo.name}</Text>
                    <Text style={styles.suitabilityText}>{suitability}</Text>
                  </View>

                  {/* Right: Circular Light Green Arrow Button */}
                  <View style={styles.actionCircle}>
                    <Ionicons name="arrow-forward" size={18} color="#1B5E20" />
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {/* Provenance Footer */}
        {recommendations.length > 0 && (
          <View style={styles.provenanceFooter}>
            <Ionicons name="shield-checkmark-outline" size={16} color="#2E7D32" />
            <Text style={styles.provenanceText}>
              Ranked by APY agricultural suitability model. Suitability reflects historical agro-climatic viability in {district}.
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  rootContainer: {
    flex: 1,
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerLeafLogo: {
    width: 38,
    height: 38,
  },
  headerRightSpacer: {
    width: 44,
  },
  titleSection: {
    alignItems: 'center',
    marginTop: 6,
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  mainHeading: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0F1A13',
    letterSpacing: -0.3,
    marginBottom: 4,
    textAlign: 'center',
  },
  subHeading: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    textAlign: 'center',
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  cardsList: {
    gap: 14,
  },
  cropCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1.5,
    borderColor: '#F0F4F1',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
  },
  cropThumb: {
    width: 78,
    height: 78,
    borderRadius: 16,
    backgroundColor: '#E8F5E9',
  },
  cropDetails: {
    flex: 1,
    paddingLeft: 14,
    justifyContent: 'center',
  },
  cropName: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F1A13',
    marginBottom: 4,
  },
  suitabilityText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1E2D4A',
    lineHeight: 18,
  },
  actionCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#B4EB78',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 56,
    paddingHorizontal: 24,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyDescription: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#1E8234',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 14,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  provenanceFooter: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F3F9F4',
    padding: 12,
    borderRadius: 12,
    marginTop: 24,
    gap: 8,
  },
  provenanceText: {
    flex: 1,
    fontSize: 12,
    color: '#2E7D32',
    lineHeight: 16,
    fontWeight: '500',
  },
});
