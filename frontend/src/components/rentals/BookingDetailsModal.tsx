import React, { useState } from 'react';
import {
  X, CheckCircle2, Clock, AlertTriangle, MapPin, Phone, User, Calendar,
  IndianRupee, ShieldCheck, Printer, LineChart, Star, RotateCcw, Truck, Loader2, QrCode
} from 'lucide-react';
import { RentalBooking } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';
import UPIPaymentModal from './UPIPaymentModal';

interface BookingDetailsModalProps {
  booking: RentalBooking;
  onClose: () => void;
  onUpdate: (updatedBooking: RentalBooking) => void;
  onRebook?: (listingId: string) => void;
}

export default function BookingDetailsModal({
  booking,
  onClose,
  onUpdate,
  onRebook
}: BookingDetailsModalProps) {
  const [cancelling, setCancelling] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [showCancelPrompt, setShowCancelPrompt] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showUpiModal, setShowUpiModal] = useState<boolean>(false);

  // Review states
  const [showReviewPrompt, setShowReviewPrompt] = useState(false);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');

  const handleCancel = async () => {
    if (!cancelReason.trim()) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const updated = await rentalApi.cancelBooking(booking.id, cancelReason);
      setActionSuccess('Booking successfully cancelled according to policy.');
      setShowCancelPrompt(false);
      onUpdate(updated);
    } catch (err: any) {
      setActionError(err.message || 'Failed to cancel booking');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecordExpense = async () => {
    setActionLoading(true);
    setActionError(null);
    try {
      if (booking.is_demo !== false) {
        // Mock / Demo isolation safeguard: Never create a real farm expense from a mock booking
        setActionSuccess(`Simulated Farm Economics expense entry of ₹${booking.total_amount}. (Isolated Demo Mode — real farm ledgers protected).`);
        onUpdate({ ...booking, recorded_in_economics: true, farm_expense_id: 'DEMO_EXP_ISOLATED' });
        return;
      }
      const res = await rentalApi.recordExpenseToFarm(booking.id, {
        farm_id: booking.farm_id || 'FARM_001',
        field_id: booking.field_id || 'FLD_01',
        crop: booking.crop_name || 'Cotton',
        expense_category: booking.category === 'labour' ? 'labour_hire' : booking.category === 'transport' ? 'transport' : 'machinery_rental'
      });
      setActionSuccess(`Recorded expense of ₹${booking.total_amount} into Farm Economics (Expense Ref: ${res.expense_id})`);
      onUpdate({ ...booking, recorded_in_economics: true, farm_expense_id: res.expense_id });
    } catch (err: any) {
      setActionError(err.message || 'Failed to record expense');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitReview = async () => {
    if (!reviewText.trim()) return;
    setActionLoading(true);
    setActionError(null);
    try {
      await rentalApi.submitReview({
        booking_id: booking.id,
        listing_id: booking.listing_id,
        farmer_name: booking.farmer_name,
        rating,
        review_text: reviewText
      });
      setActionSuccess('Thank you! Your verified review has been published.');
      setShowReviewPrompt(false);
    } catch (err: any) {
      setActionError(err.message || 'Failed to submit review');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'completed':
        return 'bg-green-100 text-green-900 border-green-300';
      case 'pending_confirmation':
        return 'bg-amber-100 text-amber-900 border-amber-300';
      case 'cancelled':
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-2xl w-full my-8 shadow-2xl border border-[#E5DDCF] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#103D2C] text-white p-5 flex items-center justify-between shrink-0">
          <div>
            <span className="text-[10px] font-bold tracking-wider uppercase bg-[#17643E] text-emerald-100 px-2 py-0.5 rounded">
              Booking Details
            </span>
            <h3 className="font-serif font-bold text-lg text-white mt-1">
              Ref: {booking.booking_reference}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 text-[#292B26]">
          {actionSuccess && (
            <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-2xl text-xs flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
              <span>{actionSuccess}</span>
            </div>
          )}

          {actionError && (
            <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-2xl text-xs flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-600 shrink-0" />
              <span>{actionError}</span>
            </div>
          )}

          {/* Status Bar */}
          <div className="flex flex-wrap items-center justify-between p-4 bg-[#FBF7EF] rounded-2xl border border-[#E5DDCF] gap-3">
            <div>
              <div className="text-xs text-gray-500 font-medium">Current Lifecycle Status</div>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${getStatusColor(booking.status)}`}>
                  {booking.status.replace('_', ' ')}
                </span>
                {booking.dispatch_status && (
                  <span className="text-xs font-medium text-gray-600 bg-white px-2.5 py-1 rounded-full border border-gray-200 flex items-center gap-1">
                    <Truck size={12} /> Dispatch: {booking.dispatch_status}
                  </span>
                )}
              </div>
            </div>

            <div className="text-right">
              <div className="text-xs text-gray-500 font-medium">Agreed Total</div>
              <div className="text-lg font-bold text-[#103D2C]">
                ₹{booking.total_amount.toLocaleString('en-IN')}
              </div>
            </div>
          </div>

          {/* Equipment & Schedule Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border border-[#E5DDCF] rounded-2xl p-4 space-y-2 text-xs">
              <h4 className="font-bold text-sm text-[#103D2C]">{booking.listing_title}</h4>
              <div className="text-gray-600">Category: <span className="font-semibold text-gray-800">{booking.category.toUpperCase()}</span></div>
              <div className="text-gray-600">
                Booked For: <span className="font-semibold text-gray-800">{booking.duration} {booking.billing_unit.replace('per_', '')}s</span>
              </div>
              {booking.acreage > 0 && (
                <div className="text-gray-600">Field Area: <span className="font-semibold text-gray-800">{booking.acreage} Acres</span></div>
              )}
            </div>

            <div className="bg-white border border-[#E5DDCF] rounded-2xl p-4 space-y-2 text-xs">
              <div className="flex items-center gap-2 text-[#103D2C] font-semibold">
                <Calendar size={14} /> Schedule & Timing
              </div>
              <div className="text-gray-600">
                Date: <span className="font-semibold text-gray-800">{booking.start_date}</span>
                {booking.end_date !== booking.start_date && <span> to {booking.end_date}</span>}
              </div>
              <div className="text-gray-600">
                Start Time: <span className="font-semibold text-gray-800">{booking.start_time}</span>
              </div>
              <div className="text-gray-600 flex items-center gap-1">
                <MapPin size={12} className="text-gray-400" />
                <span>{booking.farm_location || 'Shioni Shivahar, Akola'}</span>
              </div>
            </div>
          </div>

          {/* Provider Contact Section */}
          <div className="bg-[#FBF7EF] rounded-2xl p-4 border border-[#E5DDCF] text-xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-[#103D2C]">
                <User size={14} /> Provider Details
              </div>
              <span className="text-[10px] text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded font-semibold flex items-center gap-1">
                <ShieldCheck size={12} /> Verified Custom Hiring Provider
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
              <div>
                <span className="text-gray-500">Business: </span>
                <span className="font-semibold text-gray-800">{booking.provider_name}</span>
              </div>
              <div>
                <span className="text-gray-500">Contact: </span>
                {booking.status === 'confirmed' || booking.status === 'in_progress' || booking.status === 'completed' ? (
                  <a href={`tel:${booking.provider_phone}`} className="font-semibold text-[#17643E] hover:underline flex items-center gap-1 inline-flex">
                    <Phone size={11} /> {booking.provider_phone}
                  </a>
                ) : (
                  <span className="text-gray-500 italic">Revealed upon owner confirmation</span>
                )}
              </div>
            </div>
          </div>

          {/* Price Breakdown */}
          <div className="border border-[#E5DDCF] rounded-2xl p-4 space-y-2 text-xs">
            <h5 className="font-bold text-[#103D2C] uppercase tracking-wider text-[11px] mb-2">Itemized Financial Breakdown</h5>
            <div className="flex justify-between py-1 border-b border-[#E5DDCF]/50">
              <span className="text-gray-600">Base Rental Charge ({booking.billing_unit.replace('_', ' ')})</span>
              <span className="font-semibold text-gray-800">₹{booking.base_rental_charge.toLocaleString('en-IN')}</span>
            </div>
            {booking.operator_charge > 0 && (
              <div className="flex justify-between py-1 border-b border-[#E5DDCF]/50">
                <span className="text-gray-600">Certified Operator Charge</span>
                <span className="font-semibold text-gray-800">₹{booking.operator_charge.toLocaleString('en-IN')}</span>
              </div>
            )}
            {booking.transport_charge > 0 && (
              <div className="flex justify-between py-1 border-b border-[#E5DDCF]/50">
                <span className="text-gray-600">Mobilization / Farm Delivery</span>
                <span className="font-semibold text-gray-800">₹{booking.transport_charge.toLocaleString('en-IN')}</span>
              </div>
            )}
            <div className="flex justify-between py-1 border-b border-[#E5DDCF]/50">
              <span className="text-gray-600">Platform Support Fee (Disclosed)</span>
              <span className="font-semibold text-gray-800">₹{booking.platform_fee.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between py-1 pt-2 font-bold text-sm text-[#103D2C]">
              <span>Total Payable</span>
              <span className="text-[#17643E]">₹{booking.total_amount.toLocaleString('en-IN')}</span>
            </div>
            <div className="text-[11px] text-gray-500 pt-1">
              Payment Method: <strong>{booking.payment_method === 'pay_on_service' ? 'Pay on Delivery / Service Completion (Cash or UPI)' : 'Online UPI'}</strong>
            </div>
          </div>

          {/* Direct UPI Settlement Panel */}
          {booking.payment_method === 'online_upi' && (
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-2xl text-xs space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-purple-900 flex items-center gap-1.5">
                  <QrCode size={15} />
                  Direct UPI Payment Settlement
                </span>
                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                  booking.payment_status === 'paid'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-purple-200 text-purple-900'
                }`}>
                  {booking.payment_status === 'paid' ? 'Paid / Verified' : 'Awaiting Settlement'}
                </span>
              </div>
              <p className="text-[11px] text-purple-800">
                {booking.payment_status === 'paid'
                  ? `Payment of ₹${booking.total_amount} verified via UPI Transaction Ref: ${booking.upi_transaction_ref || 'UPI-CONFIRMED'}.`
                  : `Settle direct rental payment to the equipment owner's verified UPI ID with zero platform commission.`}
              </p>
              <button
                type="button"
                onClick={() => setShowUpiModal(true)}
                className="bg-[#103D2C] hover:bg-[#17643E] text-white font-bold py-2 px-4 rounded-xl transition-colors text-xs flex items-center gap-1.5 shadow-sm"
              >
                <QrCode size={13} />
                <span>{booking.payment_status === 'paid' ? 'View UPI Receipt' : `Pay ₹${booking.total_amount} via UPI`}</span>
              </button>
            </div>
          )}

          {/* Farm Economics Sync Card */}
          {booking.status === 'completed' && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-emerald-900">
                  <LineChart size={16} /> Farm Digital Twin & Economics Sync
                </div>
                {booking.recorded_in_economics ? (
                  <span className="bg-emerald-200 text-emerald-900 font-bold px-2 py-0.5 rounded text-[10px]">
                    Recorded in Ledger ({booking.farm_expense_id})
                  </span>
                ) : (
                  <span className="bg-amber-100 text-amber-800 font-medium px-2 py-0.5 rounded text-[10px]">
                    Pending Ledger Recording
                  </span>
                )}
              </div>
              <p className="text-emerald-800/80">
                Connect this completed ₹{booking.total_amount} rental cost directly to your Cotton crop economics and Farm Memory.
              </p>
              {!booking.recorded_in_economics && (
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleRecordExpense}
                  className="mt-2 bg-[#17643E] hover:bg-[#103D2C] text-white font-semibold px-4 py-2 rounded-xl text-xs flex items-center gap-2 shadow-sm transition-colors"
                >
                  {actionLoading ? <Loader2 size={12} className="animate-spin" /> : <LineChart size={12} />}
                  Record Expense in Farm Economics
                </button>
              )}
            </div>
          )}

          {/* Cancellation section */}
          {showCancelPrompt ? (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-4 space-y-3 text-xs">
              <div className="font-bold text-red-900">Cancel Booking Request</div>
              <p className="text-red-700">Please provide a reason for cancellation:</p>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="e.g. Work postponed due to unseasonal rain in Akola"
                className="w-full bg-white border border-red-200 rounded-xl p-2.5 text-xs text-gray-800 focus:outline-none focus:ring-2 focus:ring-red-400"
                rows={2}
              />
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowCancelPrompt(false)}
                  className="px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 bg-white"
                >
                  Keep Booking
                </button>
                <button
                  type="button"
                  disabled={actionLoading || !cancelReason.trim()}
                  onClick={handleCancel}
                  className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold disabled:bg-gray-300"
                >
                  {actionLoading ? 'Cancelling...' : 'Confirm Cancellation'}
                </button>
              </div>
            </div>
          ) : null}

          {/* Review prompt */}
          {showReviewPrompt ? (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 space-y-3 text-xs">
              <div className="font-bold text-amber-900">Rate & Review Your Experience</div>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setRating(s)}
                    className="p-1 hover:scale-110 transition-transform"
                  >
                    <Star
                      size={20}
                      className={s <= rating ? 'text-amber-500 fill-amber-500' : 'text-gray-300'}
                    />
                  </button>
                ))}
              </div>
              <textarea
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                placeholder="Share your experience (e.g., machine condition, operator punctuality, fuel consumption)..."
                className="w-full bg-white border border-amber-200 rounded-xl p-2.5 text-xs text-gray-800 focus:outline-none focus:ring-2 focus:ring-amber-400"
                rows={3}
              />
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowReviewPrompt(false)}
                  className="px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 bg-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={actionLoading || !reviewText.trim()}
                  onClick={handleSubmitReview}
                  className="px-4 py-1.5 rounded-lg bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold disabled:bg-gray-300"
                >
                  {actionLoading ? 'Submitting...' : 'Post Verified Review'}
                </button>
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-[#E5DDCF] bg-[#FBF7EF] flex flex-wrap gap-2 justify-between items-center shrink-0">
          <div className="flex gap-2">
            {(booking.status === 'pending_confirmation' || booking.status === 'confirmed') && !showCancelPrompt && (
              <button
                type="button"
                onClick={() => setShowCancelPrompt(true)}
                className="text-xs font-semibold text-red-700 hover:bg-red-50 border border-red-200 px-3 py-2 rounded-xl transition-colors"
              >
                Cancel Booking
              </button>
            )}

            {booking.status === 'completed' && !showReviewPrompt && (
              <button
                type="button"
                onClick={() => setShowReviewPrompt(true)}
                className="text-xs font-semibold text-amber-900 hover:bg-amber-100 border border-amber-300 bg-amber-50 px-3 py-2 rounded-xl transition-colors flex items-center gap-1"
              >
                <Star size={13} className="text-amber-600 fill-amber-600" /> Leave Review
              </button>
            )}
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="text-xs font-semibold text-gray-700 hover:bg-gray-100 border border-gray-300 bg-white px-3 py-2 rounded-xl transition-colors flex items-center gap-1"
            >
              <Printer size={13} /> Print Invoice
            </button>

            {onRebook && (
              <button
                type="button"
                onClick={() => onRebook(booking.listing_id)}
                className="text-xs font-semibold text-white bg-[#103D2C] hover:bg-[#17643E] px-4 py-2 rounded-xl transition-colors flex items-center gap-1 shadow-sm"
              >
                <RotateCcw size={13} /> Book Again
              </button>
            )}
          </div>
        </div>
      </div>

      {showUpiModal && (
        <UPIPaymentModal
          booking={booking}
          onClose={() => setShowUpiModal(false)}
          onPaymentSuccess={(updated) => {
            onUpdate(updated);
            setShowUpiModal(false);
          }}
        />
      )}
    </div>
  );
}
