import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, MapPin, Search, Loader2, Calendar, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';

const SUPPORTED_PAIRS: Record<string, string[]> = {
  onion: ['Pune(Pimpri)', 'Baramati', 'Junnar'],
  tomato: ['Pune(Pimpri)', 'Baramati'],
  cabbage: ['Pune(Manjri)', 'Pune(Pimpri)'],
  potato: ['Pune(Manjri) APMC', 'Pune(Manjri)'],
  cauliflower: ['Pune(Manjri) APMC', 'Pune(Manjri)']
};

export default function MarketIntelligence() {
  const [crop, setCrop] = useState('onion');
  const [market, setMarket] = useState('Pune(Pimpri)');
  const [forecastDate, setForecastDate] = useState('2025-11-04');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Keep market selection valid for selected crop
    const available = SUPPORTED_PAIRS[crop] || ['Pune(Pimpri)'];
    if (!available.includes(market)) {
      setMarket(available[0]);
    }
  }, [crop]);

  useEffect(() => {
    fetchMarketData();
  }, [crop, market, forecastDate]);

  const fetchMarketData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMarketPrice(crop, market, forecastDate);
      setData(res.data);
      setIsDemo(res.isDemo);
    } catch (e: any) {
      console.error(e);
      const msg = e.toString().toLowerCase();
      if (msg.includes("422")) {
        setError("Insufficient trailing historical data for this target date. The XGBoost model requires at least 14 days of prior mandi arrivals.");
      } else if (msg.includes("404")) {
        setError("XGBoost market price model not found for this crop and APMC market combination.");
      } else {
        setError(`Failed to retrieve forecast: ${e.message || String(e)}`);
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const availableMarkets = SUPPORTED_PAIRS[crop] || ['Pune(Pimpri)'];

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <WorkflowStepper currentStageId={5} />

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Market Intelligence</h1>
          <p className="text-[#292B26]/70 mt-1">APMC mandi price trends and trained XGBoost price forecasts.</p>
        </div>
        <div className="flex items-center gap-4 w-full md:w-auto">
          {isDemo ? (
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-1 rounded-full border border-amber-300 uppercase tracking-wider whitespace-nowrap">
              Sample Market Data
            </span>
          ) : (
            <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-1 rounded-full border border-emerald-300 uppercase tracking-wider whitespace-nowrap">
              Live Mandi Model
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 border-b border-[#E5DDCF]">
          <div className="p-4 border-r border-[#E5DDCF]">
            <label className="text-xs text-[#292B26]/60 font-medium">Commodity Crop</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full text-base font-bold text-[#103D2C] outline-none mt-1 bg-transparent cursor-pointer"
            >
              <option value="onion">Onion (Kanda)</option>
              <option value="tomato">Tomato</option>
              <option value="cabbage">Cabbage</option>
              <option value="potato">Potato</option>
              <option value="cauliflower">Cauliflower</option>
            </select>
          </div>

          <div className="p-4 border-r border-[#E5DDCF]">
            <label className="text-xs text-[#292B26]/60 font-medium">APMC Market Location</label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="w-full text-base font-bold text-[#103D2C] outline-none mt-1 bg-transparent cursor-pointer"
            >
              {availableMarkets.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className="p-4 border-r border-[#E5DDCF]">
            <label className="text-xs text-[#292B26]/60 font-medium">Forecast Baseline Date</label>
            <input
              type="date"
              value={forecastDate}
              onChange={(e) => setForecastDate(e.target.value)}
              className="w-full text-sm font-bold text-[#103D2C] outline-none mt-1 bg-transparent cursor-pointer"
            />
          </div>

          <div className="p-4 bg-[#FBF7EF]">
            <label className="text-xs text-[#292B26]/60 font-medium">AI 7-Day Price Forecast</label>
            <div className="text-base font-bold text-[#103D2C] mt-1">
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin text-[#17643E]" />
              ) : data ? (
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xl text-[#103D2C]">₹{data.forecast_7d || data.predicted_price_7d || data.current_price}</span>
                    <span className="text-xs font-normal text-[#292B26]/60">/ qtl</span>
                  </div>
                  <span className={`text-xs font-semibold ${
                    String(data.trend).includes('+') || data.trend === 'Up' ? 'text-[#17643E]' : 'text-[#B6532A]'
                  }`}>
                    {data.trend || '7-day projection'}
                  </span>
                </div>
              ) : (
                <span className="text-sm font-normal text-[#292B26]/50">--</span>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="p-6 bg-red-50 border-t border-red-100 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-red-900 font-bold text-sm mb-1">Mandi Model Notice</h3>
              <p className="text-red-700 text-xs leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {!error && data && (
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="font-bold text-[#103D2C]">Mandi Price Breakdown & Historical Lags</h3>
                <p className="text-xs text-[#292B26]/60 mt-0.5">Extracted from Agmarknet modal price series</p>
              </div>
              <button onClick={fetchMarketData} className="text-xs text-[#17643E] font-medium hover:underline">
                Refresh Forecast
              </button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 bg-[#FBF7EF] rounded-xl border border-[#E5DDCF]">
                <span className="text-xs text-[#292B26]/60 block mb-1">Current Base Price</span>
                <span className="text-lg font-bold text-[#103D2C]">₹{data.current_price || '--'} / qtl</span>
              </div>
              <div className="p-3 bg-[#FBF7EF] rounded-xl border border-[#E5DDCF]">
                <span className="text-xs text-[#292B26]/60 block mb-1">7-Day Projected Range</span>
                <span className="text-lg font-bold text-[#103D2C]">
                  ₹{data.forecast_min ? `${data.forecast_min} - ₹${data.forecast_max}` : `${data.forecast_7d || '--'}`}
                </span>
              </div>
              <div className="p-3 bg-[#FBF7EF] rounded-xl border border-[#E5DDCF]">
                <span className="text-xs text-[#292B26]/60 block mb-1">Model Architecture</span>
                <span className="text-sm font-bold text-[#103D2C]">{data.model_type || 'XGBoost v1.0'}</span>
              </div>
              <div className="p-3 bg-[#FBF7EF] rounded-xl border border-[#E5DDCF]">
                <span className="text-xs text-[#292B26]/60 block mb-1">Provenience</span>
                <span className="text-sm font-bold text-emerald-800">
                  {isDemo ? 'Sample Cache' : 'Agmarknet APMC'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <WorkflowFooter
        currentStageNumber={5}
        currentStageName="Market & Post-Harvest Storage"
        completedActionMessage={data ? `Mandi forecast loaded for ${crop} at ${market}! Next step: Calculate storage losses to plan your best selling window.` : null}
        prevStep={{ label: "Farm Economics", path: "/economics" }}
        nextStep={{
          label: "Post-Harvest Storage Loss",
          labelMr: "साठवणूक नुकसान",
          path: "/post-harvest",
          description: "Optimize holding period vs storage loss"
        }}
        alternativeNextStep={{
          label: "Government Schemes",
          path: "/schemes"
        }}
      />
    </div>
  );
}
