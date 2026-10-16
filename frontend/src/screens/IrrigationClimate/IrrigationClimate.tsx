import React, { useState, useEffect } from 'react';
import { Droplets, CloudRain, Sun, Wind, AlertTriangle, Calendar, Loader2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function IrrigationClimate() {
  const [crop, setCrop] = useState('Soybean');
  const [soilMoisture, setSoilMoisture] = useState<number>(24);
  const [daysSinceRain, setDaysSinceRain] = useState<number>(8);
  const [temperature, setTemperature] = useState<number>(36);
  const [humidity, setHumidity] = useState<number>(62);
  const [rainfallForecast, setRainfallForecast] = useState<number>(10);

  const [irrigationData, setIrrigationData] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isDemo, setIsDemo] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchAdvisories();
  }, [crop, soilMoisture, daysSinceRain, temperature, humidity, rainfallForecast]);

  const fetchAdvisories = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [irrigRes, riskRes] = await Promise.all([
        api.recommendIrrigation(crop, soilMoisture, daysSinceRain),
        api.assessWeatherRisk(temperature, humidity, rainfallForecast)
      ]);
      setIrrigationData(irrigRes.data);
      setRiskData(riskRes.data);
      setIsDemo(irrigRes.isDemo || riskRes.isDemo);
    } catch (err: any) {
      console.error('Failed to fetch irrigation / climate advisory:', err);
      setErrorMessage(`Advisory Service Notice: ${err.message || String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Irrigation & Climate</h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Advisory Data
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                Live Agro-Climate Model
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">Weather forecasts and precise irrigation scheduling.</p>
        </div>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Field Conditions Simulator / Input Bar */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-[#E5DDCF] grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold text-[#103D2C] mb-1">Target Crop</label>
          <select
            value={crop}
            onChange={(e) => setCrop(e.target.value)}
            className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-1.5 text-xs font-medium text-[#103D2C]"
          >
            <option value="Soybean">Soybean</option>
            <option value="Cotton">Cotton</option>
            <option value="Wheat">Wheat</option>
            <option value="Rice">Rice</option>
            <option value="Tomato">Tomato</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#103D2C] mb-1">Soil Moisture ({soilMoisture}%)</label>
          <input
            type="range"
            min="5"
            max="95"
            value={soilMoisture}
            onChange={(e) => setSoilMoisture(Number(e.target.value))}
            className="w-full accent-[#103D2C]"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-[#103D2C] mb-1">Days Since Rain ({daysSinceRain} days)</label>
          <input
            type="range"
            min="0"
            max="30"
            value={daysSinceRain}
            onChange={(e) => setDaysSinceRain(Number(e.target.value))}
            className="w-full accent-[#103D2C]"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#103D2C] text-white rounded-3xl p-8 relative overflow-hidden">
            <div className="absolute right-0 top-0 bottom-0 opacity-10 pointer-events-none">
              <Sun className="w-64 h-64 -translate-y-10 translate-x-10" />
            </div>
            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-8">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Sun className="text-yellow-400" />
                  <span className="text-xl font-medium text-[#FBF7EF]">Partly Cloudy</span>
                </div>
                <div className="text-6xl font-bold font-serif mb-2">{temperature}°C</div>
                <p className="text-[#A8C69A]">Nagpur, Maharashtra</p>
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                <div>
                  <div className="text-[#A8C69A] text-xs">Humidity</div>
                  <div className="font-bold text-lg">{humidity}%</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Wind</div>
                  <div className="font-bold text-lg">12 km/h</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Rain Forecast</div>
                  <div className="font-bold text-lg">{rainfallForecast} mm</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Evapotranspiration</div>
                  <div className="font-bold text-lg">4.2 mm/d</div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-4">7-Day Forecast</h3>
            <div className="flex justify-between items-end overflow-x-auto gap-4 custom-scrollbar pb-2">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => (
                <div key={day} className="flex flex-col items-center gap-2 min-w-[60px]">
                  <span className="text-xs font-bold text-[#292B26]/60">{day}</span>
                  {i === 2 || i === 3 ? <CloudRain className="text-blue-500 w-6 h-6" /> : <Sun className="text-yellow-500 w-6 h-6" />}
                  <span className="text-sm font-bold text-[#103D2C]">{30 - i}°</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-4 flex items-center gap-2">
              <Droplets className="text-[#17643E]" /> Irrigation Decision Engine
            </h3>

            {loading ? (
              <div className="py-8 text-center">
                <Loader2 className="w-6 h-6 animate-spin text-[#103D2C] mx-auto mb-2" />
                <span className="text-xs text-[#292B26]/60">Calculating water requirement...</span>
              </div>
            ) : irrigationData ? (
              <div className="bg-white rounded-xl border border-[#E5DDCF] p-4 mb-4 space-y-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-[#103D2C]">{crop} Field</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                    irrigationData.irrigation_required
                      ? 'bg-[#B6532A]/10 text-[#B6532A]'
                      : 'bg-[#17643E]/10 text-[#17643E]'
                  }`}>
                    {irrigationData.irrigation_required ? 'Needs Water' : 'Optimal Moisture'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[#292B26]/80">
                  <Calendar size={14} /> Recommended Volume:
                </div>
                <p className="text-sm font-bold text-[#103D2C]">
                  {irrigationData.recommended_amount_liters_per_acre} Liters / Acre
                </p>
                <p className="text-xs text-[#292B26]/70 italic">
                  {irrigationData.reasoning}
                </p>
              </div>
            ) : null}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-2 flex items-center gap-2">
              <AlertTriangle className="text-[#B6532A]" /> Weather Risk Model
            </h3>
            {loading ? (
              <p className="text-xs text-[#292B26]/60">Evaluating meteorological risks...</p>
            ) : riskData ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#292B26]/60">Overall Risk Level:</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                    riskData.overall_risk === 'High' ? 'bg-red-100 text-red-800' :
                    riskData.overall_risk === 'Medium' ? 'bg-orange-100 text-orange-800' :
                    'bg-emerald-100 text-emerald-800'
                  }`}>
                    {riskData.overall_risk}
                  </span>
                </div>
                <div className="text-xs text-[#292B26]/80">
                  <ul className="list-disc pl-4 space-y-1">
                    {riskData.identified_risks?.map((r: string, i: number) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
                {riskData.mitigation && (
                  <div className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF] text-xs text-[#103D2C]">
                    <span className="font-semibold">Mitigation: </span>{riskData.mitigation}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
