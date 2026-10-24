import React, { useState, useEffect, useMemo } from 'react';
import {
  TrendingUp, TrendingDown, MapPin, Search, Loader2, RefreshCw,
  AlertCircle, ArrowUpRight, SlidersHorizontal, RotateCcw, Calendar,
  ChevronRight, Sparkles, Clock, Building2, Scale, X, ExternalLink,
  ShieldCheck, Check, Info, ArrowRight
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from 'recharts';
import { api } from '../../services/api';

type SupportedCrop = 'Cotton' | 'Soyabean' | 'Tur';
type SupportedMarket = 'Akola' | 'Amravati' | 'Akot';
type SupportedTimeRange = '7D' | '14D' | '30D';

export default function MarketIntelligence() {
  // Active query state
  const [crop, setCrop] = useState<SupportedCrop>('Cotton');
  const [market, setMarket] = useState<SupportedMarket>('Akola');
  const [timeRange, setTimeRange] = useState<SupportedTimeRange>('7D');

  // Staged filter state (in the control panel)
  const [stagedCrop, setStagedCrop] = useState<SupportedCrop>('Cotton');
  const [stagedMarket, setStagedMarket] = useState<SupportedMarket>('Akola');
  const [stagedTimeRange, setStagedTimeRange] = useState<SupportedTimeRange>('7D');

  // Search & Sorting state
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<'currentPrice' | 'priceChangePct' | 'name'>('currentPrice');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Async & UI state
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('23 Oct 2026, 05:30 PM IST');
  const [refreshToast, setRefreshToast] = useState(false);

  // Detail Modal / Slide-over state
  const [selectedDetailMarket, setSelectedDetailMarket] = useState<any>(null);

  useEffect(() => {
    fetchMarketData(crop, market, timeRange);
  }, [crop, market, timeRange]);

  const fetchMarketData = async (
    targetCrop: SupportedCrop,
    targetMarket: SupportedMarket,
    targetRange: SupportedTimeRange
  ) => {
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await api.getMarketPrice(targetCrop, targetMarket, today, targetRange);
      setData(res.data);
      if (res.data?.last_updated) {
        setLastUpdated(res.data.last_updated);
      }
    } catch (e: any) {
      console.error('Market fetch error:', e);
      setError('Unable to load market data for the selected parameters. Please retry.');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await api.getMarketPrice(crop, market, today, timeRange);
      setData(res.data);
      const now = new Date();
      const formatted = `${now.getDate()} Oct 2026, ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST`;
      setLastUpdated(formatted);
      setRefreshToast(true);
      setTimeout(() => setRefreshToast(false), 2500);
    } catch (err) {
      setError('Refresh failed. Please check network connectivity.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleApplyFilters = () => {
    setCrop(stagedCrop);
    setMarket(stagedMarket);
    setTimeRange(stagedTimeRange);
  };

  const handleResetFilters = () => {
    setStagedCrop('Cotton');
    setStagedMarket('Akola');
    setStagedTimeRange('7D');
    setCrop('Cotton');
    setMarket('Akola');
    setTimeRange('7D');
    setSearchQuery('');
  };

  // Filter and sort nearby comparison mandis
  const filteredMarkets = useMemo(() => {
    if (!data?.nearby_markets) return [];
    return data.nearby_markets
      .filter((m: any) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return (
          m.name.toLowerCase().includes(q) ||
          m.location.toLowerCase().includes(q) ||
          m.variety.toLowerCase().includes(q) ||
          m.marketKey.toLowerCase().includes(q)
        );
      })
      .sort((a: any, b: any) => {
        let diff = 0;
        if (sortField === 'currentPrice') diff = a.currentPrice - b.currentPrice;
        else if (sortField === 'priceChangePct') diff = a.priceChangePct - b.priceChangePct;
        else diff = a.name.localeCompare(b.name);
        return sortOrder === 'asc' ? diff : -diff;
      });
  }, [data?.nearby_markets, searchQuery, sortField, sortOrder]);

  // Prepared chart slice based on selected time range
  const chartPoints = useMemo(() => {
    if (!data?.chart_data) return [];
    const allPoints = data.chart_data;
    const historicalPoints = allPoints.filter((p: any) => !p.isForecast);
    const forecastPoints = allPoints.filter((p: any) => p.isForecast);

    let histSliceCount = 7;
    let forecastSliceCount = 7;

    if (timeRange === '14D') {
      histSliceCount = 14;
      forecastSliceCount = 14;
    } else if (timeRange === '30D') {
      histSliceCount = 30;
      forecastSliceCount = 14;
    }

    const histSlice = historicalPoints.slice(-histSliceCount);
    const forecastSlice = forecastPoints.slice(0, forecastSliceCount);

    return [...histSlice, ...forecastSlice];
  }, [data?.chart_data, timeRange]);

  // Custom Recharts Tooltip
  const CustomChartTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload;
      const isForecast = point.isForecast;
      const price = isForecast ? point.forecastPrice : point.historicalPrice;
      return (
        <div className="bg-[#103D2C] text-white p-3 rounded-xl shadow-xl border border-[#17643E] text-xs space-y-1 z-50">
          <p className="font-semibold text-[#A8C69A]">{point.label} (2026)</p>
          <div className="flex items-baseline gap-1">
            <span className="text-base font-bold text-white">₹{price?.toLocaleString('en-IN')}</span>
            <span className="text-[10px] text-white/70">/ quintal</span>
          </div>
          <div className="flex items-center gap-1.5 pt-1.5 border-t border-white/10 mt-1">
            <span className={`w-2 h-2 rounded-full ${isForecast ? 'bg-[#B6532A]' : 'bg-[#A8C69A]'}`} />
            <span className="text-white/80 font-medium">
              {isForecast ? 'AI Forecast Projection' : 'Historical Modal Price'}
            </span>
          </div>
          {isForecast && point.forecastMin && (
            <p className="text-[11px] text-amber-200/90 pt-0.5">
              Confidence Band: ₹{point.forecastMin} – ₹{point.forecastMax}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* 1. TOP HEADER & CONTEXT BAR */}
      <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#17643E]/10 text-[#17643E]">
                Vidarbha Agri-Exchange Monitor
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
                SAMPLE MARKET DATA
              </span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-serif font-bold text-[#103D2C] mt-2">
              Market Intelligence
            </h1>
            <p className="text-[#292B26]/75 text-sm mt-0.5 font-medium">
              Understand market movement. Compare nearby prices. Make better selling decisions.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#FBF7EF] hover:bg-[#F2E8D5] text-[#103D2C] border border-[#E5DDCF] rounded-xl text-sm font-semibold transition-all hover:shadow-sm disabled:opacity-50"
              title="Refresh latest market data"
            >
              <RefreshCw size={15} className={refreshing ? 'animate-spin text-[#17643E]' : ''} />
              <span>{refreshing ? 'Updating...' : 'Refresh Data'}</span>
            </button>
          </div>
        </div>

        {/* Compact status/context bar */}
        <div className="pt-3 border-t border-[#E5DDCF]/80 flex flex-wrap items-center justify-between text-xs text-[#292B26]/70 gap-y-2">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span className="flex items-center gap-1.5">
              <span className="font-semibold text-[#103D2C]">Selected Farm:</span> Green Acres (Field 1)
            </span>
            <span className="text-[#E5DDCF]">•</span>
            <span className="flex items-center gap-1.5">
              <span className="font-semibold text-[#103D2C]">Region:</span> Maharashtra (Vidarbha Belt)
            </span>
            <span className="text-[#E5DDCF]">•</span>
            <span className="flex items-center gap-1.5 text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              <ShieldCheck size={13} className="text-amber-700" />
              <span>Demonstration dataset — not live Agmarknet mandi prices</span>
            </span>
          </div>
          <div className="flex items-center gap-2 text-right">
            <Clock size={13} className="text-[#17643E]" />
            <span>Last Updated: <span className="font-medium text-[#103D2C]">{lastUpdated}</span></span>
            {refreshToast && (
              <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 animate-fade-in">
                ✓ Updated just now
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. MARKET CONTROL PANEL */}
      <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={16} className="text-[#17643E]" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#103D2C]">
              Market Control Panel
            </h2>
          </div>
          <span className="text-xs text-[#292B26]/60">
            Select crop & mandi to recompute projections
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 items-end">
          {/* CROP SELECTOR */}
          <div>
            <label className="block text-xs font-semibold text-[#292B26]/70 mb-1">
              CROP
            </label>
            <div className="relative">
              <select
                value={stagedCrop}
                onChange={(e) => setStagedCrop(e.target.value as SupportedCrop)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3.5 py-2.5 text-sm font-bold text-[#103D2C] focus:outline-none focus:border-[#17643E] transition-colors cursor-pointer appearance-none"
              >
                <option value="Cotton">Cotton (Kapas)</option>
                <option value="Soyabean">Soyabean</option>
                <option value="Tur">Tur (Pigeon Pea)</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-[#103D2C]">
                ▼
              </div>
            </div>
          </div>

          {/* MARKET REGION SELECTOR */}
          <div>
            <label className="block text-xs font-semibold text-[#292B26]/70 mb-1">
              MARKET REGION
            </label>
            <div className="relative">
              <select
                value={stagedMarket}
                onChange={(e) => setStagedMarket(e.target.value as SupportedMarket)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3.5 py-2.5 text-sm font-bold text-[#103D2C] focus:outline-none focus:border-[#17643E] transition-colors cursor-pointer appearance-none"
              >
                <option value="Akola">Akola APMC</option>
                <option value="Amravati">Amravati APMC</option>
                <option value="Akot">Akot APMC</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-[#103D2C]">
                ▼
              </div>
            </div>
          </div>

          {/* TIME RANGE SELECTOR */}
          <div>
            <label className="block text-xs font-semibold text-[#292B26]/70 mb-1">
              TIME RANGE
            </label>
            <div className="relative">
              <select
                value={stagedTimeRange}
                onChange={(e) => setStagedTimeRange(e.target.value as SupportedTimeRange)}
                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3.5 py-2.5 text-sm font-bold text-[#103D2C] focus:outline-none focus:border-[#17643E] transition-colors cursor-pointer appearance-none"
              >
                <option value="7D">7 Days Horizon</option>
                <option value="14D">14 Days Horizon</option>
                <option value="30D">30 Days Historical</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-[#103D2C]">
                ▼
              </div>
            </div>
          </div>

          {/* SEARCH INPUT */}
          <div className="lg:col-span-1">
            <label className="block text-xs font-semibold text-[#292B26]/70 mb-1">
              FILTER MANDIS
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search crop or mandi..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-7 py-2.5 bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-sm focus:outline-none focus:border-[#17643E] transition-colors placeholder:text-gray-400"
              />
              <Search className="absolute left-3 top-3 text-gray-400 w-4 h-4" />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-3 text-gray-400 hover:text-gray-600"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>

          {/* ACTION BUTTONS */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleApplyFilters}
              disabled={loading}
              className="flex-1 bg-[#17643E] hover:bg-[#103D2C] text-white py-2.5 px-3 rounded-xl text-sm font-semibold transition-colors shadow-sm disabled:opacity-50 text-center"
            >
              Apply Filters
            </button>
            <button
              onClick={handleResetFilters}
              title="Reset all filters to default"
              className="p-2.5 bg-[#FBF7EF] hover:bg-[#F2E8D5] text-[#292B26]/70 border border-[#E5DDCF] rounded-xl transition-colors"
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* ERROR STATE */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-3 text-red-800">
            <AlertCircle size={20} className="shrink-0 text-red-600" />
            <div>
              <p className="font-bold text-sm">Failed to retrieve market updates</p>
              <p className="text-xs text-red-700">{error}</p>
            </div>
          </div>
          <button
            onClick={() => fetchMarketData(crop, market, timeRange)}
            className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* 3. MARKET SNAPSHOT ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* CARD 1: CURRENT MARKET PRICE */}
        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-[#292B26]/60">
                Current Market Price
              </span>
              <span className="text-[10px] bg-[#17643E]/10 text-[#17643E] font-semibold px-2 py-0.5 rounded-full">
                {crop} • {market}
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              {loading ? (
                <div className="h-9 w-32 bg-gray-200 rounded animate-pulse" />
              ) : (
                <>
                  <span className="text-3xl font-extrabold text-[#103D2C]">
                    ₹{data?.current_price?.toLocaleString('en-IN') || '--'}
                  </span>
                  <span className="text-xs text-[#292B26]/60 font-medium">/ quintal</span>
                </>
              )}
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-[#E5DDCF]/60 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1 font-semibold">
              {(data?.price_change_pct ?? 0) >= 0 ? (
                <span className="text-[#17643E] flex items-center gap-0.5">
                  <TrendingUp size={14} /> +{data?.price_change_pct}%
                </span>
              ) : (
                <span className="text-[#B6532A] flex items-center gap-0.5">
                  <TrendingDown size={14} /> {data?.price_change_pct}%
                </span>
              )}
              <span className="text-[#292B26]/50 font-normal">vs prev period</span>
            </div>
            <span className="text-[11px] text-[#292B26]/70 truncate max-w-[120px]">
              MSP: ₹{data?.msp_benchmark?.toLocaleString('en-IN')}
            </span>
          </div>
        </div>

        {/* CARD 2: MARKET TREND */}
        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm flex flex-col justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#292B26]/60">
              Market Trend
            </span>
            <div className="mt-3 flex items-center gap-2">
              {loading ? (
                <div className="h-9 w-28 bg-gray-200 rounded animate-pulse" />
              ) : (
                <span className={`text-2xl font-bold flex items-center gap-2 ${
                  data?.trend === 'Rising' ? 'text-[#17643E]' : data?.trend === 'Falling' ? 'text-[#B6532A]' : 'text-[#103D2C]'
                }`}>
                  {data?.trend === 'Rising' ? <TrendingUp size={24} /> : data?.trend === 'Falling' ? <TrendingDown size={24} /> : null}
                  {data?.trend || 'Stable'}
                </span>
              )}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-[#E5DDCF]/60 flex items-center justify-between text-xs text-[#292B26]/70">
            <span>7-Day Movement Index</span>
            <span className="font-semibold text-[#103D2C]">{data?.modal_variety || 'Commercial'}</span>
          </div>
        </div>

        {/* CARD 3: BEST REGIONAL MANDI */}
        <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-[#292B26]/60">
                Best Regional Mandi
              </span>
              <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">
                TOP PRICE
              </span>
            </div>
            <div className="mt-3">
              {loading ? (
                <div className="h-9 w-32 bg-gray-200 rounded animate-pulse" />
              ) : (
                <div>
                  <span className="text-2xl font-extrabold text-[#103D2C]">
                    {data?.best_market?.name || 'Akot APMC'}
                  </span>
                  <div className="text-sm font-semibold text-[#17643E] mt-0.5">
                    ₹{data?.best_market?.price?.toLocaleString('en-IN')} / qtl
                  </div>
                </div>
              )}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-[#E5DDCF]/60 flex items-center justify-between text-xs">
            <span className="text-[#292B26]/70">Premium vs {market}:</span>
            <span className="font-bold text-[#17643E]">
              {data?.best_market?.difference > 0 ? `+₹${data.best_market.difference} / qtl` : 'Selected is Top'}
            </span>
          </div>
        </div>

        {/* CARD 4: AI FORECAST */}
        <div className="bg-[#FBF7EF] rounded-2xl p-5 border border-[#E5DDCF] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-[#103D2C]/70 flex items-center gap-1.5">
                <Sparkles size={13} className="text-[#B6532A]" /> AI 7-Day Forecast
              </span>
              <span className="text-[10px] font-semibold bg-white border border-[#E5DDCF] px-2 py-0.5 rounded-full text-[#103D2C]">
                {data?.forecast?.confidence || 'Sample Model'}
              </span>
            </div>
            <div className="mt-3">
              {loading ? (
                <div className="h-9 w-36 bg-gray-200 rounded animate-pulse" />
              ) : (
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-extrabold text-[#103D2C]">
                    ₹{data?.forecast?.expected_price?.toLocaleString('en-IN') || '--'}
                  </span>
                  <span className="text-xs font-semibold text-[#17643E]">
                    ({data?.forecast?.trend || 'Upward'})
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-[#E5DDCF]/60 flex items-center justify-between text-xs text-[#292B26]/70">
            <span>Projected Range:</span>
            <span className="font-semibold text-[#103D2C]">
              ₹{data?.forecast?.min_price} – ₹{data?.forecast?.max_price}
            </span>
          </div>
        </div>
      </div>

      {/* 4. ADVANCED PRICE TREND SECTION */}
      <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-serif font-bold text-[#103D2C]">
                Price Trend & AI Projections
              </h3>
              <span className="text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full">
                Demo dataset
              </span>
            </div>
            <p className="text-xs text-[#292B26]/70 mt-0.5">
              Historical modal prices and projected trajectory for {crop} at {market} APMC.
            </p>
          </div>

          {/* Horizon Tabs */}
          <div className="flex items-center bg-[#FBF7EF] p-1 rounded-xl border border-[#E5DDCF]">
            {(['7D', '14D', '30D'] as SupportedTimeRange[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setTimeRange(tab)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  timeRange === tab
                    ? 'bg-[#17643E] text-white shadow-sm'
                    : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                {tab === '7D' ? '7 Days' : tab === '14D' ? '14 Days' : '30 Days'}
              </button>
            ))}
          </div>
        </div>

        {/* RECHARTS CHART CONTAINER */}
        <div className="h-72 w-full pt-2">
          {loading ? (
            <div className="h-full w-full flex flex-col items-center justify-center text-[#292B26]/50 space-y-2">
              <Loader2 className="w-8 h-8 animate-spin text-[#17643E]" />
              <p className="text-xs font-medium">Recomputing mandi price curves...</p>
            </div>
          ) : chartPoints.length === 0 ? (
            <div className="h-full w-full flex items-center justify-center text-[#292B26]/50 text-sm">
              No price data available for the selected range.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartPoints} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorHistorical" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#17643E" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#17643E" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5DDCF" vertical={false} />
                <XAxis
                  dataKey="label"
                  stroke="#292B26"
                  opacity={0.6}
                  fontSize={11}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="#292B26"
                  opacity={0.6}
                  fontSize={11}
                  tickLine={false}
                  domain={['auto', 'auto']}
                  tickFormatter={(val) => `₹${val}`}
                />
                <Tooltip content={<CustomChartTooltip />} />
                <Legend
                  verticalAlign="top"
                  align="right"
                  height={30}
                  iconSize={10}
                  wrapperStyle={{ fontSize: '11px', paddingBottom: '8px' }}
                />
                <Area
                  type="monotone"
                  dataKey="historicalPrice"
                  name="Historical Modal Price (₹/qtl)"
                  stroke="#17643E"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorHistorical)"
                  activeDot={{ r: 5, fill: '#17643E' }}
                />
                <Line
                  type="monotone"
                  dataKey="forecastPrice"
                  name="AI Forecast (₹/qtl)"
                  stroke="#B6532A"
                  strokeWidth={2.2}
                  strokeDasharray="4 4"
                  dot={{ r: 3, fill: '#B6532A' }}
                  activeDot={{ r: 6, fill: '#B6532A' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between text-[11px] text-[#292B26]/60 pt-2 border-t border-[#E5DDCF]/70">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#17643E]" /> Solid Green: Historical Daily Modal Price
            <span className="w-2.5 h-2.5 rounded-full bg-[#B6532A] ml-3" /> Dashed Rust: AI Forecast Horizon
          </span>
          <span>Baseline Mandi: {market} APMC</span>
        </div>
      </div>

      {/* 5. MARKET COMPARISON SECTION & DECISION INSIGHT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* COMPARE NEARBY MARKETS CARDS */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-serif font-bold text-[#103D2C]">
                Compare Regional Mandis ({crop})
              </h3>
              <p className="text-xs text-[#292B26]/70">
                Click any mandi to set active baseline or view in-depth metrics.
              </p>
            </div>
            <span className="text-xs font-semibold text-[#17643E]">
              3 Mandis Monitored
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {data?.nearby_markets?.map((m: any) => {
              const isSelected = market === m.marketKey;
              const isTop = data?.best_market?.name.includes(m.marketKey);

              return (
                <div
                  key={m.id}
                  onClick={() => {
                    setMarket(m.marketKey as SupportedMarket);
                    setStagedMarket(m.marketKey as SupportedMarket);
                  }}
                  className={`p-4 rounded-xl border transition-all cursor-pointer relative ${
                    isSelected
                      ? 'bg-[#FBF7EF] border-[#17643E] ring-2 ring-[#17643E]/20 shadow-sm'
                      : 'bg-white border-[#E5DDCF] hover:border-[#17643E]/40 hover:bg-[#FBF7EF]/50'
                  }`}
                >
                  {isTop && (
                    <span className="absolute -top-2.5 right-3 bg-[#17643E] text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                      Highest Price
                    </span>
                  )}
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-[#103D2C] flex items-center gap-1.5">
                        <MapPin size={13} className={isSelected ? 'text-[#17643E]' : 'text-gray-400'} />
                        {m.marketKey} APMC
                      </h4>
                      <p className="text-[11px] text-[#292B26]/60 mt-0.5">{m.distance}</p>
                    </div>
                  </div>

                  <div className="mt-3">
                    <span className="text-xl font-extrabold text-[#103D2C]">
                      ₹{m.currentPrice.toLocaleString('en-IN')}
                    </span>
                    <span className="text-xs text-[#292B26]/60 ml-1">/ qtl</span>
                  </div>

                  <div className="mt-2.5 pt-2.5 border-t border-[#E5DDCF]/70 flex items-center justify-between text-xs">
                    <span className={`font-semibold flex items-center gap-0.5 ${
                      m.priceChangePct >= 0 ? 'text-[#17643E]' : 'text-[#B6532A]'
                    }`}>
                      {m.priceChangePct >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {m.priceChangePct >= 0 ? `+${m.priceChangePct}%` : `${m.priceChangePct}%`}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDetailMarket(m);
                      }}
                      className="text-[11px] text-[#17643E] font-bold hover:underline"
                    >
                      View Details →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* DECISION INSIGHT PANEL */}
        <div className="bg-[#103D2C] text-white rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles size={16} className="text-[#A8C69A]" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#A8C69A]">
                Market Insight
              </h3>
            </div>
            <p className="text-xs text-white/70">
              Rule-based selling opportunity analysis
            </p>

            <div className="mt-5 space-y-3.5">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-white/50 block font-semibold">
                  BEST REGIONAL PRICE
                </span>
                <span className="text-xl font-bold text-white">
                  {data?.rule_based_insight?.best_market_name || 'Akot APMC'} (₹{data?.rule_based_insight?.best_price?.toLocaleString('en-IN')})
                </span>
              </div>

              <div>
                <span className="text-[11px] uppercase tracking-wider text-white/50 block font-semibold">
                  PRICE SIGNAL
                </span>
                <span className="inline-flex items-center gap-1.5 text-sm font-bold text-emerald-300">
                  <TrendingUp size={14} /> {data?.rule_based_insight?.price_signal || 'Rising'} Trend Momentum
                </span>
              </div>

              <div className="p-3 bg-white/10 rounded-xl border border-white/10">
                <span className="text-[11px] uppercase tracking-wider text-amber-200 block font-bold mb-1">
                  RECOMMENDED ACTION
                </span>
                <p className="text-xs text-white/90 leading-relaxed">
                  {data?.rule_based_insight?.recommended_action ||
                    'Monitor Akot APMC for higher selling margins.'}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/10 text-[10px] text-white/50">
            {data?.rule_based_insight?.disclaimer ||
              'Based on available market prices and trend rules — not a black-box ML prediction.'}
          </div>
        </div>
      </div>

      {/* 6. NEARBY MARKETS TABLE */}
      <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h3 className="text-lg font-serif font-bold text-[#103D2C]">
              Regional APMC Comparison Table
            </h3>
            <p className="text-xs text-[#292B26]/70 mt-0.5">
              Compare mandi prices, distances, and varieties. Click "View" to open full market dossiers.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#292B26]/60">Sort by:</span>
            <select
              value={sortField}
              onChange={(e) => setSortField(e.target.value as any)}
              className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg px-2.5 py-1 text-xs font-semibold text-[#103D2C] outline-none cursor-pointer"
            >
              <option value="currentPrice">Price (High to Low)</option>
              <option value="priceChangePct">Change (%)</option>
              <option value="name">Market Name</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="p-1 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs font-bold text-[#103D2C] px-2"
              title="Toggle sort direction"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>

        {/* TABLE CONTAINER */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[700px]">
            <thead>
              <tr className="text-xs uppercase text-[#292B26]/60 border-b border-[#E5DDCF] bg-[#FBF7EF]/50">
                <th className="py-3 px-3 font-semibold">Market Name</th>
                <th className="py-3 px-3 font-semibold">Location</th>
                <th className="py-3 px-3 font-semibold">Distance</th>
                <th className="py-3 px-3 font-semibold">Current Price</th>
                <th className="py-3 px-3 font-semibold">24h Change</th>
                <th className="py-3 px-3 font-semibold">Trend</th>
                <th className="py-3 px-3 font-semibold">Data Status</th>
                <th className="py-3 px-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-[#292B26]/50">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-[#17643E]" />
                    Loading APMC market listings...
                  </td>
                </tr>
              ) : filteredMarkets.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center">
                    <div className="max-w-md mx-auto space-y-2">
                      <p className="text-sm font-semibold text-[#103D2C]">
                        No mandis found matching "{searchQuery}"
                      </p>
                      <p className="text-xs text-[#292B26]/60">
                        Clear your search query or reset the control panel to see all Vidarbha mandis.
                      </p>
                      <button
                        onClick={() => setSearchQuery('')}
                        className="mt-2 px-3 py-1.5 bg-[#17643E] text-white text-xs font-semibold rounded-lg hover:bg-[#103D2C]"
                      >
                        Clear Search Query
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredMarkets.map((m: any, idx: number) => {
                  const isSelected = market === m.marketKey;
                  return (
                    <tr
                      key={m.id || idx}
                      className={`border-b border-[#E5DDCF]/60 transition-colors ${
                        isSelected ? 'bg-emerald-50/60 font-medium' : 'hover:bg-[#FBF7EF]'
                      }`}
                    >
                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-2">
                          <Building2 size={15} className={isSelected ? 'text-[#17643E]' : 'text-gray-400'} />
                          <span className="font-bold text-[#103D2C]">{m.name}</span>
                          {isSelected && (
                            <span className="text-[10px] bg-[#17643E] text-white px-1.5 py-0.2 rounded font-semibold">
                              ACTIVE
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-3 text-xs text-[#292B26]/80">{m.location}</td>
                      <td className="py-3.5 px-3 text-xs text-[#292B26]/80">{m.distance}</td>
                      <td className="py-3.5 px-3 font-extrabold text-sm text-[#103D2C]">
                        ₹{m.currentPrice.toLocaleString('en-IN')} <span className="text-xs font-normal text-[#292B26]/60">/ qtl</span>
                      </td>
                      <td className={`py-3.5 px-3 text-xs font-bold ${
                        m.priceChangePct >= 0 ? 'text-[#17643E]' : 'text-[#B6532A]'
                      }`}>
                        {m.priceChangePct >= 0 ? `+${m.priceChangePct}%` : `${m.priceChangePct}%`}
                      </td>
                      <td className="py-3.5 px-3">
                        <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                          m.trend === 'Rising'
                            ? 'bg-emerald-100 text-emerald-800'
                            : m.trend === 'Falling'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {m.trend === 'Rising' ? <TrendingUp size={11} /> : m.trend === 'Falling' ? <TrendingDown size={11} /> : null}
                          {m.trend}
                        </span>
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="text-[10px] font-semibold bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded-full">
                          {m.dataStatus}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-right">
                        <button
                          onClick={() => setSelectedDetailMarket(m)}
                          className="px-3 py-1 bg-[#17643E] hover:bg-[#103D2C] text-white text-xs font-semibold rounded-lg transition-colors shadow-xs"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 7. MARKET DETAIL MODAL / DRAWER */}
      {selectedDetailMarket && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl border border-[#E5DDCF] animate-scale-up">
            {/* Modal Header */}
            <div className="bg-[#103D2C] text-white p-6 relative">
              <button
                onClick={() => setSelectedDetailMarket(null)}
                className="absolute top-5 right-5 p-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                title="Close dialog"
              >
                <X size={18} />
              </button>
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#A8C69A]">
                <Building2 size={14} /> APMC Mandi Dossier
              </div>
              <h3 className="text-2xl font-serif font-bold text-white mt-1">
                {selectedDetailMarket.name}
              </h3>
              <p className="text-xs text-white/70 mt-0.5">
                {selectedDetailMarket.location} • {selectedDetailMarket.distance}
              </p>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4 text-sm text-[#292B26]">
              {/* Top stats */}
              <div className="grid grid-cols-2 gap-3 p-4 bg-[#FBF7EF] rounded-2xl border border-[#E5DDCF]">
                <div>
                  <span className="text-xs text-[#292B26]/60 font-semibold block">CURRENT MODAL PRICE</span>
                  <div className="text-2xl font-extrabold text-[#103D2C] mt-0.5">
                    ₹{selectedDetailMarket.currentPrice.toLocaleString('en-IN')}
                    <span className="text-xs font-normal text-[#292B26]/60"> / qtl</span>
                  </div>
                </div>
                <div>
                  <span className="text-xs text-[#292B26]/60 font-semibold block">24H PRICE SHIFT</span>
                  <div className={`text-base font-bold mt-1.5 flex items-center gap-1 ${
                    selectedDetailMarket.priceChangePct >= 0 ? 'text-[#17643E]' : 'text-[#B6532A]'
                  }`}>
                    {selectedDetailMarket.priceChangePct >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                    {selectedDetailMarket.priceChangePct >= 0 ? `+${selectedDetailMarket.priceChangePct}%` : `${selectedDetailMarket.priceChangePct}%`}
                    <span className="text-xs font-normal text-[#292B26]/60">({selectedDetailMarket.trend})</span>
                  </div>
                </div>
              </div>

              {/* Dossier Specs */}
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between py-1.5 border-b border-[#E5DDCF]/60">
                  <span className="text-[#292B26]/60">Monitored Crop:</span>
                  <span className="font-bold text-[#103D2C]">{crop}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#E5DDCF]/60">
                  <span className="text-[#292B26]/60">Modal Commercial Variety:</span>
                  <span className="font-semibold text-[#103D2C]">{selectedDetailMarket.variety}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#E5DDCF]/60">
                  <span className="text-[#292B26]/60">Weekly Price Range:</span>
                  <span className="font-semibold text-[#103D2C]">
                    ₹{selectedDetailMarket.weeklyLow} – ₹{selectedDetailMarket.weeklyHigh} / qtl
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#E5DDCF]/60">
                  <span className="text-[#292B26]/60">Trading Hours:</span>
                  <span className="font-semibold text-[#103D2C]">{selectedDetailMarket.tradingHours}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-[#E5DDCF]/60">
                  <span className="text-[#292B26]/60">Data Provenance:</span>
                  <span className="font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded">
                    Sample Demonstration Dataset
                  </span>
                </div>
              </div>

              {/* Farmer Tip */}
              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-900 space-y-1">
                <span className="font-bold flex items-center gap-1 text-[#17643E]">
                  <Sparkles size={13} /> Practical Selling Note
                </span>
                <p className="text-emerald-800 leading-relaxed">
                  Peak transaction volumes at {selectedDetailMarket.name} occur between 09:30 AM and 11:30 AM. Moisture levels under 8% for {crop} avoid APMC grading deductions.
                </p>
              </div>

              {/* Action */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  onClick={() => {
                    setMarket(selectedDetailMarket.marketKey as SupportedMarket);
                    setStagedMarket(selectedDetailMarket.marketKey as SupportedMarket);
                    setSelectedDetailMarket(null);
                  }}
                  className="flex-1 bg-[#17643E] hover:bg-[#103D2C] text-white py-2.5 rounded-xl font-semibold text-xs transition-colors shadow-sm text-center"
                >
                  Set as Active Baseline Mandi
                </button>
                <button
                  onClick={() => setSelectedDetailMarket(null)}
                  className="px-4 py-2.5 bg-[#FBF7EF] hover:bg-[#F2E8D5] text-[#292B26] border border-[#E5DDCF] rounded-xl font-semibold text-xs"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
