import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Typography, BorderRadius } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

interface DocumentItem {
  id: string;
  title: string;
  uploadedAt: string;
  type: 'pdf' | 'bill' | 'insurance';
  iconColor: string;
  bgColor: string;
}

const RECENT_DOCUMENTS: DocumentItem[] = [
  {
    id: 'doc-1',
    title: '7/12 Extract',
    uploadedAt: 'Uploaded • 12 Aug 2024',
    type: 'pdf',
    iconColor: '#DC2626',
    bgColor: '#FEE2E2',
  },
  {
    id: 'doc-2',
    title: 'Soil Test Report',
    uploadedAt: 'Uploaded • 5 Aug 2024',
    type: 'pdf',
    iconColor: '#DC2626',
    bgColor: '#FEE2E2',
  },
  {
    id: 'doc-3',
    title: 'Fertilizer Bill (₹2,850)',
    uploadedAt: '₹2,850 • 28 Jul 2024',
    type: 'bill',
    iconColor: '#0284C7',
    bgColor: '#E0F2FE',
  },
  {
    id: 'doc-4',
    title: 'Crop Insurance Policy',
    uploadedAt: 'Uploaded • 15 Jul 2024',
    type: 'insurance',
    iconColor: '#16A34A',
    bgColor: '#DCFCE7',
  },
];

export default function FinancesScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'loans' | 'schemes'>('overview');

  return (
    <View style={styles.screenWrapper}>
      {/* Top Header matching Screen 8 of UIs.png */}
      <View style={styles.topHeader}>
        <TouchableOpacity
          onPress={() => router.back()}
          style={styles.backButton}
          activeOpacity={0.7}
        >
          <Ionicons name="arrow-back" size={24} color="#1F2937" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Finances & Documents</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Segmented Toggle Pills: Overview | Documents | Loans | Schemes */}
        <View style={styles.togglePillContainer}>
          {(['overview', 'documents', 'loans', 'schemes'] as const).map((tab) => (
            <TouchableOpacity
              key={tab}
              style={[
                styles.togglePill,
                activeTab === tab && styles.togglePillActive,
              ]}
              onPress={() => setActiveTab(tab)}
            >
              <Text
                style={[
                  styles.togglePillText,
                  activeTab === tab && styles.togglePillTextActive,
                ]}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* 2x2 Financial Metric Cards matching Screen 8 */}
        <View style={styles.metricsGrid}>
          {/* Card 1: Total Cost */}
          <View style={styles.metricCard}>
            <View style={[styles.metricIconCircle, { backgroundColor: '#FFEDD5' }]}>
              <Ionicons name="wallet-outline" size={22} color="#EA580C" />
            </View>
            <Text style={styles.metricLabel}>Total Cost</Text>
            <Text style={styles.metricValue}>₹46,200</Text>
            <Text style={styles.metricSub}>This Season</Text>
          </View>

          {/* Card 2: Expected Revenue */}
          <View style={styles.metricCard}>
            <View style={[styles.metricIconCircle, { backgroundColor: '#DCFCE7' }]}>
              <Ionicons name="trending-up-outline" size={22} color="#16A34A" />
            </View>
            <Text style={styles.metricLabel}>Expected Revenue</Text>
            <Text style={styles.metricValue}>₹1,06,700</Text>
            <Text style={[styles.metricSub, { color: '#16A34A' }]}>Projected</Text>
          </View>

          {/* Card 3: Expected Profit */}
          <View style={styles.metricCard}>
            <View style={[styles.metricIconCircle, { backgroundColor: '#F3E8FF' }]}>
              <Ionicons name="cash-outline" size={22} color="#9333EA" />
            </View>
            <Text style={styles.metricLabel}>Expected Profit</Text>
            <Text style={[styles.metricValue, { color: '#9333EA' }]}>₹60,500</Text>
            <Text style={styles.metricSub}>Net Income</Text>
          </View>

          {/* Card 4: Loan Eligibility */}
          <View style={styles.metricCard}>
            <View style={[styles.metricIconCircle, { backgroundColor: '#E0F2FE' }]}>
              <Ionicons name="business-outline" size={22} color="#0284C7" />
            </View>
            <Text style={styles.metricLabel}>Loan Eligibility</Text>
            <Text style={styles.metricValue}>₹2,00,000</Text>
            <Text style={styles.metricSub}>Estimated (KCC)</Text>
          </View>
        </View>

        {/* Recent Documents Header Row */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Recent Documents</Text>
          <TouchableOpacity
            onPress={() => Alert.alert('Documents', 'All 4 farm land records and invoices are verified.')}
          >
            <Text style={styles.viewAllText}>View All &gt;</Text>
          </TouchableOpacity>
        </View>

        {/* Document Rows matching Screen 8 in UIs.png */}
        <View style={styles.documentsCard}>
          {RECENT_DOCUMENTS.map((doc, idx) => (
            <TouchableOpacity
              key={doc.id}
              style={[
                styles.documentRow,
                idx === RECENT_DOCUMENTS.length - 1 && { borderBottomWidth: 0 },
              ]}
              onPress={() =>
                Alert.alert(
                  doc.title,
                  `Document details:\n${doc.uploadedAt}\nStatus: Digitally Verified on Maharashtra Bhulekh portal.`
                )
              }
              activeOpacity={0.7}
            >
              <View style={[styles.docIconBox, { backgroundColor: doc.bgColor }]}>
                <Ionicons
                  name={doc.type === 'pdf' ? 'document-text' : doc.type === 'bill' ? 'receipt' : 'shield-checkmark'}
                  size={20}
                  color={doc.iconColor}
                />
              </View>

              <View style={styles.docInfoCol}>
                <Text style={styles.docTitle}>{doc.title}</Text>
                <Text style={styles.docSubtitle}>{doc.uploadedAt}</Text>
              </View>

              <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
            </TouchableOpacity>
          ))}
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
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 36,
  },
  togglePillContainer: {
    flexDirection: 'row',
    backgroundColor: '#E5E7EB',
    borderRadius: 24,
    padding: 3,
    marginBottom: 20,
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
    fontSize: 11,
    fontWeight: '600',
    color: '#4B5563',
  },
  togglePillTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 22,
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  metricIconCircle: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  metricLabel: {
    fontSize: 12,
    color: '#64748B',
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
    marginTop: 2,
  },
  metricSub: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 2,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: '#111827',
  },
  viewAllText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#16A34A',
  },
  documentsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
  },
  documentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  docIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  docInfoCol: {
    flex: 1,
  },
  docTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E293B',
  },
  docSubtitle: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
});
