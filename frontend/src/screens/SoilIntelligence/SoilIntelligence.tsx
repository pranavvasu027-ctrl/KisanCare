import React, { useState, useEffect, useRef } from 'react';
import {
  TestTube, Upload, FileText, CheckCircle2, AlertTriangle, Download,
  Plus, RefreshCw, Clock, ShieldAlert, Sparkles, Calendar,
  TrendingUp, TrendingDown, Layers, ExternalLink, Eye, Check, X,
  ChevronRight, Info, Lock, AlertCircle, FileCheck, FileUp, Trash2
} from 'lucide-react';
import {
  soilIntelligenceApi,
  PlotStatusResponse,
  ParseReportResponse,
  AgronomicEventResponse,
  BenchmarksResponse,
  ComparisonResponse
} from '../../services/soilIntelligenceApi';

const SAMPLE_SHC_TEXT = `GOVERNMENT OF MAHARASHTRA
DISTRICT SOIL TESTING LABORATORY, LATUR
Soil Health Card Certificate
Sample No: MH6092432/2024-25/441209
Date: 15-Oct-2024
Plot No: PLOT_MH_LAT_881
Farmer Name: Ramesh Patil

SOIL PARAMETERS:
pH: 7.40 (Normal)
EC: 0.65 dS/m
Organic Carbon: 0.55 %
Available Nitrogen: 240.0 kg/ha (Low)
Available Phosphorus: 18.5 kg/ha P2O5 (Medium)
Available Potassium: 310.0 kg/ha K2O (High)
`;

const OUT_OF_BOUNDS_SAMPLE_TEXT = `GOVERNMENT OF MAHARASHTRA
DISTRICT SOIL TESTING LABORATORY, LATUR
Soil Health Card Certificate
Sample No: LAB_ERR_FLAG_88
Date: 15-Oct-2024
Plot No: PLOT_MH_LAT_881
Farmer Name: Ramesh Patil

SOIL PARAMETERS:
pH: 13.50 (Abnormal)
Available Nitrogen: 12000.0 kg/ha (Suspect)
Available Phosphorus: 18.5 kg/ha P2O5
Available Potassium: 310.0 kg/ha K2O
`;

type TabType = 'overview' | 'upload' | 'baseline' | 'timeline' | 'compare';

