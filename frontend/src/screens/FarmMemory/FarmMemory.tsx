import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar, Sprout, TrendingUp, Plus, Trash2, Edit3, X,
  CheckCircle2, AlertCircle, Loader2, ArrowRight, BarChart3,
  BookOpen, Layers, Database, Droplets, FlaskConical,
  DollarSign, Bug, Wind, ChevronRight, Info
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../services/supabase';

export interface HistoricalSeason {
  id: string;
  farmId: string;
  farmName: string;
  fieldId: string;
  fieldName: string;
  year: number;
  seasonName: string;
  seasonType: 'Kharif' | 'Rabi' | 'Summer' | 'Whole Year';
  crop: string;
  variety?: string;
  sowingDate?: string;
  harvestDate?: string;
  areaAcres?: number;
  yieldQuantity?: number;
  yieldUnit: string;
  soilTest?: {
    n?: number;
    p?: number;
    k?: number;
    ph?: number;
    organicMatter?: number;
  };
  fertilizers?: Array<{
    product: string;
    quantityKg?: number;
    cost?: number;
    applicationDate?: string;
  }>;
  pesticides?: Array<{
    product: string;
    targetPest?: string;
    quantityMl?: number;
    cost?: number;
    applicationDate?: string;
  }>;
  irrigation?: {
    method?: string;
    waterAvailability?: 'Low' | 'Medium' | 'High';
    hoursTotal?: number;
    cost?: number;
  };
  weatherObservations?: string;
  economics?: {
    inputCost?: number;
    laborCost?: number;
    irrigationCost?: number;
    sellingPrice?: number;
    revenue?: number;
    profit?: number;
  };
  learnings: string[];
  farmerNotes?: string;
  isDemo?: boolean;
}

const DEFAULT_SAMPLE_SEASONS: HistoricalSeason[] = [
  {
    id: 'demo-season-cotton-2026',
    farmId: '52120432-c948-4026-87c4-7e2c481a7bf5',
    farmName: 'Pranav Vasu Farm',
    fieldId: 'e5d69ac6-bfe4-4015-a3cd-7cab06c476a6',
    fieldName: 'Field A (3.0 ac)',
    year: 2026,
    seasonName: 'Kharif 2026–27',
    seasonType: 'Kharif',
    crop: 'Cotton',
    variety: 'godavari',
    sowingDate: '2026-06-18',
    harvestDate: '2026-11-20',
    areaAcres: 3.0,
    yieldQuantity: 10.0,
    yieldUnit: 'qtl/ac',
    soilTest: {
      ph: 8.05
    },
    fertilizers: [
      { product: 'Fertilizers (bulk unitemized)', cost: 20000, applicationDate: '2026-07-02' }
    ],
    pesticides: [
      { product: 'Pesticide application', cost: 10, applicationDate: '2026-08-15' }
    ],
    irrigation: {
      method: 'Primarily Rainfed / Monsoon Dependent',
      waterAvailability: 'Low',
      hoursTotal: 0,
      cost: 0
    },
    weatherObservations: 'Rainfall monsoon dependent; severe dry spell in late monsoon causing boll development stress.',
    economics: {
      inputCost: 31010,
      laborCost: 50000,
      irrigationCost: 65000,
      sellingPrice: 8000,
      revenue: 240000,
      profit: 93990
    },
    learnings: [
      'Black cotton soil (koralvahu jamin) retains moisture during vegetative growth but requires supplementary irrigation at boll development.',
      'Cotton price benchmark at Akot APMC recorded at ₹8,000/qtl.'
    ],
    farmerNotes: 'Field A: 3 acres sown with Cotton variety godavari. Drought stress symptoms visible; bolls are few and small. Water source 100–500m away.',
    isDemo: true
  },
  {
    id: 'demo-season-cotton-2025',
    farmId: '52120432-c948-4026-87c4-7e2c481a7bf5',
    farmName: 'Pranav Vasu Farm',
    fieldId: 'e5d69ac6-bfe4-4015-a3cd-7cab06c476a6',
    fieldName: 'Field A (3.0 ac)',
    year: 2025,
    seasonName: 'Kharif 2025–26',
    seasonType: 'Kharif',
    crop: 'Cotton',
    variety: 'godavari',
    sowingDate: '2025-06-20',
    harvestDate: '2025-11-25',
    areaAcres: 3.0,
    yieldQuantity: 10.0,
    yieldUnit: 'qtl/ac',
    soilTest: {
      ph: 8.0
    },
    fertilizers: [],
    pesticides: [],
    irrigation: {
      method: 'Rainfed + Occasional Irrigation',
      waterAvailability: 'Medium',
      hoursTotal: 12,
      cost: 1500
    },
    weatherObservations: 'Adequate late-monsoon showers supported boll development.',
    economics: {
      inputCost: 28000,
      laborCost: 45000,
      irrigationCost: 1500,
      sellingPrice: 7600,
      revenue: 228000,
      profit: 153500
    },
    learnings: [
      'Historical yield of 10 quintals/acre verified when late-season moisture is preserved.',
      'Akot APMC market provides best price realization for Vidarbha medium-staple cotton.'
    ],
    farmerNotes: 'Achieved 10 quintals/acre historical benchmark.',
    isDemo: true
  }
];

