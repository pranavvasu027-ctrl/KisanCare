import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, MapPin, Search, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

export default function MarketIntelligence() {
  const [crop, setCrop] = useState('onion');
  const [market, setMarket] = useState('Pune Pimpri');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketData();
  }, [crop, market]);

  const fetchMarketData = async () => {
    setLoading(true);
    setError(null);
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await api.getMarketPrice(crop, market, today);
      setData(res.data);
      setIsDemo(res.isDemo);
    } catch (e: any) {
      console.error(e);
      // Determine error message based on common API failure patterns
      const msg = e.toString().toLowerCase();
      if (msg.includes("422")) {
        setError("Insufficient historical data for reliable forecasting. Please try a different market or ingest fresh data.");
      } else if (msg.includes("404")) {
        setError("Market price model not available for this crop and market combination.");
      } else {
        setError("An error occurred while communicating with the forecast model.");
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Market Intelligence</h1>
          <p className="text-[#292B26]/70 mt-1">Live market prices and AI-driven price forecasts.</p>
        </div>
        <div className="flex items-center gap-4 w-full md:w-auto">
          {isDemo && <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded-full uppercase tracking-wider whitespace-nowrap">Demo Mode</span>}
          <div className="relative w-full md:w-64">
            <input type="text" placeholder="Search crops or markets..." className="w-full pl-10 pr-4 py-2 bg-white border border-[#E5DDCF] rounded-lg focus:outline-none focus:border-[#17643E]" />
            <Search className="absolute left-3 top-2.5 text-[#292B26]/40 w-4 h-4" />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-4 border-b border-[#E5DDCF]">
          <div className="p-4 border-r border-[#E5DDCF]">
            <label className="text-xs text-[#292B26]/60 font-medium">Crop</label>
            <select 
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full text-lg font-bold text-[#103D2C] outline-none mt-1 bg-transparent cursor-pointer"
            >
              <option value="onion">Onion</option>
              <option value="tomato">Tomato</option>
              <option value="potato">Potato</option>
              <option value="cabbage">Cabbage</option>
            </select>
          </div>
          <div className="p-4 border-r border-[#E5DDCF]">
            <label className="text-xs text-[#292B26]/60 font-medium">Market Location</label>
            <select 
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="w-full text-lg font-bold text-[#103D2C] outline-none mt-1 bg-transparent cursor-pointer"
            >
              <option value="Pune">Pune</option>
              <option value="Mumbai">Mumbai</option>
              <option value="Nagpur">Nagpur</option>
            </select>
          </div>
          <div className="p-4 border-r border-[#E5DDCF]">
            <label className="text-xs text-[#292B26]/60 font-medium">Current Avg Price</label>
            <div className="text-2xl font-bold text-[#103D2C] mt-1">
              {loading ? <Loader2 className="w-6 h-6 animate-spin text-[#17643E]" /> : `₹${data?.current_price || '--'} `}
              {!loading && <span className="text-sm font-normal">/ qtl</span>}
            </div>
          </div>
          <div className="p-4 bg-[#FBF7EF]">
            <label className="text-xs text-[#292B26]/60 font-medium">AI Forecast (Next 7 Days)</label>
            <div className="text-lg font-bold text-[#103D2C] mt-1">
              {loading ? <Loader2 className="w-5 h-5 animate-spin text-[#17643E]" /> : (
                <>
                  {data?.trend === 'Up' ? 'Upward' : data?.trend === 'Down' ? 'Downward' : 'Stable'}
                  <span className="text-sm text-[#17643E] ml-2">(₹{data?.forecast_7d || '--'})</span>
                </>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="p-6 bg-red-50 border-t border-red-100">
            <h3 className="text-red-800 font-bold mb-2">Error Generating Forecast</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {!error && (

        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-[#103D2C]">Nearby Markets</h3>
            <button onClick={fetchMarketData} className="text-sm text-[#17643E] font-medium hover:underline">Refresh Data</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-xs uppercase text-[#292B26]/60 border-b border-[#E5DDCF]">
                  <th className="py-3 font-medium">Market Location</th>
                  <th className="py-3 font-medium">Distance</th>
                  <th className="py-3 font-medium">Price (per qtl)</th>
                  <th className="py-3 font-medium">Arrivals (Tons)</th>
                  <th className="py-3 font-medium">Trend (Today)</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                   <tr><td colSpan={5} className="py-8 text-center text-[#292B26]/50"><Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />Loading market data...</td></tr>
                ) : data?.nearby_markets?.map((m: any, i: number) => (
                  <tr key={i} className="border-b border-[#E5DDCF]/50 hover:bg-[#FBF7EF]">
                    <td className="py-4 font-bold text-[#103D2C] flex items-center gap-2">
                      <MapPin size={14} className={i === 0 ? "text-[#B6532A]" : "text-[#292B26]/40"} /> {m.name}
                    </td>
                    <td className="py-4 text-[#292B26]/80">{m.distance} km</td>
                    <td className="py-4 font-bold">₹{m.price}</td>
                    <td className="py-4 text-[#292B26]/80">{m.arrivals}</td>
                    <td className={`py-4 flex items-center gap-1 ${m.trend.startsWith('+') ? 'text-[#17643E]' : m.trend.startsWith('-') ? 'text-[#B6532A]' : 'text-[#292B26]/50'}`}>
                      {m.trend.startsWith('+') ? <TrendingUp size={14} /> : m.trend.startsWith('-') ? <TrendingDown size={14} /> : null}
                      {m.trend}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        )}
      </div>
    </div>
  );
}
