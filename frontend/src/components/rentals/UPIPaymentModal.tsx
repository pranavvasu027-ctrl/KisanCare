import React, { useState } from 'react';
import {
  X, CheckCircle2, Copy, Check, QrCode, ExternalLink, IndianRupee,
  ShieldCheck, AlertCircle, Loader2, Smartphone, ArrowRight
} from 'lucide-react';
import { RentalBooking } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';

interface UPIPaymentModalProps {
  booking: RentalBooking;
  onClose: () => void;
  onPaymentSuccess: (updatedBooking: RentalBooking) => void;
}

export default function UPIPaymentModal({
  booking,
  onClose,
  onPaymentSuccess
}: UPIPaymentModalProps) {
  const [copied, setCopied] = useState(false);
  const [utrNumber, setUtrNumber] = useState('');
  const [payerVpa, setPayerVpa] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paidSuccess, setPaidSuccess] = useState<RentalBooking | null>(null);

  const shopkeeperUpiId = booking.upi_id || 'vidarbha-agro@oksbi';
  const payeeName = booking.upi_payee_name || booking.provider_name || 'Agri Equipment Partner';
  const amount = booking.total_amount;
  const refCode = booking.booking_reference;

  // Standard India UPI Intent Protocol URI
  const upiUri = `upi://pay?pa=${shopkeeperUpiId}&pn=${encodeURIComponent(payeeName)}&am=${amount.toFixed(2)}&cu=INR&tn=${encodeURIComponent(refCode)}`;

  // Dynamic QR Code SVG renderer using QuickChart / API QR image for guaranteed mobile scannability
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(upiUri)}&margin=8`;

  const handleCopyUpi = () => {
    navigator.clipboard.writeText(shopkeeperUpiId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirmPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!utrNumber || utrNumber.trim().length < 4) {
      setError('Please enter a valid 12-digit UPI UTR or Transaction Reference number.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const updated = await rentalApi.submitUpiPayment(booking.id, {
        upi_transaction_ref: utrNumber.trim(),
        paid_amount: amount,
        payer_vpa: payerVpa.trim() || undefined
      });
      setPaidSuccess(updated);
      onPaymentSuccess(updated);
    } catch (err: any) {
      setError(err.message || 'Payment confirmation failed. Please check your transaction reference.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-[#292B26]/10 overflow-hidden max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#1E3A2F] text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center text-[#E5A93C]">
              <IndianRupee className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base leading-tight">Direct UPI Settlement to Owner</h3>
              <p className="text-xs text-white/70">Ref: {refCode}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-white/70 hover:text-white rounded-full hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {paidSuccess ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto animate-bounce">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <h4 className="text-xl font-bold text-[#1E3A2F]">Payment Recorded Successfully!</h4>
              <p className="text-sm text-[#292B26]/70 max-w-sm mx-auto">
                Your direct UPI payment of <span className="font-bold text-[#1E3A2F]">₹{amount.toLocaleString('en-IN')}</span> has been registered and verified with <span className="font-semibold">{payeeName}</span>.
              </p>

              <div className="p-4 bg-[#F1F3EE] rounded-2xl text-left text-xs space-y-2 border border-[#292B26]/10">
                <div className="flex justify-between">
                  <span className="text-[#292B26]/60">Transaction Reference / UTR:</span>
                  <span className="font-mono font-bold text-[#1E3A2F]">{paidSuccess.upi_transaction_ref}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#292B26]/60">Payment Status:</span>
                  <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                    PAID / SETTLED
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#292B26]/60">Payee UPI ID:</span>
                  <span className="font-mono text-[#292B26]/80">{shopkeeperUpiId}</span>
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-full py-3 bg-[#1E3A2F] text-white font-semibold rounded-2xl hover:bg-[#1E3A2F]/90 transition-colors shadow-md"
              >
                Close & Return to Bookings
              </button>
            </div>
          ) : (
            <>
              {/* Amount Due Card */}
              <div className="p-4 rounded-2xl bg-gradient-to-br from-[#F5F7F2] to-[#ECEFE6] border border-[#292B26]/10 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-[#292B26]/60 uppercase tracking-wider">Payable Amount</span>
                  <div className="text-2xl font-black text-[#1E3A2F]">₹{amount.toLocaleString('en-IN')}</div>
                  <div className="text-xs text-[#292B26]/70 truncate max-w-[200px]">{booking.listing_title}</div>
                </div>
                <div className="text-right">
                  <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                    Direct to Owner
                  </span>
                  <div className="text-xs text-[#292B26]/60 mt-1">{payeeName}</div>
                </div>
              </div>

              {/* QR Code Section */}
              <div className="flex flex-col items-center justify-center p-4 bg-white border border-[#292B26]/10 rounded-2xl shadow-sm text-center">
                <span className="text-xs font-semibold text-[#1E3A2F] mb-2 flex items-center gap-1.5">
                  <QrCode className="w-4 h-4 text-[#E5A93C]" />
                  Scan with any UPI App (GPay / PhonePe / Paytm / BHIM)
                </span>
                <div className="p-3 bg-white border-2 border-[#1E3A2F]/20 rounded-2xl shadow-inner relative group">
                  <img
                    src={qrCodeUrl}
                    alt="Scan UPI QR"
                    className="w-48 h-48 rounded-xl object-contain"
                  />
                  <div className="absolute inset-0 bg-[#1E3A2F]/5 rounded-2xl pointer-events-none" />
                </div>
                <span className="text-[11px] text-[#292B26]/50 mt-2">
                  Amount ₹{amount} and Reference {refCode} pre-embedded
                </span>
              </div>

              {/* UPI ID Copy Card */}
              <div className="p-3.5 bg-[#F9FBF7] rounded-2xl border border-[#292B26]/10 flex items-center justify-between">
                <div className="min-w-0 pr-3">
                  <div className="text-[11px] text-[#292B26]/60 font-medium">Shopkeeper UPI ID</div>
                  <div className="text-sm font-mono font-bold text-[#1E3A2F] truncate">{shopkeeperUpiId}</div>
                  <div className="text-[11px] text-[#292B26]/50">Payee: {payeeName}</div>
                </div>
                <button
                  type="button"
                  onClick={handleCopyUpi}
                  className={`px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    copied
                      ? 'bg-emerald-600 text-white'
                      : 'bg-[#1E3A2F]/10 text-[#1E3A2F] hover:bg-[#1E3A2F]/20'
                  }`}
                >
                  {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copied!' : 'Copy UPI'}
                </button>
              </div>

              {/* Quick Mobile App Intent Button */}
              <a
                href={upiUri}
                target="_blank"
                rel="noreferrer"
                className="w-full py-2.5 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-transform active:scale-[0.98]"
              >
                <Smartphone className="w-4 h-4" />
                Open Installed UPI App (Mobile Device)
                <ExternalLink className="w-3.5 h-3.5" />
              </a>

              {/* UTR Input Form */}
              <form onSubmit={handleConfirmPayment} className="space-y-3 pt-2 border-t border-[#292B26]/10">
                <div>
                  <label className="block text-xs font-bold text-[#1E3A2F] mb-1">
                    Enter 12-Digit UTR / Transaction Reference Number <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={utrNumber}
                    onChange={(e) => setUtrNumber(e.target.value)}
                    placeholder="e.g. 429188492019 or UPI Ref ID"
                    className="w-full px-3.5 py-2.5 text-sm bg-white border border-[#292B26]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A2F] font-mono"
                  />
                  <p className="text-[11px] text-[#292B26]/60 mt-1">
                    Found in your payment app under "Google Pay / PhonePe Transaction Details".
                  </p>
                </div>

                {error && (
                  <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-xl flex items-center gap-2 border border-rose-200">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-3 bg-[#1E3A2F] hover:bg-[#1E3A2F]/90 text-white font-bold rounded-2xl flex items-center justify-center gap-2 shadow-md transition-all disabled:opacity-50"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Verifying Payment...
                    </>
                  ) : (
                    <>
                      Confirm & Submit Payment
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
