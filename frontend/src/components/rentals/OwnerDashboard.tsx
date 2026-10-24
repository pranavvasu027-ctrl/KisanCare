import React, { useState, useEffect } from 'react';
import {
  Tractor, CheckCircle, XCircle, Clock, PlusCircle, AlertCircle,
  Truck, Users, DollarSign, Calendar, Eye, Power, Loader2, Star, ShieldCheck
} from 'lucide-react';
import { RentalListing, RentalBooking, RentalCategory, BillingUnit } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';

interface OwnerDashboardProps {
  onListingCreated?: (newListing: RentalListing) => void;
}

export default function OwnerDashboard({ onListingCreated }: OwnerDashboardProps) {
  const [activeTab, setActiveTab] = useState<'requests' | 'listings' | 'create'>('requests');
  const [listings, setListings] = useState<RentalListing[]>([]);
  const [requests, setRequests] = useState<RentalBooking[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
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
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadOwnerData();
  }, []);

  const loadOwnerData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ownerListings, ownerRequests] = await Promise.all([
        rentalApi.getOwnerListings('PROV_AKOLA_01'),
        rentalApi.getOwnerRequests('PROV_AKOLA_01')
      ]);
      setListings(ownerListings);
      setRequests(ownerRequests);
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
      }, 'PROV_AKOLA_01');

      setMessage(`Listing '${created.title}' published successfully!`);
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

  return (
    <div className="space-y-6">
      {/* Provider Header Banner */}
      <div className="bg-[#103D2C] text-white rounded-3xl p-6 lg:p-8 shadow-sm border border-[#E5DDCF] flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#17643E] text-emerald-100 flex items-center gap-1">
              <ShieldCheck size={12} /> CHC Authorized Custom Hiring Center
            </span>
            <span className="text-xs text-emerald-200">Akola District FPO Federation</span>
          </div>
          <h2 className="text-2xl font-serif font-bold text-white mt-1">Vidarbha Agro Machinery CHC Portal</h2>
          <p className="text-xs text-emerald-200/80 mt-1">
            Manage your agricultural fleet, accept farmer bookings, and track daily machine dispatch.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('create')}
            className="bg-[#17643E] hover:bg-emerald-600 text-white font-bold text-xs px-4 py-2.5 rounded-xl flex items-center gap-2 transition-colors shadow-sm"
          >
            <PlusCircle size={15} /> Add Equipment / Service
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
      <div className="flex border-b border-[#E5DDCF] gap-2">
        <button
          onClick={() => setActiveTab('requests')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 ${
            activeTab === 'requests'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          Incoming & Active Bookings ({requests.length})
        </button>

        <button
          onClick={() => setActiveTab('listings')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 ${
            activeTab === 'listings'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          My Listed Machinery ({listings.length})
        </button>

        <button
          onClick={() => setActiveTab('create')}
          className={`pb-3 px-4 font-bold text-xs uppercase tracking-wider transition-colors border-b-2 ${
            activeTab === 'create'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-gray-400 hover:text-gray-700'
          }`}
        >
          + List New Machinery / Team
        </button>
      </div>

      {/* TAB 1: REQUESTS */}
      {activeTab === 'requests' && (
        <div className="space-y-4">
          {requests.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-[#E5DDCF] text-gray-500 text-sm">
              No booking requests received yet.
            </div>
          ) : (
            requests.map((req) => (
              <div
                key={req.id}
                className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
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
                  </div>

                  <h4 className="font-bold text-sm text-[#103D2C]">{req.listing_title}</h4>
                  <div className="text-xs text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
                    <span>Farmer: <strong>{req.farmer_name}</strong> ({req.farmer_phone})</span>
                    <span>Date: <strong>{req.start_date} ({req.start_time})</strong></span>
                    <span>Duration: <strong>{req.duration} {req.billing_unit.replace('per_', '')}s</strong></span>
                    <span>Agreed Amount: <strong className="text-[#17643E]">₹{req.total_amount}</strong></span>
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

      {/* TAB 2: LISTINGS */}
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
                    <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold text-[10px]">
                      Active for Rent
                    </span>
                  </div>
                  <h4 className="font-serif font-bold text-sm text-[#103D2C] mt-1">{l.title}</h4>
                  <p className="text-xs text-gray-500 line-clamp-2 mt-1">{l.description}</p>
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

      {/* TAB 3: CREATE LISTING */}
      {activeTab === 'create' && (
        <form onSubmit={handleCreateListing} className="bg-white rounded-3xl p-6 lg:p-8 border border-[#E5DDCF] shadow-sm space-y-6 max-w-3xl">
          <div>
            <h3 className="font-serif font-bold text-xl text-[#103D2C]">List New Agricultural Equipment or Service</h3>
            <p className="text-xs text-gray-500 mt-1">Make your machinery or farm workers available to local farmers across Akola & Vidarbha.</p>
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

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Taluka / Location</label>
              <input
                type="text"
                value={newTaluka}
                onChange={(e) => setNewTaluka(e.target.value)}
                placeholder="e.g. Murtizapur, Akola"
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-semibold text-[#103D2C]"
              />
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
          </div>

          <div className="flex gap-3 pt-4 border-t border-[#E5DDCF]">
            <button
              type="submit"
              disabled={creating}
              className="bg-[#103D2C] hover:bg-[#17643E] text-white font-bold py-3 px-6 rounded-xl transition-colors text-xs flex items-center gap-2 shadow-sm"
            >
              {creating ? <Loader2 size={14} className="animate-spin" /> : <PlusCircle size={14} />}
              Publish Listing to KisanCare Marketplace
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
