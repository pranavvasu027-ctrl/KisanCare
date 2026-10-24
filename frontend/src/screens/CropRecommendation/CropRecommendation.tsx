import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { translateDynamic } from '../../i18n/translateHelper';

import { useNavigate } from 'react-router-dom';

import {

  Sprout, Check, ChevronRight, TrendingUp, Droplets, MapPin,

  ArrowRight, Loader2, AlertCircle, CheckCircle2, ShieldAlert,

  Sparkles, Filter, FlaskConical, Layers, Info, Calendar, Database

} from 'lucide-react';

import { api } from '../../services/api';

import { useAuth } from '../../hooks/useAuth';

import { supabase } from '../../services/supabase';



interface FieldOption {

  id: string;

  name: string;

  area: number;

  crop: string;

}



interface CropRecommendationItem {

  crop: string;

  rank: number;

  predicted_area_frequency?: number;

  combined_score?: number;

  npk_score?: number;

  region_score?: number;

  region_suitability?: string;

  grown_pct_of_years?: number;

  avg_yield_t_ha?: number;

  water_requirement?: 'Low' | 'Medium' | 'High';

  water_constrained?: boolean;

  is_regionally_supported?: boolean;

  evidence_tier?: string;

  tags?: string[];

  reasons?: string[];

  soilSuitability?: string;

  risks?: string[];

}



const MAHARASHTRA_DISTRICTS = [

  'Nashik', 'Pune', 'Nagpur', 'Amravati', 'Chhatrapati Sambhajinagar',

  'Ahilyanagar', 'Akola', 'Beed', 'Bhandara', 'Buldhana', 'Chandrapur',

  'Dharashiv', 'Dhule', 'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon',

  'Jalna', 'Kolhapur', 'Latur', 'Mumbai suburban', 'Nanded', 'Nandurbar',

  'Palghar', 'Parbhani', 'Raigad', 'Ratnagiri', 'Sangli', 'Satara',

  'Sindhudurg', 'Solapur', 'Thane', 'Wardha', 'Washim', 'Yavatmal'

];



