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
  { name: 'Akola (अकोला)', coords: [20.7002, 77.0082] as [number, number] },
  { name: 'Amravati (अमरावती)', coords: [20.9320, 77.7523] as [number, number] },
  { name: 'Wardha (वर्धा)', coords: [20.7453, 78.6022] as [number, number] },
  { name: 'Yavatmal (यवतमाळ)', coords: [20.3888, 78.1204] as [number, number] },
  { name: 'Washim (वाशीम)', coords: [20.1090, 77.1350] as [number, number] },
  { name: 'Latur (लातूर)', coords: [18.4088, 76.5604] as [number, number] },
  { name: 'Jalna (जालना)', coords: [19.8347, 75.8816] as [number, number] },
  { name: 'Baramati (बारामती)', coords: [18.1519, 74.5770] as [number, number] },
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
  const [customLocationName, setCustomLocationName] = useState<string>('Akola, Maharashtra');

  // GPS / Location state
  const [farmerCoords, setFarmerCoords] = useState<[number, number]>(() => {
    if (activeFarm?.latitude && activeFarm?.longitude) {
      return [activeFarm.latitude, activeFarm.longitude];
    }
    return [20.7002, 77.0082]; // Default Akola farm center
  });

  // UI & Data State
  const [data, setData] = useState<MarketApiResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMarketName, setSelectedMarketName] = useState<string | null>(null);
  const [gpsLoading, setGpsLoading] = useState<boolean>(false);

  // Sync with activeFarm coordinates if updated
  useEffect(() => {
    if (activeFarm?.latitude && activeFarm?.longitude) {
      setFarmerCoords([activeFarm.latitude, activeFarm.longitude]);
      if (activeFarm.location) {
        setCustomLocationName(activeFarm.location);
      }
    }
  }, [activeFarm]);

  // Fetch recommendations whenever crop, quantity, or coordinates change
  useEffect(() => {
    loadMarketIntelligence();
  }, [crop, quantity, farmerCoords]);

  const loadMarketIntelligence = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMarketPrice(
        crop,
        quantity,
        farmerCoords[0],
        farmerCoords[1]
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
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(4));
        const lon = Number(pos.coords.longitude.toFixed(4));
        setFarmerCoords([lat, lon]);
        setCustomLocationName(`GPS (${lat.toFixed(2)}, ${lon.toFixed(2)})`);
        setGpsLoading(false);
      },
      (err) => {
        console.warn('GPS location error:', err);
        setGpsLoading(false);
        alert('Could not detect GPS location. You can select your district from the presets below.');
      },
      { timeout: 8000 }
    );
  };

  const handleSelectDistrict = (hubName: string, coords: [number, number]) => {
    setFarmerCoords(coords);
    setCustomLocationName(hubName);
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
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-[#FBF7EF] text-xs font-semibold mb-2">
            <Sparkles size={14} className="text-[#F1A93B]" />
            <span>Smart Mandi Decision Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Market Intelligence (बाजार भाव)
          </h1>
          <p className="text-[#FBF7EF]/80 text-sm mt-1 max-w-2xl">
            Where and when should you sell your harvest to make the maximum money in your pocket after transport.
          </p>
        </div>

        <button
          onClick={loadMarketIntelligence}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2.5 rounded-2xl text-xs font-semibold transition self-start sm:self-center border border-white/20"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Prices</span>
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
            <p className="text-[11px] text-[#292B26]/60">
              Prices benchmarked directly from official Agmarknet APMC mandi auctions.
            </p>
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

          {/* Question 3: Farmer Location with GPS & District Hub Presets */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                <span>📍</span> Step 3: Farm Location
              </label>
              <button
                type="button"
                onClick={handleUseCurrentGPS}
                disabled={gpsLoading}
                className="text-[11px] font-bold text-[#17643E] hover:underline flex items-center gap-1"
              >
                <Compass size={12} className={gpsLoading ? 'animate-spin' : ''} />
                <span>{gpsLoading ? 'Locating...' : 'Use My GPS'}</span>
              </button>
            </div>

            <div className="p-3 bg-[#FBF7EF] border border-[#E5DDCF] rounded-2xl flex items-center justify-between text-xs font-semibold text-[#103D2C]">
              <div className="flex items-center gap-2 truncate">
                <MapPin size={16} className="text-[#17643E] shrink-0" />
                <span className="truncate">{customLocationName}</span>
              </div>
              <span className="text-[10px] bg-white px-2 py-0.5 rounded-full border border-[#E5DDCF] text-[#292B26]/60 shrink-0">
                {farmerCoords[0].toFixed(2)}°, {farmerCoords[1].toFixed(2)}°
              </span>
            </div>

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
                      farmerCoords[0] === hub.coords[0] && farmerCoords[1] === hub.coords[1]
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

      {/* LOADING SKELETON */}
      {loading && !data && (
        <div className="p-12 text-center bg-white rounded-3xl border border-[#E5DDCF] space-y-3">
          <RefreshCw size={32} className="animate-spin text-[#17643E] mx-auto" />
          <h3 className="text-base font-bold text-[#103D2C]">Analyzing Mandi Prices & Calculating Hauling Costs...</h3>
          <p className="text-xs text-[#292B26]/60 max-w-md mx-auto">
            Evaluating real APMC arrival prices, road distances, and trained XGBoost price forecasts for {crop}.
          </p>
        </div>
      )}

      {/* SECTION 2: THE CORE DECISION ENGINE HERO CARD */}
      {data && (
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

            {/* Why This Mandi? Plain Language Explanation */}
            <div className="bg-black/20 p-4 rounded-2xl border border-white/10 flex items-start gap-3 text-xs leading-relaxed">
              <Info size={18} className="text-[#F1A93B] shrink-0 mt-0.5" />
              <div>
                <strong className="text-white block mb-0.5">Why this recommendation?</strong>
                <span className="text-white/90">{data.why_recommendation}</span>
                <span className="block text-[11px] text-white/60 mt-1">
                  {data.confidence_description}
                </span>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* SECTION 3: PRICE TREND FORECASTING (7, 14, 28 DAYS) */}
      {data && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
                <TrendingUp size={18} className="text-[#17643E]" />
                <span>Price Trend Outlook (किंमतीचा अंदाज)</span>
              </h2>
              <p className="text-xs text-[#292B26]/60">
                Trained time-series XGBoost models based on 5,500+ daily Agmarknet APMC records with zero data leakage.
              </p>
            </div>
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
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column: Mandi Comparison Cards (7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
                  <Scale size={18} className="text-[#17643E]" />
                  <span>Compare Nearby Markets (बाजार तुलना)</span>
                </h2>
                <p className="text-xs text-[#292B26]/60">
                  Sorted by net in-hand payout after deducting hauling costs.
                </p>
              </div>
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
                        <div className="flex items-center gap-2">
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
                        </div>
                        <p className="text-xs text-[#292B26]/60 mt-0.5">
                          {m.district}, {m.state} • ~{m.estimated_road_km} km road ({m.straight_line_km} km air)
                        </p>
                        <div className="text-[10px] text-[#292B26]/50 mt-1 flex items-center gap-2">
                          <span className="bg-[#FBF7EF] px-1.5 py-0.5 rounded border border-[#E5DDCF]">
                            {m.data_freshness_label}
                          </span>
                          <span>• Modal Price</span>
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
                    <div className="mt-3 pt-2.5 border-t border-[#E5DDCF]/60 flex items-center justify-between text-xs">
                      <span className="text-[11px] text-[#292B26]/60">
                        Freight cost: ₹{m.transport_cost_per_qtl}/q
                      </span>
                      <a
                        href={m.google_maps_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-[#17643E] hover:underline font-bold flex items-center gap-1"
                      >
                        <Navigation size={12} />
                        <span>Google Maps Directions</span>
                        <ExternalLink size={10} />
                      </a>
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