export default function SoilIntelligence() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [plotId, setPlotId] = useState<string>('PLOT_MH_LAT_881');
  const [farmId, setFarmId] = useState<string>('FARM_LAT_01');

  // Status & API State
  const [status, setStatus] = useState<PlotStatusResponse | null>(null);
  const [events, setEvents] = useState<AgronomicEventResponse[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarksResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [pdfDownloading, setPdfDownloading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // OCR Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [uploadPhase, setUploadPhase] = useState<'idle' | 'selected' | 'uploading' | 'processing' | 'validation' | 'results' | 'error'>('idle');
  const [fileValidationError, setFileValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [reportText, setReportText] = useState<string>(SAMPLE_SHC_TEXT);
  const [parsedDoc, setParsedDoc] = useState<ParseReportResponse | null>(null);
  const [parsingLoading, setParsingLoading] = useState<boolean>(false);

  // Agronomist Correction State
  const [correctionField, setCorrectionField] = useState<string>('');
  const [correctionValue, setCorrectionValue] = useState<string>('');
  const [correctionNotes, setCorrectionNotes] = useState<string>('');
  const [correctingLoading, setCorrectingLoading] = useState<boolean>(false);
  const [showRawOcrText, setShowRawOcrText] = useState<boolean>(false);

  // Baseline Form State
  const [baseDate, setBaseDate] = useState<string>('2023-06-15');
  const [baseLabName, setBaseLabName] = useState<string>('District Soil Testing Laboratory, Latur');
  const [baseCertNo, setBaseCertNo] = useState<string>('STL-2023-8871');
  const [baseAccredId, setBaseAccredId] = useState<string>('NABL-TC-8812');
  const [baseAccredVerified, setBaseAccredVerified] = useState<boolean>(true);
  const [baseAccredSource, setBaseAccredSource] = useState<string>('NABL State Accreditation Portal');
  const [baseN, setBaseN] = useState<number>(245.0);
  const [baseP, setBaseP] = useState<number>(18.5);
  const [baseK, setBaseK] = useState<number>(320.0);
  const [basePh, setBasePh] = useState<number>(7.80);
  const [baseEc, setBaseEc] = useState<number>(0.35);
  const [baseOc, setBaseOc] = useState<number>(0.52);

  // Event Form State
  const [fertGrade, setFertGrade] = useState<string>('DAP');
  const [fertQty, setFertQty] = useState<number>(100.0);
  const [fertDate, setFertDate] = useState<string>('2023-06-20');
  const [fertNotes, setFertNotes] = useState<string>('Basal application at sowing');

  const [harvestCrop, setHarvestCrop] = useState<string>('Soybean');
  const [harvestYield, setHarvestYield] = useState<number>(2.2);
  const [harvestDate, setHarvestDate] = useState<string>('2023-10-15');
  const [harvestResidue, setHarvestResidue] = useState<boolean>(false);

  // Retest Comparison State
  const [retestDate, setRetestDate] = useState<string>('2024-05-15');
  const [retestLabName, setRetestLabName] = useState<string>('District Soil Testing Laboratory, Latur');
  const [retestN, setRetestN] = useState<number>(238.0);
  const [retestP, setRetestP] = useState<number>(17.2);
  const [retestK, setRetestK] = useState<number>(305.0);
  const [retestPh, setRetestPh] = useState<number>(7.75);
  const [retestAccred, setRetestAccred] = useState<boolean>(true);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResponse | null>(null);
  const [comparingLoading, setComparingLoading] = useState<boolean>(false);

  // Initial Data Load
  useEffect(() => {
    loadBenchmarks();
    refreshPlotData();
  }, [plotId]);

  const loadBenchmarks = async () => {
    try {
      const data = await soilIntelligenceApi.getBenchmarks();
      setBenchmarks(data);
    } catch (err: any) {
      console.warn('Could not load benchmarks:', err);
    }
  };

  const refreshPlotData = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const statusData = await soilIntelligenceApi.getPlotStatus(plotId);
      setStatus(statusData);

      const eventsData = await soilIntelligenceApi.listPlotEvents(plotId);
      setEvents(eventsData);
    } catch (err: any) {
      // If 404, plot timeline doesn't exist yet in memory
      if (err.message && err.message.includes('404')) {
        setStatus(null);
        setEvents([]);
      } else {
        setErrorMessage(`Failed to fetch plot status: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const notify = (msg: string, isError = false) => {
    if (isError) {
      setErrorMessage(msg);
      setSuccessMessage(null);
    } else {
      setSuccessMessage(msg);
      setErrorMessage(null);
      setTimeout(() => setSuccessMessage(null), 6000);
    }
  };

  // File Upload Helpers & Actions
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const validateFile = (file: File): string | null => {
    if (!file) return 'No file selected.';
    if (file.size === 0) {
      return 'The selected file is empty (0 bytes). Please choose a valid Soil Health Card or laboratory report.';
    }
    const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
    if (file.size > MAX_SIZE) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      return `File size (${sizeMb} MB) exceeds the maximum allowed limit of 5 MB.`;
    }
    const name = file.name.toLowerCase();
    const isSupported = name.endsWith('.pdf') || name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png');
    if (!isSupported) {
      return 'Unsupported file format. Please upload a PDF document (.pdf) or image (.jpg, .jpeg, .png).';
    }
    return null;
  };

  const handleFileSelect = (file: File) => {
    setFileValidationError(null);
    const err = validateFile(file);
    if (err) {
      setFileValidationError(err);
      setSelectedFile(null);
      setUploadPhase('error');
      return;
    }
    setSelectedFile(file);
    setUploadPhase('selected');
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    setFileValidationError(null);
    setUploadPhase('idle');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadAndParse = async () => {
    if (!selectedFile) {
      setFileValidationError('Please choose a file to upload.');
      return;
    }
    const valErr = validateFile(selectedFile);
    if (valErr) {
      setFileValidationError(valErr);
      setUploadPhase('error');
      return;
    }

    setFileValidationError(null);
    setUploadPhase('uploading');

    try {
      const timer = setTimeout(() => {
        setUploadPhase((prev) => (prev === 'uploading' ? 'processing' : prev));
      }, 500);

      const doc = await soilIntelligenceApi.uploadSoilReport(selectedFile, plotId, farmId);
      clearTimeout(timer);
      setUploadPhase('validation');
      setParsedDoc(doc);

      setTimeout(() => {
        setUploadPhase('results');
        notify(`File "${selectedFile.name}" processed: Extracted ${doc.report_id || 'document'} with ${(doc.confidence_score * 100).toFixed(0)}% confidence.`);
      }, 350);
    } catch (err: any) {
      setUploadPhase('error');
      setFileValidationError(err.message || 'Failed to process soil report document.');
      notify(`File Processing Failed: ${err.message}`, true);
    }
  };

  // 1. OCR Report Parsing Action
  const handleParseReport = async () => {
    setParsingLoading(true);
    setErrorMessage(null);
    try {
      const doc = await soilIntelligenceApi.parseReport({
        report_text: reportText,
        plot_id: plotId,
        farm_id: farmId
      });
      setParsedDoc(doc);
      notify('Soil Health Card extracted and normalized successfully.');
    } catch (err: any) {
      notify(`OCR Extraction Error: ${err.message}`, true);
    } finally {
      setParsingLoading(false);
    }
  };

  // 2. Submit Agronomist Correction
  const handleCorrection = async () => {
    if (!parsedDoc?.review_token) return;
    setCorrectingLoading(true);
    try {
      await soilIntelligenceApi.submitManualCorrection({
        review_token: parsedDoc.review_token,
        reviewer_id: 'AGRONOMIST_DESK_01',
        corrections: { [correctionField]: correctionValue },
        notes: correctionNotes
      });
      notify(`Correction for ${correctionField} (${correctionValue}) submitted and re-normalized.`);
      // Refresh parse state
      handleParseReport();
    } catch (err: any) {
      notify(`Correction Error: ${err.message}`, true);
    } finally {
      setCorrectingLoading(false);
    }
  };

  // 3. Promote parsed values to baseline form
  const toIsoDateString = (dateStr?: string | null): string => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) {
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      }
    } catch {
      // fallback to original string
    }
    return dateStr;
  };

  const populateBaselineFromOCR = () => {
    if (!parsedDoc) return;
    if (parsedDoc.sample_date) setBaseDate(toIsoDateString(parsedDoc.sample_date));
    if (parsedDoc.ph) setBasePh(parsedDoc.ph);
    if (parsedDoc.ec_ds_m) setBaseEc(parsedDoc.ec_ds_m);
    if (parsedDoc.organic_carbon_pct) setBaseOc(parsedDoc.organic_carbon_pct);
    if (parsedDoc.nitrogen?.normalized_value_kg_ha) setBaseN(parsedDoc.nitrogen.normalized_value_kg_ha);
    if (parsedDoc.phosphorus?.normalized_value_kg_ha) setBaseP(parsedDoc.phosphorus.normalized_value_kg_ha);
    if (parsedDoc.potassium?.normalized_value_kg_ha) setBaseK(parsedDoc.potassium.normalized_value_kg_ha);
    setActiveTab('baseline');
    notify('OCR normalized values transferred to Baseline Laboratory Confirmation form.');
  };

  // 4. Confirm Baseline Report
  const handleConfirmBaseline = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await soilIntelligenceApi.confirmBaselineReport({
        plot_id: plotId,
        farm_id: farmId,
        sample_date: baseDate,
        lab_name: baseLabName,
        lab_certificate_no: baseCertNo,
        lab_accreditation_id: baseAccredId,
        accreditation_verified: baseAccredVerified,
        accreditation_source: baseAccredSource,
        nitrogen_kg_ha: Number(baseN),
        phosphorus_kg_ha: Number(baseP),
        potassium_kg_ha: Number(baseK),
        ph: Number(basePh),
        ec_ds_m: Number(baseEc),
        organic_carbon_pct: Number(baseOc)
      });
      notify(`Laboratory baseline registered for plot ${plotId}.`);
      await refreshPlotData();
      setActiveTab('overview');
    } catch (err: any) {
      notify(`Baseline Confirmation Error: ${err.message}`, true);
    } finally {
      setLoading(false);
    }
  };

  // 5. Record Fertilizer Event
  const handleRecordFertilizer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await soilIntelligenceApi.recordFertilizerEvent(plotId, {
        fertilizer_grade: fertGrade,
        quantity_kg_ha: Number(fertQty),
        application_date: fertDate,
        notes: fertNotes
      });
      notify(`Fertilizer application (${fertGrade} - ${fertQty} kg/ha) logged on timeline.`);
      await refreshPlotData();
    } catch (err: any) {
      notify(`Event Error: ${err.message}`, true);
    }
  };

  // 6. Record Harvest Event
  const handleRecordHarvest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await soilIntelligenceApi.recordHarvestEvent(plotId, {
        crop_name: harvestCrop,
        yield_tonnes_ha: Number(harvestYield),
        harvest_date: harvestDate,
        residue_retained: harvestResidue
      });
      notify(`Crop harvest (${harvestCrop} - ${harvestYield} t/ha) logged on timeline.`);
      await refreshPlotData();
    } catch (err: any) {
      notify(`Harvest Error: ${err.message}`, true);
    }
  };

  // 7. Download PDF Report
  const handleDownloadPdf = async () => {
    setPdfDownloading(true);
    try {
      const blob = await soilIntelligenceApi.downloadReportPdf(plotId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `soil_report_${plotId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      notify(`Soil Intelligence report downloaded for ${plotId}.`);
    } catch (err: any) {
      notify(`PDF Generation Error: ${err.message}`, true);
    } finally {
      setPdfDownloading(false);
    }
  };

  // 8. Ingest Retest & Compare
  const handleCompareRetest = async (e: React.FormEvent) => {
    e.preventDefault();
    setComparingLoading(true);
    setComparisonResult(null);
    try {
      const comp = await soilIntelligenceApi.compareRetest(plotId, {
        retest_date: retestDate,
        lab_name: retestLabName,
        accreditation_verified: retestAccred,
        nitrogen_kg_ha: Number(retestN),
        phosphorus_kg_ha: Number(retestP),
        potassium_kg_ha: Number(retestK),
        ph: Number(retestPh)
      });
      setComparisonResult(comp);
      notify(`Paired continuous comparison completed for sample date ${retestDate}.`);
    } catch (err: any) {
      notify(`Comparator Error: ${err.message}`, true);
    } finally {
      setComparingLoading(false);
    }
  };

  // 9. Reset Plot Timeline
  const handleDeletePlot = async () => {
    if (!window.confirm(`Are you sure you want to reset timeline for plot "${plotId}"?`)) return;
    try {
      await soilIntelligenceApi.deletePlot(plotId);
      notify(`Plot timeline ${plotId} reset.`);
      setStatus(null);
      setEvents([]);
      setParsedDoc(null);
      setComparisonResult(null);
    } catch (err: any) {
      notify(`Reset Error: ${err.message}`, true);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-[#103D2C] rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-[#17643E]/40 to-transparent pointer-events-none" />
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-3">
              <span className="p-2 bg-emerald-500/20 rounded-xl border border-emerald-400/30">
                <TestTube className="w-6 h-6 text-emerald-300" />
              </span>
              <div>
                <h1 className="text-2xl lg:text-3xl font-serif font-bold tracking-tight">Soil Intelligence V1</h1>
                <p className="text-emerald-100/80 text-xs mt-0.5">
                  Dynamic Multi-Year Nutrient Ledger & Agronomic Depletion Engine
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-[#072B1E] px-3 py-1.5 rounded-xl border border-emerald-800/60 flex items-center gap-2">
              <span className="text-xs text-emerald-300 font-medium">Active Plot:</span>
              <input
                type="text"
                value={plotId}
                onChange={(e) => setPlotId(e.target.value.toUpperCase())}
                className="bg-transparent text-white font-mono text-xs font-bold focus:outline-none w-32 border-b border-emerald-500/50 pb-0.5"
                placeholder="PLOT_ID"
              />
            </div>

            <button
              onClick={refreshPlotData}
              disabled={loading}
              className="bg-[#17643E] hover:bg-[#1C7A4C] text-white px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Refresh Plot Timeline"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            {status && (
              <button
                onClick={handleDownloadPdf}
                disabled={pdfDownloading}
                className="bg-[#DDA74A] hover:bg-[#C9963E] text-[#103D2C] px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
              >
                <Download className={`w-3.5 h-3.5 ${pdfDownloading ? 'animate-spin' : ''}`} />
                {pdfDownloading ? 'Generating PDF...' : 'Download Soil PDF'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl text-xs flex items-center justify-between shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-700 hover:text-emerald-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* FARMER OBSERVATION & INTEGRITY DISCLOSURE */}
      <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 text-amber-900 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="bg-amber-200 text-amber-900 text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded">
            Soil Data Provenance: Farmer Observation
          </span>
          <span className="text-xs text-amber-800 font-semibold">Laboratory Verification Pending</span>
        </div>
        <p className="text-xs leading-relaxed text-amber-900">
          <strong>Soil Classification:</strong> Black cotton soil (&ldquo;koralvahu jamin&rdquo;), deep, flat terrain with good drainage.<br/>
          <strong>Reported pH Range:</strong> 7.6 &ndash; 8.5 (mean 8.05 recorded; laboratory verification pending).<br/>
          <strong>NPK &amp; Micronutrients:</strong> Intentionally unpopulated (NULL). The farmer reports a soil test report is available and may be uploaded later. Fabricated laboratory values are strictly prohibited.
        </p>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center justify-between shadow-sm animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span className="font-medium">{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-red-700 hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-[#E5DDCF] gap-2 overflow-x-auto pb-1">
        {[
          { id: 'overview', label: 'Soil Status & Overview', icon: Layers },
          { id: 'upload', label: 'Upload & OCR Ingestion', icon: Upload },
          { id: 'baseline', label: 'Laboratory Baseline', icon: FileCheck },
          { id: 'timeline', label: 'Nutrient Timeline Ledger', icon: Clock },
          { id: 'compare', label: 'Lab Retest & Comparator', icon: TrendingUp },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                isActive
                  ? 'bg-white text-[#103D2C] border-t-2 border-l border-r border-[#103D2C] border-b-0 -mb-1 shadow-sm'
                  : 'text-[#292B26]/60 hover:text-[#103D2C] hover:bg-[#FBF7EF]'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[#103D2C]' : 'text-stone-400'}`} />
              {tab.label}
              {tab.id === 'upload' && parsedDoc?.requires_human_review && (
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              )}
            </button>
          );
        })}
      </div>

      {/* =================================================================== */}
      {/* TAB 1: OVERVIEW & STATUS                                            */}
      {/* =================================================================== */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Scientific Safeguard Banner (Unconditional Operational Abstention Disclosure) */}
          <div className="bg-amber-50/80 border border-amber-300 rounded-2xl p-5 shadow-sm">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-amber-900">
                    Scientific Data Gate & Prediction Safeguard
                  </h4>
                  <span className="bg-amber-200/70 text-amber-900 text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                    PREDICTION GATE: STRICTLY BLOCKED
                  </span>
                </div>
                <p className="text-xs text-amber-900/90 leading-relaxed">
                  <strong>Empirical prediction currently unavailable</strong> — additional validated longitudinal data is required.
                  KISANcare refuses to fabricate synthetic soil numbers or extrapolate static Soil Health Cards without authentic multi-season field trials.
                  Current values reflect our <strong>First-Principles Agronomic Mass-Balance Ledger</strong> anchored in physical lab baselines.
                </p>
                {status?.abstention_recommendation && (
                  <p className="text-[11px] text-amber-800 font-medium mt-1">
                    Recommendation: {status.abstention_recommendation}
                  </p>
                )}
              </div>
            </div>
          </div>

          {!status && !loading && (
            <div className="bg-white rounded-2xl p-8 border border-[#E5DDCF] text-center space-y-4">
              <TestTube className="w-12 h-12 text-[#103D2C]/30 mx-auto" />
              <div>
                <h3 className="font-bold text-base text-[#103D2C]">No Baseline Established for Plot "{plotId}"</h3>
                <p className="text-xs text-stone-500 max-w-md mx-auto mt-1">
                  Upload an existing Soil Health Card (SHC) or directly enter an accredited laboratory soil test to anchor the digital timeline.
                </p>
              </div>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => setActiveTab('upload')}
                  className="bg-[#103D2C] hover:bg-[#17643E] text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2"
                >
                  <Upload className="w-3.5 h-3.5" /> Upload Lab Report
                </button>
                <button
                  onClick={() => setActiveTab('baseline')}
                  className="border border-[#103D2C] text-[#103D2C] hover:bg-stone-50 px-4 py-2 rounded-xl text-xs font-semibold"
                >
                  Enter Baseline Manually
                </button>
              </div>
            </div>
          )}

          {status && (
            <>
              {/* Baseline Summary & Accreditation Badge */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs text-stone-500">
                    <span>Laboratory Baseline</span>
                    {status.accreditation_verified ? (
                      <span className="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded text-[10px] flex items-center gap-1">
                        <Check className="w-3 h-3" /> VERIFIED ACCREDITED
                      </span>
                    ) : (
                      <span className="bg-stone-100 text-stone-600 px-2 py-0.5 rounded text-[10px]">
                        UNVERIFIED ACCREDITATION
                      </span>
                    )}
                  </div>
                  <div className="font-mono text-xl font-bold text-[#103D2C]">
                    {status.baseline_date || 'N/A'}
                  </div>
                  <p className="text-[11px] text-stone-500 truncate" title={status.baseline_lab_name || ''}>
                    {status.baseline_lab_name || 'Standard Soil Lab'}
                  </p>
                </div>

                {/* Nitrogen */}
                <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs text-stone-500">
                    <span>Available Nitrogen (N)</span>
                    <span className="font-mono text-[10px] bg-stone-100 px-1.5 py-0.5 rounded">Subbiah & Asija</span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold text-[#103D2C]">
                      {status.baseline_npk_kg_ha?.N?.toFixed(1) ?? '—'}
                    </span>
                    <span className="text-xs text-stone-500">kg/ha elemental N</span>
                  </div>
                  <p className="text-[11px] text-stone-400">Baseline furrow depth: 0-15 cm</p>
                </div>

                {/* Phosphorus */}
                <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs text-stone-500">
                    <span>Available Phosphorus (P)</span>
                    <span className="font-mono text-[10px] bg-stone-100 px-1.5 py-0.5 rounded">Olsen NaHCO3</span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold text-[#103D2C]">
                      {status.baseline_npk_kg_ha?.P?.toFixed(1) ?? '—'}
                    </span>
                    <span className="text-xs text-stone-500">kg/ha elemental P</span>
                  </div>
                  <p className="text-[11px] text-stone-400">Normalized from P2O5 (x0.4364)</p>
                </div>

                {/* Potassium */}
                <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-xs text-stone-500">
                    <span>Available Potassium (K)</span>
                    <span className="font-mono text-[10px] bg-stone-100 px-1.5 py-0.5 rounded">Hanway NH4OAc</span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold text-[#103D2C]">
                      {status.baseline_npk_kg_ha?.K?.toFixed(1) ?? '—'}
                    </span>
                    <span className="text-xs text-stone-500">kg/ha elemental K</span>
                  </div>
                  <p className="text-[11px] text-stone-400">Normalized from K2O (x0.8302)</p>
                </div>
              </div>

              {/* Dynamic Mass-Balance Ledger Card */}
              {status.net_mass_balance_ledger && (
                <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
                  <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-stone-100 pb-3">
                    <div>
                      <h3 className="font-bold text-sm text-[#103D2C] uppercase tracking-wider">
                        Dynamic Multi-Year Nutrient Ledger
                      </h3>
                      <p className="text-xs text-stone-500">
                        Span: {status.net_mass_balance_ledger.start_date} to {status.net_mass_balance_ledger.end_date} ({status.net_mass_balance_ledger.days_elapsed} days)
                      </p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-stone-500">
                      <Clock className="w-3.5 h-3.5 text-stone-400" />
                      <span>Unrecorded Gap: <strong>{status.net_mass_balance_ledger.unrecorded_days_estimate} days</strong></span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Nitrogen Net Flux */}
                    <div className="p-4 bg-stone-50 rounded-xl space-y-2 border border-stone-200">
                      <div className="flex justify-between text-xs font-semibold text-stone-700">
                        <span>Nitrogen (N) Flux</span>
                        <span className={status.net_mass_balance_ledger.net_balance_n_kg_ha >= 0 ? 'text-emerald-700' : 'text-amber-700'}>
                          {status.net_mass_balance_ledger.net_balance_n_kg_ha >= 0 ? '+' : ''}
                          {status.net_mass_balance_ledger.net_balance_n_kg_ha.toFixed(1)} kg/ha
                        </span>
                      </div>
                      <div className="text-[11px] text-stone-500 space-y-1">
                        <div className="flex justify-between">
                          <span>Gross Additions (Fertilizer/BNF):</span>
                          <span className="font-mono text-emerald-600">+{status.net_mass_balance_ledger.gross_n_added_kg_ha.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Gross Removals (Harvest):</span>
                          <span className="font-mono text-amber-600">-{status.net_mass_balance_ledger.gross_n_removed_kg_ha.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between text-stone-400 border-t border-stone-200 pt-1">
                          <span>Quadrature Uncertainty:</span>
                          <span className="font-mono">±{status.net_mass_balance_ledger.balance_uncertainty_n_kg_ha.toFixed(1)} kg/ha</span>
                        </div>
                      </div>
                    </div>

                    {/* Phosphorus Net Flux */}
                    <div className="p-4 bg-stone-50 rounded-xl space-y-2 border border-stone-200">
                      <div className="flex justify-between text-xs font-semibold text-stone-700">
                        <span>Phosphorus (P) Flux</span>
                        <span className={status.net_mass_balance_ledger.net_balance_p_kg_ha >= 0 ? 'text-emerald-700' : 'text-amber-700'}>
                          {status.net_mass_balance_ledger.net_balance_p_kg_ha >= 0 ? '+' : ''}
                          {status.net_mass_balance_ledger.net_balance_p_kg_ha.toFixed(1)} kg/ha
                        </span>
                      </div>
                      <div className="text-[11px] text-stone-500 space-y-1">
                        <div className="flex justify-between">
                          <span>Gross Additions:</span>
                          <span className="font-mono text-emerald-600">+{status.net_mass_balance_ledger.gross_p_added_kg_ha.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Gross Removals:</span>
                          <span className="font-mono text-amber-600">-{status.net_mass_balance_ledger.gross_p_removed_kg_ha.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between text-stone-400 border-t border-stone-200 pt-1">
                          <span>Quadrature Uncertainty:</span>
                          <span className="font-mono">±{status.net_mass_balance_ledger.balance_uncertainty_p_kg_ha.toFixed(1)} kg/ha</span>
                        </div>
                      </div>
                    </div>

                    {/* Potassium Net Flux */}
                    <div className="p-4 bg-stone-50 rounded-xl space-y-2 border border-stone-200">
                      <div className="flex justify-between text-xs font-semibold text-stone-700">
                        <span>Potassium (K) Flux</span>
                        <span className={status.net_mass_balance_ledger.net_balance_k_kg_ha >= 0 ? 'text-emerald-700' : 'text-amber-700'}>
                          {status.net_mass_balance_ledger.net_balance_k_kg_ha >= 0 ? '+' : ''}
                          {status.net_mass_balance_ledger.net_balance_k_kg_ha.toFixed(1)} kg/ha
                        </span>
                      </div>
                      <div className="text-[11px] text-stone-500 space-y-1">
                        <div className="flex justify-between">
                          <span>Gross Additions:</span>
                          <span className="font-mono text-emerald-600">+{status.net_mass_balance_ledger.gross_k_added_kg_ha.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Gross Removals:</span>
                          <span className="font-mono text-amber-600">-{status.net_mass_balance_ledger.gross_k_removed_kg_ha.toFixed(1)}</span>
                        </div>
                        <div className="flex justify-between text-stone-400 border-t border-stone-200 pt-1">
                          <span>Quadrature Uncertainty:</span>
                          <span className="font-mono">±{status.net_mass_balance_ledger.balance_uncertainty_k_kg_ha.toFixed(1)} kg/ha</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Educational Agronomic Advisory Cards */}
              <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
                <div className="border-b border-stone-100 pb-3">
                  <h3 className="font-bold text-sm text-[#103D2C] uppercase tracking-wider">
                    Agronomic Educational Guidance (Peer-Reviewed Benchmarks)
                  </h3>
                  <p className="text-xs text-stone-500">
                    Grounded in ICAR, Jackson (1973), Olsen (1954), Subbiah & Asija (1956), and Tandon (2004) standards.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {status.advisories.map((adv, idx) => (
                    <div key={idx} className="p-4 bg-stone-50/70 rounded-xl border border-stone-200 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-xs text-[#103D2C] uppercase">{adv.parameter}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                          adv.status_tier.includes('LOW') || adv.status_tier.includes('ACID') || adv.status_tier.includes('ALKALINE')
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {adv.status_label || adv.status_tier}
                        </span>
                      </div>
                      <p className="text-xs text-stone-700 leading-relaxed">
                        {adv.educational_interpretation}
                      </p>
                      {adv.management_considerations?.length > 0 && (
                        <ul className="text-[11px] text-stone-600 space-y-1 list-disc list-inside">
                          {adv.management_considerations.map((c, ci) => (
                            <li key={ci}>{c}</li>
                          ))}
                        </ul>
                      )}
                      <div className="text-[10px] text-stone-400 italic pt-1 border-t border-stone-200">
                        Standard: {adv.scientific_reference}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200/60 space-y-1">
                  <h5 className="font-bold text-xs text-emerald-900">General Agronomic Principles:</h5>
                  <ul className="text-xs text-emerald-800/90 list-disc list-inside space-y-0.5">
                    {status.general_recommendations.map((rec, ri) => (
                      <li key={ri}>{rec}</li>
                    ))}
                  </ul>
                  <p className="text-[10px] text-emerald-700 pt-1 italic">
                    {status.agronomic_disclaimer}
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: UPLOAD & OCR INGESTION                                       */}
      {/* =================================================================== */}
      {activeTab === 'upload' && (
        <div className="space-y-6">
          {/* Card 1: Real File Upload */}
          <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-stone-100 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-base text-[#103D2C]">Upload Soil Health Card / Laboratory Report</h3>
                  <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Real Upload
                  </span>
                </div>
                <p className="text-xs text-stone-500 mt-0.5">
                  Directly upload scanned or digital Soil Health Cards and laboratory test reports.
                </p>
              </div>
              <div className="text-[11px] text-stone-500 font-mono">
                Formats: <strong className="text-stone-700">PDF, JPG, JPEG, PNG</strong> • Max: <strong className="text-stone-700">5 MB</strong>
              </div>
            </div>

            {/* Drag & Drop Zone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
                dragActive
                  ? 'border-[#103D2C] bg-emerald-50/50 scale-[0.99]'
                  : selectedFile
                  ? 'border-emerald-400 bg-emerald-50/20'
                  : 'border-stone-300 hover:border-[#103D2C]/60 hover:bg-stone-50/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
                className="hidden"
              />

              {!selectedFile ? (
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-full bg-emerald-100/70 text-[#103D2C] flex items-center justify-center mx-auto">
                    <FileUp className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#103D2C]">
                      Drag &amp; drop your soil report here
                    </p>
                    <p className="text-xs text-stone-500 mt-1">
                      or click below to choose a file from your computer
                    </p>
                  </div>
                  <div>
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="bg-[#103D2C] hover:bg-[#17643E] text-white px-5 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 cursor-pointer transition-colors shadow-sm"
                    >
                      <Upload className="w-4 h-4" /> Choose File
                    </button>
                  </div>
                  <p className="text-[11px] text-stone-400 font-medium">
                    Accepted: PDF, JPG, JPEG, PNG up to 5MB
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-emerald-200 max-w-lg mx-auto shadow-sm">
                    <div className="flex items-center gap-3 text-left">
                      <div className="w-10 h-10 rounded-lg bg-emerald-100 text-[#103D2C] flex items-center justify-center shrink-0">
                        {selectedFile.name.toLowerCase().endsWith('.pdf') ? (
                          <FileText className="w-5 h-5 text-emerald-800" />
                        ) : (
                          <FileCheck className="w-5 h-5 text-emerald-800" />
                        )}
                      </div>
                      <div className="overflow-hidden">
                        <div className="text-xs font-bold text-stone-800 truncate" title={selectedFile.name}>
                          {selectedFile.name}
                        </div>
                        <div className="text-[11px] text-stone-500">
                          {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Document'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation'}
                        className="text-[11px] font-semibold text-[#103D2C] hover:underline px-2 py-1"
                      >
                        Replace
                      </button>
                      <button
                        type="button"
                        onClick={clearSelectedFile}
                        disabled={uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation'}
                        className="text-stone-400 hover:text-rose-600 p-1 rounded-lg hover:bg-stone-100 transition-colors"
                        title="Remove file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Processing Stepper */}
                  {(uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation' || uploadPhase === 'results') && (
                    <div className="max-w-lg mx-auto bg-stone-50 p-3 rounded-xl border border-stone-200 space-y-2">
                      <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-bold">
                        <div className={`p-1 rounded ${uploadPhase === 'uploading' ? 'bg-amber-100 text-amber-900 ring-2 ring-amber-400 animate-pulse' : 'bg-emerald-100 text-emerald-900'}`}>
                          1. Uploading
                        </div>
                        <div className={`p-1 rounded ${uploadPhase === 'processing' ? 'bg-amber-100 text-amber-900 ring-2 ring-amber-400 animate-pulse' : (uploadPhase === 'validation' || uploadPhase === 'results') ? 'bg-emerald-100 text-emerald-900' : 'bg-stone-200 text-stone-500'}`}>
                          2. OCR Extract
                        </div>
                        <div className={`p-1 rounded ${uploadPhase === 'validation' ? 'bg-amber-100 text-amber-900 ring-2 ring-amber-400 animate-pulse' : uploadPhase === 'results' ? 'bg-emerald-100 text-emerald-900' : 'bg-stone-200 text-stone-500'}`}>
                          3. Validation
                        </div>
                        <div className={`p-1 rounded ${uploadPhase === 'results' ? 'bg-emerald-100 text-emerald-900 ring-2 ring-emerald-500' : 'bg-stone-200 text-stone-500'}`}>
                          4. Results
                        </div>
                      </div>
                      <div className="text-[11px] text-stone-600 font-medium text-center">
                        {uploadPhase === 'uploading' && 'Uploading document to secure processing adapter...'}
                        {uploadPhase === 'processing' && 'Running document parser and OCR text extraction...'}
                        {uploadPhase === 'validation' && 'Normalizing stoichiometric nutrients & verifying ICAR bounds...'}
                        {uploadPhase === 'results' && 'Document parsing completed successfully!'}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex justify-center gap-3 pt-2">
                    <button
                      type="button"
                      onClick={handleUploadAndParse}
                      disabled={uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation'}
                      className="bg-[#103D2C] hover:bg-[#17643E] disabled:bg-stone-400 text-white px-6 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 cursor-pointer shadow-sm transition-colors"
                    >
                      <Sparkles className={`w-4 h-4 ${(uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation') ? 'animate-spin' : ''}`} />
                      {(uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation') ? 'Processing Document...' : 'Upload & Parse Document'}
                    </button>
                    <button
                      type="button"
                      onClick={clearSelectedFile}
                      disabled={uploadPhase === 'uploading' || uploadPhase === 'processing' || uploadPhase === 'validation'}
                      className="border border-stone-300 hover:bg-stone-100 text-stone-700 px-4 py-2 rounded-xl text-xs font-semibold"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Validation Error Banner */}
            {fileValidationError && (
              <div className="bg-rose-50 border border-rose-200 text-rose-800 p-3 rounded-xl text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{fileValidationError}</span>
              </div>
            )}
          </div>

          {/* Card 2: Demo Sample & OCR Text Ingestion (Clearly distinguished) */}
          <div className="bg-stone-50/70 rounded-2xl p-6 border border-stone-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-sm text-[#103D2C]">Demo Samples &amp; OCR Text Stream</h4>
                  <span className="bg-stone-200 text-stone-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                    Demo Mode
                  </span>
                </div>
                <p className="text-xs text-stone-500">
                  Or test the parser directly using standard benchmark cards or pasted raw OCR stream text.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setUploadPhase('idle');
                    if (fileInputRef.current) fileInputRef.current.value = '';
                    setReportText(SAMPLE_SHC_TEXT);
                    notify('Loaded valid Maharashtra Soil Health Card benchmark sample.');
                  }}
                  className="text-xs px-3 py-1.5 rounded-lg border border-emerald-600 bg-white text-emerald-700 hover:bg-emerald-50 font-medium transition-colors"
                >
                  Load Valid Maharashtra SHC Sample
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setUploadPhase('idle');
                    if (fileInputRef.current) fileInputRef.current.value = '';
                    setReportText(OUT_OF_BOUNDS_SAMPLE_TEXT);
                    notify('Loaded out-of-bounds sample (triggers agronomist review).');
                  }}
                  className="text-xs px-3 py-1.5 rounded-lg border border-amber-600 bg-white text-amber-700 hover:bg-amber-50 font-medium transition-colors"
                >
                  Load Out-of-Bounds Test (Triggers Review)
                </button>
              </div>
            </div>

            <div>
              <textarea
                value={reportText}
                onChange={(e) => setReportText(e.target.value)}
                rows={6}
                className="w-full font-mono text-xs p-3 bg-white border border-stone-300 rounded-xl focus:ring-2 focus:ring-[#103D2C] focus:outline-none"
                placeholder="Paste OCR text stream here..."
              />
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleParseReport}
                disabled={parsingLoading}
                className="bg-[#103D2C] hover:bg-[#17643E] text-white px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 cursor-pointer transition-colors shadow-sm"
              >
                <Sparkles className={`w-4 h-4 ${parsingLoading ? 'animate-spin' : ''}`} />
                {parsingLoading ? 'Parsing & Normalizing...' : 'Parse & Validate Text'}
              </button>
            </div>
          </div>

          {/* Parsed Results Presentation */}
          {parsedDoc && (
            <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-stone-100 pb-3">
                <div>
                  <h4 className="font-bold text-sm text-[#103D2C] uppercase tracking-wider">
                    Extracted Soil Parameters & Range Validation
                  </h4>
                  <p className="text-xs text-stone-500 mt-0.5">
                    Confidence: <strong>{(parsedDoc.confidence_score * 100).toFixed(1)}%</strong> • Sample ID: <strong className="text-stone-700">{parsedDoc.report_id || 'Not detected'}</strong> • Date: <strong className="text-stone-700">{parsedDoc.sample_date || 'Not detected'}</strong>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {parsedDoc.requires_human_review ? (
                    <span className="bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1 border border-amber-300">
                      <AlertTriangle className="w-3.5 h-3.5" /> Agronomist Review Required
                    </span>
                  ) : (
                    <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1 border border-emerald-300">
                      <CheckCircle2 className="w-3.5 h-3.5" /> High Confidence Normalization
                    </span>
                  )}

                  <button
                    onClick={populateBaselineFromOCR}
                    className="bg-[#DDA74A] hover:bg-[#C9963E] text-[#103D2C] px-3 py-1 rounded-lg text-xs font-bold"
                  >
                    Transfer to Baseline
                  </button>
                </div>
              </div>

              {/* Extraction Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-stone-50 text-stone-600 uppercase font-semibold border-b border-stone-200">
                    <tr>
                      <th className="p-3">Parameter</th>
                      <th className="p-3">Raw Reported</th>
                      <th className="p-3">Reported Form</th>
                      <th className="p-3">Normalized (Elemental)</th>
                      <th className="p-3">Analytical Method</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {/* Nitrogen */}
                    <tr>
                      <td className="p-3 font-bold text-[#103D2C]">Available Nitrogen (N)</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.nitrogen?.reported_value != null ? `${parsedDoc.nitrogen.reported_value} ${parsedDoc.nitrogen.reported_unit || 'kg/ha'}` : '—'}
                      </td>
                      <td className="p-3 font-mono">{parsedDoc.nitrogen?.reported_form ?? '—'}</td>
                      <td className="p-3 font-mono font-bold text-emerald-700">
                        {parsedDoc.nitrogen?.normalized_value_kg_ha != null ? `${parsedDoc.nitrogen.normalized_value_kg_ha.toFixed(1)} kg/ha` : '—'}
                      </td>
                      <td className="p-3 text-stone-500 text-[11px]">{parsedDoc.nitrogen?.test_method ?? 'Alkaline Permanganate (Subbiah & Asija)'}</td>
                      <td className="p-3">
                        {parsedDoc.nitrogen?.normalized_value_kg_ha != null ? (
                          <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[10px] font-bold">NORMALIZED</span>
                        ) : (
                          <span className="bg-stone-100 text-stone-500 px-2 py-0.5 rounded text-[10px] font-semibold">NOT DETECTED</span>
                        )}
                      </td>
                    </tr>

                    {/* Phosphorus */}
                    <tr>
                      <td className="p-3 font-bold text-[#103D2C]">Available Phosphorus (P)</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.phosphorus?.reported_value != null ? `${parsedDoc.phosphorus.reported_value} ${parsedDoc.phosphorus.reported_unit || 'kg/ha'}` : '—'}
                      </td>
                      <td className="p-3 font-mono">{parsedDoc.phosphorus?.reported_form ?? '—'}</td>
                      <td className="p-3 font-mono font-bold text-emerald-700">
                        {parsedDoc.phosphorus?.normalized_value_kg_ha != null ? `${parsedDoc.phosphorus.normalized_value_kg_ha.toFixed(2)} kg/ha` : '—'}
                      </td>
                      <td className="p-3 text-stone-500 text-[11px]">{parsedDoc.phosphorus?.test_method ?? 'Olsen 0.5M NaHCO3'}</td>
                      <td className="p-3">
                        {parsedDoc.phosphorus?.normalized_value_kg_ha != null ? (
                          <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[10px] font-bold">
                            {parsedDoc.phosphorus.reported_form?.toUpperCase().includes('P2O5') || parsedDoc.phosphorus.reported_form?.toUpperCase().includes('P205')
                              ? 'OXIDE-TO-ELEMENTAL (×0.4364)'
                              : 'NORMALIZED'}
                          </span>
                        ) : (
                          <span className="bg-stone-100 text-stone-500 px-2 py-0.5 rounded text-[10px] font-semibold">NOT DETECTED</span>
                        )}
                      </td>
                    </tr>

                    {/* Potassium */}
                    <tr>
                      <td className="p-3 font-bold text-[#103D2C]">Available Potassium (K)</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.potassium?.reported_value != null ? `${parsedDoc.potassium.reported_value} ${parsedDoc.potassium.reported_unit || 'kg/ha'}` : '—'}
                      </td>
                      <td className="p-3 font-mono">{parsedDoc.potassium?.reported_form ?? '—'}</td>
                      <td className="p-3 font-mono font-bold text-emerald-700">
                        {parsedDoc.potassium?.normalized_value_kg_ha != null ? `${parsedDoc.potassium.normalized_value_kg_ha.toFixed(1)} kg/ha` : '—'}
                      </td>
                      <td className="p-3 text-stone-500 text-[11px]">{parsedDoc.potassium?.test_method ?? 'Neutral 1N NH4OAc (Hanway)'}</td>
                      <td className="p-3">
                        {parsedDoc.potassium?.normalized_value_kg_ha != null ? (
                          <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[10px] font-bold">
                            {parsedDoc.potassium.reported_form?.toUpperCase().includes('K2O') || parsedDoc.potassium.reported_form?.toUpperCase().includes('K20')
                              ? 'OXIDE-TO-ELEMENTAL (×0.8302)'
                              : 'NORMALIZED'}
                          </span>
                        ) : (
                          <span className="bg-stone-100 text-stone-500 px-2 py-0.5 rounded text-[10px] font-semibold">NOT DETECTED</span>
                        )}
                      </td>
                    </tr>

                    {/* pH */}
                    <tr>
                      <td className="p-3 font-bold text-[#103D2C]">Soil Reaction (pH)</td>
                      <td className="p-3 font-mono font-bold">
                        {parsedDoc.ph != null ? parsedDoc.ph.toFixed(2) : '—'}
                      </td>
                      <td className="p-3 text-stone-400">1:2.5 soil-water suspension</td>
                      <td className="p-3 font-mono font-bold">
                        {parsedDoc.ph != null ? parsedDoc.ph.toFixed(2) : '—'}
                      </td>
                      <td className="p-3 text-stone-500 text-[11px]">Potentiometric Glass Electrode (Jackson 1973)</td>
                      <td className="p-3">
                        {parsedDoc.ph != null ? (
                          <span className="bg-stone-100 text-stone-700 px-2 py-0.5 rounded text-[10px] font-semibold">MEASURED</span>
                        ) : (
                          <span className="bg-stone-100 text-stone-500 px-2 py-0.5 rounded text-[10px] font-semibold">NOT DETECTED</span>
                        )}
                      </td>
                    </tr>

                    {/* Electrical Conductivity (EC) */}
                    <tr>
                      <td className="p-3 font-bold text-[#103D2C]">Electrical Conductivity (EC)</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.ec_ds_m != null ? `${parsedDoc.ec_ds_m.toFixed(2)} dS/m` : '—'}
                      </td>
                      <td className="p-3 text-stone-400">1:2.5 suspension</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.ec_ds_m != null ? `${parsedDoc.ec_ds_m.toFixed(2)} dS/m` : '—'}
                      </td>
                      <td className="p-3 text-stone-500 text-[11px]">Conductivity Bridge (25°C)</td>
                      <td className="p-3">
                        {parsedDoc.ec_ds_m != null ? (
                          <span className="bg-stone-100 text-stone-700 px-2 py-0.5 rounded text-[10px] font-semibold">MEASURED</span>
                        ) : (
                          <span className="bg-stone-100 text-stone-500 px-2 py-0.5 rounded text-[10px] font-semibold">NOT DETECTED</span>
                        )}
                      </td>
                    </tr>

                    {/* Organic Carbon (OC) */}
                    <tr>
                      <td className="p-3 font-bold text-[#103D2C]">Organic Carbon (OC)</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.organic_carbon_pct != null ? `${parsedDoc.organic_carbon_pct.toFixed(2)} %` : '—'}
                      </td>
                      <td className="p-3 text-stone-400">Soil organic mass %</td>
                      <td className="p-3 font-mono">
                        {parsedDoc.organic_carbon_pct != null ? `${parsedDoc.organic_carbon_pct.toFixed(2)} %` : '—'}
                      </td>
                      <td className="p-3 text-stone-500 text-[11px]">Walkley-Black Wet Oxidation</td>
                      <td className="p-3">
                        {parsedDoc.organic_carbon_pct != null ? (
                          <span className="bg-stone-100 text-stone-700 px-2 py-0.5 rounded text-[10px] font-semibold">MEASURED</span>
                        ) : (
                          <span className="bg-stone-100 text-stone-500 px-2 py-0.5 rounded text-[10px] font-semibold">NOT DETECTED</span>
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Collapsible Raw Extracted OCR Stream Panel */}
              {parsedDoc.raw_ocr_text && (
                <div className="border border-stone-200 rounded-xl overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setShowRawOcrText((prev) => !prev)}
                    className="w-full flex items-center justify-between p-3 bg-stone-50 hover:bg-stone-100 text-xs font-semibold text-stone-700 transition-colors cursor-pointer text-left"
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-[#103D2C]" />
                      <span>View Raw Extracted OCR Text Stream ({parsedDoc.raw_ocr_text.length} characters)</span>
                    </span>
                    <span className="text-[11px] font-mono text-stone-500">
                      {showRawOcrText ? 'Hide ▲' : 'Show ▼'}
                    </span>
                  </button>
                  {showRawOcrText && (
                    <div className="p-4 bg-stone-900 border-t border-stone-800">
                      <div className="flex justify-between items-center pb-2 mb-2 border-b border-stone-800 text-[11px] text-stone-400">
                        <span>Direct output from OCR engine &amp; document parser:</span>
                        <span className="font-mono">{parsedDoc.raw_ocr_text.split('\n').length} lines</span>
                      </div>
                      <pre className="text-xs text-emerald-400 font-mono overflow-x-auto max-h-60 whitespace-pre-wrap select-all leading-relaxed">
                        {parsedDoc.raw_ocr_text}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Validation Issues / Agronomist Review Section */}
              {parsedDoc.requires_human_review && (
                <div className="bg-amber-50 p-4 rounded-xl border border-amber-300 space-y-3">
                  <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>Out-of-Bounds Fields Queued for Agronomist Verification (Review Token: {parsedDoc.review_token})</span>
                  </div>

                  <p className="text-[11px] text-amber-800">
                    Click any flagged issue below to pre-select it for manual review and entry:
                  </p>

                  <div className="space-y-1.5">
                    {parsedDoc.validation_issues.map((iss, ii) => (
                      <button
                        key={ii}
                        type="button"
                        onClick={() => {
                          setCorrectionField(iss.field);
                          setCorrectionValue('');
                        }}
                        className="w-full text-left text-xs bg-white/80 hover:bg-white border border-amber-200 hover:border-amber-400 p-2 rounded-lg transition-colors flex items-center justify-between"
                      >
                        <div>
                          <strong className="text-amber-950 font-semibold">{iss.field}:</strong>{' '}
                          <span className="text-amber-900">{iss.message}</span>
                        </div>
                        <span className="text-[10px] font-mono bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-bold">
                          {iss.issue_code}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Correction Form */}
                  <div className="pt-3 border-t border-amber-200 grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
                    <div>
                      <label className="block text-[11px] font-medium text-amber-900 mb-1">Target Field</label>
                      <input
                        type="text"
                        placeholder="e.g. nitrogen, ph"
                        value={correctionField}
                        onChange={(e) => setCorrectionField(e.target.value)}
                        className="w-full text-xs p-2 bg-white border border-amber-300 rounded-lg focus:ring-1 focus:ring-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-amber-900 mb-1">Corrected Value</label>
                      <input
                        type="text"
                        placeholder="Enter verified value"
                        value={correctionValue}
                        onChange={(e) => setCorrectionValue(e.target.value)}
                        className="w-full text-xs p-2 bg-white border border-amber-300 rounded-lg font-mono focus:ring-1 focus:ring-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-amber-900 mb-1">Audit Notes</label>
                      <input
                        type="text"
                        placeholder="Reason for change"
                        value={correctionNotes}
                        onChange={(e) => setCorrectionNotes(e.target.value)}
                        className="w-full text-xs p-2 bg-white border border-amber-300 rounded-lg focus:ring-1 focus:ring-amber-500"
                      />
                    </div>
                    <div>
                      <button
                        onClick={handleCorrection}
                        disabled={correctingLoading || !correctionField || !correctionValue}
                        className="w-full bg-amber-700 hover:bg-amber-800 disabled:bg-stone-300 disabled:text-stone-500 text-white font-bold py-2 rounded-lg text-xs cursor-pointer transition-colors"
                      >
                        {correctingLoading ? 'Submitting...' : 'Apply Correction'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 3: LABORATORY BASELINE CONFIRMATION                             */}
      {/* =================================================================== */}
      {activeTab === 'baseline' && (
        <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-6">
          <div>
            <h3 className="font-bold text-base text-[#103D2C]">Register Physical Laboratory Baseline</h3>
            <p className="text-xs text-stone-500">
              Anchors the plot's digital twin with certified laboratory measurements (MEASURED provenance).
            </p>
          </div>

          <form onSubmit={handleConfirmBaseline} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Plot Identifier</label>
                <input
                  type="text"
                  value={plotId}
                  onChange={(e) => setPlotId(e.target.value.toUpperCase())}
                  required
                  className="w-full text-xs p-2.5 border border-stone-300 rounded-xl font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Sampling Date (YYYY-MM-DD)</label>
                <input
                  type="date"
                  value={baseDate}
                  onChange={(e) => setBaseDate(e.target.value)}
                  required
                  className="w-full text-xs p-2.5 border border-stone-300 rounded-xl font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Laboratory Name</label>
                <input
                  type="text"
                  value={baseLabName}
                  onChange={(e) => setBaseLabName(e.target.value)}
                  required
                  className="w-full text-xs p-2.5 border border-stone-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Lab Certificate Number</label>
                <input
                  type="text"
                  value={baseCertNo}
                  onChange={(e) => setBaseCertNo(e.target.value)}
                  className="w-full text-xs p-2.5 border border-stone-300 rounded-xl font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">Accreditation ID</label>
                <input
                  type="text"
                  value={baseAccredId}
                  onChange={(e) => setBaseAccredId(e.target.value)}
                  className="w-full text-xs p-2.5 border border-stone-300 rounded-xl font-mono"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="accredVerified"
                  checked={baseAccredVerified}
                  onChange={(e) => setBaseAccredVerified(e.target.checked)}
                  className="w-4 h-4 accent-[#103D2C] rounded"
                />
                <label htmlFor="accredVerified" className="text-xs font-medium text-stone-700">
                  Accreditation explicitly verified via portal
                </label>
              </div>
            </div>

            <div className="border-t border-stone-100 pt-4">
              <h4 className="font-bold text-xs uppercase tracking-wider text-stone-600 mb-3">
                Laboratory Soil Chemical Measurements (Normalized)
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">N (kg/ha)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={baseN}
                    onChange={(e) => setBaseN(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono font-bold text-[#103D2C]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">P (kg/ha elemental)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={baseP}
                    onChange={(e) => setBaseP(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono font-bold text-[#103D2C]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">K (kg/ha elemental)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={baseK}
                    onChange={(e) => setBaseK(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono font-bold text-[#103D2C]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">pH</label>
                  <input
                    type="number"
                    step="0.05"
                    value={basePh}
                    onChange={(e) => setBasePh(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">EC (dS/m)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={baseEc}
                    onChange={(e) => setBaseEc(Number(e.target.value))}
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">Organic Carbon (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={baseOc}
                    onChange={(e) => setBaseOc(Number(e.target.value))}
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="bg-[#103D2C] hover:bg-[#17643E] text-white px-6 py-2.5 rounded-xl text-xs font-bold shadow-sm transition-colors cursor-pointer"
              >
                {loading ? 'Confirming...' : 'Confirm Laboratory Baseline'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 4: NUTRIENT TIMELINE LEDGER                                     */}
      {/* =================================================================== */}
      {activeTab === 'timeline' && (
        <div className="space-y-6">
          {/* Action Modals / In-line Forms */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Log Fertilizer */}
            <form onSubmit={handleRecordFertilizer} className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-stone-100 pb-2">
                <Plus className="w-4 h-4 text-emerald-600" />
                <h4 className="font-bold text-xs uppercase tracking-wider text-[#103D2C]">Log Fertilizer / Manure Event</h4>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Fertilizer Grade</label>
                  <select
                    value={fertGrade}
                    onChange={(e) => setFertGrade(e.target.value)}
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg bg-white"
                  >
                    {benchmarks?.supported_fertilizers.map((f) => (
                      <option key={f} value={f}>{f.toUpperCase()}</option>
                    )) || (
                      <>
                        <option value="DAP">DAP (18-46-0)</option>
                        <option value="Urea">Urea (46-0-0)</option>
                        <option value="MOP">MOP (0-0-60)</option>
                        <option value="10:26:26">NPK 10:26:26</option>
                        <option value="FYM">Farmyard Manure (FYM)</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Quantity (kg/ha)</label>
                  <input
                    type="number"
                    step="1"
                    value={fertQty}
                    onChange={(e) => setFertQty(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Application Date</label>
                  <input
                    type="date"
                    value={fertDate}
                    onChange={(e) => setFertDate(e.target.value)}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Notes</label>
                  <input
                    type="text"
                    value={fertNotes}
                    onChange={(e) => setFertNotes(e.target.value)}
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-1">
                <button
                  type="submit"
                  className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-4 py-2 rounded-lg text-xs"
                >
                  Add Nutrient Input
                </button>
              </div>
            </form>

            {/* Log Crop Harvest */}
            <form onSubmit={handleRecordHarvest} className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-stone-100 pb-2">
                <TrendingDown className="w-4 h-4 text-amber-600" />
                <h4 className="font-bold text-xs uppercase tracking-wider text-[#103D2C]">Log Crop Harvest Depletion</h4>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Harvested Crop</label>
                  <select
                    value={harvestCrop}
                    onChange={(e) => setHarvestCrop(e.target.value)}
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg bg-white"
                  >
                    {benchmarks?.supported_crops.map((c) => (
                      <option key={c} value={c}>{c.toUpperCase()}</option>
                    )) || (
                      <>
                        <option value="Soybean">Soybean</option>
                        <option value="Wheat">Wheat</option>
                        <option value="Cotton">Cotton</option>
                        <option value="Rice">Rice</option>
                        <option value="Maize">Maize</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Economic Yield (t/ha)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={harvestYield}
                    onChange={(e) => setHarvestYield(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-stone-600 mb-1">Harvest Date</label>
                  <input
                    type="date"
                    value={harvestDate}
                    onChange={(e) => setHarvestDate(e.target.value)}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>

                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="residueRetained"
                    checked={harvestResidue}
                    onChange={(e) => setHarvestResidue(e.target.checked)}
                    className="w-4 h-4 accent-[#103D2C] rounded"
                  />
                  <label htmlFor="residueRetained" className="text-xs text-stone-700">
                    Stover/straw retained
                  </label>
                </div>
              </div>

              <div className="flex justify-end pt-1">
                <button
                  type="submit"
                  className="bg-amber-700 hover:bg-amber-800 text-white font-bold px-4 py-2 rounded-lg text-xs"
                >
                  Record Crop Depletion
                </button>
              </div>
            </form>
          </div>

          {/* Chronological Event History */}
          <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
            <div className="flex justify-between items-center border-b border-stone-100 pb-3">
              <div>
                <h3 className="font-bold text-sm text-[#103D2C] uppercase tracking-wider">Chronological Farm Plot History</h3>
                <p className="text-xs text-stone-500">Total Events: {events.length}</p>
              </div>

              {events.length > 0 && (
                <button
                  onClick={handleDeletePlot}
                  className="text-xs text-red-600 hover:text-red-800 font-medium"
                >
                  Reset Timeline
                </button>
              )}
            </div>

            {events.length === 0 ? (
              <p className="text-xs text-stone-400 py-6 text-center italic">
                No events recorded yet. Log a fertilizer application or crop harvest above.
              </p>
            ) : (
              <div className="space-y-3">
                {events.map((ev) => {
                  const isDepletion = ev.n_flux_kg_ha < 0 || ev.p_flux_kg_ha < 0 || ev.k_flux_kg_ha < 0;
                  return (
                    <div
                      key={ev.event_id}
                      className="p-4 rounded-xl border border-stone-200 bg-stone-50/60 flex flex-col sm:flex-row justify-between sm:items-center gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            isDepletion ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                          }`}>
                            {ev.event_type}
                          </span>
                          <span className="font-mono text-xs font-semibold text-stone-800">{ev.event_date}</span>
                        </div>
                        <p className="text-xs text-stone-700 font-medium">{ev.description}</p>
                        <p className="text-[10px] text-stone-400 italic">Source: {ev.source_citation}</p>
                      </div>

                      <div className="flex items-center gap-4 text-xs font-mono">
                        <div className="text-right">
                          <span className="text-[10px] text-stone-400 block">Δ N</span>
                          <span className={ev.n_flux_kg_ha >= 0 ? 'text-emerald-600 font-bold' : 'text-amber-600 font-bold'}>
                            {ev.n_flux_kg_ha >= 0 ? '+' : ''}{ev.n_flux_kg_ha.toFixed(1)}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-[10px] text-stone-400 block">Δ P</span>
                          <span className={ev.p_flux_kg_ha >= 0 ? 'text-emerald-600 font-bold' : 'text-amber-600 font-bold'}>
                            {ev.p_flux_kg_ha >= 0 ? '+' : ''}{ev.p_flux_kg_ha.toFixed(1)}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-[10px] text-stone-400 block">Δ K</span>
                          <span className={ev.k_flux_kg_ha >= 0 ? 'text-emerald-600 font-bold' : 'text-amber-600 font-bold'}>
                            {ev.k_flux_kg_ha >= 0 ? '+' : ''}{ev.k_flux_kg_ha.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 5: LAB RETEST & COMPARATOR                                      */}
      {/* =================================================================== */}
      {activeTab === 'compare' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
            <div>
              <h3 className="font-bold text-base text-[#103D2C]">Ingest Ground-Truth Physical Re-Test</h3>
              <p className="text-xs text-stone-500">
                Tests continuous prediction drift and verifies whether field measurements meet provisional tolerances (N ±25, P ±5, K ±30 kg/ha).
              </p>
            </div>

            <form onSubmit={handleCompareRetest} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Re-test Date</label>
                  <input
                    type="date"
                    value={retestDate}
                    onChange={(e) => setRetestDate(e.target.value)}
                    required
                    className="w-full text-xs p-2.5 border border-stone-300 rounded-xl font-mono"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-semibold text-stone-700 mb-1">Testing Laboratory Name</label>
                  <input
                    type="text"
                    value={retestLabName}
                    onChange={(e) => setRetestLabName(e.target.value)}
                    required
                    className="w-full text-xs p-2.5 border border-stone-300 rounded-xl"
                  />
                </div>

                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="retestAccred"
                    checked={retestAccred}
                    onChange={(e) => setRetestAccred(e.target.checked)}
                    className="w-4 h-4 accent-[#103D2C] rounded"
                  />
                  <label htmlFor="retestAccred" className="text-xs text-stone-700">
                    Accreditation verified
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">Re-tested N (kg/ha)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={retestN}
                    onChange={(e) => setRetestN(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">Re-tested P (kg/ha)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={retestP}
                    onChange={(e) => setRetestP(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">Re-tested K (kg/ha)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={retestK}
                    onChange={(e) => setRetestK(Number(e.target.value))}
                    required
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-stone-600 mb-1">Re-tested pH</label>
                  <input
                    type="number"
                    step="0.05"
                    value={retestPh}
                    onChange={(e) => setRetestPh(Number(e.target.value))}
                    className="w-full text-xs p-2 border border-stone-300 rounded-lg font-mono"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={comparingLoading}
                  className="bg-[#103D2C] hover:bg-[#17643E] text-white px-6 py-2.5 rounded-xl text-xs font-bold"
                >
                  {comparingLoading ? 'Evaluating...' : 'Run Comparator & Drift Audit'}
                </button>
              </div>
            </form>
          </div>

          {/* Comparison Output */}
          {comparisonResult && (
            <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
              <div className="flex justify-between items-center border-b border-stone-100 pb-3">
                <div>
                  <h4 className="font-bold text-sm text-[#103D2C] uppercase tracking-wider">
                    Continuous Comparator Evaluation Record
                  </h4>
                  <p className="text-xs text-stone-500">
                    ID: {comparisonResult.comparison_id} • Target Date: {comparisonResult.retest_date}
                  </p>
                </div>

                <div>
                  <span className="bg-amber-100 text-amber-900 text-xs font-mono px-3 py-1 rounded-full font-bold">
                    PREDICTION ABSTAINED (UNCALIBRATED)
                  </span>
                </div>
              </div>

              {/* Nutrients Evaluation Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { key: 'N', comp: comparisonResult.nitrogen_comparison },
                  { key: 'P', comp: comparisonResult.phosphorus_comparison },
                  { key: 'K', comp: comparisonResult.potassium_comparison }
                ].map(({ key, comp }) => (
                  <div key={key} className="p-4 bg-stone-50 rounded-xl border border-stone-200 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-xs text-stone-800">{comp.nutrient}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-200 text-stone-700">
                        Tol: ±{comp.provisional_tolerance_kg_ha} kg/ha
                      </span>
                    </div>

                    <div className="text-xs space-y-1">
                      <div className="flex justify-between text-stone-600">
                        <span>Actual Lab Measurement:</span>
                        <span className="font-mono font-bold text-[#103D2C]">{comp.actual_lab_kg_ha.toFixed(1)} kg/ha</span>
                      </div>
                      <div className="flex justify-between text-stone-500">
                        <span>Model Estimate:</span>
                        <span className="font-mono italic">{comp.estimated_or_predicted_kg_ha?.toFixed(1) ?? 'Abstained'}</span>
                      </div>
                      <div className="flex justify-between text-stone-500 border-t border-stone-200 pt-1">
                        <span>Directional Bias:</span>
                        <span className="font-mono text-[10px] font-bold text-amber-700">{comp.directional_bias}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {comparisonResult.drift_alert && (
                <div className="bg-amber-50 p-3 rounded-xl border border-amber-300 text-xs text-amber-900 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>{comparisonResult.drift_alert}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