export default function FarmMemory() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAuthenticated = Boolean(user);

  const [seasons, setSeasons] = useState<HistoricalSeason[]>([]);
  const [selectedSeasonId, setSelectedSeasonId] = useState<string>('demo-season-1');
  const [activeTab, setActiveTab] = useState<'records' | 'comparison' | 'lessons' | 'connections'>('records');

  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modal State for Adding/Editing Season
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSeasonId, setEditingSeasonId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Form Fields
  const [formFarmName, setFormFarmName] = useState('Pranav Vasu Farm');
  const [formFieldName, setFormFieldName] = useState('Field 1 (North Parcel)');
  const [formYear, setFormYear] = useState<number>(new Date().getFullYear());
  const [formSeasonType, setFormSeasonType] = useState<'Kharif' | 'Rabi' | 'Summer' | 'Whole Year'>('Kharif');
  const [formCrop, setFormCrop] = useState('Cotton');
  const [formVariety, setFormVariety] = useState('');
  const [formSowingDate, setFormSowingDate] = useState('');
  const [formHarvestDate, setFormHarvestDate] = useState('');
  const [formAreaAcres, setFormAreaAcres] = useState<string>('6.5');
  const [formYieldQty, setFormYieldQty] = useState<string>('2.5');
  const [formYieldUnit, setFormYieldUnit] = useState<'tonnes/ac' | 'qtl/ac'>('tonnes/ac');

  // Soil info
  const [formN, setFormN] = useState<string>('');
  const [formP, setFormP] = useState<string>('');
  const [formK, setFormK] = useState<string>('');
  const [formPh, setFormPh] = useState<string>('');

  // Input & Economics
  const [formFertilizerProduct, setFormFertilizerProduct] = useState('');
  const [formFertilizerCost, setFormFertilizerCost] = useState('');
  const [formPesticideProduct, setFormPesticideProduct] = useState('');
  const [formPesticideCost, setFormPesticideCost] = useState('');
  const [formIrrigationMethod, setFormIrrigationMethod] = useState('Drip');
  const [formIrrigationCost, setFormIrrigationCost] = useState('');
  const [formWeatherNotes, setFormWeatherNotes] = useState('');
  const [formProductionCost, setFormProductionCost] = useState('');
  const [formSellingPrice, setFormSellingPrice] = useState('');
  const [formRevenue, setFormRevenue] = useState('');
  const [formNetProfit, setFormNetProfit] = useState('');
  const [formLearnings, setFormLearnings] = useState('');
  const [formNotes, setFormNotes] = useState('');

  // Load Seasons on mount
  useEffect(() => {
    if (user && isAuthenticated) {
      loadUserSeasons(user.id);
    } else {
      // Load from localStorage or defaults
      try {
        const stored = localStorage.getItem('kisancare_historical_seasons');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setSeasons(parsed);
            setSelectedSeasonId(parsed[0].id);
            return;
          }
        }
      } catch {
        // Fallback
      }
      setSeasons(DEFAULT_SAMPLE_SEASONS);
      setSelectedSeasonId(DEFAULT_SAMPLE_SEASONS[0].id);
    }
  }, [user, isAuthenticated]);

  const loadUserSeasons = async (userId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // 1. Fetch user farms and fields with seasons
      const { data: farmData, error: farmErr } = await supabase
        .from('farms')
        .select('id, farm_name, fields(id, field_name, area, seasons(*))')
        .eq('user_id', userId);

      if (farmErr) {
        console.error('Error fetching farms for seasons:', farmErr);
        setErrorMessage(`Could not load seasons from database: ${farmErr.message}`);
        setSeasons([]);
        return;
      }

      // 2. Fetch extended season records from farm_data_records
      const farmIds = farmData ? farmData.map((f: any) => f.id) : [];
      const extendedRecordsMap: Record<string, any> = {};
      if (farmIds.length > 0) {
        const { data: extRecords } = await supabase
          .from('farm_data_records')
          .select('season_id, record_data')
          .in('farm_id', farmIds)
          .eq('record_type', 'historical_season_detail');

        if (Array.isArray(extRecords)) {
          extRecords.forEach((r: any) => {
            if (r.season_id && r.record_data) {
              extendedRecordsMap[r.season_id] = r.record_data;
            }
          });
        }
      }

      const parsedSeasons: HistoricalSeason[] = [];
      if (farmData && farmData.length > 0) {
        farmData.forEach((farm: any) => {
          if (Array.isArray(farm.fields)) {
            farm.fields.forEach((field: any) => {
              if (Array.isArray(field.seasons)) {
                field.seasons.forEach((s: any) => {
                  const ext = extendedRecordsMap[s.id] || {};
                  parsedSeasons.push({
                    id: s.id,
                    farmId: farm.id,
                    farmName: farm.farm_name || 'My Farm',
                    fieldId: field.id,
                    fieldName: field.field_name || 'Field',
                    year: s.sowing_date ? new Date(s.sowing_date).getFullYear() : 2025,
                    seasonName: s.season_name,
                    seasonType: s.season_name.includes('Rabi') ? 'Rabi' : s.season_name.includes('Summer') ? 'Summer' : 'Kharif',
                    crop: s.crop || 'Crop',
                    variety: s.crop_variety || undefined,
                    sowingDate: s.sowing_date || undefined,
                    harvestDate: s.actual_harvest_date || undefined,
                    areaAcres: field.area || undefined,
                    yieldQuantity: ext.yieldQuantity,
                    yieldUnit: ext.yieldUnit || 'tonnes/ac',
                    soilTest: ext.soilTest,
                    fertilizers: ext.fertilizers,
                    pesticides: ext.pesticides,
                    irrigation: ext.irrigation,
                    weatherObservations: ext.weatherObservations,
                    economics: ext.economics,
                    learnings: ext.learnings && ext.learnings.length > 0 ? ext.learnings : (s.previous_crop ? [`Previous crop recorded was ${s.previous_crop}.`] : []),
                    farmerNotes: ext.farmerNotes,
                    isDemo: Boolean(ext.isDemo)
                  });
                });
              }
            });
          }
        });
      }

      if (parsedSeasons.length > 0) {
        parsedSeasons.sort((a, b) => {
          if (b.year !== a.year) return b.year - a.year;
          return (b.sowingDate || '').localeCompare(a.sowingDate || '');
        });
        setSeasons(parsedSeasons);
        setSelectedSeasonId(parsedSeasons[0].id);
      } else {
        // No server seasons found, show empty state
        setSeasons([]);
      }
    } catch (err: any) {
      console.error('Unexpected error loading seasons:', err);
      setErrorMessage(`Error: ${err.message || String(err)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedSeason = seasons.find((s) => s.id === selectedSeasonId) || seasons[0];

  const resetForm = () => {
    setEditingSeasonId(null);
    setFormFarmName('Pranav Vasu Farm');
    setFormFieldName('Field 1 (North Parcel)');
    setFormYear(new Date().getFullYear());
    setFormSeasonType('Kharif');
    setFormCrop('Soybean');
    setFormVariety('');
    setFormSowingDate('');
    setFormHarvestDate('');
    setFormAreaAcres('6.5');
    setFormYieldQty('');
    setFormYieldUnit('tonnes/ac');
    setFormN('');
    setFormP('');
    setFormK('');
    setFormPh('');
    setFormFertilizerProduct('');
    setFormFertilizerCost('');
    setFormPesticideProduct('');
    setFormPesticideCost('');
    setFormIrrigationMethod('Drip');
    setFormIrrigationCost('');
    setFormWeatherNotes('');
    setFormProductionCost('');
    setFormSellingPrice('');
    setFormRevenue('');
    setFormNetProfit('');
    setFormLearnings('');
    setFormNotes('');
  };

  const handleOpenAddModal = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (season: HistoricalSeason) => {
    setEditingSeasonId(season.id);
    setFormFarmName(season.farmName);
    setFormFieldName(season.fieldName);
    setFormYear(season.year);
    setFormSeasonType(season.seasonType);
    setFormCrop(season.crop);
    setFormVariety(season.variety || '');
    setFormSowingDate(season.sowingDate || '');
    setFormHarvestDate(season.harvestDate || '');
    setFormAreaAcres(season.areaAcres ? String(season.areaAcres) : '');
    setFormYieldQty(season.yieldQuantity ? String(season.yieldQuantity) : '');
    setFormYieldUnit((season.yieldUnit as any) || 'tonnes/ac');
    setFormN(season.soilTest?.n ? String(season.soilTest.n) : '');
    setFormP(season.soilTest?.p ? String(season.soilTest.p) : '');
    setFormK(season.soilTest?.k ? String(season.soilTest.k) : '');
    setFormPh(season.soilTest?.ph ? String(season.soilTest.ph) : '');
    setFormFertilizerProduct(season.fertilizers?.[0]?.product || '');
    setFormFertilizerCost(season.fertilizers?.[0]?.cost ? String(season.fertilizers[0].cost) : '');
    setFormPesticideProduct(season.pesticides?.[0]?.product || '');
    setFormPesticideCost(season.pesticides?.[0]?.cost ? String(season.pesticides[0].cost) : '');
    setFormIrrigationMethod(season.irrigation?.method || 'Drip');
    setFormIrrigationCost(season.irrigation?.cost ? String(season.irrigation.cost) : '');
    setFormWeatherNotes(season.weatherObservations || '');
    setFormProductionCost(season.economics?.inputCost ? String(season.economics.inputCost) : '');
    setFormSellingPrice(season.economics?.sellingPrice ? String(season.economics.sellingPrice) : '');
    setFormRevenue(season.economics?.revenue ? String(season.economics.revenue) : '');
    setFormNetProfit(season.economics?.profit ? String(season.economics.profit) : '');
    setFormLearnings(season.learnings.join('\n'));
    setFormNotes(season.farmerNotes || '');
    setIsModalOpen(true);
  };

  const handleSaveSeason = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formCrop.trim()) {
      setErrorMessage('Crop name is required.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setStatusMessage(null);

    const fullSeasonName = `${formSeasonType} ${formYear}`;
    const learningsArray = formLearnings
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);

    const newRecord: HistoricalSeason = {
      id: editingSeasonId || `season-${Date.now()}`,
      farmId: 'farm-1',
      farmName: formFarmName.trim() || 'My Farm',
      fieldId: 'field-1',
      fieldName: formFieldName.trim() || 'Field 1',
      year: Number(formYear) || new Date().getFullYear(),
      seasonName: fullSeasonName,
      seasonType: formSeasonType,
      crop: formCrop.trim(),
      variety: formVariety.trim() || undefined,
      sowingDate: formSowingDate || undefined,
      harvestDate: formHarvestDate || undefined,
      areaAcres: formAreaAcres ? parseFloat(formAreaAcres) : undefined,
      yieldQuantity: formYieldQty ? parseFloat(formYieldQty) : undefined,
      yieldUnit: formYieldUnit,
      soilTest: (formN || formP || formK || formPh) ? {
        n: formN ? parseFloat(formN) : undefined,
        p: formP ? parseFloat(formP) : undefined,
        k: formK ? parseFloat(formK) : undefined,
        ph: formPh ? parseFloat(formPh) : undefined
      } : undefined,
      fertilizers: formFertilizerProduct ? [
        {
          product: formFertilizerProduct.trim(),
          cost: formFertilizerCost ? parseFloat(formFertilizerCost) : undefined
        }
      ] : undefined,
      pesticides: formPesticideProduct ? [
        {
          product: formPesticideProduct.trim(),
          cost: formPesticideCost ? parseFloat(formPesticideCost) : undefined
        }
      ] : undefined,
      irrigation: {
        method: formIrrigationMethod,
        cost: formIrrigationCost ? parseFloat(formIrrigationCost) : undefined
      },
      weatherObservations: formWeatherNotes.trim() || undefined,
      economics: (formProductionCost || formRevenue || formNetProfit || formSellingPrice) ? {
        inputCost: formProductionCost ? parseFloat(formProductionCost) : undefined,
        sellingPrice: formSellingPrice ? parseFloat(formSellingPrice) : undefined,
        revenue: formRevenue ? parseFloat(formRevenue) : undefined,
        profit: formNetProfit ? parseFloat(formNetProfit) : undefined
      } : undefined,
      learnings: learningsArray,
      farmerNotes: formNotes.trim() || undefined,
      isDemo: !isAuthenticated
    };

    try {
      if (user && isAuthenticated) {
        // Authenticated Persistence: Ensure user farm & field exist
        let targetFarmId = '';
        let targetFieldId = '';
        const { data: existingFarms } = await supabase
          .from('farms')
          .select('id, fields(id)')
          .eq('user_id', user.id)
          .limit(1)
          .maybeSingle();

        if (existingFarms) {
          targetFarmId = existingFarms.id;
          if (existingFarms.fields?.[0]?.id) {
            targetFieldId = existingFarms.fields[0].id;
          } else {
            const { data: newField } = await supabase
              .from('fields')
              .insert({
                farm_id: targetFarmId,
                field_name: formFieldName.trim() || 'Field 1',
                area: formAreaAcres ? parseFloat(formAreaAcres) : 5
              })
              .select('id')
              .single();
            if (newField) targetFieldId = newField.id;
          }
        } else {
          const { data: newFarm } = await supabase
            .from('farms')
            .insert({
              user_id: user.id,
              farm_name: formFarmName.trim() || 'My Farm',
              total_area: formAreaAcres ? parseFloat(formAreaAcres) : 5
            })
            .select('id')
            .single();
          if (newFarm) {
            targetFarmId = newFarm.id;
            const { data: newField } = await supabase
              .from('fields')
              .insert({
                farm_id: targetFarmId,
                field_name: formFieldName.trim() || 'Field 1',
                area: formAreaAcres ? parseFloat(formAreaAcres) : 5
              })
              .select('id')
              .single();
            if (newField) targetFieldId = newField.id;
          }
        }

        if (targetFieldId) {
          const isRealUuid = editingSeasonId && !editingSeasonId.startsWith('demo-') && !editingSeasonId.startsWith('season-');
          const { data: savedSeason, error: seasonErr } = await supabase
            .from('seasons')
            .upsert({
              id: isRealUuid ? editingSeasonId : undefined,
              field_id: targetFieldId,
              season_name: fullSeasonName,
              crop: formCrop.trim(),
              crop_variety: formVariety.trim() || null,
              sowing_date: formSowingDate || null,
              actual_harvest_date: formHarvestDate || null,
              status: 'COMPLETED'
            })
            .select('id')
            .single();

          if (seasonErr) throw seasonErr;

          const seasonUuid = savedSeason?.id || (isRealUuid ? editingSeasonId : undefined);

          if (seasonUuid && targetFarmId) {
            newRecord.id = seasonUuid;
            newRecord.fieldId = targetFieldId;
            newRecord.farmId = targetFarmId;

            // Store extended agronomic attributes in farm_data_records
            const extendedData = {
              yieldQuantity: newRecord.yieldQuantity,
              yieldUnit: newRecord.yieldUnit,
              soilTest: newRecord.soilTest,
              fertilizers: newRecord.fertilizers,
              pesticides: newRecord.pesticides,
              irrigation: newRecord.irrigation,
              weatherObservations: newRecord.weatherObservations,
              economics: newRecord.economics,
              learnings: newRecord.learnings,
              farmerNotes: newRecord.farmerNotes
            };

            await supabase
              .from('farm_data_records')
              .delete()
              .eq('season_id', seasonUuid)
              .eq('record_type', 'historical_season_detail');

            await supabase
              .from('farm_data_records')
              .insert({
                farm_id: targetFarmId,
                field_id: targetFieldId,
                season_id: seasonUuid,
                record_type: 'historical_season_detail',
                record_data: extendedData,
                source: 'farmer_manual_entry',
                reliability: 1.0,
                created_by: user.id
              });
          }
        }
      }

      // Update local state and localStorage
      setSeasons((prev) => {
        let updated: HistoricalSeason[];
        if (editingSeasonId) {
          updated = prev.map((s) => (s.id === editingSeasonId ? newRecord : s));
        } else {
          updated = [newRecord, ...prev];
        }
        try {
          localStorage.setItem('kisancare_historical_seasons', JSON.stringify(updated));
        } catch {
          // localStorage disabled
        }
        return updated;
      });

      setSelectedSeasonId(newRecord.id);
      setIsModalOpen(false);
      resetForm();
      setStatusMessage(`Historical season "${fullSeasonName} (${newRecord.crop})" saved successfully!`);
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to save historical season:', err);
      setErrorMessage(`Failed to persist season: ${err.message || String(err)}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteSeason = async (season: HistoricalSeason) => {
    if (!window.confirm(`Are you sure you want to delete "${season.seasonName} (${season.crop})"?`)) {
      return;
    }

    setErrorMessage(null);
    try {
      if (user && isAuthenticated && !season.id.startsWith('demo-') && !season.id.startsWith('season-')) {
        await supabase.from('farm_data_records').delete().eq('season_id', season.id);
        const { error } = await supabase.from('seasons').delete().eq('id', season.id);
        if (error) throw error;
      }

      setSeasons((prev) => {
        const next = prev.filter((s) => s.id !== season.id);
        try {
          localStorage.setItem('kisancare_historical_seasons', JSON.stringify(next));
        } catch {}
        if (selectedSeasonId === season.id && next.length > 0) {
          setSelectedSeasonId(next[0].id);
        }
        return next;
      });

      setStatusMessage(`Season "${season.seasonName}" removed.`);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      console.error('Delete failed:', err);
      setErrorMessage(`Failed to delete season: ${err.message || String(err)}`);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Memory</h1>
            {isAuthenticated ? (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <Database size={11} className="text-emerald-700" />
                Connected Farm Records
              </span>
            ) : (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Historical Logs
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1 text-sm">
            Permanent institutional memory: historical crop performance, input costs, soil health, and empirical learnings.
          </p>
        </div>

        <button
          onClick={handleOpenAddModal}
          className="bg-[#103D2C] hover:bg-[#17643E] text-white px-4 py-2.5 rounded-xl font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
        >
          <Plus size={16} />
          <span>+ Add Historical Season</span>
        </button>
      </div>

      {statusMessage && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-xs">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Persistence Architecture Notice */}
      <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-2xl p-4 text-xs text-[#292B26]/80 flex items-start gap-3">
        <Database size={16} className="text-[#17643E] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#103D2C]">Institutional Storage Architecture</span>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.2 rounded-full border border-emerald-200">
              {isAuthenticated ? 'Live Supabase Sync' : 'Demo Mode / Browser Storage'}
            </span>
          </div>
          <p className="text-[11px] leading-relaxed">
            Core season records (crop, variety, planting and harvest dates, field association) are mapped directly to the Supabase <code className="bg-white px-1 py-0.5 rounded border border-[#E5DDCF] font-mono text-[10px]">seasons</code> table. Extended farm intelligence (recorded yield, soil test values, input applications, production costs, and empirical learnings) is persisted to <code className="bg-white px-1 py-0.5 rounded border border-[#E5DDCF] font-mono text-[10px]">farm_data_records</code> (JSONB) with client-side caching, ensuring complete data retention across sessions.
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-2xl p-2 shadow-xs border border-[#E5DDCF] flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('records')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'records'
              ? 'bg-[#103D2C] text-white shadow-xs'
              : 'text-[#292B26]/70 hover:bg-[#FBF7EF]'
          }`}
        >
          <Calendar size={14} />
          <span>Season Records & Details</span>
        </button>
        <button
          onClick={() => setActiveTab('comparison')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'comparison'
              ? 'bg-[#103D2C] text-white shadow-xs'
              : 'text-[#292B26]/70 hover:bg-[#FBF7EF]'
          }`}
        >
          <BarChart3 size={14} />
          <span>Historical Comparison View</span>
        </button>
        <button
          onClick={() => setActiveTab('lessons')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'lessons'
              ? 'bg-[#103D2C] text-white shadow-xs'
              : 'text-[#292B26]/70 hover:bg-[#FBF7EF]'
          }`}
        >
          <BookOpen size={14} />
          <span>Empirical Lessons</span>
        </button>
        <button
          onClick={() => setActiveTab('connections')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
            activeTab === 'connections'
              ? 'bg-[#103D2C] text-white shadow-xs'
              : 'text-[#292B26]/70 hover:bg-[#FBF7EF]'
          }`}
        >
          <Layers size={14} />
          <span>Connected Decision Modules</span>
        </button>
      </div>

      {/* TAB 1: Season Records & Details */}
      {activeTab === 'records' && (
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
          {/* Season Selector Cards */}
          <div className="p-6 border-b border-[#E5DDCF] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoading ? (
              <div className="col-span-full py-8 text-center text-xs text-[#292B26]/60">
                <Loader2 className="w-6 h-6 animate-spin text-[#103D2C] mx-auto mb-2" />
                Loading historical farm seasons...
              </div>
            ) : seasons.length === 0 ? (
              <div className="col-span-full py-8 text-center text-xs text-[#292B26]/60">
                No historical seasons recorded yet. Click "+ Add Historical Season" above to record your previous harvests.
              </div>
            ) : (
              seasons.map((s) => {
                const isSelected = s.id === selectedSeasonId;
                return (
                  <div
                    key={s.id}
                    onClick={() => setSelectedSeasonId(s.id)}
                    className={`rounded-xl border p-4 flex justify-between items-center cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-[#FBF7EF] border-[#17643E] ring-1 ring-[#17643E]/20 shadow-xs'
                        : 'bg-white border-[#E5DDCF] hover:bg-[#FBF7EF]/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-11 h-11 rounded-full flex items-center justify-center shrink-0 ${
                          isSelected ? 'bg-[#17643E] text-white' : 'bg-[#FBF7EF] text-[#292B26]/60'
                        }`}
                      >
                        <Calendar className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-[#103D2C] flex items-center gap-1.5">
                          <span>{s.seasonName}</span>
                          {s.isDemo && (
                            <span className="text-[9px] bg-amber-50 text-amber-700 px-1 py-0.2 rounded border border-amber-200">
                              Demo
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-[#292B26]/60">
                          {s.crop} {s.variety ? `(${s.variety})` : ''} • {s.yieldQuantity ? `${s.yieldQuantity} ${s.yieldUnit}` : 'Yield unrecorded'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Details of Selected Season */}
          {selectedSeason && (
            <div className="p-6 space-y-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-[#E5DDCF]">
                <div>
                  <h3 className="font-serif font-bold text-xl text-[#103D2C] flex items-center gap-2">
                    <span>{selectedSeason.seasonName}: {selectedSeason.crop}</span>
                    {selectedSeason.variety && (
                      <span className="text-sm font-normal text-[#292B26]/60">({selectedSeason.variety})</span>
                    )}
                  </h3>
                  <p className="text-xs text-[#292B26]/60 mt-0.5">
                    {selectedSeason.farmName} • {selectedSeason.fieldName} {selectedSeason.areaAcres ? `(${selectedSeason.areaAcres} Acres)` : ''}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenEditModal(selectedSeason)}
                    className="p-2 text-[#103D2C] hover:bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors"
                  >
                    <Edit3 size={14} />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => handleDeleteSeason(selectedSeason)}
                    className="p-2 text-red-600 hover:bg-red-50 border border-red-200 rounded-lg text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors"
                  >
                    <Trash2 size={14} />
                    <span>Delete</span>
                  </button>
                </div>
              </div>

              {/* Primary Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
                  <p className="text-xs text-[#292B26]/60 mb-1">Harvested Yield</p>
                  <div className="text-lg font-bold text-[#103D2C]">
                    {selectedSeason.yieldQuantity !== undefined ? `${selectedSeason.yieldQuantity} ${selectedSeason.yieldUnit}` : '—'}
                  </div>
                  <span className="text-[10px] text-[#292B26]/50">
                    {selectedSeason.harvestDate ? `Harvested ${selectedSeason.harvestDate}` : 'Date unrecorded'}
                  </span>
                </div>

                <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
                  <p className="text-xs text-[#292B26]/60 mb-1">Net Profitability</p>
                  <div className="text-lg font-bold text-[#17643E]">
                    {selectedSeason.economics?.profit !== undefined ? `₹${selectedSeason.economics.profit.toLocaleString()}` : '—'}
                  </div>
                  <span className="text-[10px] text-[#292B26]/50">
                    {selectedSeason.economics?.revenue !== undefined ? `Rev: ₹${selectedSeason.economics.revenue.toLocaleString()}` : 'Revenue not logged'}
                  </span>
                </div>

                <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
                  <p className="text-xs text-[#292B26]/60 mb-1">Production Expenses</p>
                  <div className="text-lg font-bold text-[#292B26]">
                    {selectedSeason.economics?.inputCost !== undefined ? `₹${selectedSeason.economics.inputCost.toLocaleString()}` : '—'}
                  </div>
                  <span className="text-[10px] text-[#292B26]/50">Fertilizer, seed & labor</span>
                </div>

                <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
                  <p className="text-xs text-[#292B26]/60 mb-1">Irrigation Method</p>
                  <div className="text-base font-bold text-[#103D2C]">
                    {selectedSeason.irrigation?.method || '—'}
                  </div>
                  <span className="text-[10px] text-[#292B26]/50">
                    {selectedSeason.irrigation?.hoursTotal ? `${selectedSeason.irrigation.hoursTotal} hrs pumped` : 'Hours not logged'}
                  </span>
                </div>
              </div>

              {/* Detailed Breakdown Accordion / Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Soil & Nutrient Memory */}
                <div className="bg-white border border-[#E5DDCF] rounded-xl p-5 space-y-3">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                    <FlaskConical size={14} className="text-[#17643E]" /> Recorded Soil Health
                  </h4>
                  {selectedSeason.soilTest ? (
                    <div className="grid grid-cols-4 gap-2 text-center pt-1">
                      <div className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF]">
                        <span className="text-[10px] text-[#292B26]/60 block">N</span>
                        <span className="font-bold text-xs text-[#103D2C]">{selectedSeason.soilTest.n ?? '—'}</span>
                        <span className="text-[9px] text-[#292B26]/50 block">kg/ha</span>
                      </div>
                      <div className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF]">
                        <span className="text-[10px] text-[#292B26]/60 block">P</span>
                        <span className="font-bold text-xs text-[#103D2C]">{selectedSeason.soilTest.p ?? '—'}</span>
                        <span className="text-[9px] text-[#292B26]/50 block">kg/ha</span>
                      </div>
                      <div className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF]">
                        <span className="text-[10px] text-[#292B26]/60 block">K</span>
                        <span className="font-bold text-xs text-[#103D2C]">{selectedSeason.soilTest.k ?? '—'}</span>
                        <span className="text-[9px] text-[#292B26]/50 block">kg/ha</span>
                      </div>
                      <div className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF]">
                        <span className="text-[10px] text-[#292B26]/60 block">pH</span>
                        <span className="font-bold text-xs text-[#103D2C]">{selectedSeason.soilTest.ph ?? '—'}</span>
                        <span className="text-[9px] text-[#292B26]/50 block">Index</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[#292B26]/60 italic">No soil laboratory test recorded for this season.</p>
                  )}

                  {/* Fertilizers List */}
                  <div className="pt-2">
                    <span className="text-xs font-semibold text-[#292B26] block mb-1.5">Fertilizers Applied:</span>
                    {selectedSeason.fertilizers && selectedSeason.fertilizers.length > 0 ? (
                      <div className="space-y-1.5">
                        {selectedSeason.fertilizers.map((f, i) => (
                          <div key={i} className="flex justify-between text-xs bg-[#FBF7EF] p-2 rounded-lg border border-[#E5DDCF]">
                            <span className="font-medium text-[#103D2C]">{f.product}</span>
                            <span className="text-[#292B26]/70">
                              {f.quantityKg ? `${f.quantityKg} kg` : ''} {f.cost ? `(₹${f.cost})` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-[#292B26]/60 italic">No specific fertilizer applications logged.</p>
                    )}
                  </div>
                </div>

                {/* Crop Protection & Weather */}
                <div className="bg-white border border-[#E5DDCF] rounded-xl p-5 space-y-3">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                    <Bug size={14} className="text-[#17643E]" /> Pest, Disease & Weather Notes
                  </h4>
                  {selectedSeason.weatherObservations && (
                    <div className="bg-[#FBF7EF] p-3 rounded-lg border border-[#E5DDCF]">
                      <div className="flex items-center gap-1 text-[11px] font-bold text-[#103D2C] mb-1">
                        <Wind size={12} className="text-[#17643E]" /> Climate & Rainfall Observations:
                      </div>
                      <p className="text-xs text-[#292B26]/80">{selectedSeason.weatherObservations}</p>
                    </div>
                  )}

                  <div className="pt-1">
                    <span className="text-xs font-semibold text-[#292B26] block mb-1.5">Plant Protection Products:</span>
                    {selectedSeason.pesticides && selectedSeason.pesticides.length > 0 ? (
                      <div className="space-y-1.5">
                        {selectedSeason.pesticides.map((p, i) => (
                          <div key={i} className="flex justify-between text-xs bg-[#FBF7EF] p-2 rounded-lg border border-[#E5DDCF]">
                            <div>
                              <span className="font-medium text-[#103D2C] block">{p.product}</span>
                              {p.targetPest && <span className="text-[10px] text-[#292B26]/60">Target: {p.targetPest}</span>}
                            </div>
                            <span className="text-[#292B26]/70 self-center">
                              {p.quantityMl ? `${p.quantityMl} ml` : ''} {p.cost ? `(₹${p.cost})` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-[#292B26]/60 italic">No pesticide or bio-control treatments logged.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Farmer Learnings & Empirical Notes */}
              <div className="bg-white border border-[#E5DDCF] rounded-xl p-5 space-y-3">
                <h4 className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                  <BookOpen size={14} className="text-[#17643E]" /> Lessons Learned & Retained Practices
                </h4>
                {selectedSeason.learnings.length > 0 ? (
                  <ul className="space-y-2">
                    {selectedSeason.learnings.map((item, i) => (
                      <li key={i} className="bg-[#FBF7EF] p-3 rounded-lg text-xs text-[#292B26]/90 flex gap-2.5 items-start border border-[#E5DDCF]/70">
                        <Sprout className="w-4 h-4 text-[#17643E] shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-[#292B26]/60 italic">No specific lessons logged for this season.</p>
                )}

                {selectedSeason.farmerNotes && (
                  <div className="pt-2 text-xs text-[#292B26]/75 border-t border-[#E5DDCF]/60">
                    <span className="font-semibold text-[#103D2C]">Farmer Field Notes: </span>
                    {selectedSeason.farmerNotes}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Historical Comparison View */}
      {activeTab === 'comparison' && (
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-6">
          <div>
            <h3 className="text-lg font-serif font-bold text-[#103D2C]">Multi-Season Performance Comparison</h3>
            <p className="text-xs text-[#292B26]/70 mt-1">
              Compare harvested yield, profit, input costs, and fertilizer expenditure across recorded seasons.
              (Note: Unrecorded values are denoted as "— Not recorded" to prevent distorted zero calculations).
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-[#FBF7EF] text-[#103D2C] border-b border-[#E5DDCF] uppercase text-[11px] font-bold">
                <tr>
                  <th className="py-3 px-4">Season</th>
                  <th className="py-3 px-4">Crop & Variety</th>
                  <th className="py-3 px-4">Yield</th>
                  <th className="py-3 px-4">Profitability</th>
                  <th className="py-3 px-4">Fertilizer Cost</th>
                  <th className="py-3 px-4">Irrigation</th>
                  <th className="py-3 px-4">Weather Context</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5DDCF]">
                {seasons.map((s) => {
                  const totalFertCost = s.fertilizers?.reduce((acc, curr) => acc + (curr.cost || 0), 0);
                  return (
                    <tr key={s.id} className="hover:bg-[#FBF7EF]/50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-[#103D2C]">
                        {s.seasonName}
                        {s.isDemo && (
                          <span className="ml-1.5 text-[9px] bg-amber-50 text-amber-700 px-1 py-0.2 rounded border border-amber-200">
                            Sample
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-[#292B26]">{s.crop}</span>
                        {s.variety && <span className="text-xs text-[#292B26]/60 block">{s.variety}</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        {s.yieldQuantity !== undefined ? (
                          <span className="font-bold text-[#103D2C]">{s.yieldQuantity} {s.yieldUnit}</span>
                        ) : (
                          <span className="text-[#292B26]/40 italic">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {s.economics?.profit !== undefined ? (
                          <span className="font-bold text-emerald-800">₹{s.economics.profit.toLocaleString()}</span>
                        ) : (
                          <span className="text-[#292B26]/40 italic">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {totalFertCost ? (
                          <span className="text-[#292B26]">₹{totalFertCost.toLocaleString()}</span>
                        ) : (
                          <span className="text-[#292B26]/40 italic">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-xs text-[#292B26]">{s.irrigation?.method || '—'}</span>
                        {s.irrigation?.hoursTotal && (
                          <span className="text-[10px] text-[#292B26]/60 block">{s.irrigation.hoursTotal} hrs</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 max-w-xs truncate text-xs text-[#292B26]/70" title={s.weatherObservations}>
                        {s.weatherObservations || '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Empirical Lessons */}
      {activeTab === 'lessons' && (
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-6">
          <div>
            <h3 className="text-lg font-serif font-bold text-[#103D2C]">Empirical Farm Observations</h3>
            <p className="text-xs text-[#292B26]/70 mt-1">
              Practices validated on your soil based exclusively on recorded historical cycles.
            </p>
          </div>

          <div className="space-y-4">
            {seasons.map((s) => (
              <div key={s.id} className="border border-[#E5DDCF] rounded-xl p-5 bg-[#FBF7EF]/40 space-y-2">
                <div className="flex items-center justify-between border-b border-[#E5DDCF]/60 pb-2">
                  <span className="font-bold text-sm text-[#103D2C]">{s.seasonName} • {s.crop}</span>
                  <span className="text-xs text-[#292B26]/60">{s.fieldName}</span>
                </div>
                {s.learnings.length > 0 ? (
                  <ul className="space-y-1.5 pt-1">
                    {s.learnings.map((l, idx) => (
                      <li key={idx} className="text-xs text-[#292B26]/85 flex items-start gap-2">
                        <Sprout size={14} className="text-[#17643E] shrink-0 mt-0.5" />
                        <span>{l}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-[#292B26]/50 italic">No structured lessons entered for this season.</p>
                )}
              </div>
            ))}
          </div>

          <div className="bg-[#FBF7EF] border border-[#E5DDCF] p-4 rounded-xl text-xs text-[#292B26]/70 flex items-start gap-2">
            <Info size={16} className="text-[#103D2C] shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-[#103D2C]">Scientific Caution: </span>
              Farm insights reflect direct field observations. Correlated factors (e.g. fertilizer rate and yield in a single season) are recorded as historical context and should not be interpreted as absolute agronomic causation without replicated soil and weather controls.
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Connected Decision Modules */}
      {activeTab === 'connections' && (
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-6">
          <div>
            <h3 className="text-lg font-serif font-bold text-[#103D2C]">How Farm Memory Powers Other Modules</h3>
            <p className="text-xs text-[#292B26]/70 mt-1">
              Historical records serve as real baseline inputs for predictive planning across KISANcare.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-[#E5DDCF] rounded-xl p-5 bg-[#FBF7EF]/30 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-sm text-[#103D2C] flex items-center gap-1.5">
                  <Sprout size={16} className="text-[#17643E]" /> Crop Intelligence
                </h4>
                <button
                  onClick={() => navigate('/crop-recommendation')}
                  className="text-xs text-[#17643E] font-semibold hover:underline flex items-center gap-1"
                >
                  Open <ChevronRight size={12} />
                </button>
              </div>
              <p className="text-xs text-[#292B26]/75">
                Supplies previous crop history for rotation planning (preventing monoculture soil depletion) and historical yield benchmarks.
              </p>
            </div>

            <div className="border border-[#E5DDCF] rounded-xl p-5 bg-[#FBF7EF]/30 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-sm text-[#103D2C] flex items-center gap-1.5">
                  <FlaskConical size={16} className="text-[#17643E]" /> Soil Intelligence
                </h4>
                <button
                  onClick={() => navigate('/soil')}
                  className="text-xs text-[#17643E] font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                >
                  Open <ChevronRight size={12} />
                </button>
              </div>
              <p className="text-xs text-[#292B26]/75">
                Tracks multi-year NPK and pH trends across seasons, identifying gradual depletion of organic carbon and phosphorus.
              </p>
            </div>

            <div className="border border-[#E5DDCF] rounded-xl p-5 bg-[#FBF7EF]/30 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-sm text-[#103D2C] flex items-center gap-1.5">
                  <DollarSign size={16} className="text-[#17643E]" /> Farm Economics
                </h4>
                <button
                  onClick={() => navigate('/farm-economics')}
                  className="text-xs text-[#17643E] font-semibold hover:underline flex items-center gap-1"
                >
                  Open <ChevronRight size={12} />
                </button>
              </div>
              <p className="text-xs text-[#292B26]/75">
                Supplies empirical input costs and historical selling prices (₹/qtl) to refine break-even predictions and crop budgets.
              </p>
            </div>

            <div className="border border-[#E5DDCF] rounded-xl p-5 bg-[#FBF7EF]/30 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-sm text-[#103D2C] flex items-center gap-1.5">
                  <Droplets size={16} className="text-[#17643E]" /> Irrigation & Climate
                </h4>
                <button
                  onClick={() => navigate('/irrigation-climate')}
                  className="text-xs text-[#17643E] font-semibold hover:underline flex items-center gap-1"
                >
                  Open <ChevronRight size={12} />
                </button>
              </div>
              <p className="text-xs text-[#292B26]/75">
                Supplies past water stress observations and dry-spell logs to benchmark supplementary irrigation schedules.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal: + Add / Edit Historical Season */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-[#E5DDCF] shadow-xl p-6 space-y-5">
            <div className="flex justify-between items-center border-b border-[#E5DDCF] pb-3">
              <div>
                <h3 className="font-serif font-bold text-lg text-[#103D2C]">
                  {editingSeasonId ? 'Edit Historical Season' : '+ Add Historical Season Record'}
                </h3>
                <p className="text-xs text-[#292B26]/60">
                  Record previous crop performance. Enter only the historical details you have recorded.
                </p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-[#292B26]/50 hover:text-[#103D2C] p-1.5 rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveSeason} className="space-y-4 text-xs">
              {/* Row 1: Season & Crop Identifiers (Required) */}
              <div className="bg-[#FBF7EF] p-4 rounded-xl border border-[#E5DDCF] space-y-3">
                <h4 className="font-bold text-[#103D2C] text-[11px] uppercase tracking-wider">
                  Basic Season Details <span className="text-red-600">* Required</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Season</label>
                    <select
                      value={formSeasonType}
                      onChange={(e) => setFormSeasonType(e.target.value as any)}
                      className="w-full bg-white border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    >
                      <option value="Kharif">Kharif (Monsoon)</option>
                      <option value="Rabi">Rabi (Winter)</option>
                      <option value="Summer">Summer (Zaid)</option>
                      <option value="Whole Year">Whole Year</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Year</label>
                    <input
                      type="number"
                      min="2010"
                      max="2035"
                      value={formYear}
                      onChange={(e) => setFormYear(Number(e.target.value))}
                      className="w-full bg-white border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Crop Name *</label>
                    <input
                      type="text"
                      placeholder="e.g. Soybean, Wheat"
                      value={formCrop}
                      onChange={(e) => setFormCrop(e.target.value)}
                      required
                      className="w-full bg-white border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Crop Variety (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. JS 335, GW 322"
                      value={formVariety}
                      onChange={(e) => setFormVariety(e.target.value)}
                      className="w-full bg-white border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Field Name (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. Field 1 (North Parcel)"
                      value={formFieldName}
                      onChange={(e) => setFormFieldName(e.target.value)}
                      className="w-full bg-white border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Row 2: Sowing, Harvest & Yield */}
              <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-3">
                <h4 className="font-bold text-[#103D2C] text-[11px] uppercase tracking-wider">
                  Timeline & Yield Output (Optional)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Sowing Date</label>
                    <input
                      type="date"
                      value={formSowingDate}
                      onChange={(e) => setFormSowingDate(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Harvest Date</label>
                    <input
                      type="date"
                      value={formHarvestDate}
                      onChange={(e) => setFormHarvestDate(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Harvested Yield</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 2.6"
                      value={formYieldQty}
                      onChange={(e) => setFormYieldQty(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Unit</label>
                    <select
                      value={formYieldUnit}
                      onChange={(e) => setFormYieldUnit(e.target.value as any)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    >
                      <option value="tonnes/ac">tonnes/ac</option>
                      <option value="qtl/ac">quintals/ac</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Row 3: Optional Soil Test */}
              <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-3">
                <h4 className="font-bold text-[#103D2C] text-[11px] uppercase tracking-wider">
                  Recorded Soil Test (Optional)
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Nitrogen (kg/ha)</label>
                    <input
                      type="number"
                      placeholder="e.g. 22"
                      value={formN}
                      onChange={(e) => setFormN(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Phosphorus (kg/ha)</label>
                    <input
                      type="number"
                      placeholder="e.g. 28"
                      value={formP}
                      onChange={(e) => setFormP(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Potassium (kg/ha)</label>
                    <input
                      type="number"
                      placeholder="e.g. 175"
                      value={formK}
                      onChange={(e) => setFormK(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Soil pH</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 7.1"
                      value={formPh}
                      onChange={(e) => setFormPh(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Row 4: Inputs, Costs & Economics */}
              <div className="bg-white p-4 rounded-xl border border-[#E5DDCF] space-y-3">
                <h4 className="font-bold text-[#103D2C] text-[11px] uppercase tracking-wider">
                  Expenses & Profitability (Optional)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Total Production Cost (₹)</label>
                    <input
                      type="number"
                      placeholder="e.g. 15000"
                      value={formProductionCost}
                      onChange={(e) => setFormProductionCost(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Gross Revenue (₹)</label>
                    <input
                      type="number"
                      placeholder="e.g. 45000"
                      value={formRevenue}
                      onChange={(e) => setFormRevenue(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#292B26] mb-1">Net Profit (₹)</label>
                    <input
                      type="number"
                      placeholder="e.g. 30000"
                      value={formNetProfit}
                      onChange={(e) => setFormNetProfit(e.target.value)}
                      className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* Row 5: Notes & Observations */}
              <div>
                <label className="block font-semibold text-[#292B26] mb-1">
                  Empirical Learnings (One per line)
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Second irrigation at CRI stage prevented lodging."
                  value={formLearnings}
                  onChange={(e) => setFormLearnings(e.target.value)}
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg p-2 text-xs"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-[#E5DDCF]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-[#292B26]/70 hover:bg-[#FBF7EF] rounded-lg text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="bg-[#103D2C] hover:bg-[#17643E] text-white px-5 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {isSaving ? <Loader2 size={14} className="animate-spin" /> : null}
                  <span>{isSaving ? 'Saving...' : 'Save Historical Season'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
