import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQueryClient } from '@tanstack/react-query';
import { getCropAgronomicInfo } from '@/constants/cropsData';
import { assignCropToFarm } from '@/services/farmService';

export default function CropDetailsScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const queryClient = useQueryClient();

  const params = useLocalSearchParams<{
    cropName?: string;
    farmId?: string;
    farmName?: string;
    district?: string;
    season?: string;
    dateStr?: string;
    rank?: string;
    score?: string;
    isRecommended?: string;
  }>();

  const cropName = params.cropName || 'Cotton';
  const farmId = params.farmId || '';
  const farmName = params.farmName || 'Your Farm';
  const dateStr = params.dateStr || '25 Oct 2026';
  const rank = params.rank ? parseInt(params.rank, 10) : 1;
  const score = params.score ? parseFloat(params.score) : 0.35;
  const isRecommended = params.isRecommended !== 'false';

  const cropInfo = getCropAgronomicInfo(cropName);

  const [isAssigning, setIsAssigning] = useState(false);

  const handleChooseCrop = async () => {
    if (!farmId) {
      Alert.alert(
        'Farm Required',
        'Please return to Crop Recommendation to link this crop to a registered farm parcel.',
        [{ text: 'OK' }]
      );
      return;
    }

    setIsAssigning(true);

    try {
      await assignCropToFarm(farmId, {
        crop: cropInfo.name,
        sowing_date: dateStr,
      });

      setIsAssigning(false);

      // Invalidate query cache to refresh farm state app-wide
      await queryClient.invalidateQueries({ queryKey: ['farms'] });

      Alert.alert(
        `✓ ${cropInfo.name} Selected`,
        `${cropInfo.name} has been chosen for ${farmName}.\n\nPlanned Sowing: ${dateStr}\n\nYour Farm management dashboard and seasonal advisory schedules have been updated.`,
        [
          {
            text: 'View Farm',
            onPress: () => router.replace('/(tabs)/farm'),
          },
          {
            text: 'Done',
            onPress: () => router.back(),
            style: 'cancel',
          },
        ]
      );
    } catch (err: any) {
      setIsAssigning(false);
      Alert.alert(
        'Crop Assignment Failed',
        err?.message || 'Unable to update farm crop. Please try again.',
        [{ text: 'OK' }]
      );
    }
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
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 90 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* 2. Crop Hero Card with Image, Name & Badge */}
        <View style={styles.heroCard}>
          <Image
            source={cropInfo.heroImage || cropInfo.thumbImage}
            style={styles.heroImage}
            resizeMode="cover"
          />

          {/* Dark gradient overlay for bottom text */}
          <View style={styles.heroOverlay}>
            <Text style={styles.heroCropName}>{cropInfo.name}</Text>
            {isRecommended && (
              <View style={styles.recommendedBadge}>
                <Ionicons name="checkmark-circle" size={16} color="#1E8234" />
                <Text style={styles.recommendedBadgeText}>Recommended</Text>
              </View>
            )}
          </View>
        </View>

        {/* 3. Section: "Why [Crop]?" */}
        <View style={styles.whyCropCard}>
          <View style={styles.leafIconContainer}>
            <Ionicons name="leaf" size={22} color="#1E8234" />
          </View>
          <View style={styles.whyCropContent}>
            <Text style={styles.whyCropTitle}>Why {cropInfo.name}?</Text>
            <Text style={styles.whyCropDescription}>
              {cropInfo.whyCrop || 'Suitable for your soil, weather and current season.'}
            </Text>
            {score > 0 && (
              <Text style={styles.modelScoreNote}>
                Suitability Rank #{rank} ({(score * 100).toFixed(1)}% historical area frequency in {params.district || 'district'})
              </Text>
            )}
          </View>
        </View>

        {/* 4. Agronomic Characteristic Cards */}
        <View style={styles.attributesCard}>
          {/* Water Need Row */}
          <View style={styles.attributeRow}>
            <View style={styles.attributeLeft}>
              <View style={[styles.attrIconCircle, { backgroundColor: '#E3F2FD' }]}>
                <Ionicons name="water-outline" size={20} color="#1976D2" />
              </View>
              <Text style={styles.attributeLabel}>Water Need</Text>
            </View>
            <Text style={styles.attributeValue}>{cropInfo.waterNeed}</Text>
          </View>

          <View style={styles.divider} />

          {/* Sowing Time Row */}
          <View style={styles.attributeRow}>
            <View style={styles.attributeLeft}>
              <View style={[styles.attrIconCircle, { backgroundColor: '#E8F5E9' }]}>
                <Ionicons name="calendar-outline" size={20} color="#2E7D32" />
              </View>
              <Text style={styles.attributeLabel}>Sowing Time</Text>
            </View>
            <Text style={styles.attributeValue}>{cropInfo.sowingTime}</Text>
          </View>

          <View style={styles.divider} />

          {/* Soil Suitability Row */}
          <View style={styles.attributeRow}>
            <View style={styles.attributeLeft}>
              <View style={[styles.attrIconCircle, { backgroundColor: '#F1F8E9' }]}>
                <Ionicons name="leaf-outline" size={20} color="#558B2F" />
              </View>
              <Text style={styles.attributeLabel}>Soil</Text>
            </View>
            <Text style={styles.attributeValue}>{cropInfo.soil}</Text>
          </View>
        </View>

        {/* Target Field Context */}
        <View style={styles.fieldContextCard}>
          <Ionicons name="location-outline" size={16} color="#1E8234" />
          <Text style={styles.fieldContextText}>
            Target Field: <Text style={styles.fieldContextBold}>{farmName}</Text> • Sowing: <Text style={styles.fieldContextBold}>{dateStr}</Text>
          </Text>
        </View>
      </ScrollView>

      {/* 5. Sticky Bottom Action Button */}
      <View style={[styles.bottomBar, { paddingBottom: Math.max(insets.bottom, 16) }]}>
        <TouchableOpacity
          style={[styles.primaryButton, isAssigning && styles.primaryButtonDisabled]}
          onPress={handleChooseCrop}
          disabled={isAssigning}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel={`Choose ${cropInfo.name} for this field`}
        >
          {isAssigning ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <View style={styles.buttonInner}>
              <Ionicons name="checkmark" size={22} color="#FFFFFF" style={styles.buttonCheckIcon} />
              <Text style={styles.primaryButtonText}>
                Choose {cropInfo.name} for This Field
              </Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
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
    paddingHorizontal: 20,
    paddingTop: 8,
  },
  heroCard: {
    width: '100%',
    height: 220,
    borderRadius: 24,
    overflow: 'hidden',
    backgroundColor: '#E8F5E9',
    marginBottom: 16,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  heroOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.42)',
    paddingHorizontal: 20,
    paddingVertical: 16,
    flexDirection: 'column',
    alignItems: 'flex-start',
  },
  heroCropName: {
    fontSize: 28,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 6,
    letterSpacing: -0.3,
  },
  recommendedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 14,
    gap: 6,
  },
  recommendedBadgeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E8234',
  },
  whyCropCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    borderWidth: 1.5,
    borderColor: '#F0F4F1',
    marginBottom: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  leafIconContainer: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  whyCropContent: {
    flex: 1,
  },
  whyCropTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#0F1A13',
    marginBottom: 4,
  },
  whyCropDescription: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1E2D4A',
    lineHeight: 20,
  },
  modelScoreNote: {
    fontSize: 12,
    color: '#2E7D32',
    fontWeight: '600',
    marginTop: 6,
  },
  attributesCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderWidth: 1.5,
    borderColor: '#F0F4F1',
    marginBottom: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
  },
  attributeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
  attributeLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  attrIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  attributeLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0F1A13',
  },
  attributeValue: {
    fontSize: 15,
    fontWeight: '600',
    color: '#374151',
  },
  divider: {
    height: 1,
    backgroundColor: '#F3F4F6',
    width: '100%',
  },
  fieldContextCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F9F4',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    gap: 8,
  },
  fieldContextText: {
    fontSize: 13,
    color: '#1B5E20',
  },
  fieldContextBold: {
    fontWeight: '700',
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F4F1',
  },
  primaryButton: {
    width: '100%',
    height: 54,
    backgroundColor: '#1B8032',
    borderRadius: 27,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#1B8032',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.28,
    shadowRadius: 8,
  },
  primaryButtonDisabled: {
    opacity: 0.7,
  },
  buttonInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonCheckIcon: {
    marginRight: 8,
  },
  primaryButtonText: {
    fontSize: 17,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.2,
  },
});
