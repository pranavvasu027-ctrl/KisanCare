import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  FlaskConical, Sprout, Store, ExternalLink, AlertTriangle,
  CheckCircle2, Info, Loader2, ArrowLeft, RefreshCw, ShoppingCart,
  MapPin, Phone, ShieldAlert, Sparkles, Scale
} from 'lucide-react';
import {
  api,
  FertilizerAdvisoryInput,
  FertilizerAdvisoryResult,
  FertilizerStoreItem,
  AmazonProductLinkItem
} from '../../services/api';

const CROPS_LIST = [
  { value: 'Corn', label: 'Corn (Maize) — Core Model Class' },
  { value: 'Potato', label: 'Potato — Core Model Class' },
  { value: 'Cabbage', label: 'Cabbage — Core Model Class' },
  { value: 'Coffee', label: 'Coffee (Green Beans) — Core Model Class' },
  { value: 'Soybean', label: 'Soybean — Indian Field Crop' },
  { value: 'Cotton', label: 'Cotton — Maharashtra Cash Crop' },
  { value: 'Tomato', label: 'Tomato — Horticultural Crop' },
  { value: 'Wheat', label: 'Wheat — Rabi Cereal' },
  { value: 'Rice', label: 'Rice (Paddy) — Kharif Cereal' },
  { value: 'Chilli', label: 'Chilli / Bell Pepper' },
  { value: 'Onion', label: 'Onion — Cash Crop' },
];

