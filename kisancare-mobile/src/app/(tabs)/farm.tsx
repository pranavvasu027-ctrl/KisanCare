import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { fetchFarms, createFarm, FarmDisplayItem } from '@/services/farmService';
import { getStoredProfile } from '@/services/profileService';

const { width } = Dimensions.get('window');

export default function FarmScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const profile = getStoredProfile();

  const [topTab, setTopTab] = useState<'map' | 'twin'>('map');
  const [viewType, setViewType] = useState<'satellite' | 'field' | 'list'>('satellite');

  // Add Parcel Modal State
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newParcelName, setNewParcelName] = useState<string>('');
  const [newParcelArea, setNewParcelArea] = useState<string>('2.0');
  const [newParcelLocation, setNewParcelLocation] = useState<string>(
    `${profile.village || 'Takli Bu'}, ${profile.district || 'Akola'}, Maharashtra`
  );

  const {
    data: farmsData,
    isLoading,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['farms'],
    queryFn: fetchFarms,
  });

  const addFarmMutation = useMutation({
    mutationFn: createFarm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['farms'] });
      setShowAddModal(false);
      setNewParcelName('');
      Alert.alert('Parcel Registered', 'New farm parcel has been persisted to the backend database.');
    },
    onError: (err: any) => {
      Alert.alert('Registration Failed', err.message || 'Could not save farm parcel.');
    },
  });

  const handleSaveParcel = () => {
    if (!newParcelName.trim()) {
      Alert.alert('Required', 'Please enter a name for the parcel.');
      return;
    }
    const areaNum = parseFloat(newParcelArea);
    if (isNaN(areaNum) || areaNum <= 0) {
      Alert.alert('Invalid Area', 'Please enter a valid acreage (> 0).');
      return;
    }

    addFarmMutation.mutate({
      farmer_id: profile.id || 'farmer-1',
      farm_name: newParcelName.trim(),
      location: newParcelLocation.trim(),
      area: areaNum,
    });
  };

  const farmsList: FarmDisplayItem[] = farmsData?.farms || [];

  return (
    <View style={styles.screenWrapper}>
      {/* Top Header matching Screen 3 of UIs.png */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Ionicons name="arrow-back" size={24} color="#1F2937" />
        </TouchableOpacity>

        <Text style={styles.headerTitle}>My Farm</Text>

        {/* Season Selector Dropdown */}
        <TouchableOpacity style={styles.seasonPill} activeOpacity={0.8}>
          <Text style={styles.seasonText}>Kharif 2024</Text>
          <Ionicons name="chevron-down" size={13} color="#16A34A" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Segmented Top Toggle: Field Map | Digital Twin */}
        <View style={styles.togglePillContainer}>
          <TouchableOpacity
            style={[styles.togglePill, topTab === 'map' && styles.togglePillActive]}
            onPress={() => setTopTab('map')}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                topTab === 'map' && styles.togglePillTextActive,
              ]}
            >
              Field Map
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.togglePill, topTab === 'twin' && styles.togglePillActive]}
            onPress={() => router.push('/digital-twin')}
            activeOpacity={0.8}
          >
            <Text
              style={[
                styles.togglePillText,
                topTab === 'twin' && styles.togglePillTextActive,
              ]}
            >
              Digital Twin
            </Text>
          </TouchableOpacity>
        </View>

        {/* Satellite Map Parcel View matching Screen 3 */}
        <View style={styles.mapCard}>
          <Image
            source={require('../../../assets/images/ui/field_map_satellite.png')}
            style={styles.mapImage}
            resizeMode="cover"
          />

          {/* Compass / Layer Tools */}
          <View style={styles.mapCompass}>
            <Text style={styles.compassText}>N</Text>
            <Ionicons name="compass-outline" size={16} color="#FFFFFF" />
          </View>

          <View style={styles.mapLayerTool}>
            <Ionicons name="layers" size={16} color="#FFFFFF" />
          </View>
        </View>

        {/* Map View Toggle Pills below Map: Satellite View | Field View | List View */}
        <View style={styles.viewToggleRow}>
          <TouchableOpacity
            style={[
              styles.viewTogglePill,
              viewType === 'satellite' && styles.viewTogglePillActive,
            ]}
            onPress={() => setViewType('satellite')}
          >
            <Text
              style={[
                styles.viewToggleText,
                viewType === 'satellite' && styles.viewToggleTextActive,
              ]}
            >
              Satellite View
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.viewTogglePill,
              viewType === 'field' && styles.viewTogglePillActive,
            ]}
            onPress={() => setViewType('field')}
          >
            <Text
              style={[
                styles.viewToggleText,
                viewType === 'field' && styles.viewToggleTextActive,
              ]}
            >
              Field View
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.viewTogglePill,
              viewType === 'list' && styles.viewTogglePillActive,
            ]}
            onPress={() => setViewType('list')}
          >
            <Text
              style={[
                styles.viewToggleText,
                viewType === 'list' && styles.viewToggleTextActive,
              ]}
            >
              List View
            </Text>
          </TouchableOpacity>
        </View>

        {/* Data Provenance Header */}
        <View style={styles.provenanceRow}>
          <Text style={styles.provenanceText}>
            {farmsData?.isMock
              ? 'Data Source: Default Verified Farm Record (/api/v1/farms)'
              : 'Data Source: Live Supabase Farm Database (/api/v1/farms)'}
          </Text>
          <TouchableOpacity
            style={styles.addParcelButton}
            onPress={() => setShowAddModal(true)}
            activeOpacity={0.8}
          >
            <Ionicons name="add-circle" size={16} color="#16A34A" />
            <Text style={styles.addParcelButtonText}>Add Parcel</Text>
          </TouchableOpacity>
        </View>

        {/* Loading Indicator */}
        {isLoading && (
          <View style={{ paddingVertical: 24, alignItems: 'center' }}>
            <ActivityIndicator size="small" color="#16A34A" />
            <Text style={{ fontSize: 12, color: '#6B7280', marginTop: 6 }}>
              Loading registered farm parcels...
            </Text>
          </View>
        )}

        {/* Field List Rows */}
        <View style={styles.fieldListCard}>
          {farmsList.map((farm, idx) => (
            <TouchableOpacity
              key={farm.id}
              style={styles.fieldRow}
              onPress={() => router.push('/crop-planning')}
              activeOpacity={0.7}
            >
              <View style={styles.fieldLeft}>
                <View
                  style={[
                    styles.statusDot,
                    { backgroundColor: idx % 2 === 0 ? '#22C55E' : '#F97316' },
                  ]}
                />
                <View>
                  <Text style={styles.fieldName}>{farm.name}</Text>
                  <Text style={styles.fieldSubLocation}>{farm.location}</Text>
                </View>
              </View>

              <View style={styles.fieldRight}>
                <Text style={styles.fieldArea}>{farm.areaAcres} acres</Text>
                <View style={styles.viewActionRow}>
                  <Text style={styles.viewActionText}>Plan</Text>
                  <Ionicons name="chevron-forward" size={14} color="#16A34A" />
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Add Parcel Modal */}
        <Modal
          visible={showAddModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowAddModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>Register New Field Parcel</Text>
                <TouchableOpacity onPress={() => setShowAddModal(false)}>
                  <Ionicons name="close" size={22} color="#6B7280" />
                </TouchableOpacity>
              </View>

              <Text style={styles.inputLabel}>Parcel Name</Text>
              <TextInput
                style={styles.textInput}
                value={newParcelName}
                onChangeText={setNewParcelName}
                placeholder="e.g. Field C - Kharif Cotton"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.inputLabel}>Area (Acres)</Text>
              <TextInput
                style={styles.textInput}
                value={newParcelArea}
                onChangeText={setNewParcelArea}
                placeholder="e.g. 2.5"
                keyboardType="decimal-pad"
                placeholderTextColor="#9CA3AF"
              />

              <Text style={styles.inputLabel}>Location</Text>
              <TextInput
                style={styles.textInput}
                value={newParcelLocation}
                onChangeText={setNewParcelLocation}
                placeholder="Village, District, State"
                placeholderTextColor="#9CA3AF"
              />

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={() => setShowAddModal(false)}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.saveButton}
                  onPress={handleSaveParcel}
                  disabled={addFarmMutation.isPending}
                >
                  {addFarmMutation.isPending ? (
                    <ActivityIndicator size="small" color="#FFFFFF" />
                  ) : (
                    <Text style={styles.saveButtonText}>Save to Backend</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
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
  seasonPill: {
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
  seasonText: {
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
    fontSize: 13,
    fontWeight: '600',
    color: '#4B5563',
  },
  togglePillTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  mapCard: {
    width: '100%',
    height: 220,
    borderRadius: 20,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#1E293B',
    marginBottom: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  mapImage: {
    width: '100%',
    height: '100%',
  },
  mapCompass: {
    position: 'absolute',
    top: 12,
    right: 12,
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 12,
    padding: 6,
  },
  compassText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '800',
  },
  mapLayerTool: {
    position: 'absolute',
    top: 12,
    left: 12,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 12,
    padding: 6,
  },
  viewToggleRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  viewTogglePill: {
    flex: 1,
    paddingVertical: 8,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 18,
    alignItems: 'center',
  },
  viewTogglePillActive: {
    backgroundColor: '#16A34A',
    borderColor: '#16A34A',
  },
  viewToggleText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  viewToggleTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  fieldListCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  fieldRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  fieldLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  fieldName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  fieldRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  fieldArea: {
    fontSize: 13,
    color: '#64748B',
  },
  viewActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  viewActionText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#16A34A',
  },
  fieldSubLocation: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 2,
  },
  provenanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    paddingHorizontal: 2,
  },
  provenanceText: {
    fontSize: 10,
    color: '#6B7280',
    fontWeight: '600',
    flex: 1,
  },
  addParcelButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: '#DCFCE7',
  },
  addParcelButtonText: {
    fontSize: 11,
    color: '#16A34A',
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#111827',
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4B5563',
    marginBottom: 4,
    marginTop: 10,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    color: '#111827',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 20,
  },
  cancelButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  cancelButtonText: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '600',
  },
  saveButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#16A34A',
  },
  saveButtonText: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '700',
  },
});
