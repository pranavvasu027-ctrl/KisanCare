import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  MapPin, TrendingUp, TrendingDown, ArrowRight, RefreshCw,
  AlertCircle, ShieldCheck, CheckCircle2, Navigation,
  Scale, Calendar, ExternalLink, Sparkles, Truck, IndianRupee,
  Compass, Info, ChevronRight, Check
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../../services/api';
import { useFarm } from '../../context/FarmContext';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';

// Scope: Strictly Cotton and Tur
export type SupportedCrop = 'Cotton' | 'Tur';

interface SupportingWebsite {
  name: string;
  url: string;
  description: string;
  badge: string;
}

interface MarketData {
  name: string;
  district: string;
  state: string;
  address: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  straight_line_km: number;
  estimated_road_km: number;
  distance_display: string;
  price_type: string;
  current_price: number;
  min_price?: number;
  max_price?: number;
  price_source?: string;
  is_live?: boolean;
  source_portal?: string;
  transport_cost_per_qtl: number;
  net_price_per_qtl: number;
  expected_gross_amount: number;
  expected_net_amount: number;
  last_updated: string;
  data_age_days: number;
  data_freshness_label: string;
  data_freshness_status: string;
  google_maps_url: string;
}

interface ForecastInfo {
  horizon_days: number;
  expected_price: number;
  trend: string;
  change_pct: number;
  empirical_mae: number;
  empirical_mape: number;
  range_min: number;
  range_max: number;
  range_display: string;
}

interface MarketApiResponse {
  status: string;
  crop: string;
  crop_display: string;
  price_type: string;
  quantity_quintals: number;
  data_source?: {
    type: string;
    server_status: string;
    provider: string;
    api_endpoint: string;
    portal_url: string;
    last_synced: string;
    live_reporting_mandis: number;
    supporting_websites: SupportingWebsite[];
  };
  farmer_location: {
    latitude: number;
    longitude: number;
    is_fallback: boolean;
    label: string;
  };
  recommended_market: MarketData;
  best_price_market: MarketData;
  closest_market: MarketData;
  markets: MarketData[];
  current_price: number;
  forecast_7d: ForecastInfo;
  forecast_14d: ForecastInfo;
  forecast_28d: ForecastInfo;
  recommended_sell_window: string;
  sell_action: string;
  sell_advice_reason: string;
  expected_amount: number;
  distance_km: number;
  estimated_road_km: number;
  transport_rate_per_qtl_per_km: number;
  confidence: string;
  confidence_description: string;
  why_recommendation: string;
  timestamp: string;
}

// Regional Agricultural Hub Presets for rapid zero-friction selection
const REGIONAL_DISTRICT_HUBS = [
  { name: 'Pune (पुणे)', coords: [18.4636, 73.8682] as [number, number] },
  { name: 'Nashik (नाशिक)', coords: [20.0120, 73.7920] as [number, number] },
  { name: 'Akola (अकोला)', coords: [20.7002, 77.0082] as [number, number] },
  { name: 'Amravati (अमरावती)', coords: [20.9320, 77.7523] as [number, number] },
  { name: 'Baramati (बारामती)', coords: [18.1519, 74.5770] as [number, number] },
  { name: 'Latur (लातूर)', coords: [18.4088, 76.5604] as [number, number] },
  { name: 'Solapur (सोलापूर)', coords: [17.6599, 75.9064] as [number, number] },
  { name: 'Ahmednagar (अहमदनगर)', coords: [19.0950, 74.7490] as [number, number] },
  { name: 'Wardha (वर्धा)', coords: [20.7453, 78.6022] as [number, number] },
  { name: 'Yavatmal (यवतमाळ)', coords: [20.3888, 78.1204] as [number, number] },
  { name: 'Washim (वाशीम)', coords: [20.1090, 77.1350] as [number, number] },
  { name: 'Jalna (जालना)', coords: [19.8347, 75.8816] as [number, number] },
];

// Leaflet custom marker generator
const createMarkerIcon = (color: string, label: string) => {
  return L.divIcon({
    className: 'custom-mandi-pin',
    html: `
      <div style="background-color: ${color}; color: white; padding: 4px 8px; border-radius: 9999px; font-weight: bold; font-size: 11px; display: flex; align-items: center; gap: 4px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); border: 2px solid white; white-space: nowrap;">
        <span>📍</span><span>${label}</span>
      </div>
    `,
    iconSize: [80, 30],
    iconAnchor: [40, 15]
  });
};

const farmerIcon = L.divIcon({
  className: 'custom-farmer-pin',
  html: `
    <div style="background-color: #17643E; color: white; padding: 5px 10px; border-radius: 9999px; font-weight: bold; font-size: 12px; display: flex; align-items: center; gap: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); border: 2px solid #FBF7EF; white-space: nowrap;">
      <span>🏡</span><span>Your Farm</span>
    </div>
  `,
  iconSize: [100, 32],
  iconAnchor: [50, 16]
});

