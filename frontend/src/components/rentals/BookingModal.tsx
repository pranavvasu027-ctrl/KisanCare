import React, { useState, useEffect } from 'react';
import {
  X, Calendar, Clock, MapPin, CheckCircle2, AlertTriangle, ShieldCheck,
  Truck, UserCheck, Info, ChevronRight, FileText, IndianRupee, Loader2, QrCode
} from 'lucide-react';
import { RentalListing, PriceCalculationResult, AvailabilityCheckResult, RentalBooking } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';
import { ListingImage } from './ListingImage';
import UPIPaymentModal from './UPIPaymentModal';

interface BookingModalProps {
  listing: RentalListing;
  onClose: () => void;
  onBookingSuccess: (booking: RentalBooking) => void;
  farmerName?: string;
  farmerPhone?: string;
  defaultFarmId?: string;
  defaultFieldId?: string;
  defaultCrop?: string;
  defaultAcreage?: number;
}

export default function BookingModal({
  listing,
  onClose,
  onBookingSuccess,
  farmerName = 'Ramesh Patil',
  farmerPhone = '+91 98220 12345',
  defaultFarmId = 'FARM_001',
  defaultFieldId = 'FLD_01',
  defaultCrop = 'Cotton',
  defaultAcreage = 4.5
}: BookingModalProps) {
  // Form state
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];

  const [startDate, setStartDate] = useState<string>(tomorrowStr);
  const [endDate, setEndDate] = useState<string>(tomorrowStr);
  const [startTime, setStartTime] = useState<string>('08:00');
  const [duration, setDuration] = useState<number>(listing.min_duration || 2);
  const [acreage, setAcreage] = useState<number>(defaultAcreage);
  const [quantity, setQuantity] = useState<number>(listing.specs?.team_size || 1);

  const [farmLocation, setFarmLocation] = useState<string>('Shioni, Akola-Murtizapur Highway');
  const [useFarmGps, setUseFarmGps] = useState<boolean>(true);
  const [includeOperator, setIncludeOperator] = useState<boolean>(!listing.specs?.operator_included);
  const [includeDelivery, setIncludeDelivery] = useState<boolean>(true);
  const [paymentMethod, setPaymentMethod] = useState<'pay_on_service' | 'online_upi'>('pay_on_service');
  const [notes, setNotes] = useState<string>('');

  // Async states
  const [pricing, setPricing] = useState<PriceCalculationResult | null>(null);
  const [availability, setAvailability] = useState<AvailabilityCheckResult | null>(null);
  const [loadingPricing, setLoadingPricing] = useState<boolean>(false);
  const [loadingAvail, setLoadingAvail] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successBooking, setSuccessBooking] = useState<RentalBooking | null>(null);
  const [showUpiModal, setShowUpiModal] = useState<boolean>(false);

  // Re-calculate price on parameter changes
  useEffect(() => {
    let isMounted = true;
    const calculate = async () => {
      setLoadingPricing(true);
      setError(null);
      try {
        const result = await rentalApi.calculatePrice({
          listing_id: listing.id,
          duration,
          acreage: listing.billing_unit === 'per_acre' ? acreage : undefined,
          quantity: (listing.category === 'labour' || listing.billing_unit === 'per_sample') ? quantity : 1,
          include_operator: includeOperator,
          include_delivery: includeDelivery,
          distance_km: 8.5
        });
        if (isMounted) setPricing(result);
      } catch (err: any) {
        if (isMounted) setError(err.message || 'Price calculation failed');
      } finally {
        if (isMounted) setLoadingPricing(false);
      }
    };
    calculate();
    return () => { isMounted = false; };
  }, [listing.id, duration, acreage, quantity, includeOperator, includeDelivery, listing.billing_unit, listing.category]);

  // Check availability
  useEffect(() => {
    let isMounted = true;
    const check = async () => {
      if (!startDate || !endDate) return;
      setLoadingAvail(true);
      try {
        const result = await rentalApi.checkAvailability({
          listing_id: listing.id,
          start_date: startDate,
          end_date: endDate,
          start_time: startTime,
          duration,
          quantity
        });
        if (isMounted) setAvailability(result);
      } catch {
        // Fallback
      } finally {
        if (isMounted) setLoadingAvail(false);
      }
    };
    check();
    return () => { isMounted = false; };
  }, [listing.id, startDate, endDate, startTime, duration, quantity]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (availability && !availability.is_available) {
      setError('Cannot submit booking: The selected machine or team has an existing confirmed reservation during these dates.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const booking = await rentalApi.createBooking({
        listing_id: listing.id,
        farmer_name: farmerName,
        farmer_phone: farmerPhone,
        farm_id: defaultFarmId,
        field_id: defaultFieldId,
        field_name: `Field 1 (${defaultCrop})`,
        crop_name: defaultCrop,
        farm_location: farmLocation,
        start_date: startDate,
        end_date: endDate,
        start_time: startTime,
        duration,
        acreage: listing.billing_unit === 'per_acre' ? acreage : 0,
        quantity,
        include_operator: includeOperator,
        include_delivery: includeDelivery,
        notes,
        payment_method: paymentMethod
      });
      setSuccessBooking(booking);
      onBookingSuccess(booking);
    } catch (err: any) {
      setError(err.message || 'Failed to submit booking');
    } finally {
      setSubmitting(false);
    }
  };

  // SUCCESS SCREEN
  if (successBooking) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <div className="bg-white rounded-3xl max-w-lg w-full p-6 md:p-8 shadow-2xl border border-[#E5DDCF] text-center space-y-6 animate-in fade-in zoom-in-95">
          <div className="w-16 h-16 bg-emerald-100 text-[#17643E] rounded-full flex items-center justify-center mx-auto shadow-inner">
            <CheckCircle2 size={36} />
          </div>

          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[#17643E] bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              Booking Request Submitted
            </span>
            <h2 className="text-2xl font-serif font-bold text-[#103D2C] mt-3">
              Reference: {successBooking.booking_reference}
            </h2>
            <p className="text-sm text-[#292B26]/70 mt-1">
              Your booking has been registered with {successBooking.provider_name}.
            </p>
          </div>

          <div className="bg-[#FBF7EF] rounded-2xl p-4 text-left border border-[#E5DDCF] text-xs space-y-2">
            <div className="flex justify-between py-1 border-b border-[#E5DDCF]/60">
              <span className="text-gray-500">Service:</span>
              <span className="font-semibold text-[#103D2C]">{successBooking.listing_title}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#E5DDCF]/60">
              <span className="text-gray-500">Scheduled Date:</span>
              <span className="font-semibold text-[#103D2C]">{successBooking.start_date} ({successBooking.start_time})</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#E5DDCF]/60">
              <span className="text-gray-500">Duration / Work:</span>
              <span className="font-semibold text-[#103D2C]">
                {successBooking.duration} {successBooking.billing_unit.replace('per_', '')}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#E5DDCF]/60">
              <span className="text-gray-500">Status:</span>
              <span className="font-semibold text-amber-800 bg-amber-100 px-2 py-0.5 rounded">
                Pending Owner Confirmation
              </span>
            </div>
            <div className="flex justify-between py-1 pt-2 font-bold text-sm text-[#103D2C]">
              <span>Agreed Total:</span>
              <span>₹{successBooking.total_amount.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Direct UPI Settlement CTA if chosen */}
          {successBooking.payment_method === 'online_upi' ? (
            <div className="p-3.5 bg-purple-50 border border-purple-200 rounded-2xl text-xs space-y-2 text-left">
              <div className="flex items-center justify-between">
                <span className="font-bold text-purple-900 flex items-center gap-1.5">
                  <QrCode size={15} />
                  Direct UPI Payment Ready
                </span>
                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                  successBooking.payment_status === 'paid'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-purple-200 text-purple-900'
                }`}>
                  {successBooking.payment_status === 'paid' ? 'Paid' : 'Unpaid'}
                </span>
              </div>
              <p className="text-[11px] text-purple-800">
                You can scan the shopkeeper's QR code or click your UPI app to complete payment directly.
              </p>
              <button
                type="button"
                onClick={() => setShowUpiModal(true)}
                className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white font-bold py-2.5 px-4 rounded-xl transition-colors text-xs flex items-center justify-center gap-2 shadow-sm"
              >
                <QrCode size={14} />
                <span>
                  {successBooking.payment_status === 'paid'
                    ? 'View Verified UPI Receipt'
                    : `Settle ₹${successBooking.total_amount.toLocaleString('en-IN')} via UPI`}
                </span>
              </button>
            </div>
          ) : (
            <div className="text-xs text-left bg-blue-50 border border-blue-200 rounded-xl p-3 text-blue-900 flex items-start gap-2">
              <Info size={16} className="text-blue-600 shrink-0 mt-0.5" />
              <div>
                <strong>Payment Policy:</strong> No advance payment required online. Pay ₹{successBooking.total_amount.toLocaleString('en-IN')} upon equipment arrival and work completion via Cash or Direct UPI.
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-[#103D2C] hover:bg-[#17643E] text-white font-medium py-3 rounded-xl transition-colors text-sm"
            >
              Track in Bookings
            </button>
          </div>

          {/* Render UPI Modal if triggered */}
          {showUpiModal && (
            <UPIPaymentModal
              booking={successBooking}
              onClose={() => setShowUpiModal(false)}
              onPaymentSuccess={(updated) => {
                setSuccessBooking(updated);
                onBookingSuccess(updated);
              }}
            />
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-2xl w-full my-8 shadow-2xl border border-[#E5DDCF] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#103D2C] text-white p-5 flex items-start justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-xl overflow-hidden border border-white/20 shrink-0">
              <ListingImage
                src={listing.image_url}
                alt={listing.title}
                category={listing.category}
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#17643E] text-emerald-100">
                  {listing.category.toUpperCase()}
                </span>
                {listing.provider.verified && (
                  <span className="text-[10px] flex items-center gap-1 font-semibold text-emerald-300">
                    <ShieldCheck size={12} /> Verified Provider
                  </span>
                )}
              </div>
              <h3 className="font-serif font-bold text-lg text-white mt-1 line-clamp-1">{listing.title}</h3>
              <p className="text-xs text-emerald-200/80">
                Offered by {listing.provider.business_name} • {listing.district}, Maharashtra
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto flex-1 text-[#292B26]">
          {error && (
            <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-2xl text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* STEP 1: Date & Time */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-2">
              <Calendar size={14} /> 1. Select Rental Schedule
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  min={new Date().toISOString().split('T')[0]}
                  value={startDate}
                  onChange={(e) => {
                    setStartDate(e.target.value);
                    if (e.target.value > endDate) setEndDate(e.target.value);
                  }}
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  min={startDate}
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Start Time</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  required
                />
              </div>
            </div>

            {/* Availability status badge */}
            <div className="pt-1">
              {loadingAvail ? (
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Loader2 size={12} className="animate-spin" /> Verifying slot availability with backend...
                </div>
              ) : availability?.is_available ? (
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl">
                  <CheckCircle2 size={14} className="text-emerald-600 shrink-0" />
                  <span>Verified Available: No conflicting bookings for {startDate}.</span>
                </div>
              ) : availability?.is_available === false ? (
                <div className="flex items-center gap-2 text-xs font-semibold text-red-800 bg-red-50 border border-red-200 px-3 py-1.5 rounded-xl">
                  <AlertTriangle size={14} className="text-red-600 shrink-0" />
                  <span>{availability.message} Please choose another date or time slot.</span>
                </div>
              ) : null}
            </div>
          </div>

          {/* STEP 2: Work Units & Duration */}
          <div className="space-y-3 pt-2 border-t border-[#E5DDCF]">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-2">
              <Clock size={14} /> 2. Duration & Job Requirements
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Required Duration ({listing.billing_unit.replace('_', ' ')})
                  <span className="text-[10px] text-gray-500 ml-1">(Min: {listing.min_duration})</span>
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={listing.min_duration || 1}
                    step={listing.billing_unit.includes('hour') ? '0.5' : '1'}
                    value={duration}
                    onChange={(e) => setDuration(Math.max(listing.min_duration || 1, parseFloat(e.target.value) || 1))}
                    className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  />
                  <span className="text-xs font-semibold text-gray-600 whitespace-nowrap">
                    {listing.billing_unit.replace('per_', '')}s
                  </span>
                </div>
              </div>

              {listing.billing_unit === 'per_acre' && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Field Acreage (Acres)
                  </label>
                  <input
                    type="number"
                    min="0.5"
                    step="0.5"
                    value={acreage}
                    onChange={(e) => setAcreage(parseFloat(e.target.value) || 1)}
                    className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  />
                </div>
              )}

              {listing.category === 'labour' && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Number of Workers / Team Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  />
                </div>
              )}

              {listing.billing_unit === 'per_sample' && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Number of Soil Samples to Test
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="25"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  />
                </div>
              )}
            </div>
          </div>

          {/* STEP 3: Farm & Field Context */}
          <div className="space-y-3 pt-2 border-t border-[#E5DDCF]">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-2">
                <MapPin size={14} /> 3. Farm Location & Field Link
              </h4>
              <span className="text-[11px] font-semibold text-[#17643E] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                Connected to {defaultCrop} Field ({defaultAcreage} acres)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Farm / Gate Address</label>
                <input
                  type="text"
                  value={farmLocation}
                  onChange={(e) => setFarmLocation(e.target.value)}
                  placeholder="e.g. Gat No. 42, Shioni Shivahar, Akola"
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                  required
                />
              </div>

              <div className="flex items-center pt-5">
                <label className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useFarmGps}
                    onChange={(e) => setUseFarmGps(e.target.checked)}
                    className="rounded border-[#E5DDCF] text-[#17643E] focus:ring-[#17643E]"
                  />
                  <span>Use saved Digital Twin GPS coordinates (20.7002° N, 77.0082° E)</span>
                </label>
              </div>
            </div>
          </div>

          {/* STEP 4: Inclusions & Add-ons */}
          <div className="space-y-3 pt-2 border-t border-[#E5DDCF]">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-2">
              <UserCheck size={14} /> 4. Service Options & Inclusions
            </h4>

            <div className="space-y-2 text-xs">
              {!listing.specs?.operator_included && (
                <label className="flex items-center justify-between p-3 rounded-xl border border-[#E5DDCF] hover:bg-[#FBF7EF] cursor-pointer">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={includeOperator}
                      onChange={(e) => setIncludeOperator(e.target.checked)}
                      className="rounded border-[#E5DDCF] text-[#17643E] focus:ring-[#17643E]"
                    />
                    <div>
                      <span className="font-semibold text-[#103D2C]">Add Certified Tractor Driver / Operator</span>
                      <p className="text-[11px] text-gray-500">Skilled driver for black cotton soil operations</p>
                    </div>
                  </div>
                  <span className="font-bold text-[#103D2C]">+₹600/day</span>
                </label>
              )}

              <label className="flex items-center justify-between p-3 rounded-xl border border-[#E5DDCF] hover:bg-[#FBF7EF] cursor-pointer">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeDelivery}
                    onChange={(e) => setIncludeDelivery(e.target.checked)}
                    className="rounded border-[#E5DDCF] text-[#17643E] focus:ring-[#17643E]"
                  />
                  <div>
                    <span className="font-semibold text-[#103D2C]">Delivery / Mobilization to Farm Gate</span>
                    <p className="text-[11px] text-gray-500">Provider delivers equipment directly to your field</p>
                  </div>
                </div>
                <span className="font-bold text-[#103D2C]">
                  +₹{listing.terms?.delivery_fee || 150}
                </span>
              </label>
            </div>
          </div>

          {/* STEP 5: Transparent Pricing Breakdown */}
          <div className="bg-[#FBF7EF] rounded-2xl p-5 border border-[#E5DDCF] space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-2">
                <IndianRupee size={14} /> Transparent Price Calculation
              </h4>
              {loadingPricing && <Loader2 size={14} className="animate-spin text-[#103D2C]" />}
            </div>

            {pricing ? (
              <div className="space-y-1.5 text-xs">
                {pricing.breakdown.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-start py-1 border-b border-[#E5DDCF]/50">
                    <div>
                      <span className="font-medium text-[#292B26]">{item.label}</span>
                      <p className="text-[10px] text-gray-500">{item.description}</p>
                    </div>
                    <span className="font-semibold text-[#103D2C]">₹{item.amount.toLocaleString('en-IN')}</span>
                  </div>
                ))}

                <div className="flex justify-between items-center pt-2 font-bold text-sm text-[#103D2C]">
                  <span>Estimated Total (All Disclosed Fees Included)</span>
                  <span className="text-base text-[#17643E]">₹{pricing.estimated_total.toLocaleString('en-IN')}</span>
                </div>

                {pricing.pdkv_benchmark_comparison && (
                  <div className="pt-2 text-[11px] text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg p-2 mt-2">
                    <strong>PDKV Akola Regional Benchmark:</strong> {pricing.pdkv_benchmark_comparison}
                  </div>
                )}
              </div>
            ) : null}
          </div>

          {/* Terms & Payment Method */}
          <div className="space-y-2 text-xs">
            <label className="block font-medium text-gray-700">Payment Preference</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPaymentMethod('pay_on_service')}
                className={`p-3 rounded-xl border text-left font-medium transition-all ${
                  paymentMethod === 'pay_on_service'
                    ? 'border-[#17643E] bg-[#17643E]/10 text-[#103D2C] ring-1 ring-[#17643E]'
                    : 'border-[#E5DDCF] bg-white text-gray-600'
                }`}
              >
                <div className="font-bold">Pay on Delivery / Service</div>
                <div className="text-[10px] text-gray-500">Pay cash or UPI to provider upon satisfactory arrival</div>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod('online_upi')}
                className={`p-3 rounded-xl border text-left font-medium transition-all ${
                  paymentMethod === 'online_upi'
                    ? 'border-[#17643E] bg-[#17643E]/10 text-[#103D2C] ring-1 ring-[#17643E]'
                    : 'border-[#E5DDCF] bg-white text-gray-600'
                }`}
              >
                <div className="font-bold">Direct UPI to Owner</div>
                <div className="text-[10px] text-gray-500">Fast UPI settlement after booking is confirmed</div>
              </button>
            </div>
          </div>

          <div className="text-[11px] text-gray-500 bg-[#FBF7EF] p-3 rounded-xl border border-[#E5DDCF]">
            <strong>Cancellation Terms:</strong> {listing.terms?.cancellation_policy || 'Free cancellation up to 12 hours prior to scheduled start.'} No hidden charges will be applied after booking submission.
          </div>

          {/* Footer Submit */}
          <div className="flex gap-3 pt-4 border-t border-[#E5DDCF]">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-3 rounded-xl border border-[#E5DDCF] text-gray-600 hover:bg-gray-50 text-xs font-semibold"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting || (availability !== null && !availability.is_available)}
              className="flex-1 bg-[#103D2C] hover:bg-[#17643E] disabled:bg-gray-300 text-white font-bold py-3 px-6 rounded-xl transition-colors text-xs flex items-center justify-center gap-2 shadow-sm"
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" /> Submitting Request...
                </>
              ) : (
                <>
                  <span>Submit Booking Request</span>
                  <ChevronRight size={14} />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
