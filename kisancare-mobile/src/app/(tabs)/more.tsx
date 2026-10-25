import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, Image } from 'react-native';
import { ScreenContainer } from '@/components/common/ScreenContainer';
import { SectionHeader } from '@/components/common/SectionHeader';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { BackendDiagnostic } from '@/components/common/BackendDiagnostic';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { t, setLanguage, getLanguage, SupportedLanguage } from '@/utils/localization';

const farmerAvatar = require('../../../assets/images/ui/farmer_avatar.png');

type IconName = keyof typeof Ionicons.glyphMap;

interface SettingItemProps {
  icon: IconName;
  title: string;
  subtitle?: string;
  onPress: () => void;
  badge?: string;
}

export default function MoreScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();
  const [currentLang, setCurrentLangState] = useState<SupportedLanguage>(getLanguage());

  const handleLanguageChange = (lang: SupportedLanguage) => {
    setLanguage(lang);
    setCurrentLangState(lang);
    Alert.alert(
      'Language Selected',
      lang === 'hi' ? 'हिंदी भाषा चुनी गई है।' : lang === 'mr' ? 'मराठी भाषा निवडली आहे.' : 'English language selected.',
    );
  };

  const renderSettingItem = ({
    icon,
    title,
    subtitle,
    onPress,
    badge,
  }: SettingItemProps) => (
    <TouchableOpacity
      style={[styles.itemRow, { borderBottomColor: theme.borderLight }]}
      onPress={onPress}
      activeOpacity={0.7}
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={title}
    >
      <View style={[styles.itemIconWrapper, { backgroundColor: theme.primaryContainer }]}>
        <Ionicons name={icon} size={20} color={theme.primary} />
      </View>
      <View style={styles.itemTextContainer}>
        <Text style={[styles.itemTitle, { color: theme.text }]}>{title}</Text>
        {subtitle ? (
          <Text style={[styles.itemSubtitle, { color: theme.textSecondary }]}>
            {subtitle}
          </Text>
        ) : null}
      </View>
      {badge ? (
        <Badge label={badge} variant="success" size="sm" />
      ) : (
        <Ionicons name="chevron-forward" size={18} color={theme.textMuted} />
      )}
    </TouchableOpacity>
  );

  return (
    <ScreenContainer>
      {/* Screen Title */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>
          {t('more.title')}
        </Text>
      </View>

      {/* Profile Overview Card */}
      <Card
        onPress={() => router.push('/profile')}
        variant="elevated"
        style={styles.profileCard}
      >
        <View style={styles.profileRow}>
          <Image source={farmerAvatar} style={styles.avatarImage} />
          <View style={{ flex: 1, marginLeft: Spacing.three }}>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={[styles.profileName, { color: theme.text }]}>
                Ramesh Patil
              </Text>
              <Ionicons
                name="checkmark-circle"
                size={16}
                color={theme.primary}
                style={{ marginLeft: 4 }}
              />
            </View>
            <Text style={[styles.profilePhone, { color: theme.textSecondary }]}>
              +91 98765 43210 • Pimpalgaon, Jalna
            </Text>
            <Text style={[styles.profileFarm, { color: theme.primary }]}>
              Patil Krishi Farm (5.2 Acres • 3 Parcels)
            </Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={theme.textMuted} />
        </View>
      </Card>

      {/* Backend Connectivity Diagnostics */}
      <SectionHeader title="API Connectivity & Diagnostics" />
      <BackendDiagnostic />

      {/* Language Switcher */}
      <SectionHeader title={t('more.languageSection')} />
      <Card variant="outlined" style={styles.cardSection}>
        <View style={styles.langRow}>
          <TouchableOpacity
            style={[
              styles.langButton,
              currentLang === 'en' && { backgroundColor: theme.primary },
            ]}
            onPress={() => handleLanguageChange('en')}
          >
            <Text
              style={[
                styles.langText,
                { color: currentLang === 'en' ? '#FFFFFF' : theme.text },
              ]}
            >
              English
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.langButton,
              currentLang === 'hi' && { backgroundColor: theme.primary },
            ]}
            onPress={() => handleLanguageChange('hi')}
          >
            <Text
              style={[
                styles.langText,
                { color: currentLang === 'hi' ? '#FFFFFF' : theme.text },
              ]}
            >
              हिंदी
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.langButton,
              currentLang === 'mr' && { backgroundColor: theme.primary },
            ]}
            onPress={() => handleLanguageChange('mr')}
          >
            <Text
              style={[
                styles.langText,
                { color: currentLang === 'mr' ? '#FFFFFF' : theme.text },
              ]}
            >
              मराठी
            </Text>
          </TouchableOpacity>
        </View>
      </Card>

      {/* Farm Features, AI & Documents */}
      <SectionHeader title="Features & Farm Records" />
      <Card variant="outlined" style={styles.cardSection}>
        {renderSettingItem({
          icon: 'chatbubble-ellipses-outline',
          title: 'KisanCare AI Copilot',
          subtitle: 'Conversational intelligence across crops, pests, mandis & rentals',
          badge: 'AI COPILOT',
          onPress: () => router.push('/chatbot' as any),
        })}
        {renderSettingItem({
          icon: 'construct-outline',
          title: 'Farm Equipment Rentals',
          subtitle: 'Live machinery directory (/api/v1/rentals)',
          badge: 'LIVE API',
          onPress: () => router.push('/rentals' as any),
        })}
        {renderSettingItem({
          icon: 'wallet-outline',
          title: 'Farm Finances & Crop Loans',
          subtitle: 'Revenue ₹2.4L • Net Profit ₹1.68L • Active KCC',
          badge: 'FINANCES',
          onPress: () => router.push('/finances' as any),
        })}
        {renderSettingItem({
          icon: 'globe-outline',
          title: 'Digital Twin Simulation',
          subtitle: 'Field-level agronomic forecasting',
          badge: 'AI SIM',
          onPress: () => router.push('/digital-twin' as any),
        })}
        {renderSettingItem({
          icon: 'document-text-outline',
          title: 'Soil Health Cards (SHC)',
          subtitle: 'Latest test dated 10 Jan 2026',
          onPress: () => router.push('/soil-report'),
        })}
        {renderSettingItem({
          icon: 'shield-checkmark-outline',
          title: 'PM-Kisan & Crop Insurance',
          subtitle: 'Active insurance policy #MH-2026-88',
          onPress: () =>
            Alert.alert(
              'Govt Schemes',
              'PM-Fasal Bima Yojana policy active for Kharif 2026.',
            ),
        })}
      </Card>

      {/* Support & Helplines */}
      <SectionHeader title={t('more.supportSection')} />
      <Card variant="outlined" style={styles.cardSection}>
        {renderSettingItem({
          icon: 'call-outline',
          title: 'Kisan Call Center (Toll Free)',
          subtitle: '1800-180-1551 (6:00 AM - 10:00 PM)',
          onPress: () =>
            Alert.alert(
              'Call Center',
              'Calling Kisan Call Center at 1800-180-1551...',
            ),
        })}
        {renderSettingItem({
          icon: 'people-outline',
          title: 'Krishi Vigyan Kendra (KVK)',
          subtitle: 'Pune District Agricultural Extension Office',
          onPress: () =>
            Alert.alert(
              'KVK Pune',
              'Baramati KVK Specialist Contact: 02112-255207',
            ),
        })}
      </Card>

      {/* App Version Info */}
      <View style={styles.versionContainer}>
        <Text style={[styles.versionText, { color: theme.textMuted }]}>
          {t('more.appVersion')}
        </Text>
        <Text style={[styles.copyrightText, { color: theme.textMuted }]}>
          KisanCare Agriculture Intelligence Platform
        </Text>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingVertical: Spacing.three,
  },
  title: {
    fontSize: Typography.sizes.xxl,
    fontWeight: Typography.weights.bold,
  },
  profileCard: {
    marginBottom: Spacing.four,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarImage: {
    width: 56,
    height: 56,
    borderRadius: 28,
  },
  profileAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileName: {
    fontSize: Typography.sizes.lg,
    fontWeight: Typography.weights.bold,
  },
  profilePhone: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
  profileFarm: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.semibold,
    marginTop: 4,
  },
  cardSection: {
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.two,
    marginBottom: Spacing.four,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.three,
    borderBottomWidth: 1,
  },
  itemIconWrapper: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.three,
  },
  itemTextContainer: {
    flex: 1,
    paddingRight: Spacing.two,
  },
  itemTitle: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.semibold,
  },
  itemSubtitle: {
    fontSize: Typography.sizes.xs,
    marginTop: 2,
  },
  langRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: Spacing.one,
  },
  langButton: {
    flex: 1,
    paddingVertical: Spacing.two,
    alignItems: 'center',
    borderRadius: BorderRadius.sm,
    marginHorizontal: Spacing.one,
    backgroundColor: '#EEF4EF',
  },
  langText: {
    fontSize: Typography.sizes.sm,
    fontWeight: Typography.weights.semibold,
  },
  versionContainer: {
    alignItems: 'center',
    paddingVertical: Spacing.six,
  },
  versionText: {
    fontSize: Typography.sizes.xs,
    fontWeight: Typography.weights.medium,
  },
  copyrightText: {
    fontSize: 11,
    marginTop: 4,
  },
});