export default function FertilizerAdvisory() {
  const location = useLocation();
  const navigate = useNavigate();

  // Navigation state passed from disease scanning
  const navState = (location.state || {}) as { crop?: string; disease?: string; location?: string };

  const [crop, setCrop] = useState<string>(navState.crop || 'Corn');
  const [diseaseContext, setDiseaseContext] = useState<string | null>(navState.disease || null);
  const [fieldSize, setFieldSize] = useState<number>(1.0);
  const [targetYield, setTargetYield] = useState<number>(3600.0);

  // Soil parameters
  const [ph, setPh] = useState<number>(6.8);
  const [organicCarbon, setOrganicCarbon] = useState<number>(11.4);
  const [totalNitrogen, setTotalNitrogen] = useState<number>(1.2);
  const [availablePhosphorus, setAvailablePhosphorus] = useState<number>(2.0);
  const [exchangeablePotassium, setExchangeablePotassium] = useState<number>(3.0);
  const [soilMoisture, setSoilMoisture] = useState<number>(20.0);

  // Locality
  const [locality, setLocality] = useState<string>('Takli Bu');
  const [pinCode, setPinCode] = useState<string>('444001');
  const [district, setDistrict] = useState<string>('Akola');

  // Execution state
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<FertilizerAdvisoryResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Auto-run if routed from disease detection with crop
  useEffect(() => {
    if (navState.crop) {
      handleCalculate();
    }
  }, []);

  const handleLoadSampleSoilCard = () => {
    setPh(7.2);
    setOrganicCarbon(10.5);
    setTotalNitrogen(1.1);
    setAvailablePhosphorus(2.2);
    setExchangeablePotassium(3.4);
    setSoilMoisture(22.0);
    setLocality('Takli Bu');
    setPinCode('444001');
    setDistrict('Akola');
  };

  const handleCalculate = async () => {
    setLoading(true);
    setErrorMessage(null);

    const payload: FertilizerAdvisoryInput = {
      crop_name: crop,
      target_yield: Number(targetYield),
      field_size: Number(fieldSize),
      ph: Number(ph),
      organic_carbon: Number(organicCarbon),
      total_nitrogen: Number(totalNitrogen),
      available_phosphorus: Number(availablePhosphorus),
      exchangeable_potassium: Number(exchangeablePotassium),
      soil_moisture: Number(soilMoisture),
      locality: locality.trim() || undefined,
      pin_code: pinCode.trim() || undefined,
      district: district.trim() || undefined,
      disease_context: diseaseContext || undefined,
    };

    try {
      const response = await api.getFertilizerAdvisory(payload);
      setResult(response.data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to execute real fertilizer ML inference.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Fertilizer & Soil Nutrition</h1>
            <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
              <Sparkles size={12} /> Real ML Random Forest
            </span>
          </div>
          <p className="text-[#292B26]/70 mt-1">
            Soil-evidence nutrient forecasting, commercial dose formulation, and local store discovery.
          </p>
        </div>

        {diseaseContext && (
          <button
            onClick={() => navigate('/disease')}
            className="text-xs text-[#103D2C] hover:text-[#17643E] font-medium flex items-center gap-1.5 bg-[#FBF7EF] border border-[#E5DDCF] px-3 py-1.5 rounded-lg cursor-pointer transition-colors"
          >
            <ArrowLeft size={14} /> Back to Disease Scan
          </button>
        )}
      </div>

      {/* Disease Context Banner (if routed from disease scan) */}
      {diseaseContext && (
        <div className="bg-amber-50 border border-amber-300 text-amber-900 p-4 rounded-xl text-xs flex items-start gap-3 shadow-xs">
          <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-sm block">Pre-filled from Recent Leaf Pathology Scan:</span>
            <p className="leading-relaxed">
              Detected Condition: <strong>{diseaseContext}</strong> for crop <strong>{crop}</strong>.
            </p>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              <strong>Clinical Guardrail:</strong> Soil nutrition and disease treatment are independent operations. Applying fertilizers does not cure fungal or viral foliar infections; ensure separate CIB&RC or IPM controls are maintained as diagnosed.
            </p>
          </div>
        </div>
      )}

      {/* Main Grid: Inputs (Left) and Results (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Soil & Farm Inputs */}
        <div className="lg:col-span-5 bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 space-y-4">
          <div className="flex justify-between items-center border-b border-[#E5DDCF]/60 pb-3">
            <h3 className="font-bold text-[#103D2C] flex items-center gap-2 text-sm uppercase tracking-wider">
              <FlaskConical size={16} className="text-[#17643E]" /> Soil & Field Parameters
            </h3>
            <button
              type="button"
              onClick={handleLoadSampleSoilCard}
              className="text-[11px] text-[#17643E] hover:underline font-semibold cursor-pointer"
            >
              Load Akola Sample Soil Data
            </button>
          </div>

          <div className="space-y-3">
            {/* Crop Selector */}
            <div>
              <label className="text-xs font-semibold text-[#292B26] block mb-1">
                Target Crop <span className="text-red-500">*</span>
              </label>
              <select
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-[#E5DDCF] bg-[#FBF7EF] focus:ring-1 focus:ring-[#103D2C] outline-hidden cursor-pointer"
              >
                {CROPS_LIST.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Target Yield & Field Size */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-[#292B26] block mb-1">
                  Field Area (ha)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={fieldSize}
                  onChange={(e) => setFieldSize(parseFloat(e.target.value) || 1.0)}
                  className="w-full text-xs p-2 rounded-lg border border-[#E5DDCF] bg-[#FBF7EF]"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#292B26] block mb-1">
                  Target Yield (kg/ha)
                </label>
                <input
                  type="number"
                  step="100"
                  min="500"
                  value={targetYield}
                  onChange={(e) => setTargetYield(parseFloat(e.target.value) || 3500.0)}
                  className="w-full text-xs p-2 rounded-lg border border-[#E5DDCF] bg-[#FBF7EF]"
                />
              </div>
            </div>

            {/* Soil Health Card Measurements */}
            <div className="pt-2 border-t border-[#E5DDCF]/60">
              <span className="text-[11px] font-bold text-[#103D2C] uppercase tracking-wider block mb-2">
                Soil Health Card (SHC) Lab Values:
              </span>
              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div>
                  <label className="text-[11px] font-medium text-[#292B26]/80 block">Soil pH (water)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="3.0"
                    max="11.0"
                    value={ph}
                    onChange={(e) => setPh(parseFloat(e.target.value) || 7.0)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-[#292B26]/80 block">Organic Carbon (g/kg)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={organicCarbon}
                    onChange={(e) => setOrganicCarbon(parseFloat(e.target.value) || 0)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-[#292B26]/80 block">Total Nitrogen (g/kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={totalNitrogen}
                    onChange={(e) => setTotalNitrogen(parseFloat(e.target.value) || 0)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-[#292B26]/80 block">Avail. Phosphorus (mg/kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={availablePhosphorus}
                    onChange={(e) => setAvailablePhosphorus(parseFloat(e.target.value) || 0)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-[#292B26]/80 block">Exch. Potassium (mmol/kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={exchangeablePotassium}
                    onChange={(e) => setExchangeablePotassium(parseFloat(e.target.value) || 0)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-[#292B26]/80 block">Soil Moisture (%)</label>
                  <input
                    type="number"
                    step="1"
                    min="0"
                    max="100"
                    value={soilMoisture}
                    onChange={(e) => setSoilMoisture(parseFloat(e.target.value) || 20)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
              </div>
            </div>

            {/* Locality Matching */}
            <div className="pt-2 border-t border-[#E5DDCF]/60">
              <span className="text-[11px] font-bold text-[#103D2C] uppercase tracking-wider block mb-2 flex items-center gap-1">
                <MapPin size={13} className="text-[#17643E]" /> Farmer Locality (Store Matching):
              </span>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-[10px] font-medium text-[#292B26]/70 block">District</label>
                  <input
                    type="text"
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-medium text-[#292B26]/70 block">Village/Town</label>
                  <input
                    type="text"
                    value={locality}
                    onChange={(e) => setLocality(e.target.value)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-medium text-[#292B26]/70 block">PIN Code</label>
                  <input
                    type="text"
                    value={pinCode}
                    onChange={(e) => setPinCode(e.target.value)}
                    className="w-full text-xs p-1.5 rounded-md border border-[#E5DDCF] bg-[#FBF7EF]"
                  />
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleCalculate}
              disabled={loading}
              className="w-full mt-4 bg-[#103D2C] text-white py-2.5 rounded-xl font-bold text-xs hover:bg-[#17643E] transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Evaluating Random Forest Regressors...</span>
                </>
              ) : (
                <>
                  <Scale size={15} />
                  <span>Calculate Real ML Fertilizer Dosage</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Advisory Outputs, Retailers & Amazon */}
        <div className="lg:col-span-7 space-y-6">
          {errorMessage && (
            <div className="bg-red-50 border border-red-300 text-red-900 p-4 rounded-xl text-xs flex items-start gap-2">
              <ShieldAlert className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">Model Evaluation Failed</span>
                <p>{errorMessage}</p>
              </div>
            </div>
          )}

          {loading ? (
            <div className="bg-white rounded-2xl border border-[#E5DDCF] p-12 text-center flex flex-col items-center justify-center min-h-[380px]">
              <Loader2 className="w-10 h-10 text-[#17643E] animate-spin mb-3" />
              <h4 className="font-bold text-[#103D2C] text-base">Running Scikit-Learn Model Inference</h4>
              <p className="text-xs text-[#292B26]/60 mt-1 max-w-sm">
                Transforming soil chemistry vectors through ColumnTransformer and evaluating 10 Random Forest regression targets (DNgigi/FertiliserApplication)...
              </p>
            </div>
          ) : result ? (
            <div className="space-y-6">
              {/* Regional Limitation & Validation Notice */}
              <div className="bg-amber-50/80 border border-amber-300 text-amber-900 p-3.5 rounded-xl text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-amber-950">
                  <AlertTriangle size={15} className="text-amber-700" />
                  <span>Experimental Status & Agricultural Disclaimer:</span>
                </div>
                <p className="text-[11px] leading-relaxed text-amber-900/90">
                  {result.validation_notice}
                </p>
                <div className="text-[10px] text-amber-800 font-mono mt-1 pt-1 border-t border-amber-200">
                  Model: {result.model_identifier} (SHA: {result.model_revision.substring(0, 8)})
                </div>
              </div>

              {/* Warnings from model adapter (e.g. crop out of distribution or alkaline vertisol) */}
              {result.warnings && result.warnings.length > 0 && (
                <div className="bg-neutral-50 border border-neutral-300 p-3 rounded-xl text-xs space-y-1">
                  <span className="font-bold text-[#103D2C] block">Model Observations:</span>
                  <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-[#292B26]/80">
                    {result.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Predicted Pure Nutrient Requirements */}
              <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 shadow-xs space-y-3">
                <h4 className="font-bold text-[#103D2C] text-sm uppercase tracking-wider flex items-center gap-2">
                  <Sparkles size={16} className="text-[#17643E]" /> Real ML Predicted Nutrient Requirements
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {result.nutrient_requirements.map((nr, idx) => (
                    <div key={idx} className="bg-[#FBF7EF] p-3 rounded-xl border border-[#E5DDCF] space-y-1">
                      <span className="text-[11px] font-bold text-[#292B26]/70 block">{nr.nutrient}</span>
                      <div className="text-xl font-bold text-[#103D2C]">
                        {nr.quantity} <span className="text-xs font-normal text-[#292B26]/60">{nr.unit}</span>
                      </div>
                      {nr.application_stage && (
                        <span className="text-[10px] text-[#17643E] font-medium block leading-tight">
                          {nr.application_stage}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Commercial Fertilizer Formulations */}
              {result.commercial_recommendations && result.commercial_recommendations.length > 0 && (
                <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 shadow-xs space-y-3">
                  <h4 className="font-bold text-[#103D2C] text-sm uppercase tracking-wider flex items-center gap-2">
                    <Scale size={16} className="text-[#17643E]" /> Commercial Product Formulations
                  </h4>
                  <div className="space-y-2.5">
                    {result.commercial_recommendations.map((cr, idx) => (
                      <div key={idx} className="bg-[#FBF7EF] p-3 rounded-xl border border-[#E5DDCF] flex flex-col sm:flex-row justify-between sm:items-center gap-2 text-xs">
                        <div>
                          <span className="font-bold text-sm text-[#103D2C] block">{cr.fertilizer_name}</span>
                          <span className="text-[11px] text-[#292B26]/60 block">{cr.grade} • {cr.application_timing}</span>
                        </div>
                        <div className="text-right sm:shrink-0 bg-white px-3 py-1.5 rounded-lg border border-[#E5DDCF]">
                          <span className="text-base font-bold text-[#B6532A]">{cr.dose_kg_ha} kg/ha</span>
                          <span className="text-[10px] text-[#292B26]/60 block">~{cr.bags_50kg_per_ha} bags/ha</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Local Demo Stores Discovery */}
              <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 shadow-xs space-y-4">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-[#103D2C] text-sm uppercase tracking-wider flex items-center gap-2">
                    <Store size={16} className="text-[#17643E]" /> Nearby Fertilizer Retailers (Demo Catalog)
                  </h4>
                  <span className="bg-neutral-100 text-[#292B26]/70 text-[10px] px-2 py-0.5 rounded font-mono">
                    Locality: {district}
                  </span>
                </div>

                <div className="space-y-3">
                  {result.matching_local_stores.map((store) => (
                    <div key={store.store_id} className="border border-[#E5DDCF] rounded-xl p-3.5 bg-[#FBF7EF]/50 space-y-2">
                      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-[#103D2C]">{store.store_name}</span>
                            <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                              store.locality_match_level === 'same_village' ? 'bg-emerald-100 text-emerald-800' :
                              store.locality_match_level === 'same_pincode' ? 'bg-blue-100 text-blue-800' :
                              'bg-amber-100 text-amber-800'
                            }`}>
                              {store.locality_match_level.replace('_', ' ')}
                            </span>
                          </div>
                          <span className="text-[11px] text-[#292B26]/70 block mt-0.5">
                            {store.address}, {store.village}, {store.district} - {store.pin_code}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-[#17643E] font-medium">
                          <Phone size={12} />
                          <span>{store.contact_phone}</span>
                        </div>
                      </div>

                      {/* Store Products */}
                      <div className="pt-2 border-t border-[#E5DDCF]/50 flex flex-wrap gap-2 text-[11px]">
                        {store.available_products.map((p, i) => (
                          <div key={i} className="bg-white px-2.5 py-1 rounded-md border border-[#E5DDCF] flex items-center gap-2">
                            <span className="font-medium text-[#292B26]">{p.product_name}</span>
                            <span className="font-bold text-[#103D2C]">₹{p.mock_price_inr}</span>
                            <span className="text-[9px] text-[#292B26]/50">({p.unit})</span>
                          </div>
                        ))}
                      </div>

                      <div className="text-[10px] italic text-[#292B26]/50">
                        {store.disclaimer}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Amazon.in Direct Product Search Discovery */}
              {result.amazon_discovery && result.amazon_discovery.length > 0 && (
                <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 shadow-xs space-y-3">
                  <div className="flex justify-between items-center">
                    <h4 className="font-bold text-[#103D2C] text-sm uppercase tracking-wider flex items-center gap-2">
                      <ShoppingCart size={16} className="text-[#17643E]" /> Online Product Discovery (Amazon.in)
                    </h4>
                    <span className="text-[10px] text-[#292B26]/60">Verified Direct Search Links</span>
                  </div>

                  <p className="text-[11px] text-[#292B26]/70 leading-relaxed">
                    Official Creators API credentials are kept server-side; when live APIs are unconfigured, direct search query links to Amazon.in agricultural supplies are provided. No artificial prices or simulated stock are claimed.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                    {result.amazon_discovery.map((item, idx) => (
                      <a
                        key={idx}
                        href={item.amazon_search_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-3 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-xl flex justify-between items-center gap-2 text-xs transition-colors cursor-pointer group"
                      >
                        <div>
                          <span className="font-bold text-[#103D2C] group-hover:text-[#17643E] block">
                            {item.product_name}
                          </span>
                          <span className="text-[10px] text-[#292B26]/60 block">
                            Search: &ldquo;{item.search_query}&rdquo;
                          </span>
                        </div>
                        <ExternalLink size={14} className="text-[#17643E] shrink-0" />
                      </a>
                    ))}
                  </div>

                  <div className="text-[10px] text-[#292B26]/50 italic pt-1">
                    Notice: Prices, delivery fees, and stock on Amazon.in fluctuate. Always check seller reputation, formulation purity, and delivery estimates before placing orders.
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-[#E5DDCF] p-12 text-center flex flex-col items-center justify-center min-h-[380px]">
              <Sprout className="w-12 h-12 text-[#A8C69A] mb-3" />
              <h4 className="font-bold text-[#103D2C] text-base">Awaiting Soil Parameters</h4>
              <p className="text-xs text-[#292B26]/60 max-w-sm mt-1">
                Enter your target crop, yield expectation, and Soil Health Card lab parameters on the left to compute real ML fertilizer recommendations and discover matching local Krishi Kendras.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
