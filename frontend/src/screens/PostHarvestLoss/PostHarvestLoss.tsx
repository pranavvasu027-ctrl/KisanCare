import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { translateDynamic } from '../../i18n/translateHelper';
import {
  Package, AlertTriangle, TrendingDown, Clock, ShieldCheck,
  ArrowRight, Loader2, Sparkles, CheckCircle2, Warehouse,
  Filter, Search, Plus, Trash2, RefreshCw, X, FileText,
  Truck, Scissors, Store, AlertCircle, Info, ChevronRight,
  TrendingUp, Database, Download
} from 'lucide-react';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, Legend, CartesianGrid, Cell
} from 'recharts';
import {
  api, LossRecord, PostHarvestCrop, PostHarvestStage
} from '../../services/api';

// Baseline mandi prices in Vidarbha/Maharashtra region
const CROP_PRICES: Record<PostHarvestCrop, number> = {
  Cotton: 7280,
  Soyabean: 4640
};

// Safe moisture guidelines for storage
const MOISTURE_THRESHOLDS: Record<PostHarvestCrop, { optimal: number; warning: number; unit: string }> = {
  Cotton: { optimal: 8.0, warning: 10.0, unit: '%' },
  Soyabean: { optimal: 10.0, warning: 12.5, unit: '%' }
};

