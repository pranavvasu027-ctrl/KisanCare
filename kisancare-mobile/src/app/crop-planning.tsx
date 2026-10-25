import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Modal,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
  fetchCropRecommendations,
  normalizeDistrictName,
  VALID_MAHARASHTRA_DISTRICTS,
} from '@/services/cropService';
import { fetchFarms, FarmDisplayItem } from '@/services/farmService';
import { CropSeason, WaterAvailability, CropRecommendationResponse } from '@/types';

/**
 * Maps a JavaScript Date object to the standard Indian agricultural season
 * - Kharif: June to October (Monsoon onset to harvest)
 * - Rabi: November to February (Winter season)
 * - Summer: March to May (Zaid / Pre-monsoon)
 */
function getSeasonFromDate(date: Date): CropSeason {
  const month = date.getMonth(); // 0-indexed: 0 = Jan, 9 = Oct
  if (month >= 5 && month <= 9) {
    return 'Kharif'; // June - Oct
  } else if (month >= 10 || month <= 1) {
    return 'Rabi'; // Nov - Feb
  } else {
    return 'Summer'; // Mar - May
  }
}

function formatDate(date: Date): string {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

export default function CropPlanningLandingScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  // Load farms belonging to current farmer
  const {
    data: farmsData,
    isLoading: isLoadingFarms,
    isError: isFarmsError,
    refetch: refetchFarms,
  } = useQuery({
    queryKey: ['farms'],
    queryFn: fetchFarms,
  });

  const farms = useMemo(() => farmsData?.farms || [], [farmsData]);

  // Selected farm state
  const [selectedFarm, setSelectedFarm] = useState<FarmDisplayItem | null>(null);
  const [isFarmModalVisible, setIsFarmModalVisible] = useState(false);

  // Auto-select first farm if available and nothing selected yet
  React.useEffect(() => {
    if (!selectedFarm && farms.length > 0) {
      setSelectedFarm(farms[0]);
    }
  }, [farms, selectedFarm]);

  // Selected date state (defaulting to current date)
  const [selectedDate, setSelectedDate] = useState<Date>(new Date(2026, 9, 25)); // 25 Oct 2026 matching reference
  const [isDateModalVisible, setIsDateModalVisible] = useState(false);

  // Temporary date for picker modal
  const [tempDay, setTempDay] = useState(selectedDate.getDate());
  const [tempMonth, setTempMonth] = useState(selectedDate.getMonth());
  const [tempYear, setTempYear] = useState(selectedDate.getFullYear());

  // Recommendation query loading & error states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  // Derive district from farm location
  const farmDistrict = useMemo(() => {
    if (!selectedFarm) return 'AKOLA';
    const loc = selectedFarm.location.toUpperCase();
    for (const d of VALID_MAHARASHTRA_DISTRICTS) {
      if (loc.includes(d)) return d;
    }
    return normalizeDistrictName(selectedFarm.location);
  }, [selectedFarm]);

  // Derive season honestly from selected date
  const derivedSeason = useMemo(() => getSeasonFromDate(selectedDate), [selectedDate]);

  // Handlers
  const handleFindBestCrops = async () => {
    if (!selectedFarm) {
      Alert.alert(
        'Farm Required',
        'Please select a farm parcel to evaluate soil, district, and agronomic conditions.',
        [{ text: 'OK', onPress: () => setIsFarmModalVisible(true) }]
      );
      return;
    }

    setIsSubmitting(true);
    setRequestError(null);

    try {
      const response: CropRecommendationResponse = await fetchCropRecommendations({
        district: farmDistrict,
        season: derivedSeason,
        water_availability: 'Medium',
        top_k: 5,
      });

      setIsSubmitting(false);

      if (response.status === 'ERROR') {
        setRequestError('Failed to generate crop recommendations. Please check district parameters.');
        return;
      }

      // Navigate to Screen 2: Recommended for You
      router.push({
        pathname: '/crop-recommendations',
        params: {
          farmId: selectedFarm.id,
          farmName: selectedFarm.name,
          farmLocation: selectedFarm.location,
          district: farmDistrict,
          season: derivedSeason,
          dateStr: formatDate(selectedDate),
          recommendationsJson: JSON.stringify(response.recommendations || []),
          status: response.status,
          dataSource: response.data_source || 'APY_2005_2015',
        },
      });
    } catch (err: any) {
      setIsSubmitting(false);
      const msg = err?.message || 'Unable to connect to crop recommendation model. Please verify network connection.';
      setRequestError(msg);
    }
  };

  const handleConfirmDate = () => {
    const newDate = new Date(tempYear, tempMonth, tempDay);
    setSelectedDate(newDate);
    setIsDateModalVisible(false);
  };

  return (
    <View style={[styles.rootContainer, { paddingTop: insets.top, backgroundColor: '#FFFFFF' }]}>
      {/* 1. Header Bar: Back Arrow & Leaf Logo */}
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

      <ScrollView
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 24 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* 2. Heading & Subtitle */}
        <View style={styles.titleSection}>
          <Text style={styles.mainHeading}>Crop Recommendation</Text>
          <Text style={styles.subHeading}>Get best crops for your farm</Text>
        </View>

        {/* 3. Landscape Illustration Card */}
        <View style={styles.illustrationWrapper}>
          <Image
            source={require('@/assets/images/ui/crop_recommendation_landscape.png')}
            style={styles.landscapeImage}
            resizeMode="cover"
          />
        </View>

        {/* 4. Selector Controls Row */}
        <View style={styles.controlsRow}>
          {/* Farm Selection Pill Button */}
          <TouchableOpacity
            style={styles.pillButton}
            onPress={() => setIsFarmModalVisible(true)}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel="Select farm"
          >
            <Ionicons name="location-sharp" size={20} color="#1E8234" style={styles.pillIcon} />
            <Text style={styles.pillText} numberOfLines={1}>
              {selectedFarm ? selectedFarm.name : 'Select farm'}
            </Text>
          </TouchableOpacity>

          {/* Date Selection Pill Button */}
          <TouchableOpacity
            style={styles.pillButton}
            onPress={() => {
              setTempDay(selectedDate.getDate());
              setTempMonth(selectedDate.getMonth());
              setTempYear(selectedDate.getFullYear());
              setIsDateModalVisible(true);
            }}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel="Select date"
          >
            <Ionicons name="calendar" size={20} color="#1E8234" style={styles.pillIcon} />
            <Text style={styles.pillText} numberOfLines={1}>
              {formatDate(selectedDate)}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Context Information Note */}
        {selectedFarm && (
          <View style={styles.farmMetaCard}>
            <Ionicons name="information-circle-outline" size={16} color="#2E7D32" />
            <Text style={styles.farmMetaText}>
              Evaluating for {farmDistrict} ({derivedSeason} Season) • {selectedFarm.areaAcres} Acres
            </Text>
          </View>
        )}

        {/* Error Banner with Retry */}
        {requestError && (
          <View style={styles.errorBanner}>
            <Ionicons name="alert-circle" size={20} color="#D32F2F" />
            <View style={styles.errorTextContainer}>
              <Text style={styles.errorText}>{requestError}</Text>
              <TouchableOpacity onPress={handleFindBestCrops} style={styles.retryButton}>
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* 5. Primary Action Button: Find Best Crops */}
        <TouchableOpacity
          style={[styles.primaryButton, isSubmitting && styles.primaryButtonDisabled]}
          onPress={handleFindBestCrops}
          disabled={isSubmitting}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Find Best Crops"
        >
          {isSubmitting ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <View style={styles.buttonInner}>
              <Ionicons name="sparkles" size={22} color="#FFFFFF" style={styles.buttonIcon} />
              <Text style={styles.primaryButtonText}>Find Best Crops</Text>
            </View>
          )}
        </TouchableOpacity>
      </ScrollView>

      {/* Farm Selection Modal */}
      <Modal
        visible={isFarmModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIsFarmModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Farm Parcel</Text>
              <TouchableOpacity onPress={() => setIsFarmModalVisible(false)}>
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            {isLoadingFarms ? (
              <View style={styles.modalLoading}>
                <ActivityIndicator color="#2E7D32" size="large" />
                <Text style={styles.modalLoadingText}>Loading registered farms...</Text>
              </View>
            ) : isFarmsError ? (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>Could not load farms.</Text>
                <TouchableOpacity onPress={() => refetchFarms()} style={styles.retrySmallBtn}>
                  <Text style={styles.retrySmallText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : farms.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Ionicons name="leaf-outline" size={44} color="#999" />
                <Text style={styles.emptyText}>No registered farms found.</Text>
                <TouchableOpacity
                  onPress={() => {
                    setIsFarmModalVisible(false);
                    router.push('/(tabs)/farm');
                  }}
                  style={styles.retrySmallBtn}
                >
                  <Text style={styles.retrySmallText}>Add Farm in Farm Tab</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <ScrollView style={styles.farmListScroll}>
                {farms.map((f) => {
                  const isSelected = selectedFarm?.id === f.id;
                  return (
                    <TouchableOpacity
                      key={f.id}
                      style={[styles.farmItemCard, isSelected && styles.farmItemCardSelected]}
                      onPress={() => {
                        setSelectedFarm(f);
                        setIsFarmModalVisible(false);
                      }}
                    >
                      <View style={styles.farmItemLeft}>
                        <Ionicons
                          name="business-outline"
                          size={22}
                          color={isSelected ? '#1E8234' : '#666'}
                        />
                        <View style={styles.farmItemTextWrapper}>
                          <Text style={[styles.farmItemName, isSelected && styles.farmItemNameSelected]}>
                            {f.name}
                          </Text>
                          <Text style={styles.farmItemLocation}>
                            {f.location} • {f.areaAcres} Acres
                          </Text>
                        </View>
                      </View>
                      {isSelected && <Ionicons name="checkmark-circle" size={22} color="#1E8234" />}
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* Date Selection Modal */}
      <Modal
        visible={isDateModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setIsDateModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Choose Sowing Date</Text>
              <TouchableOpacity onPress={() => setIsDateModalVisible(false)}>
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <Text style={styles.datePickerExplainer}>
              The selected date maps to the agricultural sowing season (Kharif, Rabi, Summer) used by the recommendation model.
            </Text>

            {/* Quick Season Presets */}
            <Text style={styles.presetHeading}>Quick Season Presets (2026):</Text>
            <View style={styles.presetsRow}>
              <TouchableOpacity
                style={[
                  styles.presetChip,
                  tempMonth >= 5 && tempMonth <= 9 && styles.presetChipActive,
                ]}
                onPress={() => {
                  setTempDay(25);
                  setTempMonth(9); // Oct (Kharif)
                  setTempYear(2026);
                }}
              >
                <Text
                  style={[
                    styles.presetChipText,
                    tempMonth >= 5 && tempMonth <= 9 && styles.presetChipTextActive,
                  ]}
                >
                  Kharif (Oct 2026)
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.presetChip,
                  (tempMonth >= 10 || tempMonth <= 1) && styles.presetChipActive,
                ]}
                onPress={() => {
                  setTempDay(15);
                  setTempMonth(10); // Nov (Rabi)
                  setTempYear(2026);
                }}
              >
                <Text
                  style={[
                    styles.presetChipText,
                    (tempMonth >= 10 || tempMonth <= 1) && styles.presetChipTextActive,
                  ]}
                >
                  Rabi (Nov 2026)
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.presetChip,
                  tempMonth >= 2 && tempMonth <= 4 && styles.presetChipActive,
                ]}
                onPress={() => {
                  setTempDay(10);
                  setTempMonth(2); // Mar (Summer)
                  setTempYear(2026);
                }}
              >
                <Text
                  style={[
                    styles.presetChipText,
                    tempMonth >= 2 && tempMonth <= 4 && styles.presetChipTextActive,
                  ]}
                >
                  Summer (Mar 2026)
                </Text>
              </TouchableOpacity>
            </View>

            {/* Day / Month / Year Selectors */}
            <View style={styles.pickerRow}>
              {/* Day */}
              <View style={styles.pickerCol}>
                <Text style={styles.pickerLabel}>Day</Text>
                <View style={styles.numberStepper}>
                  <TouchableOpacity
                    style={styles.stepBtn}
                    onPress={() => setTempDay((prev) => Math.max(1, prev - 1))}
                  >
                    <Ionicons name="remove" size={18} color="#2E7D32" />
                  </TouchableOpacity>
                  <Text style={styles.stepVal}>{tempDay}</Text>
                  <TouchableOpacity
                    style={styles.stepBtn}
                    onPress={() => setTempDay((prev) => Math.min(31, prev + 1))}
                  >
                    <Ionicons name="add" size={18} color="#2E7D32" />
                  </TouchableOpacity>
                </View>
              </View>

              {/* Month */}
              <View style={styles.pickerCol}>
                <Text style={styles.pickerLabel}>Month</Text>
                <View style={styles.numberStepper}>
                  <TouchableOpacity
                    style={styles.stepBtn}
                    onPress={() => setTempMonth((prev) => Math.max(0, prev - 1))}
                  >
                    <Ionicons name="remove" size={18} color="#2E7D32" />
                  </TouchableOpacity>
                  <Text style={styles.stepVal}>
                    {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][tempMonth]}
                  </Text>
                  <TouchableOpacity
                    style={styles.stepBtn}
                    onPress={() => setTempMonth((prev) => Math.min(11, prev + 1))}
                  >
                    <Ionicons name="add" size={18} color="#2E7D32" />
                  </TouchableOpacity>
                </View>
              </View>

              {/* Year */}
              <View style={styles.pickerCol}>
                <Text style={styles.pickerLabel}>Year</Text>
                <View style={styles.numberStepper}>
                  <TouchableOpacity
                    style={styles.stepBtn}
                    onPress={() => setTempYear((prev) => Math.max(2025, prev - 1))}
                  >
                    <Ionicons name="remove" size={18} color="#2E7D32" />
                  </TouchableOpacity>
                  <Text style={styles.stepVal}>{tempYear}</Text>
                  <TouchableOpacity
                    style={styles.stepBtn}
                    onPress={() => setTempYear((prev) => Math.min(2030, prev + 1))}
                  >
                    <Ionicons name="add" size={18} color="#2E7D32" />
                  </TouchableOpacity>
                </View>
              </View>
            </View>

            <TouchableOpacity style={styles.confirmDateBtn} onPress={handleConfirmDate}>
              <Text style={styles.confirmDateBtnText}>Set Date</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
  scrollContent: {
    paddingHorizontal: 22,
    alignItems: 'center',
  },
  titleSection: {
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 18,
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
    fontSize: 16,
    fontWeight: '500',
    color: '#1E2D4A',
    textAlign: 'center',
  },
  illustrationWrapper: {
    width: '100%',
    height: 220,
    borderRadius: 24,
    overflow: 'hidden',
    backgroundColor: '#E8F5E9',
    marginBottom: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
  },
  landscapeImage: {
    width: '100%',
    height: '100%',
  },
  controlsRow: {
    flexDirection: 'row',
    width: '100%',
    gap: 12,
    marginBottom: 16,
  },
  pillButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3F9F4',
    borderWidth: 1.5,
    borderColor: '#C8E6C9',
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  pillIcon: {
    marginRight: 8,
  },
  pillText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0A2612',
    flexShrink: 1,
  },
  farmMetaCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    width: '100%',
    marginBottom: 16,
    gap: 8,
  },
  farmMetaText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1B5E20',
    flex: 1,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFEBEE',
    borderWidth: 1,
    borderColor: '#FFCDD2',
    borderRadius: 14,
    padding: 14,
    width: '100%',
    marginBottom: 18,
    gap: 10,
  },
  errorTextContainer: {
    flex: 1,
  },
  errorText: {
    color: '#B71C1C',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 6,
  },
  retryButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#D32F2F',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  primaryButton: {
    width: '100%',
    height: 56,
    backgroundColor: '#1B8032',
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
    elevation: 4,
    shadowColor: '#1B8032',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.28,
    shadowRadius: 10,
  },
  primaryButtonDisabled: {
    opacity: 0.7,
  },
  buttonInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonIcon: {
    marginRight: 8,
  },
  primaryButtonText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 22,
    maxHeight: '80%',
    elevation: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.18,
    shadowRadius: 16,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  modalLoading: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  modalLoadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
  },
  farmListScroll: {
    maxHeight: 280,
  },
  farmItemCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderRadius: 14,
    backgroundColor: '#F9FAFB',
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    marginBottom: 10,
  },
  farmItemCardSelected: {
    backgroundColor: '#E8F5E9',
    borderColor: '#1E8234',
  },
  farmItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  farmItemTextWrapper: {
    flex: 1,
  },
  farmItemName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1F2937',
  },
  farmItemNameSelected: {
    color: '#1E8234',
  },
  farmItemLocation: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 28,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 10,
    textAlign: 'center',
  },
  retrySmallBtn: {
    marginTop: 14,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#1E8234',
    borderRadius: 10,
  },
  retrySmallText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  datePickerExplainer: {
    fontSize: 13,
    color: '#4B5563',
    lineHeight: 18,
    marginBottom: 14,
  },
  presetHeading: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  presetsRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 18,
  },
  presetChip: {
    flex: 1,
    paddingVertical: 10,
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  presetChipActive: {
    backgroundColor: '#E8F5E9',
    borderColor: '#1E8234',
  },
  presetChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#374151',
  },
  presetChipTextActive: {
    color: '#1E8234',
    fontWeight: '700',
  },
  pickerRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  pickerCol: {
    flex: 1,
    alignItems: 'center',
  },
  pickerLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 6,
  },
  numberStepper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 10,
    paddingHorizontal: 4,
    paddingVertical: 6,
    width: '100%',
    justifyContent: 'space-between',
  },
  stepBtn: {
    padding: 6,
  },
  stepVal: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  confirmDateBtn: {
    backgroundColor: '#1E8234',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
  },
  confirmDateBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 16,
  },
});
