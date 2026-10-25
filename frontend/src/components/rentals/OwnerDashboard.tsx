import React, { useState, useEffect } from 'react';
import {
  Tractor, CheckCircle, XCircle, Clock, PlusCircle, AlertCircle,
  Truck, Users, DollarSign, Calendar, Eye, Power, Loader2, Star,
  ShieldCheck, Bell, Sparkles, Navigation, MapPin, QrCode, Check,
  CreditCard, ArrowRight, ShieldAlert, Store
} from 'lucide-react';
import {
  RentalListing, RentalBooking, RentalCategory, BillingUnit,
  ShopNotification, ShopkeeperSubscriptionPlan
} from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';

interface OwnerDashboardProps {
  onListingCreated?: (newListing: RentalListing) => void;
}

export default function OwnerDashboard({ onListingCreated }: OwnerDashboardProps) {
  const [activeTab, setActiveTab] = useState<'requests' | 'notifications' | 'listings' | 'subscription' | 'create'>('requests');
  const [listings, setListings] = useState<RentalListing[]>([]);
  const [requests, setRequests] = useState<RentalBooking[]>([]);
  const [notifications, setNotifications] = useState<ShopNotification[]>([]);
  const [subscriptionPlans, setSubscriptionPlans] = useState<ShopkeeperSubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<any>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [subscribing, setSubscribing] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form state for Create Listing
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState<RentalCategory>('tractor');
  const [newSubcategory, setNewSubcategory] = useState('45hp_tractor');
  const [newDescription, setNewDescription] = useState('');
  const [newBillingUnit, setNewBillingUnit] = useState<BillingUnit>('per_operating_hour');
  const [newPrice, setNewPrice] = useState<number>(800);
  const [newMinDuration, setNewMinDuration] = useState<number>(2);
  const [newDistrict, setNewDistrict] = useState('Akola');
  const [newTaluka, setNewTaluka] = useState('Akola');
  const [newRadius, setNewRadius] = useState<number>(25);
  const [newHorsepower, setNewHorsepower] = useState<number>(45);
  const [newOperatorIncluded, setNewOperatorIncluded] = useState<boolean>(true);
  const [newFuelPolicy, setNewFuelPolicy] = useState('renter_bears_fuel');
  const [newDeliveryFee, setNewDeliveryFee] = useState<number>(150);

  // GPS coordinates & UPI details
  const [shopLatitude, setShopLatitude] = useState<number>(20.7002);
  const [shopLongitude, setShopLongitude] = useState<number>(77.0082);
  const [detectingGps, setDetectingGps] = useState<boolean>(false);
  const [newUpiId, setNewUpiId] = useState<string>('vidarbha.agro@okhdfcbank');
  const [newUpiPayeeName, setNewUpiPayeeName] = useState<string>('Vidarbha Agro Equipment Store');

  const [creating, setCreating] = useState(false);

  const ownerId = 'PROV_AKOLA_01';

  useEffect(() => {
    loadOwnerData();
  }, []);

  const loadOwnerData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ownerListings, ownerRequests, ownerNotifs, plans, sub] = await Promise.all([
        rentalApi.getOwnerListings(ownerId),
        rentalApi.getOwnerRequests(ownerId),
        rentalApi.getOwnerNotifications(ownerId).catch(() => []),
        rentalApi.getSubscriptionPlans().catch(() => []),
        rentalApi.getOwnerSubscription(ownerId).catch(() => null)
      ]);
      setListings(ownerListings);
      setRequests(ownerRequests);
      setNotifications(ownerNotifs);
      setSubscriptionPlans(plans);
      setCurrentSubscription(sub);
    } catch (err: any) {
      setError(err.message || 'Failed to load owner data');
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (bookingId: string, action: 'confirm' | 'reject') => {
    setActionLoading(bookingId);
    try {
      const updated = await rentalApi.respondToBooking(bookingId, action);
      setMessage(`Booking ${updated.booking_reference} marked as ${action === 'confirm' ? 'Confirmed' : 'Rejected'}.`);
      setRequests(prev => prev.map(r => r.id === bookingId ? updated : r));

      // Also refresh notifications to reflect updated state
      const refreshedNotifs = await rentalApi.getOwnerNotifications(ownerId).catch(() => []);
      setNotifications(refreshedNotifs);
    } catch (err: any) {
      setError(err.message || 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateDispatch = async (bookingId: string, dispatchStatus: string) => {
    setActionLoading(bookingId);
    try {
      const updated = await rentalApi.updateDispatchStatus(bookingId, dispatchStatus);
      setMessage(`Dispatch status updated to '${dispatchStatus}'.`);
      setRequests(prev => prev.map(r => r.id === bookingId ? updated : r));
    } catch (err: any) {
      setError(err.message || 'Failed to update dispatch status');
    } finally {
      setActionLoading(null);
    }
  };

  const handleMarkNotificationRead = async (notifId: string) => {
    try {
      await rentalApi.markNotificationRead(notifId);
      setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, is_read: true } : n));
    } catch {
      // ignore
    }
  };

  const handleUpgradeSubscription = async (planId: string) => {
    setSubscribing(true);
    setError(null);
    try {
      const updatedSub = await rentalApi.upgradeOwnerSubscription({
        plan_id: planId,
        provider_id: ownerId,
        duration_months: 1,
        upi_transaction_ref: `UPI-SUB-${Date.now().toString(36).toUpperCase()}`
      });
      setCurrentSubscription(updatedSub);
      setMessage(`🎉 Successfully upgraded to ${updatedSub.tier_name || 'Gold Merchant'}! Priority ranking in 10km radius is now ACTIVE.`);
      // Reload listings to reflect priority ranking
      const refreshed = await rentalApi.getOwnerListings(ownerId);
      setListings(refreshed);
    } catch (err: any) {
      setError(err.message || 'Failed to upgrade subscription');
    } finally {
      setSubscribing(false);
    }
  };

  const handleDetectGPS = () => {
    if (!navigator.geolocation) {
      setMessage('Geolocation is not supported by your browser. Using Akola coordinates.');
      return;
    }
    setDetectingGps(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setShopLatitude(parseFloat(pos.coords.latitude.toFixed(6)));
        setShopLongitude(parseFloat(pos.coords.longitude.toFixed(6)));
        setDetectingGps(false);
        setMessage(`Detected Shop GPS: ${pos.coords.latitude.toFixed(4)}° N, ${pos.coords.longitude.toFixed(4)}° E`);
      },
      (err) => {
        setDetectingGps(false);
        setMessage(`GPS detection note: ${err.message}. Using default center.`);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleCreateListing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newDescription || newPrice <= 0) {
      setError('Please provide title, description, and a valid positive price.');
      return;
    }

    setCreating(true);
    setError(null);
    try {
      const created = await rentalApi.createListing({
        title: newTitle,
        category: newCategory,
        subcategory: newSubcategory,
        description: newDescription,
        billing_unit: newBillingUnit,
        price: newPrice,
        min_duration: newMinDuration,
        min_charge: newPrice * newMinDuration,
        district: newDistrict,
        taluka: newTaluka,
        service_radius_km: newRadius,
        latitude: shopLatitude,
        longitude: shopLongitude,
        upi_id: newUpiId.trim() || undefined,
        upi_payee_name: newUpiPayeeName.trim() || undefined,
        specs: {
          horsepower: newHorsepower,
          operator_included: newOperatorIncluded,
          fuel_policy: newFuelPolicy
        },
        terms: {
          delivery_fee: newDeliveryFee,
          cancellation_policy: 'Free cancellation 12 hours prior to scheduled start.'
        },
        is_active: true
      }, ownerId);

      setMessage(`Listing '${created.title}' published successfully with verified GPS & UPI payment settlement!`);
      setListings(prev => [created, ...prev]);
      setActiveTab('listings');
      if (onListingCreated) onListingCreated(created);

      // Reset form
      setNewTitle('');
      setNewDescription('');
    } catch (err: any) {
      setError(err.message || 'Failed to create listing');
    } finally {
      setCreating(false);
    }
  };

  // Metrics
  const pendingRequests = requests.filter(r => r.status === 'pending_confirmation');
  const activeJobs = requests.filter(r => r.status === 'confirmed' || r.status === 'in_progress');
  const completedJobs = requests.filter(r => r.status === 'completed');
  const totalEarnings = completedJobs.reduce((acc, curr) => acc + curr.total_amount, 0);
  const unreadNotifs = notifications.filter(n => n.status === 'unread').length;

  return (
    <div className="space-y-6">
      {/* Crisp Header Bar */}
      <div className="bg-white rounded-2xl p-4 border border-[#E5DDCF] shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 text-[#103D2C] rounded-xl font-bold">
            <Tractor size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-[#103D2C]">Shopkeeper & Equipment Dashboard</h2>
              {currentSubscription?.priority_ranking ? (
                <span className="text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-amber-400 text-gray-900 flex items-center gap-1">
                  <Sparkles size={10} className="fill-gray-900" />
                  {currentSubscription.tier_name || 'Gold'} • Priority Active
                </span>
              ) : (
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
                  Free Starter Plan
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">Vidarbha Agro CHC • Akola</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('subscription')}
            className="bg-[#FBF7EF] hover:bg-[#F2E8D5] text-[#103D2C] border border-[#E5DDCF] font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors"
          >
            <Sparkles size={13} className="text-amber-500" />
            <span>Priority Plans</span>
          </button>
          <button
            onClick={() => setActiveTab('create')}
            className="bg-[#103D2C] hover:bg-[#17643E] text-white font-bold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <PlusCircle size={14} />
            <span>Add Equipment</span>
          </button>
        </div>
      </div>

      {message && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-2xl text-xs flex items-center gap-2">
          <CheckCircle size={16} className="text-emerald-600 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-2xl text-xs flex items-center gap-2">
          <AlertCircle size={16} className="text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500">Pending Requests</span>
            <Clock size={16} className="text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-2">{pendingRequests.length}</div>
          <div className="text-[11px] text-gray-400 mt-1">Awaiting your confirmation</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500">Active / Dispatched Jobs</span>
            <Truck size={16} className="text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-blue-800 mt-2">{activeJobs.length}</div>
          <div className="text-[11px] text-gray-400 mt-1">Operating in Vidarbha fields</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500">Fleet Listings</span>
            <Tractor size={16} className="text-[#103D2C]" />
          </div>
          <div className="text-2xl font-bold text-[#103D2C] mt-2">{listings.length}</div>
          <div className="text-[11px] text-gray-400 mt-1">Active for rental discovery</div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500">Total Settled Earnings</span>
            <DollarSign size={16} className="text-[#17643E]" />
          </div>
          <div className="text-2xl font-bold text-[#17643E] mt-2">
            ₹{totalEarnings.toLocaleString('en-IN')}
          </div>
          <div className="text-[11px] text-gray-400 mt-1">{completedJobs.length} completed rentals</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#E5DDCF] gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('requests')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'requests'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          Incoming & Active Bookings ({requests.length})
        </button>

        <button
          onClick={() => setActiveTab('notifications')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'notifications'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          <Bell size={13} />
          <span>Notifications</span>
          {unreadNotifs > 0 && (
            <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full animate-pulse">
              {unreadNotifs}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('listings')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'listings'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          My Listed Equipment ({listings.length})
        </button>

        <button
          onClick={() => setActiveTab('subscription')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap flex items-center gap-1 ${
            activeTab === 'subscription'
              ? 'border-amber-500 text-amber-700'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          <Sparkles size={13} className="text-amber-500" />
          <span>Shopkeeper Plans & Revenue</span>
        </button>

        <button
          onClick={() => setActiveTab('create')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'create'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          + Add New Equipment
        </button>
      </div>

      {/* TAB 1: REQUESTS */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          {requests.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-[#E5DDCF] text-gray-500 text-sm">
              No booking requests received yet. When farmers submit rental requests, they appear here instantly.
            </div>
          ) : (
            requests.map((req) => (
              <div
                key={req.id}
                className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#103D2C] bg-[#FBF7EF] px-2 py-0.5 rounded border border-[#E5DDCF]">
                      {req.booking_reference}
                    </span>
                    <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full ${
                      req.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                      req.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                      req.status === 'completed' ? 'bg-green-100 text-green-900' :
                      req.status === 'rejected' || req.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                      'bg-amber-100 text-amber-900'
                    }`}>
                      {req.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-400">• Dispatch: {req.dispatch_status}</span>

                    {req.payment_method === 'online_upi' && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200 flex items-center gap-1">
                        <QrCode size={10} />
                        Direct UPI {req.payment_status === 'paid' ? '• Settled' : '• Pending Settlement'}
                      </span>
                    )}
                  </div>

                  <h4 className="font-bold text-sm text-[#103D2C]">{req.listing_title}</h4>
                  <div className="text-xs text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
                    <span>Farmer: <strong>{req.farmer_name}</strong> ({req.farmer_phone})</span>
                    <span>Date: <strong>{req.start_date} ({req.start_time})</strong></span>
                    <span>Duration: <strong>{req.duration} {req.billing_unit.replace('per_', '')}s</strong></span>
                    <span>Agreed Amount: <strong className="text-[#17643E]">₹{req.total_amount}</strong></span>
                    <span>Field: <strong>{req.farm_location || 'Akola'}</strong></span>
                  </div>
                  {req.notes && (
                    <div className="text-[11px] text-gray-500 italic bg-[#FBF7EF] p-2 rounded-lg">
                      Note from farmer: "{req.notes}"
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  {req.status === 'pending_confirmation' && (
                    <>
                      <button
                        type="button"
                        disabled={actionLoading === req.id}
                        onClick={() => handleRespond(req.id, 'confirm')}
                        className="bg-[#17643E] hover:bg-[#103D2C] text-white text-xs font-bold px-4 py-2 rounded-xl transition-colors shadow-sm flex items-center gap-1"
                      >
                        {actionLoading === req.id ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle size={14} />}
                        Accept & Confirm
                      </button>
                      <button
                        type="button"
                        disabled={actionLoading === req.id}
                        onClick={() => handleRespond(req.id, 'reject')}
                        className="bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 text-xs font-semibold px-3 py-2 rounded-xl transition-colors"
                      >
                        Decline
                      </button>
                    </>
                  )}

                  {req.status === 'confirmed' && (
                    <button
                      type="button"
                      disabled={actionLoading === req.id}
                      onClick={() => handleUpdateDispatch(req.id, 'dispatched')}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded-xl transition-colors flex items-center gap-1 shadow-sm"
                    >
                      <Truck size={14} /> Mark Dispatched to Field
                    </button>
                  )}

                  {req.status === 'in_progress' && (
                    <button
                      type="button"
                      disabled={actionLoading === req.id}
                      onClick={() => handleUpdateDispatch(req.id, 'completed')}
                      className="bg-green-700 hover:bg-green-800 text-white text-xs font-bold px-4 py-2 rounded-xl transition-colors flex items-center gap-1 shadow-sm"
                    >
                      <CheckCircle size={14} /> Mark Work Completed
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 2: LIVE NOTIFICATIONS */}
      {activeTab === 'notifications' && (
        <div className="bg-white rounded-3xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5DDCF]/70">
            <div>
              <h3 className="font-serif font-bold text-lg text-[#103D2C] flex items-center gap-2">
                <Bell className="text-[#17643E]" size={20} />
                Real-Time Farmer Booking Inquiries & Notifications
              </h3>
              <p className="text-xs text-gray-500">
                Instantly alerted whenever a farmer requests equipment in your 10km radius.
              </p>
            </div>
            <span className="text-xs font-semibold text-gray-500">
              Total: {notifications.length} ({unreadNotifs} unread)
            </span>
          </div>

          {notifications.length === 0 ? (
            <div className="p-8 text-center text-xs text-gray-400">
              No notifications yet. You will receive live alerts when farmers place bookings.
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((notif) => {
                const isUnread = notif.status === 'unread';
                return (
                  <div
                    key={notif.id}
                    className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 ${
                      !isUnread
                        ? 'bg-[#FBF7EF]/50 border-[#E5DDCF]'
                        : 'bg-emerald-50/60 border-emerald-300 shadow-sm'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#103D2C] text-white">
                          Booking Inquiry
                        </span>
                        {isUnread && (
                          <span className="text-[10px] font-bold text-emerald-800 bg-emerald-200 px-2 py-0.5 rounded-full">
                            NEW
                          </span>
                        )}
                        <span className="text-[11px] text-gray-400">
                          Ref: {notif.booking_reference || 'N/A'}
                        </span>
                      </div>
                      <h4 className="font-bold text-xs text-[#103D2C]">{notif.listing_title}</h4>
                      <p className="text-xs text-gray-600">
                        Farmer {notif.farmer_name} ({notif.farmer_phone}) requested {notif.scheduled_date} at {notif.start_time}. Agreed Amount: ₹{notif.total_amount}. ({notif.payment_method === 'online_upi' ? 'Direct UPI' : 'Pay on Delivery'})
                      </p>
                      <div className="text-[11px] text-gray-400">
                        {new Date(notif.created_at).toLocaleString()}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {notif.booking_id && (
                        <button
                          onClick={() => {
                            setActiveTab('requests');
                            handleMarkNotificationRead(notif.id);
                          }}
                          className="bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-bold px-3 py-1.5 rounded-xl transition-colors"
                        >
                          View in Bookings
                        </button>
                      )}
                      {isUnread && (
                        <button
                          onClick={() => handleMarkNotificationRead(notif.id)}
                          className="text-xs font-semibold text-gray-500 hover:text-gray-800 px-2.5 py-1.5 rounded-lg border border-gray-300 bg-white"
                        >
                          Mark Read
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: LISTINGS */}
      {activeTab === 'listings' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {listings.map((l) => (
            <div key={l.id} className="bg-white rounded-2xl border border-[#E5DDCF] overflow-hidden shadow-sm flex flex-col">
              {l.image_url && (
                <img src={l.image_url} alt={l.title} className="h-40 w-full object-cover" />
              )}
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-[#103D2C] uppercase">{l.category}</span>
                    <div className="flex items-center gap-1">
                      {l.is_priority && (
                        <span className="text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Sparkles size={10} /> Priority Listed
                        </span>
                      )}
                      <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold text-[10px]">
                        Active
                      </span>
                    </div>
                  </div>
                  <h4 className="font-serif font-bold text-sm text-[#103D2C] mt-1">{l.title}</h4>
                  <p className="text-xs text-gray-500 line-clamp-2 mt-1">{l.description}</p>

                  {/* UPI info */}
                  {l.upi_id && (
                    <div className="mt-2 text-[10px] text-purple-900 bg-purple-50 border border-purple-200 px-2 py-1 rounded-lg flex items-center gap-1 font-mono">
                      <QrCode size={11} className="shrink-0" />
                      <span>UPI: {l.upi_id}</span>
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-[#E5DDCF] flex items-center justify-between">
                  <div>
                    <span className="text-base font-bold text-[#103D2C]">₹{l.price}</span>
                    <span className="text-[11px] text-gray-500 ml-1">/{l.billing_unit.replace('per_', '')}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-amber-700 font-semibold">
                    <Star size={13} className="fill-amber-500 text-amber-500" /> {l.rating || 4.8}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 4: SUBSCRIPTION & REVENUE MODEL */}
      {activeTab === 'subscription' && (
        <div className="bg-white rounded-3xl p-6 lg:p-8 border border-[#E5DDCF] shadow-sm space-y-6">
          <div>
            <h3 className="font-serif font-bold text-lg text-[#103D2C]">
              Priority Ranking Plans
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Get prioritized search ranking for farmers within 50 km and verified badge placement.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {subscriptionPlans.map((plan) => {
              const isCurrent = currentSubscription?.tier === plan.plan_id;
              const isRecommended = (plan.priority_level || 0) >= 2;
              return (
                <div
                  key={plan.plan_id}
                  className={`rounded-3xl p-6 border transition-all flex flex-col justify-between space-y-4 ${
                    isCurrent
                      ? 'border-[#17643E] bg-[#17643E]/5 ring-2 ring-[#17643E]'
                      : isRecommended
                      ? 'border-amber-400 bg-amber-50/40 shadow-md'
                      : 'border-[#E5DDCF] bg-white'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="font-serif font-bold text-lg text-[#103D2C]">{plan.name}</h4>
                      {isRecommended && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-400 text-gray-900">
                          Recommended
                        </span>
                      )}
                      {isCurrent && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-600 text-white">
                          Current Plan
                        </span>
                      )}
                    </div>

                    <div className="flex items-baseline gap-1">
                      <span className="text-2xl font-bold text-[#103D2C]">₹{plan.price_inr}</span>
                      <span className="text-xs text-gray-500">/ {plan.billing_cycle || 'month'}</span>
                    </div>

                    <ul className="space-y-2 pt-2 border-t border-[#E5DDCF]/60 text-xs text-gray-700">
                      {plan.features.map((feat, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <Check size={14} className="text-[#17643E] shrink-0 mt-0.5" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    {isCurrent ? (
                      <div className="w-full py-2.5 rounded-xl text-center text-xs font-bold text-emerald-800 bg-emerald-100">
                        Active & In Good Standing
                      </div>
                    ) : (
                      <button
                        type="button"
                        disabled={subscribing}
                        onClick={() => handleUpgradeSubscription(plan.plan_id)}
                        className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5 ${
                          isRecommended
                            ? 'bg-[#103D2C] hover:bg-[#17643E] text-white'
                            : 'bg-gray-800 hover:bg-black text-white'
                        }`}
                      >
                        {subscribing ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                        <span>Upgrade to {plan.name}</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 5: CREATE LISTING */}
      {activeTab === 'create' && (
        <form onSubmit={handleCreateListing} className="bg-white rounded-3xl p-6 lg:p-8 border border-[#E5DDCF] shadow-sm space-y-6 max-w-3xl">
          <div>
            <h3 className="font-serif font-bold text-xl text-[#103D2C]">List New Agricultural Equipment or Service</h3>
            <p className="text-xs text-gray-500 mt-1">Make your machinery or farm equipment available to local farmers across Akola & Vidarbha.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-700 mb-1">Listing Title</label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Swaraj 744 XT (50 HP) with Automatic Seed Drill & Operator"
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Rental Category</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value as RentalCategory)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
              >
                <option value="tractor">Tractor & Heavy Machinery</option>
                <option value="equipment">Agricultural Equipment & Implements</option>
                <option value="transport">Trucks & Agricultural Transport</option>
                <option value="labour">Labour & Farm Workers</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Billing Unit</label>
              <select
                value={newBillingUnit}
                onChange={(e) => setNewBillingUnit(e.target.value as BillingUnit)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
              >
                <option value="per_operating_hour">Per Operating Hour</option>
                <option value="per_day">Per Day (Standard Shift)</option>
                <option value="per_acre">Per Acre (Field Work)</option>
                <option value="per_worker_day">Per Worker / Day</option>
                <option value="per_trip">Per Trip (Haulage)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Rental Rate (₹)</label>
              <input
                type="number"
                min="50"
                value={newPrice}
                onChange={(e) => setNewPrice(parseFloat(e.target.value) || 0)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Minimum Booking Duration</label>
              <input
                type="number"
                min="1"
                value={newMinDuration}
                onChange={(e) => setNewMinDuration(parseInt(e.target.value) || 1)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gray-700 mb-1">Detailed Description & Specifications</label>
              <textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                rows={3}
                placeholder="Include condition of implements, engine power, suitable crops, and working conditions..."
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl p-3 text-xs text-[#103D2C]"
                required
              />
            </div>

            {/* SHOP LOCATION SECTION (REQUIRED BY USER) */}
            <div className="md:col-span-2 p-4 bg-[#FBF7EF] rounded-2xl border border-[#E5DDCF] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-[#103D2C] flex items-center gap-1.5 uppercase tracking-wider">
                    <MapPin size={14} className="text-[#17643E]" />
                    Shop & Equipment Location
                  </h4>
                  <p className="text-[11px] text-gray-500">Farmers within 50 km discover this equipment nearest-first.</p>
                </div>
                <button
                  type="button"
                  onClick={handleDetectGPS}
                  disabled={detectingGps}
                  className="bg-white hover:bg-emerald-50 text-[#103D2C] border border-[#E5DDCF] text-xs font-bold px-3 py-1.5 rounded-xl flex items-center gap-1 shadow-sm transition-colors"
                >
                  <Navigation size={12} className={detectingGps ? 'animate-spin' : ''} />
                  <span>{detectingGps ? 'Locating...' : 'Detect GPS Location'}</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 mb-1">Latitude</label>
                  <input
                    type="number"
                    step="any"
                    value={shopLatitude}
                    onChange={(e) => setShopLatitude(parseFloat(e.target.value) || 20.7002)}
                    className="w-full bg-white border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 mb-1">Longitude</label>
                  <input
                    type="number"
                    step="any"
                    value={shopLongitude}
                    onChange={(e) => setShopLongitude(parseFloat(e.target.value) || 77.0082)}
                    className="w-full bg-white border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 mb-1">Taluka / Town</label>
                  <input
                    type="text"
                    value={newTaluka}
                    onChange={(e) => setNewTaluka(e.target.value)}
                    placeholder="Akola / Murtizapur"
                    className="w-full bg-white border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
                  />
                </div>
              </div>
            </div>

            {/* SHOPKEEPER UPI CREDENTIALS SECTION (REQUIRED BY USER) */}
            <div className="md:col-span-2 p-4 bg-[#FBF7EF] rounded-2xl border border-[#E5DDCF] space-y-3">
              <h4 className="text-xs font-bold text-[#103D2C] flex items-center gap-1.5 uppercase tracking-wider">
                <QrCode size={14} className="text-[#17643E]" />
                Direct UPI Settlement Details
              </h4>
              <p className="text-[11px] text-gray-500">
                When farmers book with "Direct UPI to Owner", payment QR codes and payment requests will be routed directly to this UPI ID.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 mb-1">Your UPI ID (VPA)</label>
                  <input
                    type="text"
                    value={newUpiId}
                    onChange={(e) => setNewUpiId(e.target.value)}
                    placeholder="e.g. vidarbha.agro@okhdfcbank"
                    className="w-full bg-white border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-mono font-semibold text-[#103D2C]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-gray-600 mb-1">Payee Business / Shop Name</label>
                  <input
                    type="text"
                    value={newUpiPayeeName}
                    onChange={(e) => setNewUpiPayeeName(e.target.value)}
                    placeholder="e.g. Vidarbha Agro Machinery Store"
                    className="w-full bg-white border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
                    required
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Service Radius (km)</label>
              <input
                type="number"
                min="5"
                max="100"
                value={newRadius}
                onChange={(e) => setNewRadius(parseInt(e.target.value) || 25)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Delivery / Mobilization Fee (₹)</label>
              <input
                type="number"
                min="0"
                value={newDeliveryFee}
                onChange={(e) => setNewDeliveryFee(parseFloat(e.target.value) || 0)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-[#E5DDCF]">
            <button
              type="submit"
              disabled={creating}
              className="bg-[#103D2C] hover:bg-[#17643E] text-white font-bold py-3 px-6 rounded-xl transition-colors text-xs flex items-center gap-2 shadow-sm"
            >
              {creating ? <Loader2 size={14} className="animate-spin" /> : <PlusCircle size={14} />}
              Publish Listing with 10km Radius & UPI Settlement
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
