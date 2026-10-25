import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
  TextInput,
  ScrollView,
  Platform,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import {
  fetchRentalListings,
  createRentalBooking,
  fetchFarmerBookings,
  calculateRentalPrice,
  RentalListing,
  BookingRecord,
  PriceCalculationResult,
} from '@/services/rentalsService';
import { getStoredProfile } from '@/services/profileService';
import { ScreenContainer } from '@/components/common/ScreenContainer';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { EmptyState } from '@/components/common/EmptyState';
import { Colors, BorderRadius, Spacing, Typography } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { ApiError } from '@/services/apiError';

function getTodayString(): string {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getOffsetDateString(daysOffset: number): string {
  const d = new Date();
  d.setDate(d.getDate() + daysOffset);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function RentalsScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];
  const router = useRouter();

  // Active view: Browse Listings vs My Bookings
  const [activeTab, setActiveTab] = useState<'browse' | 'my_bookings'>('browse');

  // Category filter for listings
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Booking Modal State
  const [selectedListing, setSelectedListing] = useState<RentalListing | null>(null);
  const [isBookingModalOpen, setIsBookingModalOpen] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const userProfile = getStoredProfile();
  const [farmerName, setFarmerName] = useState<string>(userProfile?.fullName || 'Pranav Vasu');
  const [farmerPhone, setFarmerPhone] = useState<string>(userProfile?.phone || '9876543210');
  const [startDate, setStartDate] = useState<string>(getOffsetDateString(1));
  const [endDate, setEndDate] = useState<string>(getOffsetDateString(1));
  const [duration, setDuration] = useState<string>('2');
  const [notes, setNotes] = useState<string>('');

  // Live Price Estimation State
  const [priceEstimate, setPriceEstimate] = useState<PriceCalculationResult | null>(null);
  const [isCalculatingPrice, setIsCalculatingPrice] = useState<boolean>(false);

  // Confirmation Modal State
  const [confirmedBooking, setConfirmedBooking] = useState<BookingRecord | null>(null);
  const [isConfirmationOpen, setIsConfirmationOpen] = useState<boolean>(false);

  // Query: Equipment Listings
  const {
    data: listings,
    isLoading: isListingsLoading,
    isError: isListingsError,
    error: listingsError,
    refetch: refetchListings,
    isFetching: isListingsFetching,
  } = useQuery<RentalListing[], ApiError>({
    queryKey: ['rentals-listings', selectedCategory],
    queryFn: () =>
      fetchRentalListings(
        selectedCategory !== 'all' ? { category: selectedCategory } : undefined
      ),
  });

  // Query: Farmer Bookings
  const {
    data: bookings,
    isLoading: isBookingsLoading,
    isError: isBookingsError,
    error: bookingsError,
    refetch: refetchBookings,
    isFetching: isBookingsFetching,
  } = useQuery<BookingRecord[], ApiError>({
    queryKey: ['rentals-bookings'],
    queryFn: () => fetchFarmerBookings(),
  });

  // Open booking modal for a listing
  const handleOpenBooking = (item: RentalListing) => {
    setSelectedListing(item);
    setFormError(null);
    setStartDate(getOffsetDateString(1));
    setEndDate(getOffsetDateString(1));
    setDuration('2');
    setNotes('');
    setIsBookingModalOpen(true);
  };

  // Recalculate price estimate when duration or selected listing changes
  useEffect(() => {
    if (!selectedListing || !isBookingModalOpen) return;
    const durNum = parseFloat(duration);
    if (isNaN(durNum) || durNum <= 0) return;

    let isMounted = true;
    setIsCalculatingPrice(true);
    calculateRentalPrice({
      listing_id: selectedListing.id,
      duration: durNum,
    })
      .then((res) => {
        if (isMounted) setPriceEstimate(res);
      })
      .catch(() => {
        if (isMounted) setPriceEstimate(null);
      })
      .finally(() => {
        if (isMounted) setIsCalculatingPrice(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedListing, duration, isBookingModalOpen]);

  // Handle Booking Submission
  const handleSubmitBooking = async () => {
    if (!selectedListing) return;

    // Validate inputs
    if (!farmerName.trim()) {
      setFormError('Please enter the farmer name.');
      return;
    }
    const cleanPhone = farmerPhone.replace(/\D/g, '');
    if (cleanPhone.length < 10) {
      setFormError('Please enter a valid 10-digit mobile number.');
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(startDate)) {
      setFormError('Start date must be in YYYY-MM-DD format.');
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(endDate)) {
      setFormError('End date must be in YYYY-MM-DD format.');
      return;
    }
    if (endDate < startDate) {
      setFormError('End date cannot be earlier than start date.');
      return;
    }
    const durNum = parseFloat(duration);
    if (isNaN(durNum) || durNum <= 0) {
      setFormError('Duration must be greater than 0.');
      return;
    }

    setFormError(null);
    setIsSubmitting(true);

    try {
      const result = await createRentalBooking({
        listing_id: selectedListing.id,
        farmer_name: farmerName.trim(),
        farmer_phone: cleanPhone.slice(-10),
        start_date: startDate,
        end_date: endDate,
        duration: durNum,
        payment_method: 'pay_on_service',
        notes: notes.trim() || undefined,
      });

      // Close booking modal and show verified confirmation
      setIsBookingModalOpen(false);
      setConfirmedBooking(result);
      setIsConfirmationOpen(true);

      // Invalidate and refresh bookings list
      refetchBookings();
    } catch (err: any) {
      setFormError(
        err?.message ||
          err?.userFriendlyMessage ||
          'Failed to reserve equipment. The slot may be already booked.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const categories = [
    { key: 'all', label: 'All Equipment' },
    { key: 'tractor', label: 'Tractors' },
    { key: 'equipment', label: 'Implements' },
    { key: 'transport', label: 'Transport' },
    { key: 'labour', label: 'Farm Labour' },
    { key: 'specialist', label: 'Specialists' },
  ];

  return (
    <ScreenContainer
      refreshing={activeTab === 'browse' ? isListingsFetching : isBookingsFetching}
      onRefresh={() => (activeTab === 'browse' ? refetchListings() : refetchBookings())}
    >
      {/* Top Header */}
      <View style={styles.header}>
        <View style={styles.badgeRow}>
          <Badge label="Live Backend Verified" variant="success" size="sm" />
          <Text style={[styles.endpointMeta, { color: theme.textSecondary }]}>
            /api/v1/rentals
          </Text>
        </View>
        <Text style={[styles.title, { color: theme.text }]}>Farm Equipment Rentals</Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          Verified agricultural machinery, tractors and farm services across Maharashtra
        </Text>
      </View>

      {/* Segmented Tab Controls: Browse vs My Bookings */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'browse' && styles.tabButtonActive]}
          onPress={() => setActiveTab('browse')}
          activeOpacity={0.8}
        >
          <Ionicons
            name="grid-outline"
            size={16}
            color={activeTab === 'browse' ? '#FFFFFF' : theme.textSecondary}
          />
          <Text
            style={[
              styles.tabButtonText,
              activeTab === 'browse' && styles.tabButtonTextActive,
            ]}
          >
            Available Equipment ({listings?.length ?? 0})
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'my_bookings' && styles.tabButtonActive]}
          onPress={() => setActiveTab('my_bookings')}
          activeOpacity={0.8}
        >
          <Ionicons
            name="calendar-outline"
            size={16}
            color={activeTab === 'my_bookings' ? '#FFFFFF' : theme.textSecondary}
          />
          <Text
            style={[
              styles.tabButtonText,
              activeTab === 'my_bookings' && styles.tabButtonTextActive,
            ]}
          >
            My Bookings ({bookings?.length ?? 0})
          </Text>
        </TouchableOpacity>
      </View>

      {/* ----------------- TAB 1: BROWSE LISTINGS ----------------- */}
      {activeTab === 'browse' && (
        <View>
          {/* Horizontal Category Chips */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.categoryScroll}
            contentContainerStyle={styles.categoryScrollContent}
          >
            {categories.map((c) => {
              const isSelected = selectedCategory === c.key;
              return (
                <TouchableOpacity
                  key={c.key}
                  style={[
                    styles.categoryChip,
                    isSelected && styles.categoryChipActive,
                  ]}
                  onPress={() => setSelectedCategory(c.key)}
                  activeOpacity={0.75}
                >
                  <Text
                    style={[
                      styles.categoryChipText,
                      isSelected && styles.categoryChipTextActive,
                    ]}
                  >
                    {c.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {/* Loading State */}
          {isListingsLoading && (
            <View style={styles.centerContainer}>
              <ActivityIndicator size="large" color={theme.primary} />
              <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
                Querying verified equipment listings...
              </Text>
            </View>
          )}

          {/* Error State */}
          {isListingsError && (
            <Card variant="outlined" style={[styles.errorCard, { borderColor: theme.error }]}>
              <View style={styles.errorHeader}>
                <Ionicons name="cloud-offline" size={24} color={theme.error} />
                <Text style={[styles.errorTitle, { color: theme.error }]}>
                  Unable to Load Rentals
                </Text>
              </View>
              <Text style={[styles.errorMessage, { color: theme.textSecondary }]}>
                {listingsError?.userFriendlyMessage ||
                  'Could not connect to the rental service endpoint.'}
              </Text>
              <Button
                title="Retry Connection"
                onPress={() => refetchListings()}
                variant="outline"
                size="sm"
                icon="refresh"
                style={{ marginTop: Spacing.three }}
              />
            </Card>
          )}

          {/* Empty State */}
          {!isListingsLoading && !isListingsError && listings && listings.length === 0 && (
            <EmptyState
              icon="construct-outline"
              title="No Equipment Listings Found"
              description="There are currently no active rental listings matching this category."
              actionText="View All Listings"
              onActionPress={() => setSelectedCategory('all')}
            />
          )}

          {/* Verified Listings List */}
          {!isListingsLoading && !isListingsError && listings && listings.length > 0 && (
            <View>
              {listings.map((item) => (
                <Card key={item.id} variant="elevated" style={styles.listingCard}>
                  {/* Top Row: Title, Verification Badge */}
                  <View style={styles.listingHeader}>
                    <View style={{ flex: 1, paddingRight: 8 }}>
                      <Text style={[styles.itemTitle, { color: theme.text }]}>
                        {item.title}
                      </Text>
                      <Text style={[styles.locationText, { color: theme.textSecondary }]}>
                        <Ionicons name="location" size={12} color="#16A34A" /> {item.district}
                        {item.taluka ? `, ${item.taluka}` : ''}
                      </Text>
                    </View>
                    <Badge
                      label={item.provider?.verified ? 'VERIFIED' : 'LOCAL'}
                      variant={item.provider?.verified ? 'success' : 'neutral'}
                      size="sm"
                    />
                  </View>

                  <View style={[styles.divider, { backgroundColor: theme.borderLight }]} />

                  {/* Provider & Rate Row */}
                  <View style={styles.rateRow}>
                    <View>
                      <Text style={[styles.rateLabel, { color: theme.textSecondary }]}>
                        Rental Rate
                      </Text>
                      <Text style={[styles.rateValue, { color: theme.primary }]}>
                        ₹{item.price ?? item.daily_rate ?? item.hourly_rate ?? '—'}
                        <Text style={[styles.unitText, { color: theme.textSecondary }]}>
                          /{item.billing_unit ? item.billing_unit.replace(/^per_/, '').replace(/_/g, ' ') : 'hour'}
                        </Text>
                      </Text>
                    </View>

                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={[styles.rateLabel, { color: theme.textSecondary }]}>
                        Provider
                      </Text>
                      <Text style={[styles.ownerText, { color: theme.text }]}>
                        {item.provider?.business_name || item.provider?.contact_name || item.owner_name || 'Local Agri Provider'}
                      </Text>
                      {item.provider?.phone ? (
                        <Text style={[styles.phoneSubText, { color: theme.textSecondary }]}>
                          📞 {item.provider.phone}
                        </Text>
                      ) : null}
                    </View>
                  </View>

                  {/* Single Primary Action: Book Equipment */}
                  <TouchableOpacity
                    style={styles.bookButton}
                    onPress={() => handleOpenBooking(item)}
                    activeOpacity={0.85}
                  >
                    <Ionicons name="calendar" size={15} color="#FFFFFF" />
                    <Text style={styles.bookButtonText}>Book Equipment</Text>
                  </TouchableOpacity>
                </Card>
              ))}
            </View>
          )}
        </View>
      )}

      {/* ----------------- TAB 2: MY BOOKINGS ----------------- */}
      {activeTab === 'my_bookings' && (
        <View>
          {isBookingsLoading && (
            <View style={styles.centerContainer}>
              <ActivityIndicator size="large" color={theme.primary} />
              <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
                Loading your booking history...
              </Text>
            </View>
          )}

          {isBookingsError && (
            <Card variant="outlined" style={[styles.errorCard, { borderColor: theme.error }]}>
              <Text style={[styles.errorTitle, { color: theme.error }]}>
                Could not retrieve bookings
              </Text>
              <Text style={[styles.errorMessage, { color: theme.textSecondary }]}>
                {bookingsError?.userFriendlyMessage || 'Could not connect to bookings API.'}
              </Text>
              <Button
                title="Retry"
                onPress={() => refetchBookings()}
                variant="outline"
                size="sm"
                icon="refresh"
                style={{ marginTop: Spacing.three }}
              />
            </Card>
          )}

          {!isBookingsLoading && !isBookingsError && bookings && bookings.length === 0 && (
            <EmptyState
              icon="calendar-outline"
              title="No Active Bookings"
              description="You have not booked any farm equipment yet. Browse verified tractors and machinery."
              actionText="Browse Equipment"
              onActionPress={() => setActiveTab('browse')}
            />
          )}

          {!isBookingsLoading && !isBookingsError && bookings && bookings.length > 0 && (
            <View>
              {bookings.map((b) => {
                const isPending = b.status === 'pending_confirmation';
                const isConfirmed = b.status === 'confirmed';
                const isCancelled = b.status === 'cancelled' || b.status === 'rejected';

                return (
                  <Card key={b.id} variant="elevated" style={styles.bookingCard}>
                    {/* Reference & Status */}
                    <View style={styles.bookingHeaderRow}>
                      <View>
                        <Text style={styles.bookingRefText}>{b.booking_reference}</Text>
                        <Text style={styles.bookingDateSub}>
                          Created: {b.created_at ? b.created_at.split('T')[0] : 'Today'}
                        </Text>
                      </View>
                      <Badge
                        label={
                          isPending
                            ? 'PENDING'
                            : isConfirmed
                            ? 'CONFIRMED'
                            : isCancelled
                            ? 'CANCELLED'
                            : b.status.toUpperCase()
                        }
                        variant={isConfirmed ? 'success' : isPending ? 'warning' : 'neutral'}
                        size="sm"
                      />
                    </View>

                    <View style={[styles.divider, { backgroundColor: theme.borderLight }]} />

                    {/* Equipment Title */}
                    <Text style={styles.bookingTitle}>{b.listing_title}</Text>

                    {/* Booking Details Grid */}
                    <View style={styles.bookingGrid}>
                      <View style={styles.bookingGridItem}>
                        <Text style={styles.bookingGridLabel}>Rental Dates</Text>
                        <Text style={styles.bookingGridValue}>
                          {b.start_date} → {b.end_date}
                        </Text>
                      </View>

                      <View style={styles.bookingGridItem}>
                        <Text style={styles.bookingGridLabel}>Duration</Text>
                        <Text style={styles.bookingGridValue}>
                          {b.duration} {b.duration === 1 ? 'day/hr' : 'days/hrs'}
                        </Text>
                      </View>

                      <View style={styles.bookingGridItem}>
                        <Text style={styles.bookingGridLabel}>Total Amount</Text>
                        <Text style={[styles.bookingGridValue, { color: theme.primary, fontWeight: '800' }]}>
                          ₹{b.total_amount?.toLocaleString('en-IN') ?? '—'}
                        </Text>
                      </View>

                      <View style={styles.bookingGridItem}>
                        <Text style={styles.bookingGridLabel}>Payment Mode</Text>
                        <Text style={styles.bookingGridValue}>Pay on Service</Text>
                      </View>
                    </View>

                    {/* Provider Contact Banner */}
                    {b.provider_phone ? (
                      <View style={styles.providerBanner}>
                        <Ionicons name="call" size={14} color="#16A34A" />
                        <Text style={styles.providerBannerText}>
                          Provider: {b.provider_name || 'Owner'} • {b.provider_phone}
                        </Text>
                      </View>
                    ) : null}
                  </Card>
                );
              })}
            </View>
          )}
        </View>
      )}

      {/* Return to Dashboard Button */}
      <Button
        title="Return to Dashboard"
        onPress={() => router.back()}
        variant="outline"
        icon="arrow-back"
        style={{ marginTop: Spacing.four, marginBottom: Spacing.six }}
      />

      {/* ----------------- BOOKING MODAL ----------------- */}
      <Modal
        visible={isBookingModalOpen}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {
          if (!isSubmitting) setIsBookingModalOpen(false);
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {/* Modal Header */}
            <View style={styles.modalHeaderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.modalTitle}>Book Farm Equipment</Text>
                <Text style={styles.modalSubtitle} numberOfLines={1}>
                  {selectedListing?.title}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => setIsBookingModalOpen(false)}
                disabled={isSubmitting}
                style={styles.modalCloseButton}
              >
                <Ionicons name="close" size={20} color="#64748B" />
              </TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false} style={{ maxHeight: 460 }}>
              {/* Selected Equipment Summary */}
              <View style={styles.summaryBox}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.summaryRateLabel}>Standard Rate</Text>
                  <Text style={styles.summaryRateValue}>
                    ₹{selectedListing?.price ?? '—'}{' '}
                    <Text style={{ fontSize: 12, fontWeight: 'normal', color: '#64748B' }}>
                      /{selectedListing?.billing_unit ? selectedListing.billing_unit.replace(/^per_/, '').replace(/_/g, ' ') : 'unit'}
                    </Text>
                  </Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={styles.summaryLocationText}>
                    📍 {selectedListing?.district}, {selectedListing?.taluka || 'APMC'}
                  </Text>
                  <Text style={styles.summaryProviderText}>
                    {selectedListing?.provider?.business_name || 'Verified Provider'}
                  </Text>
                </View>
              </View>

              {/* Form Input: Farmer Name */}
              <View style={styles.formGroup}>
                <Text style={styles.inputLabel}>Farmer Full Name *</Text>
                <TextInput
                  style={styles.inputField}
                  value={farmerName}
                  onChangeText={setFarmerName}
                  placeholder="Enter full name"
                  placeholderTextColor="#94A3B8"
                  editable={!isSubmitting}
                />
              </View>

              {/* Form Input: Farmer Phone */}
              <View style={styles.formGroup}>
                <Text style={styles.inputLabel}>Mobile Phone (10-digit) *</Text>
                <TextInput
                  style={styles.inputField}
                  value={farmerPhone}
                  onChangeText={setFarmerPhone}
                  placeholder="e.g. 9876543210"
                  placeholderTextColor="#94A3B8"
                  keyboardType="phone-pad"
                  maxLength={10}
                  editable={!isSubmitting}
                />
              </View>

              {/* Form Input: Start Date with Quick Presets */}
              <View style={styles.formGroup}>
                <Text style={styles.inputLabel}>Start Date (YYYY-MM-DD) *</Text>
                <TextInput
                  style={styles.inputField}
                  value={startDate}
                  onChangeText={setStartDate}
                  placeholder="YYYY-MM-DD"
                  placeholderTextColor="#94A3B8"
                  editable={!isSubmitting}
                />
                <View style={styles.presetRow}>
                  <TouchableOpacity
                    style={styles.presetChip}
                    onPress={() => setStartDate(getTodayString())}
                  >
                    <Text style={styles.presetText}>Today</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.presetChip}
                    onPress={() => setStartDate(getOffsetDateString(1))}
                  >
                    <Text style={styles.presetText}>Tomorrow</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.presetChip}
                    onPress={() => setStartDate(getOffsetDateString(2))}
                  >
                    <Text style={styles.presetText}>+2 Days</Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Form Input: End Date with Quick Presets */}
              <View style={styles.formGroup}>
                <Text style={styles.inputLabel}>End Date (YYYY-MM-DD) *</Text>
                <TextInput
                  style={styles.inputField}
                  value={endDate}
                  onChangeText={setEndDate}
                  placeholder="YYYY-MM-DD"
                  placeholderTextColor="#94A3B8"
                  editable={!isSubmitting}
                />
                <View style={styles.presetRow}>
                  <TouchableOpacity
                    style={styles.presetChip}
                    onPress={() => setEndDate(startDate)}
                  >
                    <Text style={styles.presetText}>Same Day</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.presetChip}
                    onPress={() => setEndDate(getOffsetDateString(2))}
                  >
                    <Text style={styles.presetText}>+1 Day</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.presetChip}
                    onPress={() => setEndDate(getOffsetDateString(3))}
                  >
                    <Text style={styles.presetText}>+2 Days</Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Form Input: Duration */}
              <View style={styles.formGroup}>
                <Text style={styles.inputLabel}>Required Units / Duration *</Text>
                <TextInput
                  style={styles.inputField}
                  value={duration}
                  onChangeText={setDuration}
                  placeholder="e.g. 2"
                  placeholderTextColor="#94A3B8"
                  keyboardType="numeric"
                  editable={!isSubmitting}
                />
              </View>

              {/* Form Input: Notes */}
              <View style={styles.formGroup}>
                <Text style={styles.inputLabel}>Special Instructions / Field Location</Text>
                <TextInput
                  style={[styles.inputField, { height: 60, textAlignVertical: 'top' }]}
                  value={notes}
                  onChangeText={setNotes}
                  placeholder="e.g. Near Shioni village canal road"
                  placeholderTextColor="#94A3B8"
                  multiline
                  editable={!isSubmitting}
                />
              </View>

              {/* Price Calculation Preview */}
              <View style={styles.priceEstimateCard}>
                <View style={styles.priceEstimateRow}>
                  <Text style={styles.priceEstimateLabel}>Base Charge:</Text>
                  <Text style={styles.priceEstimateVal}>
                    ₹{priceEstimate?.base_rental_charge ?? (parseFloat(duration || '1') * (selectedListing?.price || 0))}
                  </Text>
                </View>
                <View style={styles.priceEstimateRow}>
                  <Text style={styles.priceEstimateLabel}>Platform Fee (Guaranteed):</Text>
                  <Text style={styles.priceEstimateVal}>
                    ₹{priceEstimate?.platform_fee ?? 50}
                  </Text>
                </View>
                <View style={[styles.priceEstimateRow, { borderTopWidth: 1, borderTopColor: '#E2E8F0', paddingTop: 6, marginTop: 4 }]}>
                  <Text style={[styles.priceEstimateLabel, { fontWeight: '800', color: '#111827' }]}>
                    Estimated Total:
                  </Text>
                  <Text style={styles.priceEstimateTotal}>
                    ₹{priceEstimate?.estimated_total?.toLocaleString('en-IN') ?? ((parseFloat(duration || '1') * (selectedListing?.price || 0)) + 50)}
                  </Text>
                </View>
                <Text style={styles.pricePaymentNote}>
                  💳 Payment Method: Pay on Delivery / Service at Farm Gate
                </Text>
              </View>

              {/* Error Message */}
              {formError ? (
                <View style={styles.formErrorBox}>
                  <Ionicons name="alert-circle" size={16} color="#DC2626" />
                  <Text style={styles.formErrorText}>{formError}</Text>
                </View>
              ) : null}
            </ScrollView>

            {/* Modal Actions */}
            <View style={styles.modalActionRow}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setIsBookingModalOpen(false)}
                disabled={isSubmitting}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.confirmButton, isSubmitting && styles.confirmButtonDisabled]}
                onPress={handleSubmitBooking}
                disabled={isSubmitting}
                activeOpacity={0.85}
              >
                {isSubmitting ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <ActivityIndicator size="small" color="#FFFFFF" />
                    <Text style={styles.confirmButtonText}>Reserving...</Text>
                  </View>
                ) : (
                  <Text style={styles.confirmButtonText}>Confirm & Book</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* ----------------- CONFIRMATION SUCCESS MODAL ----------------- */}
      <Modal
        visible={isConfirmationOpen}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setIsConfirmationOpen(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.confirmationBox}>
            <View style={styles.successIconCircle}>
              <Ionicons name="checkmark-sharp" size={32} color="#16A34A" />
            </View>

            <Text style={styles.confirmationTitle}>Equipment Reserved!</Text>
            <Text style={styles.confirmationSubtitle}>
              Your booking has been received and confirmed by the provider.
            </Text>

            <View style={styles.confDetailsCard}>
              <View style={styles.confRow}>
                <Text style={styles.confLabel}>Booking Ref:</Text>
                <Text style={styles.confValue}>{confirmedBooking?.booking_reference}</Text>
              </View>
              <View style={styles.confRow}>
                <Text style={styles.confLabel}>Equipment:</Text>
                <Text style={styles.confValue} numberOfLines={1}>
                  {confirmedBooking?.listing_title}
                </Text>
              </View>
              <View style={styles.confRow}>
                <Text style={styles.confLabel}>Dates:</Text>
                <Text style={styles.confValue}>
                  {confirmedBooking?.start_date} → {confirmedBooking?.end_date}
                </Text>
              </View>
              <View style={styles.confRow}>
                <Text style={styles.confLabel}>Total Amount:</Text>
                <Text style={[styles.confValue, { color: '#16A34A', fontWeight: '800' }]}>
                  ₹{confirmedBooking?.total_amount?.toLocaleString('en-IN')}
                </Text>
              </View>
              <View style={styles.confRow}>
                <Text style={styles.confLabel}>Provider Contact:</Text>
                <Text style={styles.confValue}>{confirmedBooking?.provider_phone || 'Local Owner'}</Text>
              </View>
            </View>

            <Text style={styles.confPayReminder}>
              Please pay ₹{confirmedBooking?.total_amount?.toLocaleString('en-IN')} directly to the driver upon delivery.
            </Text>

            <TouchableOpacity
              style={styles.viewBookingsBtn}
              onPress={() => {
                setIsConfirmationOpen(false);
                setActiveTab('my_bookings');
              }}
              activeOpacity={0.85}
            >
              <Text style={styles.viewBookingsBtnText}>View in My Bookings</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingVertical: Spacing.three,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.two,
  },
  endpointMeta: {
    fontSize: 11,
    marginLeft: Spacing.two,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 13,
    marginTop: 4,
    lineHeight: 18,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#E5E7EB',
    borderRadius: 24,
    padding: 3,
    marginVertical: Spacing.three,
  },
  tabButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 9,
    borderRadius: 22,
  },
  tabButtonActive: {
    backgroundColor: '#16A34A',
  },
  tabButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4B5563',
  },
  tabButtonTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  categoryScroll: {
    marginBottom: Spacing.three,
  },
  categoryScrollContent: {
    gap: 8,
  },
  categoryChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  categoryChipActive: {
    backgroundColor: '#DCFCE7',
    borderColor: '#16A34A',
  },
  categoryChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  categoryChipTextActive: {
    color: '#16A34A',
    fontWeight: '700',
  },
  centerContainer: {
    paddingVertical: Spacing.eight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: Typography.sizes.sm,
    marginTop: Spacing.three,
  },
  errorCard: {
    padding: Spacing.four,
    marginBottom: Spacing.four,
  },
  errorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.two,
  },
  errorTitle: {
    fontSize: Typography.sizes.md,
    fontWeight: Typography.weights.bold,
    marginLeft: Spacing.two,
  },
  errorMessage: {
    fontSize: Typography.sizes.sm,
    lineHeight: 20,
  },
  listingCard: {
    marginBottom: Spacing.three,
    padding: 16,
    borderRadius: 16,
  },
  listingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  itemTitle: {
    fontSize: 15,
    fontWeight: '800',
  },
  locationText: {
    fontSize: 12,
    marginTop: 3,
  },
  divider: {
    height: 1,
    marginVertical: Spacing.three,
  },
  rateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rateLabel: {
    fontSize: 11,
  },
  rateValue: {
    fontSize: 16,
    fontWeight: '800',
  },
  unitText: {
    fontSize: 11,
    fontWeight: 'normal',
  },
  ownerText: {
    fontSize: 12,
    fontWeight: '700',
  },
  phoneSubText: {
    fontSize: 11,
    marginTop: 2,
  },
  bookButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#16A34A',
    paddingVertical: 10,
    borderRadius: 10,
    marginTop: 14,
  },
  bookButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  // My Bookings styles
  bookingCard: {
    marginBottom: Spacing.three,
    padding: 16,
    borderRadius: 16,
  },
  bookingHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  bookingRefText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#1E293B',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  bookingDateSub: {
    fontSize: 11,
    color: '#64748B',
    marginTop: 2,
  },
  bookingTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 10,
  },
  bookingGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    backgroundColor: '#F8FAF8',
    borderRadius: 10,
    padding: 10,
    gap: 12,
  },
  bookingGridItem: {
    width: '45%',
  },
  bookingGridLabel: {
    fontSize: 10,
    color: '#64748B',
    textTransform: 'uppercase',
  },
  bookingGridValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1E293B',
    marginTop: 2,
  },
  providerBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0FDF4',
    padding: 8,
    borderRadius: 8,
    marginTop: 10,
  },
  providerBannerText: {
    fontSize: 11,
    color: '#16A34A',
    fontWeight: '600',
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    width: '100%',
    maxWidth: 480,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 10,
    elevation: 8,
  },
  modalHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  modalSubtitle: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  modalCloseButton: {
    padding: 4,
  },
  summaryBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#F0FDF4',
    padding: 12,
    borderRadius: 10,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#DCFCE7',
  },
  summaryRateLabel: {
    fontSize: 10,
    color: '#16A34A',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  summaryRateValue: {
    fontSize: 15,
    fontWeight: '800',
    color: '#16A34A',
    marginTop: 2,
  },
  summaryLocationText: {
    fontSize: 11,
    color: '#475569',
    fontWeight: '500',
  },
  summaryProviderText: {
    fontSize: 11,
    color: '#16A34A',
    fontWeight: '600',
    marginTop: 2,
  },
  formGroup: {
    marginBottom: 12,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 5,
  },
  inputField: {
    backgroundColor: '#F8FAF8',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontSize: 14,
    color: '#0F172A',
  },
  presetRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 5,
  },
  presetChip: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  presetText: {
    fontSize: 10,
    color: '#475569',
    fontWeight: '600',
  },
  priceEstimateCard: {
    backgroundColor: '#F8FAF8',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginTop: 4,
    marginBottom: 12,
  },
  priceEstimateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 3,
  },
  priceEstimateLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  priceEstimateVal: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1E293B',
  },
  priceEstimateTotal: {
    fontSize: 16,
    fontWeight: '800',
    color: '#16A34A',
  },
  pricePaymentNote: {
    fontSize: 10,
    color: '#64748B',
    marginTop: 6,
    fontStyle: 'italic',
  },
  formErrorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FEE2E2',
    padding: 8,
    borderRadius: 8,
    marginBottom: 12,
  },
  formErrorText: {
    fontSize: 11,
    color: '#DC2626',
    flex: 1,
  },
  modalActionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 11,
    alignItems: 'center',
    borderRadius: 10,
    backgroundColor: '#F1F5F9',
  },
  cancelButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  confirmButton: {
    flex: 2,
    paddingVertical: 11,
    alignItems: 'center',
    borderRadius: 10,
    backgroundColor: '#16A34A',
  },
  confirmButtonDisabled: {
    opacity: 0.6,
  },
  confirmButtonText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  // Confirmation Modal
  confirmationBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
  },
  successIconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#DCFCE7',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  confirmationTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#111827',
  },
  confirmationSubtitle: {
    fontSize: 12,
    color: '#64748B',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 16,
  },
  confDetailsCard: {
    width: '100%',
    backgroundColor: '#F8FAF8',
    borderRadius: 12,
    padding: 12,
    marginBottom: 14,
    gap: 8,
  },
  confRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  confLabel: {
    fontSize: 12,
    color: '#64748B',
  },
  confValue: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0F172A',
    maxWidth: '60%',
    textAlign: 'right',
  },
  confPayReminder: {
    fontSize: 11,
    color: '#475569',
    textAlign: 'center',
    marginBottom: 18,
    lineHeight: 16,
  },
  viewBookingsBtn: {
    backgroundColor: '#16A34A',
    width: '100%',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  viewBookingsBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
});