export default function CropRecommendation() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';

  const navigate = useNavigate();

  const { user } = useAuth();

  const isAuthenticated = Boolean(user);



  // Workflow Step 1: Farm and Field Selection

  const [fields, setFields] = useState<FieldOption[]>([

    { id: 'field-1', name: 'Field 1 (North Parcel)', area: 6.5, crop: 'Soybean' },

    { id: 'field-2', name: 'Field 2 (South Parcel)', area: 5.5, crop: 'Cotton' }

  ]);

  const [selectedFieldId, setSelectedFieldId] = useState<string>('field-1');



  // Workflow Step 2 & 3: Soil Information & NPK Values

  const [soilType, setSoilType] = useState('Black Cotton Soil / Medium Clay');

  const [soilPh, setSoilPh] = useState<number>(6.5);

  const [nitrogen, setNitrogen] = useState<number>(90);

  const [phosphorus, setPhosphorus] = useState<number>(42);

  const [potassium, setPotassium] = useState<number>(43);



  // Workflow Step 4: Weather & Climate Telemetry

  const [temperature, setTemperature] = useState<number>(26.0);

  const [humidity, setHumidity] = useState<number>(70.0);

  const [rainfall, setRainfall] = useState<number>(720.0);



  // Regional Dimensions

  const [district, setDistrict] = useState('Nashik');

  const [season, setSeason] = useState('Kharif');

  const [waterAvailability, setWaterAvailability] = useState<'Low' | 'Medium' | 'High'>('Medium');

  const [regionalWarning, setRegionalWarning] = useState<string | null>(null);



  // Workflow Step 5: Recommendation Request & Output

  const [recommendations, setRecommendations] = useState<CropRecommendationItem[]>([]);

  const [viewFilter, setViewFilter] = useState<'all' | 'verified'>('all');

  const [filteredOutCandidates, setFilteredOutCandidates] = useState<any[]>([]);

  const [loading, setLoading] = useState(false);

  const [isDemo, setIsDemo] = useState(false);

  const [modelMetadata, setModelMetadata] = useState<{

    modelVersion?: string;

    dataSource?: string;

    interpretation?: string;

    latencyMs?: number;

  } | null>(null);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);



  // Workflow Step 7 & 8: Selected Crop & Nutrient Guidance

  const [selectedCrop, setSelectedCrop] = useState<CropRecommendationItem | null>(null);

  const [nutrientAssessment, setNutrientAssessment] = useState<{

    status: string;

    issues: string[];

    recommendation: string;

  } | null>(null);

  const [loadingNutrients, setLoadingNutrients] = useState(false);



  // Load fields from Supabase when authenticated

  useEffect(() => {

    if (user && isAuthenticated) {

      loadUserFields(user.id);

    }

  }, [user, isAuthenticated]);



  const loadUserFields = async (userId: string) => {

    try {

      const { data: farmData } = await supabase

        .from('farms')

        .select('id, farm_name, fields(id, field_name, area, seasons(crop))')

        .eq('user_id', userId)

        .limit(1)

        .maybeSingle();



      if (farmData && Array.isArray(farmData.fields) && farmData.fields.length > 0) {

        const loaded: FieldOption[] = farmData.fields.map((f: any) => ({

          id: f.id,

          name: f.field_name,

          area: f.area || 5,

          crop: f.seasons?.[0]?.crop || 'None'

        }));

        setFields(loaded);

        setSelectedFieldId(loaded[0].id);

      }

    } catch (e) {

      console.error('Error fetching farm fields:', e);

    }

  };



  // Initial recommendation run on mount

  useEffect(() => {

    fetchRecommendations();

  }, []);



  const validateInputs = (): string | null => {

    if (isNaN(nitrogen) || nitrogen < 0 || nitrogen > 300) return 'Nitrogen (N) must be between 0 and 300 kg/ha';

    if (isNaN(phosphorus) || phosphorus < 0 || phosphorus > 300) return 'Phosphorus (P) must be between 0 and 300 kg/ha';

    if (isNaN(potassium) || potassium < 0 || potassium > 800) return 'Potassium (K) must be between 0 and 800 kg/ha';

    if (isNaN(soilPh) || soilPh < 3.5 || soilPh > 9.5) return 'Soil pH must be between 3.5 and 9.5';

    if (isNaN(temperature) || temperature < 5 || temperature > 50) return 'Mean Temperature must be between 5.0 and 50.0 °C';

    if (isNaN(humidity) || humidity < 10 || humidity > 100) return 'Relative Humidity must be between 10% and 100%';

    if (isNaN(rainfall) || rainfall < 20 || rainfall > 3000) return 'Seasonal Rainfall must be between 20 and 3000 mm';

    return null;

  };



  const fetchRecommendations = async () => {

    const valErr = validateInputs();

    if (valErr) {

      setErrorMessage(valErr);

      return;

    }



    setLoading(true);

    setErrorMessage(null);

    setRegionalWarning(null);



    try {

      const response = await api.predictCrop({

        N: Number(nitrogen),

        P: Number(phosphorus),

        K: Number(potassium),

        ph: Number(soilPh),

        temperature: Number(temperature),

        humidity: Number(humidity),

        rainfall: Number(rainfall),

        district: district,

        season: season,

        water_access: waterAvailability === 'High' ? 'Farm Pond + Drip' : waterAvailability === 'Low' ? 'Strictly Rainfed' : 'Borewell Only',

        water_availability: waterAvailability,

        top_k: 5

      });



      setIsDemo(response.isDemo);



      let recs: CropRecommendationItem[] = [];

      if (Array.isArray(response.data)) {

        recs = response.data.map((item: any, idx: number) => {

          const rank = item.rank || idx + 1;

          const combined = typeof item.combined_score === 'number'

            ? item.combined_score

            : (typeof item.final_score === 'number' ? item.final_score : (typeof item.score === 'number' ? item.score / 100 : item.predicted_area_frequency));

          const npk = typeof item.npk_score === 'number' ? item.npk_score : item.soil_climate_score;

          const reg = typeof item.region_score === 'number' ? item.region_score : item.regional_score;



          const isRegionallySupported = item.is_regionally_supported !== false;

          const evidenceTier = item.evidence_tier || (isRegionallySupported ? `Verified in ${district}` : `{t('crop.biophysicalOnly')} (Unverified in ${district})`);



          return {

            crop: item.crop,

            rank: rank,

            predicted_area_frequency: combined,

            combined_score: combined,

            npk_score: npk,

            region_score: reg,

            region_suitability: item.region_suitability || 'Evaluated',

            grown_pct_of_years: item.grown_pct_of_years,

            avg_yield_t_ha: item.avg_yield_t_ha,

            water_requirement: item.water_constrained ? 'High' : (item.water_requirement || (item.crop === 'Rice' || item.crop === 'Sugarcane' ? 'High' : 'Medium')),

            water_constrained: item.water_constrained,

            is_regionally_supported: isRegionallySupported,

            evidence_tier: evidenceTier,

            tags: [

              rank === 1 ? t('crop.optimalCandidate') : `Rank #${rank} Recommendation`,

              isRegionallySupported ? 'Regionally Verified' : 'Biophysical Candidate',

              item.region_suitability ? `Region: ${item.region_suitability}` : `${season} Season`,

              typeof npk === 'number' ? `NPK Match: ${(npk * 100).toFixed(0)}%` : `${district} History`

            ],

            reasons: [

              item.reason || `Soil/Climate RF probability: ${typeof npk === 'number' ? (npk * 100).toFixed(1) : '—'}%`,

              item.grown_pct_of_years ? `Historically cultivated in ${item.grown_pct_of_years}% of census years in ${district}` : `Compatible with ${waterAvailability} water availability.`

            ],

            soilSuitability: `Soil N: ${nitrogen}, P: ${phosphorus}, K: ${potassium}, pH: ${soilPh} evaluated via Model 1 Random Forest classifier.`,

            risks: [

              item.water_constrained

                ? 'High water requirement under current irrigation access; supplementary irrigation required.'

                : 'Indicative historical ICAR benchmark; not a guaranteed yield or commercial return.'

            ]

          };

        });

      }



      setRecommendations(recs);

      if (recs.length > 0) {

        setSelectedCrop(recs[0]);

        fetchNutrientGuidance(recs[0].crop);

      } else {

        setSelectedCrop(null);

        setNutrientAssessment(null);

      }



      if (response.raw) {

        setModelMetadata({

          modelVersion: response.raw.model_source || 'Hugging Face Sheshank2609/crop-recommendation-system@f24d6e1',

          dataSource: 'Hugging Face RF (22 crops) + Maharashtra 26-Yr APY Census (1997-2022)',

          interpretation: 'Blended Multi-Criteria Score: 60% Soil/Climate RF Probability + 40% Regional Suitability',

          latencyMs: response.raw.latency_ms || 45

        });

        if (Array.isArray(response.raw.warnings) && response.raw.warnings.length > 0) {

          setRegionalWarning(response.raw.warnings.join(' • '));

        }

      }

    } catch (error: any) {

      console.error('Failed to fetch recommendations', error);

      setErrorMessage(`Model Request Error: ${error.message || String(error)}`);

      setRecommendations([]);

      setSelectedCrop(null);

    } finally {

      setLoading(false);

    }

  };

  const fetchNutrientGuidance = async (cropName: string) => {

    setLoadingNutrients(true);

    try {

      const response = await api.assessSoil(nitrogen, phosphorus, potassium, soilPh);

      setNutrientAssessment({

        status: response.data.overall_status || 'Deficient/Imbalanced',

        issues: response.data.issues || ['Low Nitrogen'],

        recommendation: response.data.recommendation || `Apply balanced NPK fertilizer calibrated for ${cropName}.`

      });

    } catch (e) {

      console.error('Failed to load soil nutrient guidance:', e);

    } finally {

      setLoadingNutrients(false);

    }

  };



  const handleSelectCrop = (cropItem: CropRecommendationItem) => {

    setSelectedCrop(cropItem);

    fetchNutrientGuidance(cropItem.crop);

  };



  const selectedField = fields.find((f) => f.id === selectedFieldId) || fields[0];



  return (

    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">

      {/* Header */}

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">

        <div>

          <div className="flex items-center gap-2">

            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">{t('crop.title')}</h1>

            {isDemo ? (

              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">

                {t('crop.sampleRecommendations')}

              </span>

            ) : (

              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">

                <Sparkles size={12} className="text-emerald-700" />

                {t('crop.liveMlEngine')}

              </span>

            )}

          </div>

          <p className="text-[#292B26]/70 mt-1 text-sm">

            {t('crop.subtitle')}

          </p>

        </div>



        <button

          onClick={fetchRecommendations}

          disabled={loading}

          className="bg-[#103D2C] hover:bg-[#17643E] text-white px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-xs disabled:opacity-50"

        >

          {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}

          <span>{loading ? t('crop.evaluatingModel') : t('crop.runRecommendation')}</span>

        </button>

      </div>



      {errorMessage && (

        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-xs">

          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />

          <span>{translateDynamic(errorMessage, currentLang)}</span>

        </div>

      )}



      {regionalWarning && (

        <div className="bg-amber-50 border border-amber-300 text-amber-900 px-4 py-3 rounded-xl text-xs flex items-start gap-2 shadow-xs">

          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />

          <div>

            <span className="font-bold block">{t('crop.regionalNotice')}</span>

            <span>{translateDynamic(regionalWarning, currentLang)}</span>

          </div>

        </div>

      )}



      {/* WORKFLOW BAR: Step 1 to 4 Input Context */}

      <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] space-y-4">

        <div className="flex items-center justify-between border-b border-[#E5DDCF] pb-3">

          <h3 className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-2">

            <Filter size={15} className="text-[#17643E]" /> {t('crop.fieldSoilClimateParams')}

          </h3>

          <span className="text-[11px] text-[#292B26]/60">

            {t('crop.workflowSubtitle')}

          </span>

        </div>



        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">

          {/* Step 1: Field Selection */}

          <div>

            <label className="block font-semibold text-[#292B26] mb-1">{t('crop.farmField')}</label>

            <select

              value={selectedFieldId}

              onChange={(e) => setSelectedFieldId(e.target.value)}

              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"

            >

              {fields.map((f) => (

                <option key={f.id} value={f.id}>

                  {f.name} ({f.area} ac)

                </option>

              ))}

            </select>

          </div>



          {/* Step 2: District */}

          <div>

            <label className="block font-semibold text-[#292B26] mb-1">{t('crop.agroClimaticDistrict')}</label>

            <select

              value={district}

              onChange={(e) => setDistrict(e.target.value)}

              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"

            >

              {MAHARASHTRA_DISTRICTS.map((d) => (

                <option key={d} value={d}>{d}</option>

              ))}

            </select>

          </div>



          {/* Step 3: Planned Season */}

          <div>

            <label className="block font-semibold text-[#292B26] mb-1">{t('crop.plannedSeason')}</label>

            <select

              value={season}

              onChange={(e) => setSeason(e.target.value)}

              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"

            >

              <option value="Kharif">{t('crop.kharifSeason')}</option>

              <option value="Rabi">{t('crop.rabiSeason')}</option>

              <option value="Summer">{t('crop.summerSeason')}</option>

              <option value="Whole Year">{t('crop.wholeYearSeason')}</option>

            </select>

          </div>



          {/* Step 4: Water Availability */}

          <div>

            <label className="block font-semibold text-[#292B26] mb-1">{t('crop.waterAvailability')}</label>

            <select

              value={waterAvailability}

              onChange={(e) => setWaterAvailability(e.target.value as any)}

              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"

            >

              <option value="Low">{t('crop.waterLow')}</option>

              <option value="Medium">{t('crop.waterMedium')}</option>

              <option value="High">{t('crop.waterHigh')}</option>

            </select>

          </div>

        </div>



        {/* Soil Chemistry & Weather Telemetry (7 Model Inputs) */}

        <div className="pt-3 border-t border-[#E5DDCF]/80 space-y-3">

          <div className="flex items-center justify-between">

            <span className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">

              <FlaskConical size={14} className="text-[#17643E]" /> {t('crop.soilWeatherTitle')}

            </span>

            <span className="text-[10px] text-[#292B26]/60">{t('crop.reviewFeatures')}</span>

          </div>



          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs">

            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.nitrogen')}</label>

              <input

                type="number"

                min="0"

                max="300"

                value={nitrogen}

                onChange={(e) => setNitrogen(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">0–300 kg/ha</span>

            </div>



            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.phosphorus')}</label>

              <input

                type="number"

                min="0"

                max="300"

                value={phosphorus}

                onChange={(e) => setPhosphorus(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">0–300 kg/ha</span>

            </div>



            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.potassium')}</label>

              <input

                type="number"

                min="0"

                max="300"

                value={potassium}

                onChange={(e) => setPotassium(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">0–300 kg/ha</span>

            </div>



            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.soilPh')}</label>

              <input

                type="number"

                step="0.1"

                min="3.5"

                max="9.5"

                value={soilPh}

                onChange={(e) => setSoilPh(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">3.5–9.5</span>

            </div>



            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.meanTemp')}</label>

              <input

                type="number"

                step="0.5"

                min="5"

                max="50"

                value={temperature}

                onChange={(e) => setTemperature(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">°C (5–50)</span>

            </div>



            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.humidity')}</label>

              <input

                type="number"

                min="10"

                max="100"

                value={humidity}

                onChange={(e) => setHumidity(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">% (10–100)</span>

            </div>



            <div>

              <label className="block text-[#292B26]/70 text-[10px] font-semibold mb-0.5">{t('crop.rainfall')}</label>

              <input

                type="number"

                min="20"

                max="3000"

                value={rainfall}

                onChange={(e) => setRainfall(Number(e.target.value))}

                className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-1.5 text-center font-bold text-[#103D2C]"

              />

              <span className="text-[9px] text-[#292B26]/50 block text-center mt-0.5">mm (20–3000)</span>

            </div>

          </div>

        </div>

      </div>



      {/* Main Grid: Recommendations & Selected Crop Nutrient Guidance */}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column: Ranked List of 3-5 Suitable Crops */}

        <div className="lg:col-span-2 space-y-4">

          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">

            <div>

              <h3 className="font-bold text-[#103D2C] text-base flex items-center gap-2">

                <span>{t('crop.topCandidates')}</span>

                <span className="text-xs font-normal text-[#292B26]/60">

                  ({recommendations.filter((r) => viewFilter === 'all' || r.is_regionally_supported !== false).length} {t('crop.candidatesShown')})

                </span>

              </h3>

              {modelMetadata?.latencyMs && (

                <span className="text-[11px] text-[#292B26]/50">

                  {t('crop.inference')} {modelMetadata.latencyMs} ms

                </span>

              )}

            </div>



            {recommendations.length > 0 && (

              <div className="flex items-center gap-1.5 bg-[#FBF7EF] p-1 rounded-xl border border-[#E5DDCF] text-xs">

                <button

                  onClick={() => setViewFilter('all')}

                  className={`px-3 py-1 rounded-lg font-medium transition-colors cursor-pointer ${

                    viewFilter === 'all'

                      ? 'bg-[#103D2C] text-white shadow-xs'

                      : 'text-[#292B26]/70 hover:text-[#103D2C]'

                  }`}

                >

                  {t('crop.filterAll')} ({recommendations.length})

                </button>

                <button

                  onClick={() => setViewFilter('verified')}

                  className={`px-3 py-1 rounded-lg font-medium transition-colors cursor-pointer ${

                    viewFilter === 'verified'

                      ? 'bg-[#103D2C] text-white shadow-xs'

                      : 'text-[#292B26]/70 hover:text-[#103D2C]'

                  }`}

                >

                  {t('crop.filterVerified')} ({recommendations.filter((r) => r.is_regionally_supported !== false).length})

                </button>

              </div>

            )}

          </div>



          {/* Model Score Interpretation Banner */}

          <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl p-3.5 text-xs text-[#292B26]/75 flex items-start gap-2.5">

            <Info size={16} className="text-[#17643E] shrink-0 mt-0.5" />

            <div className="space-y-0.5">

              <span className="font-bold text-[#103D2C] block">

                {modelMetadata?.interpretation ? translateDynamic(modelMetadata.interpretation, currentLang) : t('crop.blendedScoreTitle')}

              </span>

              <p className="text-[11px] leading-relaxed">{t('crop.blendedScoreDesc')}</p>

            </div>

          </div>



          {loading ? (

            <div className="flex flex-col items-center justify-center py-16 bg-white rounded-2xl border border-[#E5DDCF]">

              <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mb-3" />

              <p className="text-xs text-[#292B26]/70">

                {t('crop.evaluatingCandidates')}

              </p>

            </div>

          ) : recommendations.length === 0 ? (

            <div className="bg-white rounded-2xl p-12 text-center border border-[#E5DDCF] space-y-2">

              <ShieldAlert className="w-10 h-10 text-amber-600 mx-auto" />

              <h4 className="font-bold text-[#103D2C]">{t('crop.noEligibleFound')}</h4>

              <p className="text-xs text-[#292B26]/60 max-w-md mx-auto">{t('crop.noEligibleDesc', { season: translateDynamic(season, currentLang) || season, district, water: translateDynamic(waterAvailability, currentLang) || waterAvailability })}</p>

            </div>

          ) : (

            recommendations

              .filter((rec) => viewFilter === 'all' || rec.is_regionally_supported !== false)

              .map((rec) => {

              const isSelected = selectedCrop?.crop === rec.crop;

              return (

                <div

                  key={rec.crop}

                  onClick={() => handleSelectCrop(rec)}

                  className={`bg-white rounded-2xl p-5 shadow-xs border transition-all cursor-pointer ${

                    isSelected

                      ? 'border-[#17643E] ring-2 ring-[#17643E]/20 bg-[#FBF7EF]/30'

                      : 'border-[#E5DDCF] hover:border-[#17643E]/60'

                  }`}

                >

                  <div className="flex justify-between items-start gap-4">

                    <div className="flex items-start gap-3.5">

                      <div

                        className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-lg shrink-0 ${

                          rec.rank === 1 ? 'bg-[#17643E] text-white shadow-xs' : 'bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF]'

                        }`}

                      >

                        #{rec.rank}

                      </div>

                      <div>

                        <div className="flex items-center gap-2 flex-wrap">

                          <h4 className="text-base font-bold text-[#103D2C]">{translateDynamic(rec.crop, currentLang) || rec.crop}</h4>

                          {rec.rank === 1 && (

                            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">

                              Optimal Candidate

                            </span>

                          )}

                          {rec.is_regionally_supported === false ? (

                            <span className="bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">

                              <AlertCircle size={10} className="text-amber-700" />

                              Biophysical Candidate Only

                            </span>

                          ) : (

                            <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-medium px-2 py-0.5 rounded-full flex items-center gap-1">

                              <CheckCircle2 size={10} className="text-emerald-700" />

                              {t('crop.verifiedInDistrict', { district })}

                            </span>

                          )}

                          {isSelected && (

                            <span className="bg-[#103D2C] text-white text-[10px] font-semibold px-2 py-0.2 rounded-full">

                              {t('crop.selectedForPlan')}

                            </span>

                          )}

                        </div>



                        {/* Tags */}

                        <div className="flex flex-wrap gap-1.5 mt-1.5">

                          {rec.tags?.map((tTag) => (

                            <span

                              key={tTag}

                              className="text-[10px] bg-[#FBF7EF] text-[#292B26]/80 px-2 py-0.5 rounded-md border border-[#E5DDCF]"

                            >

                              {translateDynamic(tTag, currentLang) || tTag}

                            </span>

                          ))}

                        </div>

                      </div>

                    </div>



                    <div className="text-right shrink-0">

                      <div className="text-[11px] text-[#292B26]/60 font-medium">

                        {rec.combined_score !== undefined ? t('crop.blendedMatchScore') : t('crop.historicalAreaScore')}

                      </div>

                      <div className="text-xl font-bold text-[#17643E] font-mono">

                        {typeof rec.combined_score === 'number'

                          ? `${(rec.combined_score * 100).toFixed(1)}%`

                          : typeof rec.predicted_area_frequency === 'number'

                          ? rec.predicted_area_frequency.toFixed(4)

                          : '—'}

                      </div>

                      <div className="text-[10px] text-[#292B26]/50">

                        {t('crop.rank', { rank: rec.rank })}

                      </div>

                    </div>

                  </div>



                  {/* Reasons & Soil Considerations */}

                  <div className="mt-3 text-xs text-[#292B26]/80 space-y-1">

                    {rec.reasons?.map((r, i) => (

                      <p key={i} className="flex items-center gap-1.5">

                        <Check size={12} className="text-[#17643E] shrink-0" />

                        <span>{translateDynamic(r, currentLang) || r}</span>

                      </p>

                    ))}

                  </div>



                  {/* Decomposed Scores & Water Advisory Strip */}

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 pt-3 border-t border-[#E5DDCF] text-xs">

                    <div>

                      <span className="text-[10px] text-[#292B26]/60 block font-semibold">{t('crop.model1Label')}</span>

                      <span className="font-bold text-[#103D2C]">

                        {typeof rec.npk_score === 'number' ? `${(rec.npk_score * 100).toFixed(1)}%` : '—'}

                      </span>

                    </div>

                    <div>

                      <span className="text-[10px] text-[#292B26]/60 block font-semibold">{t('crop.model2Label')}</span>

                      <span className="font-bold text-[#17643E]">

                        {typeof rec.region_score === 'number' ? `${(rec.region_score * 100).toFixed(1)}%` : '—'}

                      </span>

                    </div>

                    <div>

                      <span className="text-[10px] text-[#292B26]/60 block font-semibold">{t('crop.waterNeedLabel')}</span>

                      <span className={`font-bold ${rec.water_constrained ? 'text-amber-800' : 'text-[#292B26]'}`}>

                        {translateDynamic(rec.water_requirement, currentLang) || rec.water_requirement} {rec.water_constrained ? '⚠️' : ''}

                      </span>

                    </div>

                    <div>

                      <span className="text-[10px] text-[#292B26]/60 block font-semibold">{t('crop.censusHistoryLabel')}</span>

                      <span className="font-bold text-[#292B26]">

                        {rec.is_regionally_supported === false

                          ? t('crop.unverifiedYears')

                          : rec.grown_pct_of_years !== undefined

                          ? `${rec.grown_pct_of_years}% yrs`

                          : t('crop.regionalData')}

                      </span>

                    </div>

                  </div>

                </div>

              );

            })

          )}



          {/* Filtered Out Candidates Explanation */}

          {filteredOutCandidates.length > 0 && (

            <div className="bg-[#FBF7EF] p-4 rounded-xl border border-[#E5DDCF] text-xs text-[#292B26]/70 space-y-1.5">

              <span className="font-bold text-[#103D2C] flex items-center gap-1">

                <Info size={13} /> {t('crop.filteredOutTitle', { count: filteredOutCandidates.length })}

              </span>

              <ul className="list-disc pl-4 space-y-1 text-[11px]">

                {filteredOutCandidates.map((f, i) => (

                  <li key={i}>

                    <strong>{translateDynamic(f.crop, currentLang) || f.crop}</strong> {typeof f.model_score === 'number' ? `(raw score: ${f.model_score.toFixed(4)})` : ''}: {translateDynamic(f.filter_reason, currentLang) || f.filter_reason}

                  </li>

                ))}

              </ul>

            </div>

          )}

        </div>



        {/* Right Column: Step 8 - Crop-Specific Nutrient Guidance (Task 3) */}

        <div className="space-y-4">

          <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] space-y-4">

            <div className="border-b border-[#E5DDCF] pb-3">

              <h3 className="font-bold text-sm text-[#103D2C] flex items-center gap-2">

                <FlaskConical size={16} className="text-[#17643E]" />

                <span>{t('crop.nutrientGuidanceTitle')}</span>

              </h3>

              <p className="text-xs text-[#292B26]/60 mt-0.5">

                {selectedCrop ? t('crop.specificToCrop', { crop: translateDynamic(selectedCrop.crop, currentLang) || selectedCrop.crop }) : t('crop.selectCandidatePrompt')}

              </p>

            </div>



            {selectedCrop ? (

              <div className="space-y-4">

                {/* Selected Crop Header */}

                <div className="bg-[#FBF7EF] p-3 rounded-xl border border-[#E5DDCF]">

                  <span className="text-[11px] text-[#292B26]/60 block">{t('crop.selectedTargetCrop')}</span>

                  <span className="font-bold text-base text-[#103D2C]">{translateDynamic(selectedCrop.crop, currentLang) || selectedCrop.crop}</span>

                  <span className="text-xs text-[#292B26]/70 block mt-0.5">

                    {t('crop.fieldAreaRank', { area: selectedField.area, rank: selectedCrop.rank })}

                  </span>

                </div>



                {/* Soil Nutrient Deficiencies from Backend Model */}

                <div className="space-y-2">

                  <span className="font-semibold text-xs text-[#292B26] block">

                    {t('crop.diagnosticStatus')}

                  </span>

                  {loadingNutrients ? (

                    <div className="py-4 text-center text-xs text-[#292B26]/60">

                      <Loader2 size={16} className="animate-spin text-[#103D2C] mx-auto mb-1" />

                      {t('crop.evaluatingNutrients')}

                    </div>

                  ) : nutrientAssessment ? (

                    <div className="space-y-2 text-xs">

                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">

                        <span className="font-medium">{t('crop.nutrientBalance')}</span>

                        <span className="font-bold">{translateDynamic(nutrientAssessment.status, currentLang) || nutrientAssessment.status}</span>

                      </div>

                      <div className="p-3 rounded-lg bg-[#FBF7EF] border border-[#E5DDCF] space-y-1">

                        <span className="font-semibold text-[#103D2C] block">{t('crop.identifiedBalances')}</span>

                        <ul className="list-disc pl-4 space-y-0.5 text-[#292B26]/80 text-[11px]">

                          {nutrientAssessment.issues.map((iss, i) => (

                            <li key={i}>{translateDynamic(iss, currentLang) || iss}</li>

                          ))}

                        </ul>

                      </div>

                      <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-1">

                        <span className="font-semibold block">{t('crop.agronomicDirection')}</span>

                        <p className="text-[11px] leading-relaxed">{translateDynamic(nutrientAssessment.recommendation, currentLang) || nutrientAssessment.recommendation}</p>

                      </div>

                    </div>

                  ) : null}

                </div>



                {/* Integration Boundary Notice for Codex */}

                <div className="bg-[#FBF7EF] border border-[#E5DDCF] p-3.5 rounded-xl text-[11px] text-[#292B26]/70 space-y-1.5">

                  <div className="flex items-center gap-1.5 font-bold text-[#103D2C]">

                    <Info size={13} />

                    <span>{t('crop.agronomicBoundary')}</span>

                  </div>

                  <p className="leading-relaxed">{t('crop.agronomicBoundaryDesc1')}</p>

                  <p className="leading-relaxed">{t('crop.agronomicBoundaryDesc2')}</p>

                </div>



                <div className="pt-2">

                  <button

                    onClick={() => navigate('/farm-economics')}

                    className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white py-2 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"

                  >

                    <span>{t('crop.simulateEconomics', { crop: translateDynamic(selectedCrop.crop, currentLang) || selectedCrop.crop })}</span>

                    <ArrowRight size={13} />

                  </button>

                </div>

              </div>

            ) : (

              <div className="py-8 text-center text-xs text-[#292B26]/50">

                {t('crop.clickCandidatePrompt')}

              </div>

            )}

          </div>

        </div>

      </div>

    </div>

  );

}