export default function PostHarvestLoss() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  // Global View Controls
  const [selectedCropFilter, setSelectedCropFilter] = useState<'ALL' | PostHarvestCrop>('ALL');
  const [records, setRecords] = useState<LossRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isDemo, setIsDemo] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Table Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [stageFilter, setStageFilter] = useState<'ALL' | PostHarvestStage>('ALL');
  const [sortBy, setSortBy] = useState<'date' | 'lossQty' | 'lossPct' | 'financial'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Modal State for New Record
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formCrop, setFormCrop] = useState<PostHarvestCrop>('Cotton');
  const [formBatchId, setFormBatchId] = useState('');
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0]);
  const [formStage, setFormStage] = useState<PostHarvestStage>('Harvest');
  const [formStageQty, setFormStageQty] = useState<number>(100);
  const [formObservedLoss, setFormObservedLoss] = useState<number>(3.5);
  const [formCause, setFormCause] = useState('Boll rot & trash contamination during manual picking');
  const [formFacility, setFormFacility] = useState('Manual Picking / Cloth Bags');
  const [formRecoverable, setFormRecoverable] = useState<number>(1.0);
  const [formNotes, setFormNotes] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [formSubmitting, setFormSubmitting] = useState(false);

  // Storage Simulator State (Restricted to Cotton & Soyabean only)
  const [simCrop, setSimCrop] = useState<PostHarvestCrop>('Cotton');
  const [simQuantity, setSimQuantity] = useState<number>(100);
  const [simStorageType, setSimStorageType] = useState('Traditional Gunny Bags');
  const [simStorageDays, setSimStorageDays] = useState<number>(60);
  const [simMoisture, setSimMoisture] = useState<number>(8.5);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<{
    lossPercentage: number;
    quantityLostQtl: number;
    financialLossRs: number;
    spoilageRisk: 'Low' | 'Moderate' | 'High';
    maxSafeDays: number;
    recommendations: string[];
    sellVsHoldAdvice: string;
  } | null>(null);

  // Load records on mount or refresh
  useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const res = await api.getPostHarvestRecords('ALL');
      setRecords(res.data);
      setIsDemo(res.isDemo);
    } catch (err) {
      console.error('Error loading records:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadRecords();
      setSuccessMessage('Data synchronized successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } finally {
      setRefreshing(false);
    }
  };

  const handleResetSampleData = async () => {
    if (window.confirm('Reset all records to standard demonstration dataset for Cotton & Soyabean?')) {
      setLoading(true);
      const sample = await api.resetPostHarvestSampleData();
      setRecords(sample);
      setIsDemo(true);
      setLoading(false);
      setSuccessMessage('Demonstration dataset restored.');
      setTimeout(() => setSuccessMessage(null), 3000);
    }
  };

  // Filter records by crop context
  const scopedRecords = useMemo(() => {
    if (selectedCropFilter === 'ALL') return records;
    return records.filter(r => r.crop === selectedCropFilter);
  }, [records, selectedCropFilter]);

  // Dynamic Overall Metrics
  const overviewMetrics = useMemo(() => {
    // Unique batches or cumulative volume in scope
    const totalHarvestQtl = scopedRecords.reduce((acc, r) => acc + (r.stage === 'Harvest' ? r.stageQuantityQtl : 0), 0) ||
      scopedRecords.reduce((acc, r) => acc + r.stageQuantityQtl, 0);

    const totalLossQtl = Math.round(scopedRecords.reduce((acc, r) => acc + r.observedLossQtl, 0) * 10) / 10;
    const totalFinancialLossRs = scopedRecords.reduce((acc, r) => acc + r.financialLossRs, 0);
    const recoverableQtl = Math.round(scopedRecords.reduce((acc, r) => acc + r.recoverableQuantityQtl, 0) * 10) / 10;
    const recoverableFinancialRs = scopedRecords.reduce((acc, r) => {
      const price = CROP_PRICES[r.crop] || 5000;
      return acc + Math.round(r.recoverableQuantityQtl * price);
    }, 0);

    const lossPercentage = totalHarvestQtl > 0
      ? Math.round((totalLossQtl / totalHarvestQtl) * 1000) / 10
      : 0;

    const cottonRecords = records.filter(r => r.crop === 'Cotton');
    const soyabeanRecords = records.filter(r => r.crop === 'Soyabean');

    const cottonLoss = Math.round(cottonRecords.reduce((acc, r) => acc + r.observedLossQtl, 0) * 10) / 10;
    const soyabeanLoss = Math.round(soyabeanRecords.reduce((acc, r) => acc + r.observedLossQtl, 0) * 10) / 10;

    return {
      totalHarvestQtl: Math.round(totalHarvestQtl * 10) / 10,
      totalLossQtl,
      totalFinancialLossRs,
      lossPercentage,
      recoverableQtl,
      recoverableFinancialRs,
      cottonLoss,
      soyabeanLoss
    };
  }, [scopedRecords, records]);

  // Stage Journey Metrics (Harvest -> Handling -> Storage -> Transport -> Market)
  const journeyStages = useMemo(() => {
    const stages: PostHarvestStage[] = ['Harvest', 'Handling', 'Storage', 'Transport'];
    let runningQty = overviewMetrics.totalHarvestQtl || 260;

    return stages.map((stg) => {
      const stgRecords = scopedRecords.filter(r => r.stage === stg);
      const stgLossQtl = Math.round(stgRecords.reduce((acc, r) => acc + r.observedLossQtl, 0) * 10) / 10;
      const stgInputQty = stgRecords.reduce((acc, r) => acc + r.stageQuantityQtl, 0) || runningQty;
      const lossRate = stgInputQty > 0 ? Math.round((stgLossQtl / stgInputQty) * 1000) / 10 : 0;
      const retainedQty = Math.max(0, runningQty - stgLossQtl);
      runningQty = retainedQty;

      return {
        stage: stg,
        processedQtl: Math.round(stgInputQty * 10) / 10,
        lossQtl: stgLossQtl,
        lossRate,
        retainedQty: Math.round(retainedQty * 10) / 10,
        retentionRate: overviewMetrics.totalHarvestQtl > 0
          ? Math.round((retainedQty / overviewMetrics.totalHarvestQtl) * 1000) / 10
          : 90
      };
    });
  }, [scopedRecords, overviewMetrics]);

  // Chart Data: Loss by Stage comparison
  const stageChartData = useMemo(() => {
    const stages: PostHarvestStage[] = ['Harvest', 'Handling', 'Storage', 'Transport'];
    return stages.map(stg => {
      const cottonLoss = records
        .filter(r => r.crop === 'Cotton' && r.stage === stg)
        .reduce((acc, r) => acc + r.observedLossQtl, 0);

      const soyabeanLoss = records
        .filter(r => r.crop === 'Soyabean' && r.stage === stg)
        .reduce((acc, r) => acc + r.observedLossQtl, 0);

      return {
        stage: stg,
        Cotton: Math.round(cottonLoss * 10) / 10,
        Soyabean: Math.round(soyabeanLoss * 10) / 10
      };
    });
  }, [records]);

  // Primary Causes Breakdown
  const causeBreakdown = useMemo(() => {
    const causeGroups: Record<string, { qtl: number; count: number; crops: Set<PostHarvestCrop> }> = {
      'Moisture & Fungal Spoilage': { qtl: 0, count: 0, crops: new Set() },
      'Pest & Weevil Infestation': { qtl: 0, count: 0, crops: new Set() },
      'Mechanical & Threshing Damage': { qtl: 0, count: 0, crops: new Set() },
      'Transit Spillage & Tarp Leakage': { qtl: 0, count: 0, crops: new Set() },
      'Boll Rot & Trash Contamination': { qtl: 0, count: 0, crops: new Set() }
    };

    scopedRecords.forEach(r => {
      let matchedKey = 'Moisture & Fungal Spoilage';
      const cLower = r.cause.toLowerCase();

      if (cLower.includes('pest') || cLower.includes('weevil') || cLower.includes('larvae')) {
        matchedKey = 'Pest & Weevil Infestation';
      } else if (cLower.includes('mechanical') || cLower.includes('thresh') || cLower.includes('crack') || cLower.includes('shatter')) {
        matchedKey = 'Mechanical & Threshing Damage';
      } else if (cLower.includes('transit') || cLower.includes('spillage') || cLower.includes('trolley') || cLower.includes('puncture')) {
        matchedKey = 'Transit Spillage & Tarp Leakage';
      } else if (cLower.includes('boll') || cLower.includes('trash') || cLower.includes('picking')) {
        matchedKey = 'Boll Rot & Trash Contamination';
      } else {
        matchedKey = 'Moisture & Fungal Spoilage';
      }

      if (causeGroups[matchedKey]) {
        causeGroups[matchedKey].qtl += r.observedLossQtl;
        causeGroups[matchedKey].count += 1;
        causeGroups[matchedKey].crops.add(r.crop);
      }
    });

    const total = Object.values(causeGroups).reduce((acc, g) => acc + g.qtl, 0) || 1;
    return Object.entries(causeGroups).map(([name, data]) => ({
      name,
      qtl: Math.round(data.qtl * 10) / 10,
      percentage: Math.round((data.qtl / total) * 100),
      count: data.count,
      crops: Array.from(data.crops)
    })).sort((a, b) => b.qtl - a.qtl);
  }, [scopedRecords]);

  // Filtered & Sorted Table Records
  const filteredRecords = useMemo(() => {
    return scopedRecords.filter(r => {
      const matchesSearch = searchQuery === '' ||
        r.batchId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.cause.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.notes && r.notes.toLowerCase().includes(searchQuery.toLowerCase())) ||
        r.facilityOrMethod.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStage = stageFilter === 'ALL' || r.stage === stageFilter;
      return matchesSearch && matchesStage;
    }).sort((a, b) => {
      let valA: any = a.recordedAt;
      let valB: any = b.recordedAt;

      if (sortBy === 'lossQty') {
        valA = a.observedLossQtl;
        valB = b.observedLossQtl;
      } else if (sortBy === 'lossPct') {
        valA = a.lossPercentage;
        valB = b.lossPercentage;
      } else if (sortBy === 'financial') {
        valA = a.financialLossRs;
        valB = b.financialLossRs;
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [scopedRecords, searchQuery, stageFilter, sortBy, sortOrder]);

  // Open modal with pre-generated batch ID
  const handleOpenRecordModal = () => {
    const randomSuffix = Math.floor(100 + Math.random() * 900);
    const prefix = formCrop === 'Cotton' ? 'CT' : 'SB';
    setFormBatchId(`BATCH-${prefix}-2026-${randomSuffix}`);
    setFormErrors({});
    setIsModalOpen(true);
  };

  const handleCropChangeInForm = (newCrop: PostHarvestCrop) => {
    setFormCrop(newCrop);
    const randomSuffix = Math.floor(100 + Math.random() * 900);
    const prefix = newCrop === 'Cotton' ? 'CT' : 'SB';
    setFormBatchId(`BATCH-${prefix}-2026-${randomSuffix}`);

    if (newCrop === 'Cotton') {
      setFormCause('Boll rot & trash contamination during manual picking');
      setFormFacility('Manual Picking / Cloth Bags');
    } else {
      setFormCause('Mechanical threshing & seed coat cracking');
      setFormFacility('Mechanical Thresher');
    }
  };

  // Submit new loss record with strict validation
  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};

    if (!formBatchId.trim()) errors.batchId = 'Batch ID is required';
    if (!formDate) errors.date = 'Date is required';
    if (formStageQty <= 0) errors.stageQty = 'Quantity processed must be greater than 0';
    if (formObservedLoss < 0) errors.observedLoss = 'Observed loss cannot be negative';
    if (formObservedLoss > formStageQty) {
      errors.observedLoss = `Observed loss cannot exceed processed quantity (${formStageQty} Qtl)`;
    }
    if (formRecoverable < 0) errors.recoverable = 'Recoverable quantity cannot be negative';
    if (formRecoverable > formObservedLoss) {
      errors.recoverable = `Recoverable quantity cannot exceed observed loss (${formObservedLoss} Qtl)`;
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setFormSubmitting(true);
    try {
      const res = await api.savePostHarvestRecord({
        batchId: formBatchId.trim().toUpperCase(),
        crop: formCrop,
        harvestDate: formDate,
        stage: formStage,
        stageQuantityQtl: Number(formStageQty),
        observedLossQtl: Number(formObservedLoss),
        cause: formCause.trim(),
        facilityOrMethod: formFacility.trim(),
        recoverableQuantityQtl: Number(formRecoverable),
        notes: formNotes.trim()
      });

      setRecords(prev => [res.data, ...prev]);
      setIsDemo(false);
      setIsModalOpen(false);
      setSuccessMessage(`Loss record ${res.data.batchId} saved successfully.`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Error saving record:', err);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteRecord = async (id: string, batchId: string) => {
    if (window.confirm(`Are you sure you want to delete loss record ${batchId}?`)) {
      await api.deletePostHarvestRecord(id);
      setRecords(prev => prev.filter(r => r.id !== id));
      setSuccessMessage(`Record ${batchId} deleted.`);
      setTimeout(() => setSuccessMessage(null), 3000);
    }
  };

  // Run initial simulation for Cotton on mount
  useEffect(() => {
    handleRunSimulation();
  }, []);

  // Cotton & Soyabean Storage Loss Simulation Engine
  const handleRunSimulation = () => {
    setSimLoading(true);
    setTimeout(() => {
      // Base monthly loss rate
      let baseRate = simCrop === 'Cotton' ? 0.025 : 0.045;
      let maxDays = simCrop === 'Cotton' ? 120 : 90;

      // Storage modifier
      if (simStorageType.includes('Hermetic') || simStorageType.includes('Cold')) {
        baseRate *= 0.45;
        maxDays *= 1.7;
      } else if (simStorageType.includes('Shed')) {
        baseRate *= 1.25;
        maxDays *= 0.85;
      }

      // Moisture factor: above threshold accelerates spoilage
      const targetMoisture = MOISTURE_THRESHOLDS[simCrop].optimal;
      if (simMoisture > targetMoisture) {
        const excess = simMoisture - targetMoisture;
        baseRate += excess * 0.015;
        maxDays = Math.max(20, maxDays - excess * 15);
      }

      const daysFactor = simStorageDays / 60;
      const calcLossPct = Math.min(Math.round(baseRate * daysFactor * 100 * 10) / 10, 35);
      const lostQtl = Math.round((simQuantity * (calcLossPct / 100)) * 10) / 10;
      const avgPrice = CROP_PRICES[simCrop];
      const finLoss = Math.round(lostQtl * avgPrice);

      const recommendations: string[] = [];
      if (simCrop === 'Cotton') {
        recommendations.push(
          `Target seed cotton moisture is ${MOISTURE_THRESHOLDS.Cotton.optimal}%. Current input (${simMoisture}%) requires periodic aeration.`,
          simStorageType.includes('Shed')
            ? 'Elevate lint heaps on wooden pallets at least 40cm above earthen floors to prevent capillary dampness.'
            : 'Maintain dry, well-ventilated gunny bag stacks away from direct sunlight.',
          'Inspect fortnightly for yellowing and spontaneous heating in inner layers.'
        );
      } else {
        recommendations.push(
          `Maintain grain moisture below ${MOISTURE_THRESHOLDS.Soyabean.optimal}%. High oil content causes rancidity above 12%.`,
          simStorageType.includes('Hermetic')
            ? 'Hermetic seal successfully deprives pulse beetles of oxygen, preserving germination vitality.'
            : 'Apply food-grade neem seed powder or consider hermetic bag liners to halt pulse beetle propagation.',
          'Keep storage room ventilated during low-humidity mid-day hours.'
        );
      }

      const advice = calcLossPct > 6.0
        ? `High storage attrition (${calcLossPct}%). Projected mandi price gains for ${simCrop} are likely outweighed by storage loss. Liquidating stock within 15–20 days is economically advisable.`
        : `Safe holding window. Storage degradation is contained (${calcLossPct}% over ${simStorageDays} days). Holding for anticipated market price appreciation is viable.`;

      setSimResult({
        lossPercentage: calcLossPct,
        quantityLostQtl: lostQtl,
        financialLossRs: finLoss,
        spoilageRisk: calcLossPct > 8 ? 'High' : calcLossPct > 4 ? 'Moderate' : 'Low',
        maxSafeDays: Math.round(maxDays),
        recommendations,
        sellVsHoldAdvice: advice
      });
      setSimLoading(false);
    }, 450);
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-7 text-[#292B26]">
      <WorkflowStepper currentStageId={5} />
      {/* 1. Header & Context */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-[#E5DDCF]">

        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl lg:text-3xl font-serif font-bold text-[#103D2C]">
              Post-Harvest Loss Intelligence
            </h1>
            {isDemo ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-pulse"></span>
                SAMPLE DATA
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-900 border border-emerald-300">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                LIVE FARM DATA
              </span>
            )}
          </div>
          <p className="text-sm text-[#292B26]/75 mt-1 max-w-2xl">
            Track where crops are lost, understand the causes, and identify recovery opportunities across cotton and soyabean value chains.
          </p>
        </div>

        {/* Header Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Crop Selector Context */}
          <div className="inline-flex rounded-xl bg-white p-1 border border-[#E5DDCF] shadow-sm text-xs font-semibold">
            <button
              onClick={() => setSelectedCropFilter('ALL')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                selectedCropFilter === 'ALL'
                  ? 'bg-[#103D2C] text-white shadow-xs'
                  : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              All Crops
            </button>
            <button
              onClick={() => setSelectedCropFilter('Cotton')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                selectedCropFilter === 'Cotton'
                  ? 'bg-[#103D2C] text-white shadow-xs'
                  : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              Cotton
            </button>
            <button
              onClick={() => setSelectedCropFilter('Soyabean')}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                selectedCropFilter === 'Soyabean'
                  ? 'bg-[#103D2C] text-white shadow-xs'
                  : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              Soyabean
            </button>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            title="Refresh loss records"
            className="flex items-center gap-1.5 px-3 py-2 bg-white hover:bg-[#FBF7EF] border border-[#E5DDCF] text-xs font-semibold text-[#103D2C] rounded-xl transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {/* Record Loss CTA */}
          <button
            onClick={handleOpenRecordModal}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold rounded-xl transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Record Loss</span>
          </button>
        </div>

      </div>

      {/* Success Banner */}
      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-700 hover:text-emerald-900">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 2. LOSS OVERVIEW (4 Compact KPI Cards) */}
      <section className="space-y-2">
        <div className="flex justify-between items-center">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#103D2C]/70">
            Loss Overview & Economic Impact
          </h2>
          {isDemo && (
            <button
              onClick={handleResetSampleData}
              className="text-[11px] text-[#17643E] hover:underline flex items-center gap-1 font-medium"
            >
              <Database className="w-3 h-3" />
              Reset Demonstration Data
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Total Harvest */}
          <div className="bg-white rounded-2xl p-4.5 border border-[#E5DDCF] shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs text-[#292B26]/60 mb-1">
                <span>Total Harvested</span>
                <Package className="w-4 h-4 text-[#103D2C]" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-serif text-[#103D2C]">
                  {overviewMetrics.totalHarvestQtl}
                </span>
                <span className="text-xs text-[#292B26]/60 font-medium">Quintals</span>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-[#E5DDCF]/60 flex justify-between text-[11px] text-[#292B26]/60">
              <span>Cotton: {records.filter(r => r.crop === 'Cotton').reduce((a, b) => a + (b.stage === 'Harvest' ? b.stageQuantityQtl : 0), 0) || 120} Qtl</span>
              <span>Soya: {records.filter(r => r.crop === 'Soyabean').reduce((a, b) => a + (b.stage === 'Harvest' ? b.stageQuantityQtl : 0), 0) || 140} Qtl</span>
            </div>
          </div>

          {/* Card 2: Total Loss */}
          <div className="bg-white rounded-2xl p-4.5 border border-[#E5DDCF] shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs text-[#292B26]/60 mb-1">
                <span>Observed Loss</span>
                <TrendingDown className="w-4 h-4 text-[#B6532A]" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-serif text-[#B6532A]">
                  {overviewMetrics.totalLossQtl}
                </span>
                <span className="text-xs text-[#B6532A] font-semibold">Qtl</span>
                <span className="text-xs text-[#292B26]/50">
                  (₹{overviewMetrics.totalFinancialLossRs.toLocaleString()})
                </span>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-[#E5DDCF]/60 text-[11px] text-[#292B26]/60">
              Avg Market Basis: Cotton ₹7,280 · Soya ₹4,640
            </div>
          </div>

          {/* Card 3: Overall Loss % */}
          <div className="bg-white rounded-2xl p-4.5 border border-[#E5DDCF] shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs text-[#292B26]/60 mb-1">
                <span>Loss Attrition Rate</span>
                <AlertTriangle className="w-4 h-4 text-amber-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-serif text-[#103D2C]">
                  {overviewMetrics.lossPercentage}%
                </span>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                  overviewMetrics.lossPercentage > 8
                    ? 'bg-red-50 text-red-700'
                    : 'bg-emerald-50 text-emerald-700'
                }`}>
                  {overviewMetrics.lossPercentage > 8 ? 'Above Regional Target' : 'Within Target'}
                </span>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-[#E5DDCF]/60 text-[11px] text-[#292B26]/60">
              Maharashtra Benchmark: 8.5% – 9.8%
            </div>
          </div>

          {/* Card 4: Recoverable Quantity */}
          <div className="bg-white rounded-2xl p-4.5 border border-[#E5DDCF] shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs text-[#292B26]/60 mb-1">
                <span>{t('postHarvest.recoverablePotential')}</span>
                <ShieldCheck className="w-4 h-4 text-[#17643E]" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-serif text-[#17643E]">
                  {overviewMetrics.recoverableQtl}
                </span>
                <span className="text-xs text-[#17643E] font-semibold">Qtl</span>
                <span className="text-xs text-emerald-700 font-medium">
                  (~₹{overviewMetrics.recoverableFinancialRs.toLocaleString()})
                </span>
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-[#E5DDCF]/60 text-[11px] text-[#292B26]/60">
              Recoverable via re-drying & seed grading
            </div>
          </div>
        </div>
      </section>

      {/* 3. LOSS JOURNEY (5-Stage Visual Stepper) */}
      <section className="bg-white rounded-2xl p-5 lg:p-6 border border-[#E5DDCF] shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <h3 className="text-sm font-bold text-[#103D2C] flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#17643E]" />
              Value Chain Loss Journey
            </h3>
            <p className="text-xs text-[#292B26]/60 mt-0.5">
              Cumulative crop retention across Harvest, Handling, Storage, Transport, and Market Arrival.
            </p>
          </div>
          <span className="text-xs font-semibold text-[#17643E] bg-[#FBF7EF] px-2.5 py-1 rounded-lg border border-[#E5DDCF]">
            {selectedCropFilter === 'ALL' ? 'Cotton & Soyabean Scope' : `${selectedCropFilter} Scope`}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
          {journeyStages.map((stg, idx) => (
            <div
              key={stg.stage}
              className="bg-[#FBF7EF] rounded-xl p-4 border border-[#E5DDCF] relative flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-[#103D2C] mb-2">
                  <span className="flex items-center gap-1.5">
                    {stg.stage === 'Harvest' && <Scissors className="w-3.5 h-3.5 text-[#17643E]" />}
                    {stg.stage === 'Handling' && <Warehouse className="w-3.5 h-3.5 text-[#17643E]" />}
                    {stg.stage === 'Storage' && <Package className="w-3.5 h-3.5 text-[#17643E]" />}
                    {stg.stage === 'Transport' && <Truck className="w-3.5 h-3.5 text-[#17643E]" />}
                    Stage {idx + 1}: {stg.stage}
                  </span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                    stg.lossRate > 4 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    -{stg.lossRate}% Loss
                  </span>
                </div>

                <div className="space-y-1 text-xs">
                  <div className="flex justify-between text-[#292B26]/70">
                    <span>Input Volume:</span>
                    <span className="font-semibold text-[#103D2C]">{stg.processedQtl} Qtl</span>
                  </div>
                  <div className="flex justify-between text-[#292B26]/70">
                    <span>Observed Loss:</span>
                    <span className="font-bold text-[#B6532A]">{stg.lossQtl} Qtl</span>
                  </div>
                </div>
              </div>

              {/* Progress bar showing remaining volume */}
              <div className="mt-3 pt-3 border-t border-[#E5DDCF]/70">
                <div className="flex justify-between text-[11px] text-[#292B26]/60 mb-1">
                  <span>Batch Retained</span>
                  <span className="font-bold text-[#103D2C]">{stg.retentionRate}%</span>
                </div>
                <div className="w-full bg-[#E5DDCF] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-[#17643E] h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.max(0, stg.retentionRate))}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 4. LOSS ANALYTICS (2 Recharts Visualizations) */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Loss by Stage comparison */}
        <div className="bg-white rounded-2xl p-5 lg:p-6 border border-[#E5DDCF] shadow-xs space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-sm font-bold text-[#103D2C]">Stage-wise Loss Comparison</h3>
              <p className="text-xs text-[#292B26]/60 mt-0.5">Observed losses (Quintals) across Cotton vs Soyabean</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-[#103D2C]"></span> Cotton
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-[#B6532A]"></span> Soyabean
              </span>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stageChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5DDCF" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 11, fill: '#292B26' }} axisLine={{ stroke: '#E5DDCF' }} />
                <YAxis tick={{ fontSize: 11, fill: '#292B26' }} unit=" Q" axisLine={{ stroke: '#E5DDCF' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E5DDCF',
                    borderRadius: '12px',
                    fontSize: '12px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                  }}
                  formatter={(val: any) => [`${val} Quintals`, '']}
                />
                <Bar dataKey="Cotton" fill="#103D2C" radius={[4, 4, 0, 0]} maxBarSize={36} />
                <Bar dataKey="Soyabean" fill="#B6532A" radius={[4, 4, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Primary Loss Causes Distribution */}
        <div className="bg-white rounded-2xl p-5 lg:p-6 border border-[#E5DDCF] shadow-xs space-y-4">
          <div>
            <h3 className="text-sm font-bold text-[#103D2C]">Primary Causes of Post-Harvest Loss</h3>
            <p className="text-xs text-[#292B26]/60 mt-0.5">Aggregated loss quantity by root operational cause</p>
          </div>

          <div className="space-y-3.5 pt-1">
            {causeBreakdown.map((cause) => (
              <div key={cause.name} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-[#103D2C] flex items-center gap-1.5">
                    {cause.name}
                    <span className="text-[10px] text-[#292B26]/40 font-normal">
                      ({cause.crops.join(', ')})
                    </span>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#292B26]">{cause.qtl} Qtl</span>
                    <span className="text-[#292B26]/50 text-[11px]">({cause.percentage}%)</span>
                  </div>
                </div>

                <div className="w-full bg-[#FBF7EF] border border-[#E5DDCF]/80 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 rounded-full bg-[#17643E]"
                    style={{ width: `${Math.min(100, cause.percentage)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-[#FBF7EF] rounded-xl p-3 border border-[#E5DDCF] flex items-start gap-2.5 text-xs text-[#292B26]/75">
            <Info className="w-4 h-4 text-[#17643E] shrink-0 mt-0.5" />
            <span>
              <strong>Agronomic takeaway:</strong> Controlling seed moisture before storage accounts for 68% of preventable economic losses in Cotton & Soyabean.
            </span>
          </div>
        </div>
      </section>

      {/* 5. STORAGE LOSS SIMULATOR & DECISION SUPPORT (Cotton & Soyabean Only) */}
      <section className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-[#E5DDCF]">
          <div>
            <h3 className="text-base font-bold text-[#103D2C] flex items-center gap-2">
              <Warehouse className="w-5 h-5 text-[#17643E]" />
              Storage Degradation Simulator & Sell vs. Hold Advisor
            </h3>
            <p className="text-xs text-[#292B26]/60 mt-0.5">
              Simulate shelf-life decay curves and calculate the optimal market release window for Cotton and Soyabean.
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-900 border border-amber-200 rounded-lg">
            Vidarbha APMC Calibrated
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Column */}
          <div className="lg:col-span-5 space-y-4">
            {/* Crop Select */}
            <div>
              <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                Select Crop
              </label>
              <select
                value={simCrop}
                onChange={(e) => {
                  const crop = e.target.value as PostHarvestCrop;
                  setSimCrop(crop);
                  setSimMoisture(crop === 'Cotton' ? 8.5 : 10.5);
                }}
                className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-sm font-semibold text-[#103D2C] focus:outline-none focus:border-[#17643E]"
              >
                <option value="Cotton">Cotton (Kapas)</option>
                <option value="Soyabean">Soyabean</option>
              </select>
            </div>

            {/* Quantity */}
            <div>
              <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                Stored Volume (Quintals)
              </label>
              <input
                type="number"
                min={1}
                value={simQuantity}
                onChange={(e) => setSimQuantity(Math.max(1, Number(e.target.value)))}
                className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-sm focus:outline-none focus:border-[#17643E]"
              />
            </div>

            {/* Storage Type */}
            <div>
              <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                Storage Facility Type
              </label>
              <select
                value={simStorageType}
                onChange={(e) => setSimStorageType(e.target.value)}
                className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-sm text-[#103D2C] focus:outline-none focus:border-[#17643E]"
              >
                <option value="Traditional Gunny Bags">Traditional Jute Gunny Bags</option>
                <option value="Hermetic Bags / Silo">Hermetic Bags / Metal Silo (Airtight)</option>
                <option value="Covered On-Farm Shed">Covered On-Farm / Ginning Shed</option>
                <option value="Ventilated Warehouse">Ventilated APMC Warehouse</option>
              </select>
            </div>

            {/* Storage Moisture Content Slider */}
            <div>
              <div className="flex justify-between items-center mb-1 text-xs">
                <span className="font-semibold text-[#103D2C]">Initial Moisture Content</span>
                <span className={`font-bold ${
                  simMoisture > MOISTURE_THRESHOLDS[simCrop].warning ? 'text-red-600' : 'text-[#17643E]'
                }`}>
                  {simMoisture}% (Safe Target &lt; {MOISTURE_THRESHOLDS[simCrop].optimal}%)
                </span>
              </div>
              <input
                type="range"
                min={6}
                max={16}
                step={0.5}
                value={simMoisture}
                onChange={(e) => setSimMoisture(Number(e.target.value))}
                className="w-full accent-[#17643E] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#292B26]/50">
                <span>6% (Very Dry)</span>
                <span>Optimal</span>
                <span>16% (High Rot Risk)</span>
              </div>
            </div>

            {/* Duration Slider */}
            <div>
              <div className="flex justify-between items-center mb-1 text-xs">
                <span className="font-semibold text-[#103D2C]">Planned Storage Duration</span>
                <span className="font-bold text-[#17643E]">{simStorageDays} Days</span>
              </div>
              <input
                type="range"
                min={7}
                max={180}
                step={7}
                value={simStorageDays}
                onChange={(e) => setSimStorageDays(Number(e.target.value))}
                className="w-full accent-[#17643E] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#292B26]/50">
                <span>1 Week</span>
                <span>1 Month</span>
                <span>3 Months</span>
                <span>6 Months</span>
              </div>
            </div>

            <button
              onClick={handleRunSimulation}
              disabled={simLoading}
              className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold py-2.5 px-4 rounded-xl text-xs transition-colors flex items-center justify-center gap-2 shadow-xs disabled:opacity-50"
            >
              {simLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Package className="w-4 h-4" />}
              <span>Simulate Storage Degradation</span>
            </button>
          </div>

          {/* Results Column */}
          <div className="lg:col-span-7 space-y-4">
            {simResult && (
              <>
                {/* 3 Outcome Metric Pills */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-[#FBF7EF] rounded-xl p-3.5 border border-[#E5DDCF]">
                    <span className="text-[11px] text-[#292B26]/60">Estimated Loss</span>
                    <div className="text-xl font-bold font-serif text-[#103D2C] mt-0.5">
                      {simResult.lossPercentage}%
                    </div>
                    <span className="text-[11px] text-[#292B26]/60">
                      {simResult.quantityLostQtl} Quintals lost
                    </span>
                  </div>

                  <div className="bg-[#FBF7EF] rounded-xl p-3.5 border border-[#E5DDCF]">
                    <span className="text-[11px] text-[#292B26]/60">{t('postHarvest.financialImpact')}</span>
                    <div className="text-xl font-bold font-serif text-[#B6532A] mt-0.5">
                      ₹{simResult.financialLossRs.toLocaleString()}
                    </div>
                    <span className="text-[11px] text-[#292B26]/60">
                      @ ₹{CROP_PRICES[simCrop]}/Qtl baseline
                    </span>
                  </div>

                  <div className="bg-[#FBF7EF] rounded-xl p-3.5 border border-[#E5DDCF]">
                    <span className="text-[11px] text-[#292B26]/60">Max Safe Storage</span>
                    <div className="text-xl font-bold font-serif text-[#17643E] mt-0.5">
                      ~{simResult.maxSafeDays} Days
                    </div>
                    <span className={`text-[11px] font-semibold ${
                      simResult.spoilageRisk === 'High' ? 'text-red-700' : 'text-emerald-700'
                    }`}>
                      Risk Level: {simResult.spoilageRisk}
                    </span>
                  </div>
                </div>

                {/* Sell vs Hold Strategy Window */}
                <div className="bg-[#FBF7EF] rounded-xl p-4 border border-[#E5DDCF] space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#103D2C]">
                    <Clock className="w-4 h-4 text-[#17643E]" />
                    <span>Sell vs. Hold Strategy Recommendation</span>
                  </div>
                  <p className="text-xs text-[#292B26]/80 leading-relaxed bg-white p-3 rounded-lg border border-[#E5DDCF]/70">
                    {simResult.sellVsHoldAdvice}
                  </p>
                </div>

                {/* Storage Precautions */}
                <div className="bg-white rounded-xl p-4 border border-[#E5DDCF] space-y-2.5">
                  <span className="text-xs font-bold text-[#103D2C] flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-[#17643E]" />
                    Agronomic Precautions for {simCrop}
                  </span>
                  <ul className="space-y-1.5 text-xs text-[#292B26]/80">
                    {simResult.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2 bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF]/60">
                        <span className="w-4 h-4 rounded-full bg-[#17643E]/10 text-[#17643E] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* 6. LOSS HISTORY TABLE */}
      <section className="bg-white rounded-2xl p-5 lg:p-6 border border-[#E5DDCF] shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <div>
            <h3 className="text-sm font-bold text-[#103D2C]">Historical Loss Records & Batches</h3>
            <p className="text-xs text-[#292B26]/60 mt-0.5">
              Auditable loss registry for Cotton & Soyabean batches with stage, root causes, and recovery status.
            </p>
          </div>

          {/* Table Filters & Search */}
          <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
            {/* Search */}
            <div className="relative flex-1 md:w-60">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#292B26]/40" />
              <input
                type="text"
                placeholder="Search batch, cause, note..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl focus:outline-none focus:border-[#17643E]"
              />
            </div>

            {/* Stage Filter */}
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value as any)}
              className="px-2.5 py-1.5 text-xs bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-[#292B26] focus:outline-none focus:border-[#17643E]"
            >
              <option value="ALL">All Stages</option>
              <option value="Harvest">Harvest</option>
              <option value="Handling">Handling</option>
              <option value="Storage">Storage</option>
              <option value="Transport">Transport</option>
            </select>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-2.5 py-1.5 text-xs bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-[#292B26] focus:outline-none focus:border-[#17643E]"
            >
              <option value="date">Sort: Date</option>
              <option value="lossQty">Sort: Loss Quantity</option>
              <option value="lossPct">Sort: Loss %</option>
              <option value="financial">Sort: Financial Loss</option>
            </select>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto rounded-xl border border-[#E5DDCF]">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FBF7EF] text-[#103D2C] font-bold border-b border-[#E5DDCF]">
              <tr>
                <th className="py-3 px-4">Batch ID & Date</th>
                <th className="py-3 px-4">Crop</th>
                <th className="py-3 px-4">Stage</th>
                <th className="py-3 px-4">Processed / Loss</th>
                <th className="py-3 px-4">Loss %</th>
                <th className="py-3 px-4">Primary Cause</th>
                <th className="py-3 px-4">Recoverable</th>
                <th className="py-3 px-4">Financial Loss</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5DDCF]/70">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#292B26]/50">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-[#17643E] mb-2" />
                    <span>Loading loss registry...</span>
                  </td>
                </tr>
              ) : filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-[#292B26]/60">
                    <Package className="w-8 h-8 mx-auto text-[#292B26]/30 mb-2" />
                    <p className="font-semibold text-sm text-[#103D2C]">No records match the current criteria.</p>
                    <p className="text-xs text-[#292B26]/50 mt-1">Try resetting the filters or record a new loss event.</p>
                  </td>
                </tr>
              ) : (
                filteredRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-[#FBF7EF]/60 transition-colors">
                    {/* Batch & Date */}
                    <td className="py-3 px-4 font-mono font-medium text-[#103D2C]">
                      <div>{rec.batchId}</div>
                      <div className="text-[10px] text-[#292B26]/50 font-sans">{rec.harvestDate}</div>
                    </td>

                    {/* Crop */}
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                        rec.crop === 'Cotton'
                          ? 'bg-blue-50 text-blue-800 border border-blue-200'
                          : 'bg-amber-50 text-amber-800 border border-amber-200'
                      }`}>
                        {rec.crop}
                      </span>
                    </td>

                    {/* Stage */}
                    <td className="py-3 px-4 font-medium text-[#292B26]">
                      {rec.stage}
                    </td>

                    {/* Processed / Loss */}
                    <td className="py-3 px-4">
                      <div><span className="font-bold text-[#B6532A]">{rec.observedLossQtl} Qtl</span> loss</div>
                      <div className="text-[10px] text-[#292B26]/50">from {rec.stageQuantityQtl} Qtl</div>
                    </td>

                    {/* Loss % */}
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold ${
                        rec.lossPercentage > 4
                          ? 'bg-red-50 text-red-700'
                          : 'bg-emerald-50 text-emerald-700'
                      }`}>
                        {rec.lossPercentage}%
                      </span>
                    </td>

                    {/* Cause */}
                    <td className="py-3 px-4 max-w-xs">
                      <div className="font-medium text-[#292B26] truncate" title={rec.cause}>
                        {rec.cause}
                      </div>
                      <div className="text-[10px] text-[#292B26]/50 truncate" title={rec.facilityOrMethod}>
                        {rec.facilityOrMethod}
                      </div>
                    </td>

                    {/* Recoverable */}
                    <td className="py-3 px-4 font-semibold text-[#17643E]">
                      {rec.recoverableQuantityQtl} Qtl
                    </td>

                    {/* Financial Loss */}
                    <td className="py-3 px-4 font-serif font-bold text-[#103D2C]">
                      ₹{rec.financialLossRs.toLocaleString()}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDeleteRecord(rec.id, rec.batchId)}
                        title="Delete loss record"
                        className="text-red-500 hover:text-red-700 p-1.5 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex justify-between items-center text-xs text-[#292B26]/50 pt-1">
          <span>Showing {filteredRecords.length} of {records.length} records</span>
          <span>Baseline Mandi: Akot & Amravati APMC (Vidarbha)</span>
        </div>
      </section>

      {/* 7. RECORD LOSS MODAL (Form for Recording Actual Loss Events) */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full border border-[#E5DDCF] shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-[#FBF7EF] border-b border-[#E5DDCF] flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-[#103D2C]">Record Post-Harvest Loss Event</h3>
                <p className="text-xs text-[#292B26]/60 mt-0.5">Log actual loss observed during harvest, handling, storage, or transport.</p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-[#292B26]/50 hover:text-[#103D2C] p-1.5 rounded-lg hover:bg-[#E5DDCF]/50 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body / Form */}
            <form onSubmit={handleFormSubmit} className="p-6 overflow-y-auto space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Crop Selection (Cotton or Soyabean ONLY) */}
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Crop Type *
                  </label>
                  <select
                    value={formCrop}
                    onChange={(e) => handleCropChangeInForm(e.target.value as PostHarvestCrop)}
                    className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs font-semibold text-[#103D2C] focus:outline-none focus:border-[#17643E]"
                  >
                    <option value="Cotton">Cotton (Kapas)</option>
                    <option value="Soyabean">Soyabean</option>
                  </select>
                </div>

                {/* Batch Reference ID */}
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Batch Reference ID *
                  </label>
                  <input
                    type="text"
                    value={formBatchId}
                    onChange={(e) => setFormBatchId(e.target.value)}
                    className={`w-full border rounded-xl px-3 py-2 bg-[#FBF7EF] font-mono text-xs focus:outline-none ${
                      formErrors.batchId ? 'border-red-500' : 'border-[#E5DDCF] focus:border-[#17643E]'
                    }`}
                  />
                  {formErrors.batchId && <p className="text-[10px] text-red-600 mt-0.5">{formErrors.batchId}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Harvest Date */}
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Event / Harvest Date *
                  </label>
                  <input
                    type="date"
                    value={formDate}
                    onChange={(e) => setFormDate(e.target.value)}
                    className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none focus:border-[#17643E]"
                  />
                  {formErrors.date && <p className="text-[10px] text-red-600 mt-0.5">{formErrors.date}</p>}
                </div>

                {/* Value Chain Stage */}
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Loss Stage *
                  </label>
                  <select
                    value={formStage}
                    onChange={(e) => setFormStage(e.target.value as PostHarvestStage)}
                    className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs font-medium text-[#292B26] focus:outline-none focus:border-[#17643E]"
                  >
                    <option value="Harvest">Harvest Stage</option>
                    <option value="Handling">Handling & Thrashing</option>
                    <option value="Storage">Storage & Warehousing</option>
                    <option value="Transport">Mandi Transport</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Processed Quantity */}
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Processed / Handled Quantity (Qtl) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={formStageQty}
                    onChange={(e) => setFormStageQty(Number(e.target.value))}
                    className={`w-full border rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none ${
                      formErrors.stageQty ? 'border-red-500' : 'border-[#E5DDCF] focus:border-[#17643E]'
                    }`}
                  />
                  {formErrors.stageQty && <p className="text-[10px] text-red-600 mt-0.5">{formErrors.stageQty}</p>}
                </div>

                {/* Observed Loss */}
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Observed Loss Quantity (Qtl) *
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formObservedLoss}
                    onChange={(e) => setFormObservedLoss(Number(e.target.value))}
                    className={`w-full border rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none ${
                      formErrors.observedLoss ? 'border-red-500' : 'border-[#E5DDCF] focus:border-[#17643E]'
                    }`}
                  />
                  {formErrors.observedLoss && <p className="text-[10px] text-red-600 mt-0.5">{formErrors.observedLoss}</p>}
                </div>
              </div>

              {/* Calculated preview */}
              <div className="bg-[#FBF7EF] rounded-xl p-3 border border-[#E5DDCF] flex justify-between text-xs text-[#103D2C]">
                <div>
                  <span className="text-[#292B26]/60">Calculated Loss:</span>{' '}
                  <span className="font-bold text-[#B6532A]">
                    {formStageQty > 0 ? Math.round((formObservedLoss / formStageQty) * 1000) / 10 : 0}%
                  </span>
                </div>
                <div>
                  <span className="text-[#292B26]/60">Estimated Financial Loss:</span>{' '}
                  <span className="font-bold font-serif">
                    ₹{Math.round(formObservedLoss * CROP_PRICES[formCrop]).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Cause & Facility */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Primary Cause of Loss *
                  </label>
                  <input
                    type="text"
                    value={formCause}
                    onChange={(e) => setFormCause(e.target.value)}
                    placeholder="e.g. Boll rot, weevil attack, pod cracking"
                    className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none focus:border-[#17643E]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                    Facility or Transit Method
                  </label>
                  <input
                    type="text"
                    value={formFacility}
                    onChange={(e) => setFormFacility(e.target.value)}
                    placeholder="e.g. Gunny bags, covered shed, trolley"
                    className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none focus:border-[#17643E]"
                  />
                </div>
              </div>

              {/* Recoverable Quantity */}
              <div>
                <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                  Recoverable Quantity (Qtl)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={formRecoverable}
                  onChange={(e) => setFormRecoverable(Number(e.target.value))}
                  className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none focus:border-[#17643E]"
                />
                <span className="text-[10px] text-[#292B26]/50 mt-0.5 block">
                  Amount that can be salvaged via re-drying, sieving, or grading.
                </span>
                {formErrors.recoverable && <p className="text-[10px] text-red-600 mt-0.5">{formErrors.recoverable}</p>}
              </div>

              {/* Observations & Notes */}
              <div>
                <label className="block text-xs font-semibold text-[#103D2C] mb-1">
                  Field Notes / Corrective Action
                </label>
                <textarea
                  rows={2}
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  placeholder="Additional context on weather, bag quality, or transit conditions..."
                  className="w-full border border-[#E5DDCF] rounded-xl px-3 py-2 bg-[#FBF7EF] text-xs focus:outline-none focus:border-[#17643E]"
                />
              </div>

              {/* Form Actions */}
              <div className="pt-3 border-t border-[#E5DDCF] flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-[#E5DDCF] text-xs font-semibold text-[#292B26]/80 rounded-xl hover:bg-[#FBF7EF] transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className="px-4 py-2 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold rounded-xl transition-colors shadow-xs flex items-center gap-1.5 disabled:opacity-50"
                >
                  {formSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                  <span>Save Loss Record</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <WorkflowFooter
        currentStageNumber={5}
        currentStageName="Market & Post-Harvest Storage"
        completedActionMessage="Storage assessment complete. Check government storage schemes or return to Dashboard."
        prevStep={{ label: "Market Intelligence", path: "/market" }}
        nextStep={{
          label: "Government Schemes",
          labelMr: "शासकीय योजना",
          path: "/schemes",
          description: "Explore cold chain, PM-KISAN, and agricultural warehouse subsidies"
        }}
        alternativeNextStep={{
          label: "Ask KisanCare AI",
          path: "/copilot"
        }}
      />


    </div>
  );
}
