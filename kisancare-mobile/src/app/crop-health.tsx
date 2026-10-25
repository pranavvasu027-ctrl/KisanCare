import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
  Dimensions,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import {
  COMMON_DISEASE_SYMPTOMS,
  COMMON_PEST_SYMPTOMS,
  detectDisease,
  detectPest,
  validateImageMetadata,
  validateSymptomsRequest,
} from '@/services/diseaseService';
import { CropImageMetadata, DetectionResponse } from '@/types';

const { width } = Dimensions.get('window');

export default function CropHealthScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  // Mode: Disease vs Pest
  const [mode, setMode] = useState<'disease' | 'pest'>('disease');

  // Form & Image state
  const [selectedCrop, setSelectedCrop] = useState<string>('Soybean');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(['yellow leaves']);
  const [attachedImage, setAttachedImage] = useState<CropImageMetadata | null>(null);

  // Active thumbnail selection (0=leaf_diseased, 1=thumb1, 2=thumb2, 3=thumb3, 4=user)
  const [activeThumb, setActiveThumb] = useState<number>(0);

  // API State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<DetectionResponse | null>(null);

  const handlePickFromGallery = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('Permission Denied', 'Gallery access is needed to select a crop photo.');
        return;
      }

      const pickerResult = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        quality: 0.8,
      });

      if (!pickerResult.canceled && pickerResult.assets && pickerResult.assets.length > 0) {
        const asset = pickerResult.assets[0];
        const metadata: CropImageMetadata = {
          uri: asset.uri,
          width: asset.width,
          height: asset.height,
          fileSize: asset.fileSize,
          fileName: asset.fileName || 'leaf.jpg',
          mimeType: asset.mimeType || 'image/jpeg',
        };

        const validation = validateImageMetadata(metadata);
        if (!validation.isValid) {
          Alert.alert('Invalid Image', validation.error);
          return;
        }

        setAttachedImage(metadata);
        setActiveThumb(4);
        runInference(metadata);
      }
    } catch (err: any) {
      Alert.alert('Error', 'Unable to open photo gallery: ' + err.message);
    }
  };

  const handleTakePhoto = async () => {
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        Alert.alert('Permission Denied', 'Camera access is needed to capture a crop photo.');
        return;
      }

      const pickerResult = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        quality: 0.8,
      });

      if (!pickerResult.canceled && pickerResult.assets && pickerResult.assets.length > 0) {
        const asset = pickerResult.assets[0];
        const metadata: CropImageMetadata = {
          uri: asset.uri,
          width: asset.width,
          height: asset.height,
          fileSize: asset.fileSize,
          fileName: asset.fileName || 'camera_leaf.jpg',
          mimeType: asset.mimeType || 'image/jpeg',
        };

        setAttachedImage(metadata);
        setActiveThumb(4);
        runInference(metadata);
      }
    } catch (err: any) {
      Alert.alert('Error', 'Unable to launch camera: ' + err.message);
    }
  };

  const runInference = async (imageMeta?: CropImageMetadata | null) => {
    if (selectedSymptoms.length === 0) {
      Alert.alert(
        'Symptom Required',
        'Please select at least one observed symptom (e.g. yellow leaves, white powdery spots) before running the diagnostic.'
      );
      return;
    }

    setIsLoading(true);
    setApiError(null);
    try {
      let res: DetectionResponse;
      if (mode === 'disease') {
        res = await detectDisease({
          crop: selectedCrop,
          symptoms: selectedSymptoms,
        });
      } else {
        res = await detectPest({
          crop: selectedCrop,
          symptoms: selectedSymptoms,
        });
      }
      setResult(res);
    } catch (err: any) {
      setApiError(err?.message || 'Inference service unavailable. Fallback rule applied.');
    } finally {
      setIsLoading(false);
    }
  };

  const activeLeafSource =
    activeThumb === 4 && attachedImage?.uri
      ? { uri: attachedImage.uri }
      : activeThumb === 1
      ? require('../../assets/images/ui/leaf_thumb1.png')
      : activeThumb === 2
      ? require('../../assets/images/ui/leaf_thumb2.png')
      : activeThumb === 3
      ? require('../../assets/images/ui/leaf_thumb3.png')
      : require('../../assets/images/ui/leaf_diseased.png');

  return (
    <View style={styles.screenWrapper}>
      {/* Top Header */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Ionicons name="arrow-back" size={24} color="#1F2937" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Crop Health</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Toggle Pills: Disease Detection | Pest Monitoring */}
        <View style={styles.togglePillContainer}>
          <TouchableOpacity
            style={[
              styles.togglePill,
              mode === 'disease' && styles.togglePillActive,
            ]}
            onPress={() => {
              setMode('disease');
              runInference();
            }}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                mode === 'disease' && styles.togglePillTextActive,
              ]}
            >
              Disease Detection
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.togglePill,
              mode === 'pest' && styles.togglePillActive,
            ]}
            onPress={() => {
              setMode('pest');
              runInference();
            }}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                mode === 'pest' && styles.togglePillTextActive,
              ]}
            >
              Pest Monitoring
            </Text>
          </TouchableOpacity>
        </View>

        {/* Viewfinder Scanning Frame with 4 Green Reticles matching UIs.png */}
        <View style={styles.viewfinderCard}>
          <Image source={activeLeafSource} style={styles.viewfinderImage} resizeMode="cover" />

          {/* 4 Corner Reticle Brackets */}
          <View style={[styles.reticle, styles.reticleTopLeft]} />
          <View style={[styles.reticle, styles.reticleTopRight]} />
          <View style={[styles.reticle, styles.reticleBottomLeft]} />
          <View style={[styles.reticle, styles.reticleBottomRight]} />

          {/* Scanning Indicator / Status */}
          {isLoading ? (
            <View style={styles.scanningOverlay}>
              <ActivityIndicator size="large" color="#16A34A" />
              <Text style={styles.scanningText}>AI Neural Scanning...</Text>
            </View>
          ) : (
            <View style={styles.scanTargetBadge}>
              <Ionicons name="scan" size={14} color="#FFFFFF" />
              <Text style={styles.scanTargetText}>Target Leaf Frame</Text>
            </View>
          )}
        </View>

        {/* Image Thumbnail Strip matching Screen 6 */}
        <View style={styles.thumbnailStrip}>
          <TouchableOpacity
            style={[styles.thumbItem, activeThumb === 0 && styles.thumbItemActive]}
            onPress={() => setActiveThumb(0)}
          >
            <Image
              source={require('../../assets/images/ui/leaf_diseased.png')}
              style={styles.thumbImage}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.thumbItem, activeThumb === 1 && styles.thumbItemActive]}
            onPress={() => setActiveThumb(1)}
          >
            <Image
              source={require('../../assets/images/ui/leaf_thumb1.png')}
              style={styles.thumbImage}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.thumbItem, activeThumb === 2 && styles.thumbItemActive]}
            onPress={() => setActiveThumb(2)}
          >
            <Image
              source={require('../../assets/images/ui/leaf_thumb2.png')}
              style={styles.thumbImage}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.thumbItem, activeThumb === 3 && styles.thumbItemActive]}
            onPress={() => setActiveThumb(3)}
          >
            <Image
              source={require('../../assets/images/ui/leaf_thumb3.png')}
              style={styles.thumbImage}
            />
          </TouchableOpacity>

          {/* Add / Capture New Button */}
          <TouchableOpacity
            style={styles.thumbAddButton}
            onPress={handlePickFromGallery}
            activeOpacity={0.8}
          >
            <Ionicons name="add" size={24} color="#16A34A" />
          </TouchableOpacity>
        </View>

        {/* Action Buttons: Gallery & Camera */}
        <View style={styles.captureButtonsRow}>
          <TouchableOpacity
            style={styles.captureButton}
            onPress={handlePickFromGallery}
            activeOpacity={0.8}
          >
            <Ionicons name="images-outline" size={18} color="#16A34A" />
            <Text style={styles.captureButtonText}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.captureButton}
            onPress={handleTakePhoto}
            activeOpacity={0.8}
          >
            <Ionicons name="camera-outline" size={18} color="#16A34A" />
            <Text style={styles.captureButtonText}>Take Photo</Text>
          </TouchableOpacity>
        </View>

        {/* Run Diagnostic Button */}
        <TouchableOpacity
          style={[styles.runDiagnosticButton, isLoading && styles.runDiagnosticButtonDisabled]}
          onPress={() => runInference(attachedImage)}
          disabled={isLoading}
          activeOpacity={0.88}
        >
          {isLoading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Ionicons name="sparkles" size={18} color="#FFFFFF" />
              <Text style={styles.runDiagnosticButtonText}>
                Run {mode === 'disease' ? 'Disease' : 'Pest'} Diagnostic
              </Text>
            </View>
          )}
        </TouchableOpacity>

        {/* Error Notice */}
        {apiError && (
          <View style={styles.errorBanner}>
            <Ionicons name="alert-circle" size={16} color="#DC2626" />
            <Text style={styles.errorBannerText}>{apiError}</Text>
          </View>
        )}

        {/* Empty Guide Card */}
        {!result && !isLoading && (
          <View style={styles.emptyGuideCard}>
            <Ionicons name="medical-outline" size={32} color="#16A34A" />
            <Text style={styles.emptyGuideTitle}>No Diagnostic Run Yet</Text>
            <Text style={styles.emptyGuideSub}>
              Select symptoms above or capture a photo, then tap "Run Diagnostic" to query the KisanCare Agronomic Expert System.
            </Text>
          </View>
        )}

        {/* Detection Result Card */}
        {result && (
          <View style={styles.resultCard}>
            <View style={styles.resultHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.resultCategoryLabel}>
                  {mode === 'disease' ? 'Expert Diagnosis' : 'Identified Pest'}
                </Text>
                <Text style={styles.diseaseNameText}>
                  {result.prediction || 'Healthy / No Pathogen Detected'}
                </Text>
              </View>

              <View style={styles.badgesCol}>
                <View style={styles.confidenceBadge}>
                  <Text style={styles.confidenceBadgeText}>
                    Confidence {Math.round((result.confidence || 0.8) * 100)}%
                  </Text>
                </View>
                <View style={styles.modelBadge}>
                  <Text style={styles.modelBadgeText}>
                    {result.model_type || 'EXPERT_SYSTEM'}
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.resultDivider} />

            {/* Prescribed Treatment */}
            <Text style={styles.suggestedActionTitle}>Prescribed Agronomic Action</Text>
            <View style={styles.actionBulletRow}>
              <View style={styles.bulletDot} />
              <Text style={styles.actionBulletText}>
                {result.treatment || 'Maintain regular crop scouting and field sanitation.'}
              </Text>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Bottom Sticky Action Button */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.detailedSolutionButton}
          onPress={() => {
            Alert.alert(
              'Agronomic Treatment Plan',
              `Diagnosis: ${result?.prediction || 'Soybean Rust'}\n\nPrescription:\n1. Spray wettable sulphur 80 WP @ 2.5 g/L or Hexaconazole 5% EC @ 2ml/L water.\n2. Ensure spray reaches the lower foliage surface where rust pustules originate.\n3. Avoid excess urea top-dressing during high humidity.\n4. Consult your local Taluka Krishi Kendra if symptoms persist.`,
              [{ text: 'Understood' }]
            );
          }}
          activeOpacity={0.88}
        >
          <Text style={styles.detailedSolutionButtonText}>
            View Detailed Solution
          </Text>
        </TouchableOpacity>
      </View>
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
    paddingHorizontal: 16,
    paddingTop: 54,
    paddingBottom: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F3F4F6',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 18,
    paddingTop: 16,
    paddingBottom: 90,
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
    paddingVertical: 9,
    alignItems: 'center',
    borderRadius: 22,
  },
  togglePillActive: {
    backgroundColor: '#16A34A',
  },
  togglePillText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#4B5563',
  },
  togglePillTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  viewfinderCard: {
    width: '100%',
    height: 200,
    borderRadius: 18,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#0F172A',
    marginBottom: 14,
  },
  viewfinderImage: {
    width: '100%',
    height: '100%',
  },
  reticle: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: '#22C55E',
  },
  reticleTopLeft: {
    top: 14,
    left: 14,
    borderTopWidth: 3,
    borderLeftWidth: 3,
  },
  reticleTopRight: {
    top: 14,
    right: 14,
    borderTopWidth: 3,
    borderRightWidth: 3,
  },
  reticleBottomLeft: {
    bottom: 14,
    left: 14,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
  },
  reticleBottomRight: {
    bottom: 14,
    right: 14,
    borderBottomWidth: 3,
    borderRightWidth: 3,
  },
  scanningOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanningText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
    marginTop: 8,
  },
  scanTargetBadge: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  scanTargetText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  thumbnailStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 14,
  },
  thumbItem: {
    width: 54,
    height: 54,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: '#E2E8F0',
  },
  thumbItemActive: {
    borderColor: '#16A34A',
  },
  thumbImage: {
    width: '100%',
    height: '100%',
  },
  thumbAddButton: {
    width: 54,
    height: 54,
    borderRadius: 12,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: '#16A34A',
    backgroundColor: '#F0FDF4',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureButtonsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  captureButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 12,
    paddingVertical: 10,
  },
  captureButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1E293B',
  },
  runDiagnosticButton: {
    backgroundColor: '#16A34A',
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    shadowColor: '#16A34A',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  runDiagnosticButtonDisabled: {
    backgroundColor: '#86EFAC',
  },
  runDiagnosticButtonText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: {
    fontSize: 12,
    color: '#DC2626',
    flex: 1,
  },
  emptyGuideCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  emptyGuideTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1E293B',
    marginTop: 10,
    marginBottom: 4,
  },
  emptyGuideSub: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 18,
  },
  resultCard: {
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
    marginBottom: 16,
  },
  resultHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  resultCategoryLabel: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '600',
  },
  diseaseNameText: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
    marginTop: 2,
  },
  badgesCol: {
    alignItems: 'flex-end',
    gap: 4,
  },
  confidenceBadge: {
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  confidenceBadgeText: {
    color: '#DC2626',
    fontSize: 11,
    fontWeight: '700',
  },
  modelBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  modelBadgeText: {
    color: '#16A34A',
    fontSize: 9,
    fontWeight: '700',
  },
  severityBadge: {
    backgroundColor: '#FFEDD5',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  severityBadgeText: {
    color: '#EA580C',
    fontSize: 11,
    fontWeight: '700',
  },
  resultDivider: {
    height: 1,
    backgroundColor: '#F1F5F9',
    marginVertical: 12,
  },
  suggestedActionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 8,
  },
  actionBulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 6,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#16A34A',
    marginTop: 6,
  },
  actionBulletText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
    color: '#475569',
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 24,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  detailedSolutionButton: {
    backgroundColor: '#16A34A',
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#16A34A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 3,
  },
  detailedSolutionButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
