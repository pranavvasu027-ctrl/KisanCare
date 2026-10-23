import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Sparkles, 
  Sprout, 
  Layers, 
  Droplet, 
  Wallet, 
  ShieldAlert, 
  TrendingUp, 
  Check, 
  Info, 
  Sliders, 
  Bookmark, 
  ArrowRight, 
  ExternalLink, 
  ChevronRight, 
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Activity,
  Thermometer,
  CloudRain,
  Wind,
  HelpCircle
} from 'lucide-react';
import { useFarm } from '../../context/FarmContext';
import { PageHeader } from '../../components/common/PageHeader';
import { RiskBadge, DataSourceLabel } from '../../components/common/StatusAndBadges';
import { cropRecommendationCatalog } from '../../data/mockData';
import { CropRecommendationItem, CropPredictionResponse } from '../../types';
import { apiService, ApiError } from '../../services/apiService';

// 35 Maharashtra Districts supported by Model 2
const MAHARASHTRA_DISTRICTS = [
  'Ahilyanagar', 'Akola', 'Amravati', 'Beed', 'Bhandara', 'Buldhana',
  'Chandrapur', 'Chhatrapati Sambhajinagar', 'Dharashiv', 'Dhule',
  'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 'Kolhapur',
  'Latur', 'Mumbai suburban', 'Nagpur', 'Nanded', 'Nandurbar', 'Nashik',
  'Palghar', 'Parbhani', 'Pune', 'Raigad', 'Ratnagiri', 'Sangli',
  'Satara', 'Sindhudurg', 'Solapur', 'Thane', 'Wardha', 'Washim', 'Yavatmal'
];

