import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { clearSession } from '@/services/authService';
import { getStoredProfile, saveProfile, validateProfile, FarmerProfile } from '@/services/profileService';

export default function ProfileScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const [profile, setProfile] = useState<FarmerProfile>(getStoredProfile());
  const [showEditModal, setShowEditModal] = useState<boolean>(false);
  const [editName, setEditName] = useState<string>(profile.fullName);
  const [editPhone, setEditPhone] = useState<string>(profile.phone);
  const [editVillage, setEditVillage] = useState<string>(profile.village);
  const [editDistrict, setEditDistrict] = useState<string>(profile.district);
  const [editLand, setEditLand] = useState<string>(String(profile.totalLandAcres || '5.0'));
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleOpenEdit = () => {
    setEditName(profile.fullName);
    setEditPhone(profile.phone);
    setEditVillage(profile.village);
    setEditDistrict(profile.district);
    setEditLand(String(profile.totalLandAcres || '5.0'));
    setValidationError(null);
    setShowEditModal(true);
  };

  const handleSave = async () => {
    const landNum = parseFloat(editLand);
    const updatedData: Partial<FarmerProfile> = {
      fullName: editName.trim(),
      phone: editPhone.trim(),
      village: editVillage.trim(),
      district: editDistrict.trim(),
      totalLandAcres: isNaN(landNum) ? profile.totalLandAcres : landNum,
    };

    const val = validateProfile(updatedData);
    if (!val.isValid) {
      const firstErr = Object.values(val.errors)[0];
      setValidationError(firstErr);
      return;
    }

    setIsSaving(true);
    setValidationError(null);
    try {
      const saved = await saveProfile(updatedData);
      setProfile(saved);
      setShowEditModal(false);
      Alert.alert('Profile Saved', 'Your farmer profile details have been successfully updated.');
    } catch (err: any) {
      setValidationError(err?.message || 'Could not save profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSignOut = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out from KisanCare?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await clearSession();
            router.replace('/welcome');
          },
        },
      ]
    );
  };

  const handleLanguageChoice = () => {
    Alert.alert(
      'Select Language / भाषा निवडा',
      'Choose your preferred language:',
      [
        {
          text: 'English',
          onPress: async () => {
            const saved = await saveProfile({ preferredLanguage: 'en' });
            setProfile(saved);
          },
        },
        {
          text: 'हिंदी (Hindi)',
          onPress: async () => {
            const saved = await saveProfile({ preferredLanguage: 'hi' });
            setProfile(saved);
          },
        },
        {
          text: 'मराठी (Marathi)',
          onPress: async () => {
            const saved = await saveProfile({ preferredLanguage: 'mr' });
            setProfile(saved);
          },
        },
      ]
    );
  };

  return (
    <View style={styles.screenWrapper}>
      {/* Top Header matching Screen 10 */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Ionicons name="arrow-back" size={24} color="#1F2937" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Farmer Profile</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* User Profile Card matching Screen 10 */}
        <View style={styles.profileCard}>
          <View style={styles.avatarWrapper}>
            <Image
              source={require('../../assets/images/ui/farmer_avatar.png')}
              style={styles.avatarImage}
            />
          </View>

          <View style={styles.profileInfo}>
            <Text style={styles.userName}>{profile.fullName}</Text>
            <View style={styles.locationRow}>
              <Ionicons name="location-sharp" size={13} color="#16A34A" />
              <Text style={styles.locationText}>
                {profile.village}, {profile.district}
              </Text>
            </View>
            <Text style={styles.phoneSubText}>+91 {profile.phone}</Text>
          </View>

          <TouchableOpacity
            style={styles.editButton}
            onPress={handleOpenEdit}
            activeOpacity={0.8}
          >
            <Text style={styles.editButtonText}>Edit</Text>
          </TouchableOpacity>
        </View>

        {/* Land Holding Summary Card */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryCol}>
            <Text style={styles.summaryLabel}>Total Landholding</Text>
            <Text style={styles.summaryValue}>{profile.totalLandAcres} Acres</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryCol}>
            <Text style={styles.summaryLabel}>Primary Crops</Text>
            <Text style={styles.summaryValue}>Cotton, Soybean</Text>
          </View>
        </View>

        {/* Menu Items matching Screen 10 of UIs.png */}
        <View style={styles.menuCard}>
          {/* 1. My Farm Details */}
          <TouchableOpacity
            style={styles.menuRow}
            onPress={() => router.push('/(tabs)/farm')}
            activeOpacity={0.7}
          >
            <View style={styles.menuIconBox}>
              <Ionicons name="home-outline" size={20} color="#16A34A" />
            </View>
            <Text style={styles.menuTitle}>My Farm Details</Text>
            <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
          </TouchableOpacity>

          {/* 2. Farm History */}
          <TouchableOpacity
            style={styles.menuRow}
            onPress={() => router.push('/crop-planning')}
            activeOpacity={0.7}
          >
            <View style={styles.menuIconBox}>
              <Ionicons name="document-text-outline" size={20} color="#0284C7" />
            </View>
            <Text style={styles.menuTitle}>Crop Planning</Text>
            <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
          </TouchableOpacity>

          {/* 3. Notifications */}
          <TouchableOpacity
            style={styles.menuRow}
            onPress={() => router.push('/(tabs)/advisory')}
            activeOpacity={0.7}
          >
            <View style={styles.menuIconBox}>
              <Ionicons name="notifications-outline" size={20} color="#EA580C" />
            </View>
            <Text style={styles.menuTitle}>Agro Advisories</Text>
            <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
          </TouchableOpacity>

          {/* 4. Language */}
          <TouchableOpacity
            style={styles.menuRow}
            onPress={handleLanguageChoice}
            activeOpacity={0.7}
          >
            <View style={styles.menuIconBox}>
              <Ionicons name="globe-outline" size={20} color="#16A34A" />
            </View>
            <Text style={styles.menuTitle}>Language</Text>
            <View style={styles.langValueRow}>
              <Text style={styles.langValueText}>
                {profile.preferredLanguage === 'mr'
                  ? 'मराठी'
                  : profile.preferredLanguage === 'hi'
                  ? 'हिंदी'
                  : 'English'}
              </Text>
              <Ionicons name="chevron-down" size={14} color="#64748B" />
            </View>
          </TouchableOpacity>

          {/* 5. Help & Support */}
          <TouchableOpacity
            style={styles.menuRow}
            onPress={() =>
              Alert.alert(
                'Krishi Helpline',
                'Toll-free Kisan Call Centre: 1800-180-1551\nAkola KVK Office: +91 724 2258410'
              )
            }
            activeOpacity={0.7}
          >
            <View style={styles.menuIconBox}>
              <Ionicons name="help-circle-outline" size={20} color="#7C3AED" />
            </View>
            <Text style={styles.menuTitle}>Help & Support</Text>
            <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
          </TouchableOpacity>

          {/* 6. Settings */}
          <TouchableOpacity
            style={styles.menuRow}
            onPress={() =>
              Alert.alert('Settings', 'App version: v1.0.0-hackathon\nBuild: 2026.10.25')
            }
            activeOpacity={0.7}
          >
            <View style={styles.menuIconBox}>
              <Ionicons name="settings-outline" size={20} color="#475569" />
            </View>
            <Text style={styles.menuTitle}>Settings</Text>
            <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
          </TouchableOpacity>

          {/* 7. Sign Out */}
          <TouchableOpacity
            style={[styles.menuRow, { borderBottomWidth: 0 }]}
            onPress={handleSignOut}
            activeOpacity={0.7}
          >
            <View style={[styles.menuIconBox, { backgroundColor: '#FEE2E2' }]}>
              <Ionicons name="log-out-outline" size={20} color="#DC2626" />
            </View>
            <Text style={[styles.menuTitle, { color: '#DC2626' }]}>Sign Out</Text>
            <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Edit Profile Modal */}
      <Modal
        visible={showEditModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowEditModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Edit Farmer Details</Text>
              <TouchableOpacity onPress={() => setShowEditModal(false)}>
                <Ionicons name="close" size={22} color="#6B7280" />
              </TouchableOpacity>
            </View>

            {validationError && (
              <View style={styles.errorBox}>
                <Ionicons name="alert-circle" size={16} color="#DC2626" />
                <Text style={styles.errorText}>{validationError}</Text>
              </View>
            )}

            <Text style={styles.fieldLabel}>Full Name</Text>
            <TextInput
              style={styles.inputField}
              value={editName}
              onChangeText={setEditName}
              placeholder="e.g. Ramesh Kumar"
              placeholderTextColor="#9CA3AF"
            />

            <Text style={styles.fieldLabel}>Mobile Number (10 digits)</Text>
            <TextInput
              style={styles.inputField}
              value={editPhone}
              onChangeText={setEditPhone}
              placeholder="9876543210"
              keyboardType="phone-pad"
              maxLength={10}
              placeholderTextColor="#9CA3AF"
            />

            <View style={{ flexDirection: 'row', gap: 10 }}>
              <View style={{ flex: 1 }}>
                <Text style={styles.fieldLabel}>Village</Text>
                <TextInput
                  style={styles.inputField}
                  value={editVillage}
                  onChangeText={setEditVillage}
                  placeholder="Village"
                  placeholderTextColor="#9CA3AF"
                />
              </View>

              <View style={{ flex: 1 }}>
                <Text style={styles.fieldLabel}>District</Text>
                <TextInput
                  style={styles.inputField}
                  value={editDistrict}
                  onChangeText={setEditDistrict}
                  placeholder="District"
                  placeholderTextColor="#9CA3AF"
                />
              </View>
            </View>

            <Text style={styles.fieldLabel}>Total Landholding (Acres)</Text>
            <TextInput
              style={styles.inputField}
              value={editLand}
              onChangeText={setEditLand}
              placeholder="e.g. 5.2"
              keyboardType="decimal-pad"
              placeholderTextColor="#9CA3AF"
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalCancelButton}
                onPress={() => setShowEditModal(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalSaveButton, isSaving && { opacity: 0.6 }]}
                onPress={handleSave}
                disabled={isSaving}
              >
                {isSaving ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.modalSaveText}>Save Profile</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
    paddingTop: 18,
    paddingBottom: 36,
  },
  profileCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 2,
  },
  avatarWrapper: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: '#16A34A',
    overflow: 'hidden',
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  profileInfo: {
    flex: 1,
    marginLeft: 14,
  },
  userName: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
    gap: 3,
  },
  locationText: {
    fontSize: 13,
    color: '#64748B',
  },
  editButton: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 14,
  },
  editButtonText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1E293B',
  },
  menuCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  menuIconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  menuTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
  },
  langValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginRight: 6,
  },
  langValueText: {
    fontSize: 13,
    color: '#64748B',
  },
  phoneSubText: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 2,
    fontWeight: '500',
  },
  summaryCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  summaryCol: {
    flex: 1,
    alignItems: 'center',
  },
  summaryDivider: {
    width: 1,
    height: 32,
    backgroundColor: '#E2E8F0',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
  },
  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    gap: 8,
  },
  errorText: {
    color: '#DC2626',
    fontSize: 13,
    flex: 1,
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
    marginTop: 8,
  },
  inputField: {
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 14,
    color: '#0F172A',
    backgroundColor: '#F8FAFC',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 20,
  },
  modalCancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  modalCancelText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
  },
  modalSaveButton: {
    backgroundColor: '#16A34A',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 100,
  },
  modalSaveText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
