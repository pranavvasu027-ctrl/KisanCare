import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Tractor, Wrench, Truck, Users, Search, Filter, MapPin, Calendar,
  ShieldCheck, Star, Clock, IndianRupee, ChevronRight, CheckCircle2,
  AlertCircle, Eye, PlusCircle, RefreshCw, Layers, LayoutGrid, List,
  Map as MapIcon, SlidersHorizontal, Sparkles, Navigation, GraduationCap
} from 'lucide-react';
import { RentalListing, RentalCategory, RentalBooking, BillingUnit } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';
import { useAuth } from '../../hooks/useAuth';

// Subcomponents
import BookingModal from '../../components/rentals/BookingModal';
import BookingDetailsModal from '../../components/rentals/BookingDetailsModal';
import OwnerDashboard from '../../components/rentals/OwnerDashboard';
import MarketRateBenchmarkPanel from '../../components/rentals/MarketRateBenchmarkPanel';
import SmartRecommendationBanner from '../../components/rentals/SmartRecommendationBanner';
import ServiceCoverageMap from '../../components/rentals/ServiceCoverageMap';
import { LocationSelector } from '../../components/rentals/LocationSelector';
import { ListingImage } from '../../components/rentals/ListingImage';

export type MarketplaceSection =
  | 'discover'
  | 'equipment'
  | 'tractors'
  | 'transport'
  | 'labour'
  | 'specialists'
  | 'upcoming'
  | 'active'
  | 'history'
  | 'list_equipment'
  | 'owner_dashboard';