export const CropRecommendationPage: React.FC = () => {
  const { activeFarm, activeField, historicalRecords, formatCurrency } = useFarm();
  const navigate = useNavigate();

  // Form Inputs
  const [selectedFieldId, setSelectedFieldId] = useState(activeField.id);
  const currentSelectedField = activeFarm.fields.find(f => f.id === selectedFieldId) || activeField;

  // Seven Model 1 Numerical Soil/Climate Inputs
  const [nitrogen, setNitrogen] = useState(currentSelectedField.nitrogenKgHa.toString());
  const [phosphorus, setPhosphorus] = useState(currentSelectedField.phosphorusKgHa.toString());
  const [potassium, setPotassium] = useState(currentSelectedField.potassiumKgHa.toString());
  const [soilPh, setSoilPh] = useState(currentSelectedField.soilPh.toString());
  const [seasonalRainfall, setSeasonalRainfall] = useState('720');
  const [temperature, setTemperature] = useState('26.0');
  const [humidity, setHumidity] = useState('70.0');

  // Categorical and Location Dimensions
  const [district, setDistrict] = useState(activeFarm.district || 'Nashik');
  const [season, setSeason] = useState<'Kharif' | 'Rabi' | 'Summer' | 'Whole Year'>('Kharif');
  const [waterAccess, setWaterAccess] = useState('Farm Pond + Drip');
  const [model1Weight, setModel1Weight] = useState('0.60');

  // Input Validation Errors
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // State
  const [isRecomputing, setIsRecomputing] = useState(false);
  const [recommendations, setRecommendations] = useState<CropRecommendationItem[]>(cropRecommendationCatalog);
  const [selectedCropModal, setSelectedCropModal] = useState<CropRecommendationItem | null>(null);
  const [recordedChoice, setRecordedChoice] = useState<string | null>(null);
  const [apiResult, setApiResult] = useState<CropPredictionResponse | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const validateAllInputs = (): boolean => {
    const errors: Record<string, string> = {};
    const n = parseFloat(nitrogen);
    const p = parseFloat(phosphorus);
    const k = parseFloat(potassium);
    const ph = parseFloat(soilPh);
    const rain = parseFloat(seasonalRainfall);
    const temp = parseFloat(temperature);
    const hum = parseFloat(humidity);

    if (isNaN(n) || n < 0 || n > 300) errors.nitrogen = 'Nitrogen must be between 0 and 300 kg/ha';
    if (isNaN(p) || p < 0 || p > 300) errors.phosphorus = 'Phosphorus must be between 0 and 300 kg/ha';
    if (isNaN(k) || k < 0 || k > 300) errors.potassium = 'Potassium must be between 0 and 300 kg/ha';
    if (isNaN(ph) || ph < 3.5 || ph > 9.5) errors.soilPh = 'Soil pH must be between 3.5 and 9.5';
    if (isNaN(rain) || rain < 20 || rain > 3000) errors.rainfall = 'Rainfall must be between 20 and 3000 mm';
    if (isNaN(temp) || temp < 5 || temp > 50) errors.temperature = 'Temperature must be between 5 and 50 °C';
    if (isNaN(hum) || hum < 10 || hum > 100) errors.humidity = 'Humidity must be between 10% and 100%';

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleRunRecommendation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateAllInputs()) {
      return;
    }

    setIsRecomputing(true);
    setApiError(null);

    try {
      const pastCrop = historicalRecords.find(h => h.fieldId === currentSelectedField.id)?.crop;
      
      // Connect to authentic backend endpoint with all seven model features and regional dimensions
      const res = await apiService.predictCrop({
        N: parseFloat(nitrogen),
        P: parseFloat(phosphorus),
        K: parseFloat(potassium),
        ph: parseFloat(soilPh),
        rainfall: parseFloat(seasonalRainfall),
        temperature: parseFloat(temperature),
        humidity: parseFloat(humidity),
        state: activeFarm.state || 'Maharashtra',
        district: district,
        season: season,
        water_access: waterAccess,
        w_model1: parseFloat(model1Weight) || 0.60,
        current_crop: currentSelectedField.currentCrop,
        prev_crop_1: pastCrop,
        top_k: 5,
      });

      setApiResult(res);

      // Re-order local catalog prioritizing predictions returned from authentic ML model
      if (res.prediction) {
        const updated = [...cropRecommendationCatalog].sort((a, b) => {
          if (a.crop.toLowerCase().includes(res.prediction.toLowerCase())) return -1;
          if (b.crop.toLowerCase().includes(res.prediction.toLowerCase())) return 1;
          return b.suitabilityScore - a.suitabilityScore;
        });
        setRecommendations(updated);
      }
    } catch (err: any) {
      console.warn('Backend crop recommendation call failed:', err);
      const msg = err instanceof ApiError ? err.detail : err.message || 'Crop recommendation endpoint unavailable';
      setApiError(msg);
    } finally {
      setIsRecomputing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Crop Selection Advisory"
        subtitle="Multi-model agronomic recommendation combining Hugging Face Random Forest soil/climate classifier with 26-year Maharashtra regional viability data."
        tag="HUGGING FACE MODEL INTEGRATED"
        bannerImage="https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=1600&auto=format&fit=crop&q=80"
      />

      {/* Model Architecture & Attribution Banner */}
      <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs space-y-1.5 text-emerald-950">
        <div className="flex flex-wrap items-center justify-between gap-2 font-bold text-emerald-950">
          <div className="flex items-center gap-2">
            <Cpu size={16} className="text-emerald-700 shrink-0" />
            <span>Active Model: Sheshank2609/crop-recommendation-system (Revision: f24d6e1 • MIT License)</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-mono font-bold">
            Live Inference
          </span>
        </div>
        <p className="text-[11px] leading-relaxed text-emerald-900">
          Inference executes live on <code className="bg-white/80 px-1 py-0.5 rounded text-emerald-950 font-mono">POST /api/v1/crop-recommendation</code>. Combines <strong>Model 1 (Random Forest Classifier)</strong> predicting class probabilities from 7 soil/climate features with <strong>Model 2 (26-Year Regional Scorer)</strong> covering 35 Maharashtra districts across 4 seasons.
        </p>
      </div>

      {apiError && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs flex items-start justify-between text-red-900">
          <div className="flex items-start gap-2">
            <AlertTriangle size={16} className="text-red-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block">Inference Error / Service Notice:</span>
              <span>{apiError}</span>
              <p className="text-[10px] text-red-700 mt-1">
                Please verify that the FastAPI backend is running and that all 7 soil and climate inputs fall within verified physical bounds.
              </p>
            </div>
          </div>
          <button onClick={() => setApiError(null)} className="font-bold underline ml-2 shrink-0">Dismiss</button>
        </div>
      )}

      {/* Live Model Output Display */}
      {apiResult && (
        <div className="p-5 rounded-2xl bg-white border border-forest/30 card-shadow text-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-mint flex items-center justify-center text-forest">
                <Sparkles size={18} />
              </div>
              <div>
                <span className="text-[11px] font-bold text-farm-muted uppercase tracking-wider block">Hugging Face Model Result</span>
                <span className="text-base font-extrabold text-forest-dark capitalize">
                  Optimal Recommendation: {apiResult.prediction}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {apiResult.is_demo ? (
                <span className="text-xs px-2.5 py-1 rounded-lg bg-amber-100 text-amber-900 font-extrabold border border-amber-300">
                  DEMO FALLBACK ACTIVE
                </span>
              ) : (
                <span className="text-xs px-2.5 py-1 rounded-lg bg-mint text-forest-dark font-extrabold border border-green-200">
                  Combined Score: {typeof (apiResult.combined_score ?? apiResult.final_score) === 'number' ? `${(((apiResult.combined_score ?? apiResult.final_score) as number) * 100).toFixed(1)}%` : 'Evaluated'}
                </span>
              )}
              <span className="text-xs px-2.5 py-1 rounded-lg bg-gray-100 text-farm-text font-bold">
                {apiResult.model_source || 'Hugging Face RF + Regional'}
              </span>
            </div>
          </div>

          {/* Model Warnings / Transparent Advisories */}
          {apiResult.warnings && apiResult.warnings.length > 0 && (
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 space-y-1">
              <span className="font-bold text-[11px] uppercase tracking-wider flex items-center gap-1">
                <AlertTriangle size={14} className="text-amber-700" />
                Agronomic Advisories & Transparent Constraints
              </span>
              <ul className="list-disc list-inside text-[11px] space-y-0.5">
                {apiResult.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Soil Test NPK Status */}
          {apiResult.soil_test_npk_status && (
            <div className="grid grid-cols-3 gap-3 bg-farm-bg p-3 rounded-xl border border-farm-border">
              <div>
                <span className="text-[10px] text-farm-muted block uppercase font-bold">Nitrogen (N)</span>
                <span className="font-extrabold text-farm-text capitalize">{apiResult.soil_test_npk_status.N} Adequacy</span>
              </div>
              <div>
                <span className="text-[10px] text-farm-muted block uppercase font-bold">Phosphorus (P)</span>
                <span className="font-extrabold text-farm-text capitalize">{apiResult.soil_test_npk_status.P} Adequacy</span>
              </div>
              <div>
                <span className="text-[10px] text-farm-muted block uppercase font-bold">Potassium (K)</span>
                <span className="font-extrabold text-farm-text capitalize">{apiResult.soil_test_npk_status.K} Adequacy</span>
              </div>
            </div>
          )}

          {/* Ranked ML Recommendations from Model */}
          {apiResult.recommendations && apiResult.recommendations.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-farm-text block uppercase tracking-wider">
                  Ranked Candidates & Sub-Score Decomposition
                </span>
                <span className="text-[10px] text-farm-muted">
                  Weighted formula: 60% Soil/Climate RF Probability + 40% Regional Viability
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {apiResult.recommendations.slice(0, 3).map((rec, idx) => (
                  <div key={rec.crop} className="p-3 rounded-xl border border-farm-border bg-pale/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-sm text-farm-text capitalize">
                          #{rec.rank || idx + 1} {rec.crop}
                        </span>
                        {rec.region_suitability && (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-extrabold ${
                            rec.region_suitability.includes('High')
                              ? 'bg-emerald-100 text-emerald-800'
                              : rec.region_suitability.includes('Mod')
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}>
                            {rec.region_suitability}
                          </span>
                        )}
                      </div>
                      <span className="font-extrabold text-forest text-sm">
                        {((rec.combined_score ?? rec.final_score) * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-1 text-[10px] text-center pt-1 border-t border-gray-200">
                      <div className="bg-white p-1.5 rounded">
                        <span className="text-farm-muted block text-[9px]">Model 1: NPK Probability</span>
                        <span className="font-bold text-farm-text">{((rec.npk_score ?? rec.soil_climate_score) * 100).toFixed(1)}%</span>
                      </div>
                      <div className="bg-white p-1.5 rounded">
                        <span className="text-farm-muted block text-[9px]">Model 2: Regional Viability</span>
                        <span className="font-bold text-farm-text">{(rec.regional_score * 100).toFixed(1)}%</span>
                      </div>
                    </div>

                    {rec.grown_pct_of_years !== undefined && rec.grown_pct_of_years > 0 && (
                      <div className="flex items-center justify-between text-[10px] text-farm-muted px-1">
                        <span>Grown in {rec.grown_pct_of_years}% of years</span>
                        {rec.avg_yield_t_ha ? <span>Avg: {rec.avg_yield_t_ha} T/Ha</span> : null}
                      </div>
                    )}

                    {rec.water_constrained && (
                      <div className="p-1.5 rounded bg-amber-100/70 border border-amber-300 text-[10px] text-amber-900 font-semibold flex items-center gap-1">
                        <Droplet size={12} className="text-blue-600 shrink-0" />
                        <span>High water demand; irrigation required</span>
                      </div>
                    )}

                    <p className="text-[11px] text-farm-muted leading-tight line-clamp-2">
                      {rec.reason}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Parameters Form (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white rounded-2xl border border-farm-border p-5 card-shadow">
            <h3 className="text-base font-bold text-farm-text mb-1">Agronomic Input Form</h3>
            <p className="text-xs text-farm-muted mb-4">Review and adjust all 7 model inputs and regional dimensions</p>

            <form onSubmit={handleRunRecommendation} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-farm-text mb-1">Select Farm Plot *</label>
                <select
                  value={selectedFieldId}
                  onChange={(e) => {
                    setSelectedFieldId(e.target.value);
                    const f = activeFarm.fields.find(field => field.id === e.target.value);
                    if (f) {
                      setNitrogen(f.nitrogenKgHa.toString());
                      setPhosphorus(f.phosphorusKgHa.toString());
                      setPotassium(f.potassiumKgHa.toString());
                      setSoilPh(f.soilPh.toString());
                    }
                  }}
                  className="w-full px-3 py-2 border border-farm-border rounded-xl font-bold text-farm-text bg-farm-bg"
                >
                  {activeFarm.fields.map(f => (
                    <option key={f.id} value={f.id}>
                      {f.name} ({f.currentCrop} • {f.areaAcres} Ac)
                    </option>
                  ))}
                </select>
              </div>

              {/* District & Season Selection */}
              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="block font-semibold text-farm-text mb-1">District (MH) *</label>
                  <select
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-farm-border rounded-xl bg-farm-bg font-semibold"
                  >
                    {MAHARASHTRA_DISTRICTS.map(d => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-farm-text mb-1">Season *</label>
                  <select
                    value={season}
                    onChange={(e) => setSeason(e.target.value as any)}
                    className="w-full px-2.5 py-1.5 border border-farm-border rounded-xl bg-farm-bg font-semibold"
                  >
                    <option value="Kharif">Kharif (Monsoon)</option>
                    <option value="Rabi">Rabi (Winter)</option>
                    <option value="Summer">Summer (Zaid)</option>
                    <option value="Whole Year">Whole Year (Perennial)</option>
                  </select>
                </div>
              </div>

              {/* Water Access */}
              <div>
                <label className="block font-semibold text-farm-text mb-1">Irrigation Infrastructure</label>
                <select
                  value={waterAccess}
                  onChange={(e) => setWaterAccess(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-farm-border rounded-xl bg-farm-bg"
                >
                  <option value="Farm Pond + Drip">Farm Pond + Drip Irrigation</option>
                  <option value="Borewell Only">Borewell (Moderate Water)</option>
                  <option value="Canal Seasonal">Canal Seasonal Gravity</option>
                  <option value="Strictly Rainfed">Strictly Rainfed (Dryland)</option>
                </select>
              </div>

              {/* Soil Test Chemistry (N, P, K, pH) */}
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-farm-text text-[11px] uppercase tracking-wider">
                    Soil Nutrients & Chemistry
                  </span>
                  <span className="text-[10px] text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded font-bold">
                    Lab Soil Test (0-300)
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-farm-muted text-[10px]">Nitrogen (N)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="300"
                      value={nitrogen}
                      onChange={(e) => setNitrogen(e.target.value)}
                      className="w-full px-2 py-1 border border-farm-border rounded-lg text-center font-bold"
                    />
                    {validationErrors.nitrogen && (
                      <span className="text-[9px] text-red-600 block">{validationErrors.nitrogen}</span>
                    )}
                  </div>
                  <div>
                    <label className="block text-farm-muted text-[10px]">Phosphorus (P)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="300"
                      value={phosphorus}
                      onChange={(e) => setPhosphorus(e.target.value)}
                      className="w-full px-2 py-1 border border-farm-border rounded-lg text-center font-bold"
                    />
                    {validationErrors.phosphorus && (
                      <span className="text-[9px] text-red-600 block">{validationErrors.phosphorus}</span>
                    )}
                  </div>
                  <div>
                    <label className="block text-farm-muted text-[10px]">Potassium (K)</label>
                    <input
                      type="number"
                      step="1"
                      min="0"
                      max="300"
                      value={potassium}
                      onChange={(e) => setPotassium(e.target.value)}
                      className="w-full px-2 py-1 border border-farm-border rounded-lg text-center font-bold"
                    />
                    {validationErrors.potassium && (
                      <span className="text-[9px] text-red-600 block">{validationErrors.potassium}</span>
                    )}
                  </div>
                </div>

                <div className="mt-2">
                  <label className="block font-semibold text-farm-text text-[11px] mb-1">Soil pH Level (3.5 – 9.5)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="3.5"
                    max="9.5"
                    value={soilPh}
                    onChange={(e) => setSoilPh(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-farm-border rounded-xl font-bold"
                  />
                  {validationErrors.soilPh && (
                    <span className="text-[9px] text-red-600 block">{validationErrors.soilPh}</span>
                  )}
                </div>
              </div>

              {/* Climate & Weather (Rainfall, Temp, Humidity) */}
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-farm-text text-[11px] uppercase tracking-wider">
                    Climate & Weather Parameters
                  </span>
                  <span className="text-[10px] text-blue-800 bg-blue-50 px-1.5 py-0.5 rounded font-bold">
                    Telemetry / Estimates
                  </span>
                </div>

                <div className="space-y-2">
                  <div>
                    <label className="block text-farm-muted text-[10px]">Expected Rainfall (20 - 3000 mm)</label>
                    <input
                      type="number"
                      min="20"
                      max="3000"
                      value={seasonalRainfall}
                      onChange={(e) => setSeasonalRainfall(e.target.value)}
                      className="w-full px-2.5 py-1.5 border border-farm-border rounded-xl font-semibold"
                    />
                    {validationErrors.rainfall && (
                      <span className="text-[9px] text-red-600 block">{validationErrors.rainfall}</span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-farm-muted text-[10px]">Mean Temp (5 - 50 °C)</label>
                      <input
                        type="number"
                        step="0.5"
                        min="5"
                        max="50"
                        value={temperature}
                        onChange={(e) => setTemperature(e.target.value)}
                        className="w-full px-2 py-1 border border-farm-border rounded-lg text-center font-bold"
                      />
                      {validationErrors.temperature && (
                        <span className="text-[9px] text-red-600 block">{validationErrors.temperature}</span>
                      )}
                    </div>
                    <div>
                      <label className="block text-farm-muted text-[10px]">Humidity (10 - 100 %)</label>
                      <input
                        type="number"
                        step="1"
                        min="10"
                        max="100"
                        value={humidity}
                        onChange={(e) => setHumidity(e.target.value)}
                        className="w-full px-2 py-1 border border-farm-border rounded-lg text-center font-bold"
                      />
                      {validationErrors.humidity && (
                        <span className="text-[9px] text-red-600 block">{validationErrors.humidity}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Model Weight Slider */}
              <div className="pt-2 border-t border-gray-100">
                <div className="flex items-center justify-between text-[11px] font-bold text-farm-text mb-1">
                  <span>Model 1 vs Model 2 Weight</span>
                  <span>{(parseFloat(model1Weight) * 100).toFixed(0)}% NPK / {((1 - parseFloat(model1Weight)) * 100).toFixed(0)}% Regional</span>
                </div>
                <input
                  type="range"
                  min="0.20"
                  max="0.80"
                  step="0.05"
                  value={model1Weight}
                  onChange={(e) => setModel1Weight(e.target.value)}
                  className="w-full accent-forest cursor-pointer"
                />
              </div>

              <button
                type="submit"
                disabled={isRecomputing}
                className="w-full py-2.5 rounded-xl bg-forest hover:bg-forest-dark text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-60 shadow-xs"
              >
                <RefreshCw size={14} className={isRecomputing ? 'animate-spin' : ''} />
                <span>{isRecomputing ? 'Invoking Model Service...' : 'Analyze & Recommend Crops'}</span>
              </button>
            </form>
          </div>
        </div>

        {/* Right Recommended Crop Cards (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-gray-200">
            <div>
              <h3 className="text-base font-bold text-farm-text">
                Agronomic Recommendations & Catalog Matches ({district} • {season})
              </h3>
              <p className="text-xs text-farm-muted">
                Ranked by combined score: Model 1 Random Forest NPK probabilities + Model 2 Maharashtra 26-year regional suitability
              </p>
            </div>
            <span className="text-xs font-bold text-farm-muted">
              {recommendations.length} Candidate Crops
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((item, index) => {
              const isRecorded = recordedChoice === item.crop;
              return (
                <div
                  key={item.crop}
                  className={`bg-white rounded-2xl border p-5 card-shadow space-y-3 transition-all relative overflow-hidden ${
                    index === 0 ? 'border-2 border-forest/30 bg-pale/20' : 'border-farm-border'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-gray-100 text-farm-muted">
                          Rank #{index + 1}
                        </span>
                        <RiskBadge level={item.riskLevel} />
                      </div>
                      <h4 className="text-base font-bold text-farm-text mt-1">
                        {item.crop} ({item.cropMarathi})
                      </h4>
                    </div>

                    <div className="text-right">
                      <span className="text-xs text-farm-muted block">Suitability Match</span>
                      <span className="text-lg font-extrabold text-forest">{item.suitabilityScore}/100</span>
                    </div>
                  </div>

                  <p className="text-xs text-farm-muted leading-relaxed line-clamp-2">
                    {item.reasoning}
                  </p>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 text-xs">
                    <div>
                      <span className="text-farm-muted block text-[11px]">Est. Yield:</span>
                      <span className="font-bold text-farm-text">{item.expectedYieldQuintalAcre} Q/Ac</span>
                    </div>
                    <div>
                      <span className="text-farm-muted block text-[11px]">Water Need:</span>
                      <span className="font-bold text-farm-text">{item.waterRequirementMm} mm</span>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between gap-2">
                    <button
                      onClick={() => setSelectedCropModal(item)}
                      className="text-xs font-bold text-forest hover:text-forest-dark flex items-center gap-1"
                    >
                      <span>Full Agronomic Dossier</span>
                      <ChevronRight size={14} />
                    </button>
                    <button
                      onClick={() => setRecordedChoice(item.crop)}
                      className={`text-xs px-3 py-1.5 rounded-lg font-bold transition-colors ${
                        isRecorded
                          ? 'bg-mint text-forest-dark border border-green-300'
                          : 'bg-farm-bg text-farm-text hover:bg-gray-100 border border-farm-border'
                      }`}
                    >
                      {isRecorded ? 'Selected' : 'Select Crop'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
