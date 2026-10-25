import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { setLanguage, getLanguage, SupportedLanguage } from '@/utils/localization';

const { width, height } = Dimensions.get('window');

export default function WelcomeScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const [currentLang, setCurrentLang] = useState<SupportedLanguage>(getLanguage());

  const handleLanguageSelect = (lang: SupportedLanguage) => {
    setLanguage(lang);
    setCurrentLang(lang);
  };

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />

      {/* Top Branding Section */}
      <View style={styles.headerContent}>
        {/* Leaf Logo Emblem */}
        <View style={styles.logoBadge}>
          <Ionicons name="leaf" size={48} color="#16A34A" />
        </View>

        <Text style={styles.brandTitle}>KisanCare</Text>
        <Text style={styles.tagline}>Your Farm. Smarter Decisions.</Text>
        <Text style={styles.subTagline}>
          AI-Powered Farm Digital Twin for Every Farmer
        </Text>
      </View>

      {/* Center / Lower Visual Hero: Farmer in Golden Field */}
      <View style={styles.heroContainer}>
        <Image
          source={require('../../assets/images/ui/welcome_hero.png')}
          style={styles.heroImage}
          resizeMode="cover"
        />
        {/* Bottom subtle gradient overlay */}
        <View style={styles.heroGradient} />
      </View>

      {/* Action Buttons Section */}
      <View style={styles.bottomSection}>
        {/* Primary Get Started Button */}
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => router.push('/otp')}
          activeOpacity={0.88}
        >
          <Text style={styles.primaryButtonText}>Get Started</Text>
          <Ionicons name="arrow-forward" size={18} color="#FFFFFF" style={{ marginLeft: 6 }} />
        </TouchableOpacity>

        {/* Secondary Login Link */}
        <TouchableOpacity
          style={styles.secondaryLinkRow}
          onPress={() => router.push('/otp')}
          activeOpacity={0.7}
        >
          <Text style={styles.secondaryLinkPrompt}>Already registered? </Text>
          <Text style={styles.secondaryLinkAction}>Login with Phone →</Text>
        </TouchableOpacity>

        {/* Language Switcher Row */}
        <View style={styles.languageRow}>
          <Ionicons name="globe-outline" size={16} color="#6B7280" style={{ marginRight: 6 }} />
          <TouchableOpacity onPress={() => handleLanguageSelect('en')}>
            <Text
              style={[
                styles.langOption,
                currentLang === 'en' && styles.langOptionActive,
              ]}
            >
              English
            </Text>
          </TouchableOpacity>
          <Text style={styles.langDivider}>|</Text>
          <TouchableOpacity onPress={() => handleLanguageSelect('hi')}>
            <Text
              style={[
                styles.langOption,
                currentLang === 'hi' && styles.langOptionActive,
              ]}
            >
              हिंदी
            </Text>
          </TouchableOpacity>
          <Text style={styles.langDivider}>|</Text>
          <TouchableOpacity onPress={() => handleLanguageSelect('mr')}>
            <Text
              style={[
                styles.langOption,
                currentLang === 'mr' && styles.langOptionActive,
              ]}
            >
              मराठी
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7FAF7',
    justifyContent: 'space-between',
    paddingTop: 54,
  },
  headerContent: {
    alignItems: 'center',
    paddingHorizontal: 24,
    marginTop: 12,
  },
  logoBadge: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  brandTitle: {
    fontSize: 34,
    fontWeight: '800',
    color: '#142E15',
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2E7D32',
    marginTop: 4,
    textAlign: 'center',
  },
  subTagline: {
    fontSize: 14,
    fontWeight: '400',
    color: '#4B5563',
    marginTop: 6,
    textAlign: 'center',
    paddingHorizontal: 16,
  },
  heroContainer: {
    flex: 1,
    width: width,
    maxHeight: height * 0.46,
    position: 'relative',
    overflow: 'hidden',
    marginTop: 8,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  heroGradient: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 48,
    backgroundColor: 'rgba(247, 250, 247, 0.4)',
  },
  bottomSection: {
    paddingHorizontal: 24,
    paddingBottom: 28,
    backgroundColor: '#F7FAF7',
  },
  primaryButton: {
    backgroundColor: '#16A34A',
    height: 52,
    borderRadius: 26,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#16A34A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  primaryButtonText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  secondaryLinkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginTop: 6,
  },
  secondaryLinkPrompt: {
    fontSize: 14,
    color: '#64748B',
  },
  secondaryLinkAction: {
    fontSize: 14,
    fontWeight: '700',
    color: '#16A34A',
  },
  languageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
  },
  langOption: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
    paddingHorizontal: 4,
  },
  langOptionActive: {
    color: '#16A34A',
    fontWeight: '700',
  },
  langDivider: {
    fontSize: 14,
    color: '#D1D5DB',
    paddingHorizontal: 4,
  },
});