// Helper component to recenter Leaflet map smoothly
function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, 9, { duration: 1.2 });
  }, [center, map]);
  return null;
}

export default function MarketIntelligence() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  const { activeFarm } = useFarm();

  // 1. Farmer Inputs (Only 3 essential questions)
  const [crop, setCrop] = useState<SupportedCrop>('Cotton');
  const [quantity, setQuantity] = useState<number>(20);

  // GPS / Location state: Only discover when requested by farmer or if active farm profile has coordinates
  const hasFarmLocation = Boolean(activeFarm?.latitude && activeFarm?.longitude);
  const [locationFetched, setLocationFetched] = useState<boolean>(hasFarmLocation);
  const [customLocationName, setCustomLocationName] = useState<string>(() => {
    return activeFarm?.location || 'Live GPS Location Required';
  });

  const [farmerCoords, setFarmerCoords] = useState<[number, number]>(() => {
    if (activeFarm?.latitude && activeFarm?.longitude) {
      return [activeFarm.latitude, activeFarm.longitude];
    }
    return [18.4636, 73.8682]; // Default centroid (Pune / Western Maharashtra)
  });

  // UI & Data State
  const [data, setData] = useState<MarketApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMarketName, setSelectedMarketName] = useState<string | null>(null);
  const [gpsLoading, setGpsLoading] = useState<boolean>(false);
  const [showSourcesModal, setShowSourcesModal] = useState<boolean>(false);

  // Sync with activeFarm coordinates if updated
  useEffect(() => {
    if (activeFarm?.latitude && activeFarm?.longitude) {
      setFarmerCoords([activeFarm.latitude, activeFarm.longitude]);
      setLocationFetched(true);
      if (activeFarm.location) {
        setCustomLocationName(activeFarm.location);
      }
    }
  }, [activeFarm]);

  // Fetch recommendations whenever crop, quantity, or coordinates change ONLY IF location has been fetched
  useEffect(() => {
    if (locationFetched) {
      loadMarketIntelligence(false, farmerCoords);
    }
  }, [crop, quantity, farmerCoords, locationFetched]);

  const loadMarketIntelligence = async (forceRefresh: boolean = false, coordsOverride?: [number, number]) => {
    const coords = coordsOverride || farmerCoords;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMarketPrice(
        crop,
        quantity,
        coords[0],
        coords[1],
        undefined,
        undefined,
        forceRefresh
      );
      if (res && res.status === 'success') {
        setData(res);
      } else {
        setError(res?.message || 'Could not load market data.');
      }
    } catch (err: any) {
      console.error('Market intelligence fetch failed:', err);
      setError(err?.message || 'Network error fetching market intelligence.');
    } finally {
      setLoading(false);
    }
  };

  const handleUseCurrentGPS = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setGpsLoading(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(4));
        const lon = Number(pos.coords.longitude.toFixed(4));
        const newCoords: [number, number] = [lat, lon];
        setFarmerCoords(newCoords);
        setLocationFetched(true);
        setCustomLocationName(`GPS (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`);
        
        // Reverse-geocode for human-readable locality
        try {
          const resp = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
          if (resp.ok) {
            const geodata = await resp.json();
            const locality = geodata.address?.suburb || geodata.address?.village || geodata.address?.town || geodata.address?.city || 'Your Farm';
            const district = geodata.address?.state_district || geodata.address?.county || geodata.address?.state || '';
            const resolved = district ? `${locality}, ${district}` : locality;
            setCustomLocationName(`GPS: ${resolved}`);
          }
        } catch {
          // ignore reverse geocode error
        }
        setGpsLoading(false);
        loadMarketIntelligence(false, newCoords);
      },
      (err) => {
        console.warn('GPS location error:', err);
        setGpsLoading(false);
        alert('Could not detect GPS location. You can select your district from the regional presets below.');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleSelectDistrict = (hubName: string, coords: [number, number]) => {
    setFarmerCoords(coords);
    setCustomLocationName(hubName);
    setLocationFetched(true);
    loadMarketIntelligence(false, coords);
  };

  // Find currently highlighted market in map
  const activeMarket = useMemo(() => {
    if (!data?.markets) return null;
    if (!selectedMarketName) return data.recommended_market;
    return data.markets.find(m => m.name === selectedMarketName) || data.recommended_market;
  }, [data, selectedMarketName]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16 font-sans">
      {/* Workflow Stepper Navigation */}
      <WorkflowStepper currentStageId={5} />

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-[#103D2C] to-[#17643E] p-6 rounded-3xl text-white shadow-lg">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            Market Intelligence (बाजार भाव)
          </h1>

          {/* Real-time Server Link Badge & Source Links */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-100 text-xs font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>
                {data?.data_source?.type === 'LIVE_AGMARKNET_SERVER' || data?.data_source?.server_status?.includes('ONLINE')
                  ? 'Connected to Live Agmarknet Server (data.gov.in)'
                  : 'Agmarknet APMC Market Bulletin'}
              </span>
            </div>

            <button
              type="button"
              onClick={() => setShowSourcesModal(true)}
              className="inline-flex items-center gap-1 text-xs text-[#F1A93B] hover:text-white font-semibold underline underline-offset-2 transition"
            >
              <Info size={13} />
              <span>Official Market Servers & APIs</span>
            </button>
          </div>
        </div>

        <button
          onClick={() => loadMarketIntelligence(true)}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2.5 rounded-2xl text-xs font-semibold transition self-start sm:self-center border border-white/20 shadow-sm"
          title="Force refresh prices directly from real market servers"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Live Rates</span>
        </button>
      </div>

      {/* SECTION 1: SIMPLE FARMER INPUTS (3 QUESTIONS ONLY) */}
      <div className="bg-white p-6 rounded-3xl border border-[#E5DDCF] shadow-sm space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Question 1: Crop Selection (Cotton and Tur ONLY) */}
          <div className="space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
              <span>🌾</span> Step 1: Select Your Crop
            </label>
            <div className="grid grid-cols-2 gap-3">
              {/* Cotton Option */}
              <button
                type="button"
                onClick={() => setCrop('Cotton')}
                className={`p-3.5 rounded-2xl border-2 text-left transition flex flex-col justify-between ${
                  crop === 'Cotton'
                    ? 'border-[#17643E] bg-[#E8F3ED] text-[#103D2C] shadow-sm'
                    : 'border-[#E5DDCF] bg-[#FBF7EF]/50 hover:bg-[#FBF7EF] text-[#292B26]/80'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl">☁️</span>
                  {crop === 'Cotton' && <Check size={16} className="text-[#17643E]" />}
                </div>
                <div className="mt-2">
                  <div className="font-bold text-sm">Cotton</div>
                  <div className="text-xs text-[#292B26]/60">कापूस</div>
                </div>
              </button>

              {/* Tur Option */}
              <button
                type="button"
                onClick={() => setCrop('Tur')}
                className={`p-3.5 rounded-2xl border-2 text-left transition flex flex-col justify-between ${
                  crop === 'Tur'
                    ? 'border-[#17643E] bg-[#E8F3ED] text-[#103D2C] shadow-sm'
                    : 'border-[#E5DDCF] bg-[#FBF7EF]/50 hover:bg-[#FBF7EF] text-[#292B26]/80'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl">🥣</span>
                  {crop === 'Tur' && <Check size={16} className="text-[#17643E]" />}
                </div>
                <div className="mt-2">
                  <div className="font-bold text-sm">Tur</div>
                  <div className="text-xs text-[#292B26]/60">तूर / अरहर</div>
                </div>
              </button>
            </div>
          </div>

          {/* Question 2: Harvest Quantity */}
          <div className="space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
              <span>⚖️</span> Step 2: Harvest Quantity (Quintals)
            </label>
            <div className="relative">
              <input
                type="number"
                min="1"
                max="50000"
                value={quantity || ''}
                onChange={(e) => setQuantity(Math.max(1, Math.min(50000, Number(e.target.value) || 1)))}
                className="w-full px-4 py-3 rounded-2xl border border-[#E5DDCF] focus:border-[#17643E] focus:ring-2 focus:ring-[#17643E]/20 text-sm font-bold text-[#103D2C] bg-[#FBF7EF]/40"
                placeholder="20"
              />
              <span className="absolute right-4 top-3.5 text-xs font-bold text-[#292B26]/50">
                Quintals (क्विंटल)
              </span>
            </div>
            {/* Quick Presets */}
            <div className="flex items-center gap-2">
              {[10, 20, 50, 100].map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setQuantity(preset)}
                  className={`text-[11px] px-2.5 py-1 rounded-xl font-semibold border transition ${
                    quantity === preset
                      ? 'bg-[#17643E] text-white border-[#17643E]'
                      : 'bg-white border-[#E5DDCF] text-[#292B26]/70 hover:bg-[#FBF7EF]'
                  }`}
                >
                  {preset} q
                </button>
              ))}
            </div>
          </div>

          {/* Question 3: Farmer Location with Dynamic GPS Discovery */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                <span>📍</span> Step 3: Farm Location
              </label>
              {locationFetched && (
                <button
                  type="button"
                  onClick={handleUseCurrentGPS}
                  disabled={gpsLoading}
                  className="text-[11px] font-bold text-[#17643E] hover:underline flex items-center gap-1"
                >
                  <Compass size={12} className={gpsLoading ? 'animate-spin' : ''} />
                  <span>{gpsLoading ? 'Locating...' : 'Re-fetch GPS'}</span>
                </button>
              )}
            </div>

            {!locationFetched ? (
              <button
                type="button"
                onClick={handleUseCurrentGPS}
                disabled={gpsLoading}
                className="w-full p-3.5 bg-gradient-to-r from-[#17643E] to-[#103D2C] hover:opacity-95 text-white rounded-2xl flex items-center justify-center gap-2 text-xs font-bold shadow-md transition transform active:scale-95"
              >
                <Compass size={16} className={gpsLoading ? 'animate-spin text-[#F1A93B]' : 'text-[#F1A93B]'} />
                <span>{gpsLoading ? 'Acquiring GPS Satellite Fix...' : '📍 Fetch My Location (GPS)'}</span>
              </button>
            ) : (
              <div className="p-3 bg-[#E8F3ED] border-2 border-[#17643E]/30 rounded-2xl flex items-center justify-between text-xs font-semibold text-[#103D2C]">
                <div className="flex items-center gap-2 truncate">
                  <MapPin size={16} className="text-[#17643E] shrink-0" />
                  <span className="truncate font-bold">{customLocationName}</span>
                </div>
                <span className="text-[10px] bg-white px-2 py-0.5 rounded-full border border-[#17643E]/20 text-[#292B26]/70 shrink-0 ml-2">
                  {farmerCoords[0].toFixed(2)}°, {farmerCoords[1].toFixed(2)}°
                </span>
              </div>
            )}

            {/* Quick District Presets */}
            <div className="space-y-1">
              <div className="text-[10px] font-bold text-[#292B26]/50 uppercase tracking-wider">
                Or Select District Hub:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {REGIONAL_DISTRICT_HUBS.map((hub) => (
                  <button
                    key={hub.name}
                    type="button"
                    onClick={() => handleSelectDistrict(hub.name, hub.coords)}
                    className={`text-[10px] px-2 py-0.5 rounded-lg border transition ${
                      locationFetched && farmerCoords[0] === hub.coords[0] && farmerCoords[1] === hub.coords[1]
                        ? 'bg-[#17643E] text-white border-[#17643E] font-bold'
                        : 'bg-white border-[#E5DDCF] text-[#292B26]/70 hover:bg-[#FBF7EF]'
                    }`}
                  >
                    {hub.name.split(' ')[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ERROR STATE */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 flex items-center gap-3 text-sm">
          <AlertCircle size={20} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* LOCATION DISCOVERY HERO CARD (When farmer has not fetched location yet) */}
      {!locationFetched && !loading && (
        <div className="bg-gradient-to-br from-[#103D2C] via-[#14533C] to-[#17643E] rounded-3xl text-white p-6 sm:p-8 shadow-xl relative overflow-hidden border border-[#E5DDCF]/20 text-center space-y-4">
          <div className="max-w-md mx-auto">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight">
              Discover Nearby APMC Mandis
            </h2>
          </div>

          <div className="flex justify-center">
            <button
              type="button"
              onClick={handleUseCurrentGPS}
              disabled={gpsLoading}
              className="px-8 py-3.5 rounded-2xl bg-[#F1A93B] hover:bg-[#e09828] text-[#103D2C] font-extrabold text-sm shadow-md transition transform active:scale-95 flex items-center justify-center gap-2"
            >
              <Compass size={18} className={gpsLoading ? 'animate-spin' : ''} />
              <span>{gpsLoading ? 'Acquiring GPS Fix...' : 'Fetch My Location (GPS)'}</span>
            </button>
          </div>

          <div className="pt-3 border-t border-white/10 max-w-xl mx-auto">
            <span className="text-[11px] text-[#FBF7EF]/70 font-semibold uppercase tracking-wider block mb-2">
              Or Select District Hub:
            </span>
            <div className="flex flex-wrap justify-center gap-1.5">
              {REGIONAL_DISTRICT_HUBS.map((hub) => (
                <button
                  key={hub.name}
                  type="button"
                  onClick={() => handleSelectDistrict(hub.name, hub.coords)}
                  className="text-xs px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-white font-medium transition"
                >
                  {hub.name.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* LOADING SKELETON */}
      {loading && !data && (
        <div className="p-10 text-center bg-white rounded-3xl border border-[#E5DDCF] space-y-2">
          <RefreshCw size={28} className="animate-spin text-[#17643E] mx-auto" />
          <h3 className="text-sm font-bold text-[#103D2C]">Discovering Nearby Mandis & Rates...</h3>
        </div>
      )}

      {/* SECTION 2: THE CORE DECISION ENGINE HERO CARD */}
      {data && locationFetched && (
        <div className="bg-gradient-to-br from-[#103D2C] via-[#14533C] to-[#17643E] rounded-3xl text-white p-6 sm:p-8 shadow-xl relative overflow-hidden border border-[#E5DDCF]/20">
          <div className="absolute top-0 right-0 translate-x-8 -translate-y-8 w-64 h-64 bg-white/5 rounded-full blur-2xl pointer-events-none" />

          <div className="relative z-10 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full bg-[#F1A93B] text-[#103D2C] text-xs font-extrabold uppercase tracking-wider flex items-center gap-1">
                  <Sparkles size={12} />
                  Best Selling Decision
                </span>
                <span className="text-xs text-white/70">
                  Calculated for {data.quantity_quintals} Quintals of {data.crop}
                </span>
              </div>
              
              {/* Dynamic Confidence Badge */}
              <div className="flex items-center gap-1.5 text-xs text-[#FBF7EF]/90 bg-white/10 px-3 py-1 rounded-full border border-white/15">
                <ShieldCheck size={14} className="text-[#F1A93B]" />
                <span className="font-semibold">{data.confidence}</span>
              </div>
            </div>

            {/* Main Decision 3-Column Display */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Decision 1: Where to Sell */}
              <div className="bg-white/10 p-5 rounded-2xl border border-white/10 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#F1A93B] flex items-center gap-1.5">
                  <MapPin size={14} /> Recommended Mandi
                </span>
                <div className="text-2xl font-black text-white">
                  {data.recommended_market.name}
                </div>
                <div className="text-xs text-white/80">
                  {data.recommended_market.district}, {data.recommended_market.state}
                </div>
                <div className="pt-2 flex items-center gap-2 text-xs font-semibold text-white/90">
                  <span className="bg-white/15 px-2 py-0.5 rounded-md">
                    ~{data.recommended_market.estimated_road_km} km road ({data.recommended_market.straight_line_km} km air)
                  </span>
                  <a
                    href={data.recommended_market.google_maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#F1A93B] hover:underline flex items-center gap-1"
                  >
                    <span>Route</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              </div>

              {/* Decision 2: How Much Money in Pocket */}
              <div className="bg-white/15 p-5 rounded-2xl border-2 border-[#F1A93B]/40 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#F1A93B] flex items-center gap-1.5">
                  <IndianRupee size={14} /> Expected In-Hand Amount
                </span>
                <div className="text-3xl font-black text-white">
                  ₹{data.expected_amount.toLocaleString('en-IN')}
                </div>
                <div className="text-xs text-white/80 flex items-center justify-between">
                  <span>Net Price: <strong>₹{data.recommended_market.net_price_per_qtl.toLocaleString('en-IN')}/q</strong></span>
                  <span>(Raw: ₹{data.recommended_market.current_price.toLocaleString('en-IN')}/q)</span>
                </div>
                <div className="pt-1 text-[11px] text-[#FBF7EF]/70 flex items-center gap-1">
                  <Truck size={12} />
                  <span>Freight deduction: -₹{data.recommended_market.transport_cost_per_qtl}/q (₹3.50/qtl/km)</span>
                </div>
              </div>

              {/* Decision 3: When to Sell */}
              <div className="bg-white/10 p-5 rounded-2xl border border-white/10 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#F1A93B] flex items-center gap-1.5">
                  <Calendar size={14} /> Best Time to Sell
                </span>
                <div className="text-xl font-black text-white">
                  {data.recommended_sell_window}
                </div>
                <div className="text-xs text-white/80">
                  {data.sell_advice_reason}
                </div>
                <div className="pt-2 text-[11px] text-[#F1A93B]">
                  7-Day Outlook: {data.forecast_7d?.trend || 'Stable'} ({data.forecast_7d?.range_display})
                </div>
              </div>

            </div>

          </div>
        </div>
      )}

      {/* SECTION 3: PRICE TREND FORECASTING (7, 14, 28 DAYS) */}
      {data && locationFetched && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
              <TrendingUp size={18} className="text-[#17643E]" />
              <span>Price Trend Outlook (किंमतीचा अंदाज)</span>
            </h2>
            <span className="text-[11px] bg-[#E8F3ED] text-[#17643E] px-2.5 py-1 rounded-full font-bold">
              Base Price: ₹{data.current_price.toLocaleString('en-IN')}/q
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* 7-Day Forecast */}
            <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#292B26]/60 uppercase tracking-wider">Next 7 Days</span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  data.forecast_7d.trend.includes('Rising')
                    ? 'bg-emerald-100 text-emerald-800'
                    : data.forecast_7d.trend.includes('Falling')
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {data.forecast_7d.trend}
                </span>
              </div>
              <div>
                <div className="text-xl font-bold text-[#103D2C]">
                  {data.forecast_7d.range_display}
                </div>
                <div className="text-xs text-[#292B26]/60 mt-0.5">
                  Expected Modal Price: ₹{Math.round(data.forecast_7d.expected_price).toLocaleString('en-IN')}/q
                </div>
              </div>
              <div className="text-[11px] text-[#292B26]/60 pt-2 border-t border-[#E5DDCF] flex justify-between">
                <span>Change: {data.forecast_7d.change_pct > 0 ? `+${data.forecast_7d.change_pct}%` : `${data.forecast_7d.change_pct}%`}</span>
                <span>Uncertainty: ±₹{Math.round(data.forecast_7d.empirical_mae)}/q</span>
              </div>
            </div>

            {/* 14-Day Forecast */}
            <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#292B26]/60 uppercase tracking-wider">Next 14 Days</span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  data.forecast_14d.trend.includes('Rising')
                    ? 'bg-emerald-100 text-emerald-800'
                    : data.forecast_14d.trend.includes('Falling')
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {data.forecast_14d.trend}
                </span>
              </div>
              <div>
                <div className="text-xl font-bold text-[#103D2C]">
                  {data.forecast_14d.range_display}
                </div>
                <div className="text-xs text-[#292B26]/60 mt-0.5">
                  Expected Modal Price: ₹{Math.round(data.forecast_14d.expected_price).toLocaleString('en-IN')}/q
                </div>
              </div>
              <div className="text-[11px] text-[#292B26]/60 pt-2 border-t border-[#E5DDCF] flex justify-between">
                <span>Change: {data.forecast_14d.change_pct > 0 ? `+${data.forecast_14d.change_pct}%` : `${data.forecast_14d.change_pct}%`}</span>
                <span>Uncertainty: ±₹{Math.round(data.forecast_14d.empirical_mae)}/q</span>
              </div>
            </div>

            {/* 28-Day Forecast */}
            <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#292B26]/60 uppercase tracking-wider">Next 28 Days</span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  data.forecast_28d.trend.includes('Rising')
                    ? 'bg-emerald-100 text-emerald-800'
                    : data.forecast_28d.trend.includes('Falling')
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  {data.forecast_28d.trend}
                </span>
              </div>
              <div>
                <div className="text-xl font-bold text-[#103D2C]">
                  {data.forecast_28d.range_display}
                </div>
                <div className="text-xs text-[#292B26]/60 mt-0.5">
                  Expected Modal Price: ₹{Math.round(data.forecast_28d.expected_price).toLocaleString('en-IN')}/q
                </div>
              </div>
              <div className="text-[11px] text-[#292B26]/60 pt-2 border-t border-[#E5DDCF] flex justify-between">
                <span>Change: {data.forecast_28d.change_pct > 0 ? `+${data.forecast_28d.change_pct}%` : `${data.forecast_28d.change_pct}%`}</span>
                <span>Uncertainty: ±₹{Math.round(data.forecast_28d.empirical_mae)}/q</span>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* SECTION 4: NEARBY MANDIS COMPARISON & ACTUAL MAP */}
      {data && locationFetched && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column: Mandi Comparison Cards (7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
                <Scale size={18} className="text-[#17643E]" />
                <span>Compare Nearby Markets (बाजार तुलना)</span>
              </h2>
              <span className="text-xs text-[#292B26]/50">
                {data.markets.length} Mandis Available
              </span>
            </div>

            <div className="space-y-3">
              {data.markets.map((m) => {
                const isRecommended = m.name === data.recommended_market.name;
                const isBestPrice = m.name === data.best_price_market.name;
                const isClosest = m.name === data.closest_market.name;

                return (
                  <div
                    key={m.name}
                    onClick={() => setSelectedMarketName(m.name)}
                    className={`p-4 rounded-2xl border-2 transition cursor-pointer bg-white ${
                      isRecommended
                        ? 'border-[#17643E] bg-[#E8F3ED]/30 shadow-md ring-2 ring-[#17643E]/20'
                        : selectedMarketName === m.name
                        ? 'border-[#F1A93B] shadow-sm'
                        : 'border-[#E5DDCF] hover:border-[#17643E]/40'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-bold text-sm text-[#103D2C]">{m.name}</h3>
                          {isRecommended && (
                            <span className="bg-[#17643E] text-white text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                              ⭐ BEST BALANCED
                            </span>
                          )}
                          {!isRecommended && isBestPrice && (
                            <span className="bg-[#F1A93B] text-[#103D2C] text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                              💰 HIGHEST PRICE
                            </span>
                          )}
                          {!isRecommended && isClosest && (
                            <span className="bg-blue-100 text-blue-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                              📍 CLOSEST
                            </span>
                          )}
                          {m.is_live && (
                            <span className="bg-emerald-50 text-emerald-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-200 flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                              <span>Live Server Rate</span>
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-[#292B26]/60 mt-0.5">
                          {m.district}, {m.state} • ~{m.estimated_road_km} km road ({m.straight_line_km} km air)
                        </p>
                        <div className="text-[10px] text-[#292B26]/50 mt-1 flex items-center gap-2 flex-wrap">
                          <span className="bg-[#FBF7EF] px-1.5 py-0.5 rounded border border-[#E5DDCF]">
                            {m.data_freshness_label}
                          </span>
                          {m.min_price && m.max_price && (
                            <span className="text-[#103D2C] font-semibold">
                              Auction Range: ₹{Math.round(m.min_price).toLocaleString('en-IN')} – ₹{Math.round(m.max_price).toLocaleString('en-IN')}/q
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Prices and Net Payout */}
                      <div className="text-left sm:text-right shrink-0">
                        <div className="text-base font-black text-[#103D2C]">
                          ₹{m.current_price.toLocaleString('en-IN')}/q
                        </div>
                        <div className="text-xs font-semibold text-[#17643E]">
                          Net: ₹{m.net_price_per_qtl.toLocaleString('en-IN')}/q
                        </div>
                        <div className="text-[11px] text-[#292B26]/50">
                          Total: ₹{m.expected_net_amount.toLocaleString('en-IN')}
                        </div>
                      </div>
                    </div>

                    {/* Bottom Action Footer for Each Mandi */}
                    <div className="mt-3 pt-2.5 border-t border-[#E5DDCF]/60 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-1.5">
                      <span className="text-[11px] text-[#292B26]/70">
                        Freight deduction: ₹{m.transport_cost_per_qtl}/q (~{m.estimated_road_km} km @ ₹3.50/q/km)
                      </span>
                      <div className="flex items-center gap-3">
                        <a
                          href={m.source_portal?.startsWith('http') ? m.source_portal : 'https://agmarknet.gov.in'}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-[#F1A93B] hover:underline text-[11px] font-bold flex items-center gap-1"
                          title="Official Agmarknet Market Bulletin"
                        >
                          <span>Agmarknet Portal</span>
                          <ExternalLink size={10} />
                        </a>
                        <a
                          href={m.google_maps_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-[#17643E] hover:underline font-bold flex items-center gap-1"
                        >
                          <Navigation size={12} />
                          <span>Google Maps</span>
                          <ExternalLink size={10} />
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Interactive Leaflet Map (5 cols) */}
          <div className="lg:col-span-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
                <Compass size={18} className="text-[#17643E]" />
                <span>Mandi Map Visualizer</span>
              </h2>
              <span className="text-xs text-[#292B26]/60">
                Click pin to navigate
              </span>
            </div>

            <div className="bg-white rounded-3xl border border-[#E5DDCF] shadow-sm overflow-hidden h-[540px] relative">
              <MapContainer
                center={farmerCoords}
                zoom={8}
                style={{ height: '100%', width: '100%' }}
                scrollWheelZoom={false}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapRecenter center={activeMarket ? [activeMarket.latitude, activeMarket.longitude] : farmerCoords} />

                {/* Farmer Farm Marker */}
                <Marker position={farmerCoords} icon={farmerIcon}>
                  <Popup>
                    <div className="p-1 text-xs space-y-1">
                      <p className="font-bold text-[#103D2C]">🏡 Your Farm Location</p>
                      <p className="text-gray-600">{customLocationName}</p>
                      <p className="text-[10px] text-gray-500">Lat: {farmerCoords[0]}, Lon: {farmerCoords[1]}</p>
                    </div>
                  </Popup>
                </Marker>

                {/* Mandi Pins */}
                {data.markets.map((m) => {
                  const isRec = m.name === data.recommended_market.name;
                  const pinColor = isRec ? '#17643E' : '#D97706';

                  return (
                    <Marker
                      key={m.name}
                      position={[m.latitude, m.longitude]}
                      icon={createMarkerIcon(pinColor, `₹${m.current_price}/q`)}
                      eventHandlers={{
                        click: () => setSelectedMarketName(m.name),
                      }}
                    >
                      <Popup>
                        <div className="p-1 text-xs space-y-1 min-w-[180px]">
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-bold text-[#103D2C]">{m.name}</span>
                            {isRec && (
                              <span className="bg-[#17643E] text-white text-[9px] px-1.5 py-0.2 rounded font-bold">
                                BEST
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600">{m.address}</p>
                          <div className="border-t pt-1 space-y-0.5">
                            <p className="text-[#103D2C] font-semibold">Price: ₹{m.current_price}/qtl</p>
                            <p className="text-gray-600">Distance: ~{m.estimated_road_km} km road ({m.straight_line_km} km air)</p>
                            <p className="text-[#17643E] font-bold">Net In-Hand: ₹{m.net_price_per_qtl}/qtl</p>
                          </div>
                          <a
                            href={m.google_maps_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block mt-2 text-[#17643E] font-bold hover:underline"
                          >
                            Open in Google Maps &rarr;
                          </a>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
            </div>
          </div>
        </div>
      )}

      {/* Supporting Real Market Servers Modal */}
      {showSourcesModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 space-y-5 border border-[#E5DDCF] shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold mb-1.5">
                  <ShieldCheck size={13} />
                  <span>Verified Government Market APIs</span>
                </div>
                <h3 className="text-xl font-bold text-[#103D2C]">
                  Official Real Market Sources & APIs
                </h3>
                <p className="text-xs text-[#292B26]/70 mt-0.5">
                  KisanCare fetches real-time auction rates directly from Ministry of Agriculture & Farmers Welfare servers.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowSourcesModal(false)}
                className="w-8 h-8 rounded-full bg-[#FBF7EF] hover:bg-[#E5DDCF] flex items-center justify-center text-gray-500 hover:text-black font-bold transition"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {/* Agmarknet */}
              <div className="p-4 rounded-2xl border border-[#E5DDCF] bg-[#FBF7EF]/50 flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#103D2C]">Agmarknet Portal (agmarknet.gov.in)</span>
                    <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      Official Bulletin
                    </span>
                  </div>
                  <p className="text-xs text-[#292B26]/70">
                    Directorate of Marketing & Inspection (DMI), Ministry of Agriculture and Farmers Welfare. Publishes daily spot modal, minimum, and maximum auction rates across all Indian APMC market yards.
                  </p>
                </div>
                <a
                  href="https://agmarknet.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-xs font-bold text-[#17643E] hover:underline flex items-center gap-1 mt-1 bg-white px-3 py-1.5 rounded-xl border border-[#E5DDCF]"
                >
                  <span>Portal</span>
                  <ExternalLink size={12} />
                </a>
              </div>

              {/* data.gov.in */}
              <div className="p-4 rounded-2xl border border-[#E5DDCF] bg-[#FBF7EF]/50 flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#103D2C]">Open Government Data (data.gov.in)</span>
                    <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      REST JSON API
                    </span>
                  </div>
                  <p className="text-xs text-[#292B26]/70">
                    Live API Resource <code className="text-[11px] bg-white px-1.5 py-0.5 rounded border border-[#E5DDCF]">9ef84268-d588-465a-a308-a864a43d0070</code>: "Current Daily Price of Various Commodities from Various Markets (Mandi)". Real-time programmatic feed.
                  </p>
                </div>
                <a
                  href="https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-xs font-bold text-[#17643E] hover:underline flex items-center gap-1 mt-1 bg-white px-3 py-1.5 rounded-xl border border-[#E5DDCF]"
                >
                  <span>API Docs</span>
                  <ExternalLink size={12} />
                </a>
              </div>

              {/* e-NAM */}
              <div className="p-4 rounded-2xl border border-[#E5DDCF] bg-[#FBF7EF]/50 flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#103D2C]">e-NAM (enam.gov.in)</span>
                    <span className="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      Pan-India E-Trading
                    </span>
                  </div>
                  <p className="text-xs text-[#292B26]/70">
                    National Agriculture Market pan-India electronic trading portal integrating 1,361+ wholesale APMC mandis for online transparent price bidding.
                  </p>
                </div>
                <a
                  href="https://enam.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-xs font-bold text-[#17643E] hover:underline flex items-center gap-1 mt-1 bg-white px-3 py-1.5 rounded-xl border border-[#E5DDCF]"
                >
                  <span>e-NAM</span>
                  <ExternalLink size={12} />
                </a>
              </div>

              {/* Kisan Suvidha */}
              <div className="p-4 rounded-2xl border border-[#E5DDCF] bg-[#FBF7EF]/50 flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#103D2C]">Kisan Suvidha (kisansuvidha.gov.in)</span>
                    <span className="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      Farmer Advisory
                    </span>
                  </div>
                  <p className="text-xs text-[#292B26]/70">
                    Farmer advisory portal by Department of Agriculture & Farmers Welfare providing live mandi rates, MSP procurement prices, and weather alerts.
                  </p>
                </div>
                <a
                  href="https://kisansuvidha.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-xs font-bold text-[#17643E] hover:underline flex items-center gap-1 mt-1 bg-white px-3 py-1.5 rounded-xl border border-[#E5DDCF]"
                >
                  <span>Kisan Suvidha</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>

            {/* Dynamic Real-Market Calculation Engine */}
            <div className="p-4 rounded-2xl bg-[#E8F3ED] border border-[#17643E]/30 text-xs text-[#103D2C] space-y-1.5">
              <div className="font-bold flex items-center gap-1.5 text-[#17643E]">
                <Scale size={15} />
                <span>Dynamic Real-World Freight Realization Calculation</span>
              </div>
              <p className="text-[11px] text-[#103D2C]/80 leading-relaxed">
                Rather than hardcoding static calculations, KisanCare pulls real modal auction prices directly from government market servers and calculates:
              </p>
              <div className="font-mono text-[11px] bg-white/70 p-2 rounded-xl border border-[#17643E]/20 space-y-0.5">
                <div>• Road Distance = Air Distance (GPS haversine) × 1.20 road winding factor</div>
                <div>• Haulage Cost = Road Distance (km) × ₹3.50/quintal/km standard rural freight</div>
                <div>• In-Hand Net Price = Modal Auction Rate − Haulage Cost per quintal</div>
                <div>• Total Payout = Harvest Quantity (q) × In-Hand Net Price</div>
              </div>
            </div>

            <div className="text-right pt-1">
              <button
                type="button"
                onClick={() => setShowSourcesModal(false)}
                className="bg-[#17643E] hover:bg-[#103D2C] text-white px-6 py-2 rounded-2xl text-xs font-bold transition shadow-sm"
              >
                Close & Return
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Navigation Footer */}
      <WorkflowFooter
        currentStageNumber={5}
        currentStageName="Market Intelligence"
        prevStep={{
          path: "/economics",
          label: "Farm Economics",
          description: "Review cost of production and margin benchmarks"
        }}
        nextStep={{
          path: "/rentals",
          label: "Rentals & Machinery",
          description: "Rent farm machinery or warehouse space"
        }}
      />
    </div>
  );
}
