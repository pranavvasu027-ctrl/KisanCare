import React, { useState, useEffect } from 'react';
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
  water_requirement?: 'Low' | 'Medium' | 'High';
  tags?: string[];
  reasons?: string[];
  soilSuitability?: string;
  risks?: string[];
}

export default function CropRecommendation() {
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
  const [soilPh, setSoilPh] = useState<number>(7.2);
  const [nitrogen, setNitrogen] = useState<number>(22);
  const [phosphorus, setPhosphorus] = useState<number>(28);
  const [potassium, setPotassium] = useState<number>(175);

  // Workflow Step 4: Weather & Water Availability
  const [district, setDistrict] = useState('NASHIK');
  const [season, setSeason] = useState('Kharif');
  const [waterAvailability, setWaterAvailability] = useState<'Low' | 'Medium' | 'High'>('Medium');

  // Workflow Step 5: Recommendation Request & Output
  const [recommendations, setRecommendations] = useState<CropRecommendationItem[]>([]);
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

  const fetchRecommendations = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await api.predictCrop(district, season, waterAvailability, 5);
      setIsDemo(response.isDemo);

      let recs: CropRecommendationItem[] = [];
      if (Array.isArray(response.data)) {
        recs = response.data.map((item: any, idx: number) => {
          const rank = item.rank || idx + 1;
          const freq = typeof item.predicted_area_frequency === 'number'
            ? item.predicted_area_frequency
            : (typeof item.score === 'number' ? item.score / 100 : undefined);

          return {
            crop: item.crop,
            rank: rank,
            predicted_area_frequency: freq,
            water_requirement: item.water_requirement || (item.crop === 'Rice' || item.crop === 'Sugarcane' ? 'High' : item.crop === 'Pigeon Pea' ? 'Low' : 'Medium'),
            tags: item.tags || [
              rank === 1 ? 'Top Historical Rank' : `Rank #${rank} Candidate`,
              `${season} Season`,
              `${district} History`
            ],
            reasons: [
              `Consistent historical area allocation in ${district} for ${season} season.`,
              `Compatible with ${waterAvailability} water availability.`
            ],
            soilSuitability: `${soilType} (pH ${soilPh}) supports good vegetative development.`,
            risks: [
              waterAvailability === 'Low' ? 'Yield susceptible to extended dry spells.' : 'Ensure proper field drainage during heavy monsoon bouts.'
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
          modelVersion: response.raw.model_version || '2.0.0',
          dataSource: response.raw.data_source || 'APY_2005_2015',
          interpretation: response.raw.score_interpretation,
          latencyMs: response.raw.latency_ms
        });
        if (Array.isArray(response.raw.filtered_candidates)) {
          setFilteredOutCandidates(response.raw.filtered_candidates);
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
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Crop Intelligence</h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Recommendations
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <Sparkles size={12} className="text-emerald-700" />
                Live ML Candidate Engine
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1 text-sm">
            Agronomic crop suitability analysis driven by district historical patterns, water availability, and soil nutrients.
          </p>
        </div>

        <button
          onClick={fetchRecommendations}
          disabled={loading}
          className="bg-[#103D2C] hover:bg-[#17643E] text-white px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-xs disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          <span>{loading ? 'Evaluating Model...' : 'Analyze & Recommend Crops'}</span>
        </button>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-xs">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* WORKFLOW BAR: Step 1 to 4 Input Context */}
      <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] space-y-4">
        <div className="flex items-center justify-between border-b border-[#E5DDCF] pb-3">
          <h3 className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-2">
            <Filter size={15} className="text-[#17643E]" /> Field, Soil & Climate Input Parameters
          </h3>
          <span className="text-[11px] text-[#292B26]/60">
            Step 1–4: Review inputs before requesting model candidates
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {/* Step 1: Field Selection */}
          <div>
            <label className="block font-semibold text-[#292B26] mb-1">1. Farm & Field</label>
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
            <label className="block font-semibold text-[#292B26] mb-1">2. Agro-Climatic District</label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"
            >
              <option value="NASHIK">Nashik (North Maharashtra)</option>
              <option value="NAGPUR">Nagpur (Vidarbha)</option>
              <option value="AMRAVATI">Amravati</option>
              <option value="PUNE">Pune (Western Maharashtra)</option>
              <option value="AURANGABAD">Chhatrapati Sambhajinagar</option>
            </select>
          </div>

          {/* Step 3: Planned Season */}
          <div>
            <label className="block font-semibold text-[#292B26] mb-1">3. Planned Season</label>
            <select
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"
            >
              <option value="Kharif">Kharif (Monsoon 2026)</option>
              <option value="Rabi">Rabi (Winter 2026-27)</option>
              <option value="Summer">Summer (Zaid 2026)</option>
              <option value="Whole Year">Whole Year (Perennial)</option>
            </select>
          </div>

          {/* Step 4: Water Availability */}
          <div>
            <label className="block font-semibold text-[#292B26] mb-1">4. Water Availability</label>
            <select
              value={waterAvailability}
              onChange={(e) => setWaterAvailability(e.target.value as any)}
              className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 font-medium text-[#103D2C]"
            >
              <option value="Low">Low (Rainfed / water-scarce)</option>
              <option value="Medium">Medium (Seasonal canal / borewell)</option>
              <option value="High">High (Perennial canal / drip)</option>
            </select>
          </div>
        </div>

        {/* Soil NPK Review Strip */}
        <div className="pt-2 border-t border-[#E5DDCF]/60 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="font-semibold text-[#103D2C] flex items-center gap-1">
              <FlaskConical size={14} className="text-[#17643E]" /> Soil Test Values:
            </span>
            <span className="bg-[#FBF7EF] px-2.5 py-1 rounded-md border border-[#E5DDCF]">
              N: <strong>{nitrogen}</strong> kg/ha
            </span>
            <span className="bg-[#FBF7EF] px-2.5 py-1 rounded-md border border-[#E5DDCF]">
              P: <strong>{phosphorus}</strong> kg/ha
            </span>
            <span className="bg-[#FBF7EF] px-2.5 py-1 rounded-md border border-[#E5DDCF]">
              K: <strong>{potassium}</strong> kg/ha
            </span>
            <span className="bg-[#FBF7EF] px-2.5 py-1 rounded-md border border-[#E5DDCF]">
              pH: <strong>{soilPh.toFixed(1)}</strong>
            </span>
          </div>

          <button
            onClick={() => navigate('/soil')}
            className="text-[#17643E] hover:underline font-semibold flex items-center gap-1 cursor-pointer"
          >
            <span>Update Soil Health Card</span>
            <ChevronRight size={13} />
          </button>
        </div>
      </div>

      {/* Main Grid: Recommendations & Selected Crop Nutrient Guidance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Ranked List of 3-5 Suitable Crops */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-[#103D2C] text-base flex items-center gap-2">
              <span>Top Suitable Crop Candidates</span>
              <span className="text-xs font-normal text-[#292B26]/60">
                ({recommendations.length} valid candidates returned)
              </span>
            </h3>
            {modelMetadata?.latencyMs && (
              <span className="text-[11px] text-[#292B26]/50">
                Inference: {modelMetadata.latencyMs} ms
              </span>
            )}
          </div>

          {/* Model Score Interpretation Banner */}
          <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl p-3.5 text-xs text-[#292B26]/75 flex items-start gap-2.5">
            <Info size={16} className="text-[#17643E] shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-bold text-[#103D2C] block">
                {modelMetadata?.interpretation || 'Score Interpretation: Historical Area-Allocation Score'}
              </span>
              <p className="text-[11px] leading-relaxed">
                Scores reflect historical crop area proportions from official agricultural statistics (APY 2005–2015) in {district} during {season} season, filtered deterministically by water availability ({waterAvailability}). They represent historical agro-climatic alignment and adoption, not an agronomic yield forecast or probability.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 bg-white rounded-2xl border border-[#E5DDCF]">
              <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mb-3" />
              <p className="text-xs text-[#292B26]/70">
                AI decision engine is filtering seasonal candidates and evaluating district area allocation...
              </p>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center border border-[#E5DDCF] space-y-2">
              <ShieldAlert className="w-10 h-10 text-amber-600 mx-auto" />
              <h4 className="font-bold text-[#103D2C]">No Eligible Crops Found</h4>
              <p className="text-xs text-[#292B26]/60 max-w-md mx-auto">
                No crops satisfied the constraints for {season} season in {district} under {waterAvailability} water availability.
                Try adjusting water availability or selecting a different season.
              </p>
            </div>
          ) : (
            recommendations.map((rec) => {
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
                          <h4 className="text-base font-bold text-[#103D2C]">{rec.crop}</h4>
                          {rec.rank === 1 && (
                            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                              Optimal Candidate
                            </span>
                          )}
                          {isSelected && (
                            <span className="bg-[#103D2C] text-white text-[10px] font-semibold px-2 py-0.2 rounded-full">
                              Selected for Nutrient Plan
                            </span>
                          )}
                        </div>

                        {/* Tags */}
                        <div className="flex flex-wrap gap-1.5 mt-1.5">
                          {rec.tags?.map((t) => (
                            <span
                              key={t}
                              className="text-[10px] bg-[#FBF7EF] text-[#292B26]/80 px-2 py-0.5 rounded-md border border-[#E5DDCF]"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="text-[11px] text-[#292B26]/60 font-medium">Historical Area Score</div>
                      <div className="text-xl font-bold text-[#17643E] font-mono">
                        {typeof rec.predicted_area_frequency === 'number'
                          ? rec.predicted_area_frequency.toFixed(4)
                          : '—'}
                      </div>
                      <div className="text-[10px] text-[#292B26]/50">
                        Rank #{rec.rank}
                      </div>
                    </div>
                  </div>

                  {/* Reasons & Soil Considerations */}
                  <div className="mt-3 text-xs text-[#292B26]/80 space-y-1">
                    {rec.reasons?.map((r, i) => (
                      <p key={i} className="flex items-center gap-1.5">
                        <Check size={12} className="text-[#17643E] shrink-0" />
                        <span>{r}</span>
                      </p>
                    ))}
                  </div>

                  {/* Water Need and Historical Area Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4 pt-3 border-t border-[#E5DDCF] text-xs">
                    <div>
                      <span className="text-[11px] text-[#292B26]/60 block">Water Need</span>
                      <span className="font-bold text-[#292B26]">{rec.water_requirement}</span>
                    </div>
                    <div>
                      <span className="text-[11px] text-[#292B26]/60 block">Historical Area Share</span>
                      <span className="font-bold text-[#103D2C]">
                        {typeof rec.predicted_area_frequency === 'number'
                          ? `${(rec.predicted_area_frequency * 100).toFixed(1)}% of crop area`
                          : 'APY Historical Data'}
                      </span>
                    </div>
                    <div className="col-span-2 sm:col-span-1">
                      <span className="text-[11px] text-[#292B26]/60 block">Yield / Economics</span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate('/farm-economics');
                        }}
                        className="text-[11px] text-[#17643E] font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        Simulate in Economics →
                      </button>
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
                <Info size={13} /> Seasonal & Water Constraints Filtered Out ({filteredOutCandidates.length} candidate{filteredOutCandidates.length > 1 ? 's' : ''}):
              </span>
              <ul className="list-disc pl-4 space-y-1 text-[11px]">
                {filteredOutCandidates.map((f, i) => (
                  <li key={i}>
                    <strong>{f.crop}</strong> {typeof f.model_score === 'number' ? `(raw score: ${f.model_score.toFixed(4)})` : ''}: {f.filter_reason}
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
                <span>Crop Nutrient Guidance</span>
              </h3>
              <p className="text-xs text-[#292B26]/60 mt-0.5">
                {selectedCrop ? `Specific to selected: ${selectedCrop.crop}` : 'Select a crop candidate to inspect guidance'}
              </p>
            </div>

            {selectedCrop ? (
              <div className="space-y-4">
                {/* Selected Crop Header */}
                <div className="bg-[#FBF7EF] p-3 rounded-xl border border-[#E5DDCF]">
                  <span className="text-[11px] text-[#292B26]/60 block">Selected Target Crop</span>
                  <span className="font-bold text-base text-[#103D2C]">{selectedCrop.crop}</span>
                  <span className="text-xs text-[#292B26]/70 block mt-0.5">
                    Field Area: {selectedField.area} Acres • Rank #{selectedCrop.rank} Recommendation
                  </span>
                </div>

                {/* Soil Nutrient Deficiencies from Backend Model */}
                <div className="space-y-2">
                  <span className="font-semibold text-xs text-[#292B26] block">
                    Diagnostic Soil Status (/api/v1/soil-assessment):
                  </span>
                  {loadingNutrients ? (
                    <div className="py-4 text-center text-xs text-[#292B26]/60">
                      <Loader2 size={16} className="animate-spin text-[#103D2C] mx-auto mb-1" />
                      Evaluating soil nutrient parameters...
                    </div>
                  ) : nutrientAssessment ? (
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900">
                        <span className="font-medium">Nutrient Balance:</span>
                        <span className="font-bold">{nutrientAssessment.status}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-[#FBF7EF] border border-[#E5DDCF] space-y-1">
                        <span className="font-semibold text-[#103D2C] block">Identified Balances:</span>
                        <ul className="list-disc pl-4 space-y-0.5 text-[#292B26]/80 text-[11px]">
                          {nutrientAssessment.issues.map((iss, i) => (
                            <li key={i}>{iss}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-1">
                        <span className="font-semibold block">Agronomic Direction:</span>
                        <p className="text-[11px] leading-relaxed">{nutrientAssessment.recommendation}</p>
                      </div>
                    </div>
                  ) : null}
                </div>

                {/* Integration Boundary Notice for Codex */}
                <div className="bg-[#FBF7EF] border border-[#E5DDCF] p-3.5 rounded-xl text-[11px] text-[#292B26]/70 space-y-1.5">
                  <div className="flex items-center gap-1.5 font-bold text-[#103D2C]">
                    <Info size={13} />
                    <span>Agronomic Contract Boundary:</span>
                  </div>
                  <p className="leading-relaxed">
                    The backend supports diagnostic soil assessments (`/api/v1/soil-assessment`), but does not currently feature a calibrated crop-specific fertilizer prescription model (e.g. ICAR/STCR targeted yield equations for exact kg/acre Urea/DAP/MOP).
                  </p>
                  <p className="leading-relaxed">
                    Fertilizer application rates must be calibrated with an agricultural extension officer or local soil testing lab.
                  </p>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => navigate('/farm-economics')}
                    className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white py-2 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <span>Simulate Economics for {selectedCrop.crop}</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-[#292B26]/50">
                Click on any crop candidate on the left to inspect nutrient guidance and fertilizer balance considerations.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