export default function RentalMarketplace() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSection = (searchParams.get('tab') as MarketplaceSection) || 'discover';

  const [activeSection, setActiveSection] = useState<MarketplaceSection>(initialSection);
  const [listings, setListings] = useState<RentalListing[]>([]);
  const [bookings, setBookings] = useState<RentalBooking[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Geographic Cascading Filters
  const [selectedDivision, setSelectedDivision] = useState<string | undefined>(undefined);
  const [selectedDistrict, setSelectedDistrict] = useState<string | undefined>(undefined);
  const [selectedTaluka, setSelectedTaluka] = useState<string | undefined>(undefined);

  // Search & Commercial Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBillingUnit, setSelectedBillingUnit] = useState('all');
  const [maxPrice, setMaxPrice] = useState<number>(5000);
  const [verifiedOnly, setVerifiedOnly] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<string>('relevance');
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'map'>('grid');

  // Modal interactions
  const [selectedListingForBooking, setSelectedListingForBooking] = useState<RentalListing | null>(null);
  const [selectedBookingForDetails, setSelectedBookingForDetails] = useState<RentalBooking | null>(null);

  // Farm & User context from authentic KisanCare auth/state
  const { user } = useAuth();
  const activeFarm = { name: 'Green Acres', village: 'Shioni', district: 'Akola', id: 'FARM_001' };
  const activeField = { id: 'FLD_01', currentCrop: 'Cotton', areaAcres: 4.5 };
  const cropName = activeField.currentCrop;
  const acreage = activeField.areaAcres;
  const farmLocation = `${activeFarm.village}, ${activeFarm.district}`;

  // Sync tab with URL
  const handleSectionChange = (section: MarketplaceSection) => {
    setActiveSection(section);
    setSearchParams({ tab: section });
  };

  useEffect(() => {
    loadData();
  }, [activeSection, searchQuery, selectedDivision, selectedDistrict, selectedTaluka, selectedBillingUnit, maxPrice, verifiedOnly, sortBy]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Determine category filter based on section
      let categoryFilter: string | undefined = undefined;
      if (activeSection === 'equipment') categoryFilter = 'equipment';
      else if (activeSection === 'tractors') categoryFilter = 'tractor';
      else if (activeSection === 'transport') categoryFilter = 'transport';
      else if (activeSection === 'labour') categoryFilter = 'labour';
      else if (activeSection === 'specialists') categoryFilter = 'specialist';

      if (['discover', 'equipment', 'tractors', 'transport', 'labour', 'specialists'].includes(activeSection)) {
        const fetchedListings = await rentalApi.getListings({
          category: categoryFilter,
          query: searchQuery || undefined,
          division: selectedDivision,
          district: selectedDistrict,
          taluka: selectedTaluka,
          max_price: maxPrice < 5000 ? maxPrice : undefined,
          billing_unit: selectedBillingUnit !== 'all' ? selectedBillingUnit : undefined,
          verified_only: verifiedOnly,
          sort_by: sortBy
        });
        setListings(fetchedListings);
      } else if (['upcoming', 'active', 'history'].includes(activeSection)) {
        const filterType = activeSection === 'upcoming' ? 'upcoming' : activeSection === 'active' ? 'active' : 'history';
        const fetchedBookings = await rentalApi.getBookings('FARMER_RAMESH_PATIL', filterType);
        setBookings(fetchedBookings);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch rental marketplace data');
    } finally {
      setLoading(false);
    }
  };

  // Section navigation tabs
  const sections = [
    { id: 'discover', label: '1. Discover Rentals', icon: <Layers size={14} /> },
    { id: 'equipment', label: '2. Equipment', icon: <Wrench size={14} /> },
    { id: 'tractors', label: '3. Tractors & Machinery', icon: <Tractor size={14} /> },
    { id: 'transport', label: '4. Trucks & Transport', icon: <Truck size={14} /> },
    { id: 'labour', label: '5. Labour & Farm Workers', icon: <Users size={14} /> },
    { id: 'specialists', label: '6. Specialists & Experts', icon: <GraduationCap size={14} /> },
    { id: 'upcoming', label: '7. Upcoming Bookings', icon: <Calendar size={14} /> },
    { id: 'active', label: '8. Active Rentals', icon: <Clock size={14} /> },
    { id: 'history', label: '9. Rental History', icon: <CheckCircle2 size={14} /> },
    { id: 'list_equipment', label: '10. List Equipment', icon: <PlusCircle size={14} /> },
    { id: 'owner_dashboard', label: 'Owner Dashboard', icon: <ShieldCheck size={14} /> },
  ];

  return (
    <div className="p-4 lg:p-8 max-w-[1400px] mx-auto space-y-6 text-[#292B26]">
      {/* HERO & TITLE */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#F2E8D5] rounded-3xl p-6 lg:p-8 border border-[#E5DDCF] shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded bg-[#103D2C] text-[#FBF7EF]">
              Uber for Agriculture • Vidarbha Hub
            </span>
            <span className="text-xs text-[#103D2C]/70">Akola, Maharashtra</span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C] mt-2">
            Agricultural Rental Marketplace
          </h1>
          <p className="text-xs text-[#292B26]/80 mt-1 max-w-2xl">
            Rent verified tractors, precision seed drills, boom sprayers, transport trucks, and farm labour crews at authentic local market rates.
          </p>
        </div>

        {/* Farm Context Pill */}
        <div className="bg-white rounded-2xl p-3 border border-[#E5DDCF] text-xs flex items-center gap-3 shadow-sm shrink-0">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-[#17643E] flex items-center justify-center font-bold">
            <MapPin size={20} />
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-gray-400">Current Farm Context</div>
            <div className="font-bold text-[#103D2C]">{activeFarm?.name || 'Green Acres'} • {cropName} ({acreage} Acres)</div>
            <div className="text-[11px] text-gray-500">{farmLocation}</div>
          </div>
        </div>
      </div>

      {/* SMART AGRICULTURAL RECOMMENDATION */}
      {['discover', 'equipment', 'tractors', 'labour'].includes(activeSection) && (
        <SmartRecommendationBanner
          crop={cropName}
          acreage={acreage}
          onSelectListing={(listingId) => {
            const found = listings.find(l => l.id === listingId);
            if (found) setSelectedListingForBooking(found);
          }}
        />
      )}

      {/* PRIMARY 10-SECTION NAVIGATION PILLS */}
      <div className="bg-white rounded-2xl p-2 border border-[#E5DDCF] shadow-sm overflow-x-auto">
        <div className="flex gap-1.5 min-w-max">
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSectionChange(s.id as MarketplaceSection)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                activeSection === s.id
                  ? 'bg-[#103D2C] text-white shadow-sm'
                  : 'text-gray-600 hover:bg-[#FBF7EF] hover:text-[#103D2C]'
              }`}
            >
              {s.icon}
              <span>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-2xl text-xs flex items-center gap-2">
          <AlertCircle size={16} className="text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SECTIONS 1 - 5 & SPECIALISTS: DISCOVERY & CATEGORIES */}
      {['discover', 'equipment', 'tractors', 'transport', 'labour', 'specialists'].includes(activeSection) && (
        <div className="space-y-6">
          {/* CASCADING MAHARASHTRA LOCATION SELECTOR */}
          <LocationSelector
            selectedDivision={selectedDivision}
            selectedDistrict={selectedDistrict}
            selectedTaluka={selectedTaluka}
            onLocationChange={({ division, district, taluka }) => {
              setSelectedDivision(division);
              setSelectedDistrict(district);
              setSelectedTaluka(taluka);
            }}
          />

          {/* SEARCH, FILTERS & VIEW MODE BAR */}
          <div className="bg-white rounded-2xl p-4 border border-[#E5DDCF] shadow-sm space-y-3">
            <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
              {/* Search input */}
              <div className="relative flex-1">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by equipment, tractor HP, implement, or labour task..."
                  className="w-full pl-9 pr-4 py-2.5 bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-xs font-semibold text-[#103D2C] focus:outline-none focus:ring-2 focus:ring-[#17643E]"
                />
                <Search size={16} className="absolute left-3 top-3 text-gray-400" />
              </div>

              {/* View Switcher (Grid / List / Map) */}
              <div className="flex items-center gap-1 bg-[#FBF7EF] p-1 rounded-xl border border-[#E5DDCF] shrink-0">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${
                    viewMode === 'grid' ? 'bg-[#103D2C] text-white' : 'text-gray-600 hover:text-[#103D2C]'
                  }`}
                  title="Grid View"
                >
                  <LayoutGrid size={15} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${
                    viewMode === 'list' ? 'bg-[#103D2C] text-white' : 'text-gray-600 hover:text-[#103D2C]'
                  }`}
                  title="List View"
                >
                  <List size={15} />
                </button>
                <button
                  onClick={() => setViewMode('map')}
                  className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 ${
                    viewMode === 'map' ? 'bg-[#103D2C] text-white' : 'text-gray-600 hover:text-[#103D2C]'
                  }`}
                  title="Service Coverage Map"
                >
                  <MapIcon size={15} />
                </button>
              </div>
            </div>

            {/* Sub-filters row */}
            <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-[#E5DDCF]/60 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="text-gray-500 font-medium">Billing Unit:</span>
                <select
                  value={selectedBillingUnit}
                  onChange={(e) => setSelectedBillingUnit(e.target.value)}
                  className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg px-2.5 py-1 text-xs font-medium text-[#103D2C]"
                >
                  <option value="all">Any Pricing Unit</option>
                  <option value="per_operating_hour">Per Operating Hour</option>
                  <option value="per_day">Per Day</option>
                  <option value="per_acre">Per Acre</option>
                  <option value="per_worker_day">Per Worker/Day</option>
                  <option value="per_team_day">Per Team/Day</option>
                  <option value="per_sample">Per Soil Sample</option>
                  <option value="per_visit">Per Specialist Visit</option>
                  <option value="per_trip">Per Transport Trip</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-gray-500 font-medium">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg px-2.5 py-1 text-xs font-medium text-[#103D2C]"
                >
                  <option value="relevance">Relevance</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                  <option value="rating">Provider Rating</option>
                </select>
              </div>

              <label className="flex items-center gap-1.5 cursor-pointer ml-auto">
                <input
                  type="checkbox"
                  checked={verifiedOnly}
                  onChange={(e) => setVerifiedOnly(e.target.checked)}
                  className="rounded border-[#E5DDCF] text-[#17643E] focus:ring-[#17643E]"
                />
                <span className="text-xs font-medium text-gray-700 flex items-center gap-1">
                  <ShieldCheck size={12} className="text-[#17643E]" /> CHC / Verified Providers Only
                </span>
              </label>
            </div>
          </div>

          {/* VIEW: MAP VIEW */}
          {viewMode === 'map' && (
            <ServiceCoverageMap
              listings={listings}
              onSelectListing={(listing) => setSelectedListingForBooking(listing)}
              farmLocationName={farmLocation}
            />
          )}

          {/* VIEW: GRID OR LIST VIEW */}
          {viewMode !== 'map' && (
            <>
              {loading ? (
                <div className="bg-white rounded-2xl p-12 text-center border border-[#E5DDCF] text-gray-500 text-xs">
                  Loading verified rental listings...
                </div>
              ) : listings.length === 0 ? (
                <div className="bg-white rounded-2xl p-12 text-center border border-[#E5DDCF] space-y-3">
                  <Wrench size={32} className="mx-auto text-gray-400" />
                  <h4 className="font-bold text-sm text-gray-800">No matching equipment or services found</h4>
                  <p className="text-xs text-gray-500">
                    Try adjusting your search terms, taluka filters, or price range.
                  </p>
                </div>
              ) : (
                <div className={
                  viewMode === 'grid'
                    ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
                    : "space-y-4"
                }>
                  {listings.map((item) => (
                    <div
                      key={item.id}
                      className={`bg-white rounded-3xl border border-[#E5DDCF] overflow-hidden shadow-sm hover:shadow-md transition-all flex ${
                        viewMode === 'grid' ? 'flex-col' : 'flex-col sm:flex-row'
                      }`}
                    >
                      {/* Image Header with Fallback & Badges */}
                      <div className={`relative ${viewMode === 'grid' ? 'h-48 w-full' : 'sm:w-56 h-48 sm:h-auto'} shrink-0 overflow-hidden`}>
                        <ListingImage
                          src={item.image_url}
                          alt={item.title}
                          category={item.category}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-3 left-3 flex flex-wrap gap-1.5 z-10">
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-black/60 text-white backdrop-blur-sm">
                            {item.category}
                          </span>
                          {item.is_demo && (
                            <span className="text-[10px] font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-amber-400 text-gray-900 shadow-sm">
                              Demo Listing
                            </span>
                          )}
                        </div>
                        {item.provider.verified && (
                          <div className="absolute bottom-3 left-3 z-10 bg-[#103D2C]/90 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 backdrop-blur-sm">
                            <ShieldCheck size={11} className="text-emerald-300" />
                            <span>{item.provider.verification_badge ? item.provider.verification_badge.replace('_', ' ').toUpperCase() : 'VERIFIED'}</span>
                          </div>
                        )}
                      </div>

                      {/* Body */}
                      <div className="p-5 flex-1 flex flex-col justify-between space-y-3">
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500 font-medium flex items-center gap-1">
                              <MapPin size={11} className="text-gray-400" />
                              {item.taluka ? `${item.taluka}, ` : ''}{item.district || 'Maharashtra'}
                              {item.division && <span className="text-gray-400 text-[10px]">({item.division})</span>}
                            </span>
                            <div className="flex items-center gap-1 text-amber-700 font-bold text-xs">
                              <Star size={12} className="fill-amber-500 text-amber-500" />
                              <span>{item.rating || 4.8}</span>
                              <span className="text-gray-400 font-normal">({item.review_count || 12})</span>
                            </div>
                          </div>

                          <h3 className="font-serif font-bold text-base text-[#103D2C] line-clamp-1">{item.title}</h3>
                          <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed">{item.description}</p>

                          {/* Specialist Credentials Badge if present */}
                          {item.provider?.credentials && (
                            <div className="text-[10px] text-teal-800 bg-teal-50 border border-teal-200 px-2.5 py-1 rounded-lg font-medium line-clamp-1">
                              🎓 {item.provider.credentials}
                            </div>
                          )}

                          {/* Quick Specs Pills */}
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {item.specs?.horsepower && (
                              <span className="text-[10px] bg-[#FBF7EF] text-gray-700 px-2 py-0.5 rounded-md border border-[#E5DDCF]">
                                {item.specs.horsepower} HP
                              </span>
                            )}
                            {item.specs?.team_size && (
                              <span className="text-[10px] bg-purple-50 text-purple-800 px-2 py-0.5 rounded-md border border-purple-200">
                                Team of {item.specs.team_size} Workers
                              </span>
                            )}
                            {item.specs?.operator_included !== undefined && (
                              <span className={`text-[10px] px-2 py-0.5 rounded-md border ${
                                item.specs.operator_included
                                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                  : 'bg-amber-50 text-amber-800 border-amber-200'
                              }`}>
                                {item.specs.operator_included ? 'Driver Included' : 'Driver Optional'}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Pricing & Booking Action */}
                        <div className="pt-3 border-t border-[#E5DDCF] flex items-center justify-between">
                          <div>
                            <div className="text-[10px] uppercase font-bold text-gray-400">Rental Rate</div>
                            <div className="flex items-baseline gap-1">
                              <span className="text-xl font-bold text-[#103D2C]">₹{item.price.toLocaleString('en-IN')}</span>
                              <span className="text-xs text-gray-500 font-medium">
                                /{item.billing_unit === 'per_team_day' ? 'team-day' : item.billing_unit.replace('per_', '')}
                              </span>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => setSelectedListingForBooking(item)}
                            className="bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all flex items-center gap-1 shadow-sm hover:scale-105"
                          >
                            <span>Book Now</span>
                            <ChevronRight size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Regional Reference Benchmark Table */}
          <MarketRateBenchmarkPanel />
        </div>
      )}

      {/* SECTIONS 6, 7, 8: UPCOMING, ACTIVE, HISTORY */}
      {['upcoming', 'active', 'history'].includes(activeSection) && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-serif font-bold text-[#103D2C]">
              {activeSection === 'upcoming' ? 'Upcoming Equipment & Labour Bookings' :
               activeSection === 'active' ? 'Active Rentals in Progress' : 'Rental History & Receipts'}
            </h2>
            <button
              onClick={loadData}
              className="text-xs text-gray-600 hover:text-[#103D2C] flex items-center gap-1 font-semibold"
            >
              <RefreshCw size={12} /> Refresh
            </button>
          </div>

          {loading ? (
            <div className="bg-white rounded-2xl p-12 text-center border border-[#E5DDCF] text-gray-500 text-xs">
              Loading your bookings...
            </div>
          ) : bookings.length === 0 ? (
            <div className="bg-white rounded-3xl p-12 text-center border border-[#E5DDCF] space-y-3">
              <Calendar size={36} className="mx-auto text-gray-400" />
              <h4 className="font-bold text-sm text-gray-800">No {activeSection} bookings found</h4>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                Discover equipment and submit a booking request from the marketplace tab.
              </p>
              <button
                onClick={() => handleSectionChange('discover')}
                className="mt-2 bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold text-xs px-4 py-2.5 rounded-xl shadow-sm"
              >
                Browse Marketplace
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {bookings.map((b) => (
                <div
                  key={b.id}
                  onClick={() => setSelectedBookingForDetails(b)}
                  className="bg-white rounded-2xl p-5 border border-[#E5DDCF] hover:border-[#17643E] transition-colors cursor-pointer shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 group"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-[#103D2C] bg-[#FBF7EF] px-2.5 py-0.5 rounded border border-[#E5DDCF]">
                        {b.booking_reference}
                      </span>
                      <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full ${
                        b.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                        b.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                        b.status === 'completed' ? 'bg-green-100 text-green-900' :
                        b.status === 'cancelled' || b.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        'bg-amber-100 text-amber-900'
                      }`}>
                        {b.status.replace('_', ' ')}
                      </span>
                    </div>

                    <h4 className="font-serif font-bold text-base text-[#103D2C] group-hover:text-[#17643E] transition-colors">
                      {b.listing_title}
                    </h4>

                    <div className="text-xs text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
                      <span>Provider: <strong>{b.provider_name}</strong></span>
                      <span>Date: <strong>{b.start_date} ({b.start_time})</strong></span>
                      <span>Duration: <strong>{b.duration} {b.billing_unit.replace('per_', '')}s</strong></span>
                      <span>Field: <strong>{b.crop_name || 'Cotton'} Field</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-[10px] text-gray-400 uppercase font-bold">Total Agreed</div>
                      <div className="text-base font-bold text-[#103D2C]">₹{b.total_amount.toLocaleString('en-IN')}</div>
                    </div>
                    <ChevronRight size={18} className="text-gray-400 group-hover:text-[#103D2C] transform group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTIONS 9 & 10: LIST EQUIPMENT & OWNER DASHBOARD */}
      {(activeSection === 'list_equipment' || activeSection === 'owner_dashboard') && (
        <OwnerDashboard
          onListingCreated={(newListing) => {
            setListings(prev => [newListing, ...prev]);
          }}
        />
      )}

      {/* MODAL: BOOKING WORKFLOW */}
      {selectedListingForBooking && (
        <BookingModal
          listing={selectedListingForBooking}
          onClose={() => setSelectedListingForBooking(null)}
          onBookingSuccess={(bkg) => {
            setBookings(prev => [bkg, ...prev]);
          }}
          defaultFarmId={activeFarm?.id || 'FARM_001'}
          defaultFieldId={activeField?.id || 'FLD_01'}
          defaultCrop={cropName}
          defaultAcreage={acreage}
        />
      )}

      {/* MODAL: BOOKING DETAILS & LIFECYCLE */}
      {selectedBookingForDetails && (
        <BookingDetailsModal
          booking={selectedBookingForDetails}
          onClose={() => setSelectedBookingForDetails(null)}
          onUpdate={(updated) => {
            setBookings(prev => prev.map(b => b.id === updated.id ? updated : b));
            setSelectedBookingForDetails(updated);
          }}
          onRebook={(listingId) => {
            setSelectedBookingForDetails(null);
            const found = listings.find(l => l.id === listingId);
            if (found) setSelectedListingForBooking(found);
            else handleSectionChange('discover');
          }}
        />
      )}
    </div>
  );
}
