import React, { useState, useEffect } from 'react';
import { Droplets, CloudRain, Sun, Wind, AlertTriangle, Calendar, Loader2, AlertCircle, MapPin, RefreshCw, Compass } from 'lucide-react';
import { api } from '../../services/api';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';

export default function IrrigationClimate() {
  const [crop, setCrop] = useState('Cotton');
  const [soilMoisture, setSoilMoisture] = useState<number>(24);
  const [daysSinceRain, setDaysSinceRain] = useState<number>(8);
  const [coords, setCoords] = useState<{ lat: number; lon: number }>({ lat: 20.7002, lon: 77.0082 });
  const [locationName, setLocationName] = useState<string>('Takli Bu, Akola, Maharashtra');

  const [weatherForecast, setWeatherForecast] = useState<any>(null);
  const [irrigationData, setIrrigationData] = useState<any>(null);
  const [riskData, setRiskData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [locating, setLocating] = useState<boolean>(false);
  const [isDemo, setIsDemo] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load weather forecast on mount or coordinates change
  useEffect(() => {
    fetchWeatherForecast();
  }, [coords.lat, coords.lon]);

  // Re-run agronomic and weather-risk evaluation when field conditions or forecast changes
  useEffect(() => {
    if (weatherForecast?.current) {
      const currentTemp = weatherForecast.current.temperature ?? 33.1;
      const currentHum = weatherForecast.current.humidity ?? 55;
      const rainForecast = weatherForecast.daily?.[0]?.precipitation_sum_mm ?? 5;
      fetchAdvisories(currentTemp, currentHum, rainForecast);
    } else {
      fetchAdvisories(33.1, 55, 5);
    }
  }, [crop, soilMoisture, daysSinceRain, weatherForecast]);

  const fetchWeatherForecast = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const forecastRes = await api.getWeatherForecast(coords.lat, coords.lon, 7);
      setWeatherForecast(forecastRes);
      if (forecastRes.location) {
        setLocationName(forecastRes.location);
      }
      setIsDemo(forecastRes.isDemo || false);
    } catch (err: any) {
      console.error('Failed to fetch weather forecast:', err);
      setErrorMessage(`Weather Service Notice: ${err.message || String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdvisories = async (temp: number, hum: number, rainSum: number) => {
    try {
      const [irrigRes, riskRes] = await Promise.all([
        api.recommendIrrigation(crop, soilMoisture, daysSinceRain),
        api.assessWeatherRisk(temp, hum, rainSum)
      ]);
      setIrrigationData(irrigRes.data);
      setRiskData(riskRes.data);
    } catch (err: any) {
      console.error('Failed to calculate agronomic advisory:', err);
    }
  };

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        const lat = Math.round(pos.coords.latitude * 10000) / 10000;
        const lon = Math.round(pos.coords.longitude * 10000) / 10000;
        setCoords({ lat, lon });
        setLocationName(`Farm Field (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)`);
      },
      (err) => {
        setLocating(false);
        setErrorMessage(`GPS Permission / Location error: ${err.message}`);
      },
      { timeout: 8000 }
    );
  };

  const curr = weatherForecast?.current || {};
  const daily = weatherForecast?.daily || [];
  const hourly = weatherForecast?.hourly || [];
  const advisory = weatherForecast?.agricultural_advisory || {};

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <WorkflowStepper currentStageId={3} />

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Irrigation &amp; Climate</h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Advisory Data
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                Live Agro-Climate Integration
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">Multi-day agro-meteorological forecast and field irrigation decision support.</p>
        </div>

        {/* Location selector / GPS button */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleUseMyLocation}
            disabled={locating}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#F2E8D5] hover:bg-[#E5DDCF] text-[#103D2C] text-xs font-bold rounded-xl border border-[#E5DDCF] transition-colors"
          >
            {locating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Compass className="w-3.5 h-3.5" />}
            <span>Use Field GPS</span>
          </button>
          <button
            onClick={fetchWeatherForecast}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-[#FBF7EF] text-[#103D2C] text-xs font-bold rounded-xl border border-[#E5DDCF] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
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
          {/* WEATHER SOURCE DISCLOSURE */}
          <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 text-xs text-amber-900 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <strong>Meteorological Source:</strong> {curr.data_source || 'Open-Meteo Ensemble'}<br />
              <strong>Legal Attribution:</strong> {curr.attribution || weatherForecast?.attribution || 'Weather data by Open-Meteo.com (CC BY 4.0)'}<br />
              <strong>On-Farm Cumulative Rain:</strong> <em>Unavailable</em> (Requires automated rain gauge).
            </div>
            <div className="shrink-0 flex items-center gap-2">
              {curr.is_stale && (
                <span className="bg-red-200 text-red-900 font-bold px-2 py-0.5 rounded text-[10px] uppercase">Stale Cache</span>
              )}
              <span className="bg-emerald-200 text-emerald-900 font-bold px-2 py-0.5 rounded text-[10px] uppercase tracking-wider">
                {curr.provider || 'Live'}
              </span>
            </div>
          </div>

          {/* Current Observation Hero */}
          <div className="bg-[#103D2C] text-white rounded-3xl p-8 relative overflow-hidden">
            <div className="absolute right-0 top-0 bottom-0 opacity-10 pointer-events-none">
              <Sun className="w-64 h-64 -translate-y-10 translate-x-10" />
            </div>
            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-8">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Sun className="text-yellow-400" />
                  <span className="text-xl font-medium text-[#FBF7EF]">{curr.weather_condition || 'Partly Cloudy'}</span>
                </div>
                <div className="text-6xl font-bold font-serif mb-2">
                  {curr.temperature !== undefined && curr.temperature !== null ? `${curr.temperature}°C` : '33.1°C'}
                </div>
                <p className="text-[#A8C69A] flex items-center gap-1.5 text-xs">
                  <MapPin className="w-3.5 h-3.5 text-[#E5DDCF]" />
                  {locationName} (lat {coords.lat.toFixed(2)}, lon {coords.lon.toFixed(2)})
                </p>
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                <div>
                  <div className="text-[#A8C69A] text-xs">Humidity</div>
                  <div className="font-bold text-lg">{curr.humidity !== undefined ? `${curr.humidity}%` : '35%'}</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Wind</div>
                  <div className="font-bold text-lg">{curr.wind_speed_kmh !== undefined ? `${curr.wind_speed_kmh} km/h` : '5.7 km/h'}</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Rain Probability</div>
                  <div className="font-bold text-lg">{curr.rainfall_probability || '15%'}</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Reference ET0</div>
                  <div className="font-bold text-lg">{curr.reference_evapotranspiration_mm ? `${curr.reference_evapotranspiration_mm} mm/d` : '4.2 mm/d'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Hourly Forecast Strip */}
          {hourly.length > 0 && (
            <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5">
              <h3 className="font-bold text-[#103D2C] mb-3 text-sm flex items-center justify-between">
                <span>Hourly Forecast (Next 24h)</span>
                <span className="text-xs font-normal text-[#292B26]/60">Local Time (Asia/Kolkata)</span>
              </h3>
              <div className="flex justify-between items-center overflow-x-auto gap-4 custom-scrollbar pb-2">
                {hourly.slice(0, 12).map((h: any, idx: number) => {
                  const hourLabel = h.time ? h.time.split('T')[1]?.slice(0, 5) : `${idx * 2}:00`;
                  return (
                    <div key={idx} className="flex flex-col items-center gap-1.5 min-w-[55px] p-2 rounded-xl bg-[#FBF7EF] border border-[#E5DDCF]/50">
                      <span className="text-[11px] font-semibold text-[#292B26]/70">{hourLabel}</span>
                      {h.precipitation_probability && h.precipitation_probability > 30 ? (
                        <CloudRain className="text-blue-500 w-5 h-5" />
                      ) : (
                        <Sun className="text-amber-500 w-5 h-5" />
                      )}
                      <span className="text-xs font-bold text-[#103D2C]">{h.temperature ? Math.round(h.temperature) : 30}°</span>
                      <span className="text-[9px] text-[#292B26]/50">{h.precipitation_probability ?? 0}% rain</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 7-Day Daily Forecast */}
          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-4 flex items-center justify-between">
              <span>7-Day Agro-Meteorological Forecast</span>
              <span className="text-xs font-normal text-[#292B26]/60">Metric Units (°C, mm)</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3">
              {(daily.length > 0 ? daily : [
                { date: 'Mon', temperature_max: 34, temperature_min: 22, precipitation_probability_max: 10 },
                { date: 'Tue', temperature_max: 33, temperature_min: 21, precipitation_probability_max: 15 },
                { date: 'Wed', temperature_max: 31, temperature_min: 21, precipitation_probability_max: 45 },
                { date: 'Thu', temperature_max: 30, temperature_min: 20, precipitation_probability_max: 60 },
                { date: 'Fri', temperature_max: 32, temperature_min: 21, precipitation_probability_max: 20 },
                { date: 'Sat', temperature_max: 33, temperature_min: 22, precipitation_probability_max: 10 },
                { date: 'Sun', temperature_max: 34, temperature_min: 22, precipitation_probability_max: 5 }
              ]).map((d: any, i: number) => {
                const dayName = d.date.includes('-')
                  ? new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' })
                  : d.date;
                const isRainy = (d.precipitation_probability_max ?? 0) >= 40 || (d.precipitation_sum_mm ?? 0) > 2;

                return (
                  <div key={i} className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-[#FBF7EF] border border-[#E5DDCF]">
                    <span className="text-xs font-bold text-[#103D2C]">{dayName}</span>
                    {isRainy ? <CloudRain className="text-blue-500 w-6 h-6" /> : <Sun className="text-amber-500 w-6 h-6" />}
                    <div className="text-xs font-bold text-[#103D2C]">
                      {d.temperature_max !== undefined ? Math.round(d.temperature_max) : 32}°
                      <span className="text-[10px] font-normal text-[#292B26]/50 ml-1">
                        {d.temperature_min !== undefined ? Math.round(d.temperature_min) : 21}°
                      </span>
                    </div>
                    <span className="text-[10px] font-medium text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded">
                      {d.precipitation_probability_max ?? 0}%
                    </span>
                    {d.et0_fao_evapotranspiration_mm && (
                      <span className="text-[9px] text-[#292B26]/50">
                        ET: {d.et0_fao_evapotranspiration_mm}mm
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {advisory.advisory_notes && (
              <div className="mt-4 p-3 bg-[#F2E8D5]/60 rounded-xl border border-[#E5DDCF] text-xs text-[#103D2C]">
                <strong>Agro-Climatic Guidance: </strong>
                {advisory.advisory_notes.join(' ')}
                <div className="mt-1 text-[10px] text-[#292B26]/60 italic">
                  {advisory.disclaimer}
                </div>
              </div>
            )}
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
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${irrigationData.irrigation_required
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
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${riskData.overall_risk === 'High' ? 'bg-red-100 text-red-800' :
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
                <div className="text-[10px] text-[#292B26]/50 italic pt-1 border-t border-[#E5DDCF]/50">
                  Risk assessments are indicative heuristics based on forecasted temperature, humidity, and precipitation thresholds.
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <WorkflowFooter
        currentStageNumber={3}
        currentStageName="In-Season Crop Care"
        completedActionMessage="Irrigation advisory and climate risks evaluated! Proceed to leaf disease & pest diagnosis."
        prevStep={{ label: "Crop Planning", path: "/crop-recommendation" }}
        nextStep={{
          label: "Disease & Pest Detection",
          labelMr: "रोग व कीड नियंत्रण",
          path: "/disease",
          description: "Diagnose visual leaf symptoms and identify verified treatments"
        }}
        alternativeNextStep={{
          label: "AI Recommendations",
          path: "/recommendations"
        }}
      />
    </div>
  );
}
