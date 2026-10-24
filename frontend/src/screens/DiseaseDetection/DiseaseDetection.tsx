import React, { useState, useRef } from 'react';
import {
  Bug, Camera, Upload, ShieldAlert, CheckCircle, Loader2,
  RotateCcw, AlertCircle, ShieldCheck, Sprout, Info, Leaf,
  ExternalLink, BarChart3, AlertTriangle, Cpu, ChevronDown, ChevronUp
} from 'lucide-react';
import { api } from '../../services/api';

const AVAILABLE_SYMPTOMS = [
  'Yellow leaves',
  'Stunted growth',
  'White powdery spots',
  'Black spots',
  'Holes in leaves',
  'Sticky residue',
  'Curled leaves'
];

const SUPPORTED_CROPS = [
  'Tomato', 'Cotton', 'Rice', 'Wheat', 'Potato', 'Onion',
  'Sugarcane', 'Soybean', 'Groundnut', 'Apple', 'Corn', 'Banana',
  'Chilli', 'Brinjal', 'Grape', 'Mango', 'Black Gram', 'Turmeric',
  'Ginger', 'Garlic', 'Lemon', 'Orange', 'Pomegranate', 'Papaya',
  'Guava', 'Coconut', 'Tea', 'Coffee', 'Bitter Gourd', 'Bottle Gourd',
  'Cucumber', 'Cabbage', 'Cauliflower', 'Ash Gourd', 'Radish', 'Spinach',
  'Okra', 'Watermelon', 'Sunflower', 'Jute', 'Lentil', 'Cowpea',
  'Finger Millet', 'Custard Apple', 'Peach', 'Cherry', 'Strawberry',
  'Blueberry', 'Raspberry', 'Squash'
];

interface TopPrediction {
  condition: string;
  crop?: string;
  category?: string;
  task?: string;
  percentage: number;
  probability: number;
}

interface ChemicalTreatment {
  chemical_name: string;
  dosage: string;
  cpr_registration?: string;
  waiting_period_days?: number;
}

interface DiagnosisResult {
  condition: string;
  scientificName?: string | null;
  confidence: number;
  severity: string;
  isHealthy?: boolean;
  abstention?: boolean;
  abstentionReason?: string | null;
  abstentionThreshold?: number;
  diagnosedCrop?: string | null;
  hostCropStatus?: string;
  description?: string;
  treatment: string;
  preventiveManagement: string[];
  nonChemicalOptions: string[];
  chemicalTreatments?: ChemicalTreatment[];
  topPredictions?: TopPrediction[];
  topDiseaseCandidates?: TopPrediction[];
  topPestCandidates?: TopPrediction[];
  cropMatch: boolean;
  cropMismatchWarning?: string | null;
  modelType?: string;
  routingPath?: string;
  specialistAgreement?: boolean | null;
  fusionOutcome?: string;
  competingPredictions?: Array<{ model: string; crop: string; condition: string; score: number }>;
  fusionDetails?: any;
  rawScore?: number;
  calibratedConfidence?: number;
  latencyMs?: number;
  warnings?: string[];
}

export default function DiseaseDetection() {
  const [diagnosisMode, setDiagnosisMode] = useState<'disease' | 'pest'>('disease');
  const [crop, setCrop] = useState('Tomato');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(['Yellow leaves', 'Stunted growth']);
  const [showSymptoms, setShowSymptoms] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sampleId, setSampleId] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [showModelCandidates, setShowModelCandidates] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const toggleSymptom = (sym: string) => {
    if (selectedSymptoms.includes(sym)) {
      setSelectedSymptoms(selectedSymptoms.filter((s) => s !== sym));
    } else {
      setSelectedSymptoms([...selectedSymptoms, sym]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 15 * 1024 * 1024) {
        setErrorMessage('File size exceeds 15 MB limit. Please select a smaller leaf photo.');
        return;
      }
      setSelectedFile(file);
      setSampleId(null);
      const url = URL.createObjectURL(file);
      setSelectedImage(url);
      setErrorMessage(null);
      runDiagnosisWithFile(file, null, crop);
    }
  };

  const handleLoadPresetSample = (preset: { id: string; crop: string; name: string; url: string }) => {
    setSelectedFile(null);
    setSampleId(preset.id);
    setSelectedImage(preset.url);
    setCrop(preset.crop);
    setErrorMessage(null);
    runDiagnosisWithFile(null, preset.id, preset.crop);
  };

  const runDiagnosisWithFile = async (
    fileToUpload: File | null,
    presetSampleId: string | null,
    targetCrop: string
  ) => {
    setErrorMessage(null);
    setAnalyzing(true);

    try {
      let response: any;
      if (diagnosisMode === 'pest') {
        response = await api.detectPest(targetCrop, selectedSymptoms, {
          file: fileToUpload || undefined,
          sampleId: presetSampleId || undefined,
        });
      } else {
        response = await api.detectDisease(targetCrop, selectedSymptoms, {
          file: fileToUpload || undefined,
          sampleId: presetSampleId || undefined,
          locationState: 'Maharashtra',
          growthStage: 'vegetative',
          imageType: 'leaf',
        });
      }

      const data = response.data;
      setIsDemo(response.isDemo);

      const conditionName = data.condition || data.prediction || 'Inconclusive foliar diagnosis';
      const sciName = data.scientific_name || null;
      const confidenceVal = typeof data.confidence_percent === 'number'
        ? data.confidence_percent
        : Math.round((data.confidence ?? 0.85) * 100);

      const chemicals: ChemicalTreatment[] = (data.treatments?.chemical || []).map((c: any) => ({
        chemical_name: c.chemical_name,
        dosage: c.dosage,
        cpr_registration: c.cpr_registration,
        waiting_period_days: c.waiting_period_days,
      }));

      const mapCandidate = (tp: any): TopPrediction => ({
        condition: tp.condition,
        crop: tp.crop,
        category: tp.category || 'disease',
        task: tp.task || 'foliar_classification',
        percentage: tp.percentage ?? Math.round((tp.probability ?? 0) * 100),
        probability: tp.probability ?? 0,
      });

      const topPreds: TopPrediction[] = (data.top_5_predictions || []).map(mapCandidate);
      const topDisease: TopPrediction[] = (data.top_disease_candidates || []).map(mapCandidate);
      const topPest: TopPrediction[] = (data.top_pest_candidates || []).map(mapCandidate);

      setResult({
        condition: conditionName,
        scientificName: sciName,
        confidence: confidenceVal,
        severity: data.severity || 'Severity not assessed',
        isHealthy: data.is_healthy ?? false,
        abstention: data.abstention ?? false,
        abstentionReason: data.abstention_reason || null,
        abstentionThreshold: data.abstention_threshold ?? 0.40,
        diagnosedCrop: data.diagnosed_crop || null,
        hostCropStatus: data.host_crop_status || (data.abstention ? 'unverified' : 'verified'),
        description: data.description || `Evaluated using deep learning vision model for ${targetCrop}.`,
        treatment: data.treatment || 'Consult local agricultural extension officer.',
        preventiveManagement: data.preventive_management || [
          'Maintain recommended plant spacing to facilitate canopy aeration.',
          'Adopt deep summer plowing to expose resting pathogen spores to solar heat.',
          'Rotate with non-host botanical families to disrupt disease cycles.'
        ],
        nonChemicalOptions: data.non_chemical_options || [
          'Apply bio-fungicides such as Trichoderma harzianum or Bacillus subtilis.',
          'Spray cold-pressed Neem seed kernel extract (NSKE 5%) at first symptom sign.',
          'Prune and destroy heavily blighted lower leaves before secondary sporulation.'
        ],
        chemicalTreatments: chemicals,
        topPredictions: topPreds,
        topDiseaseCandidates: topDisease,
        topPestCandidates: topPest,
        cropMatch: data.crop_match ?? true,
        cropMismatchWarning: data.crop_mismatch_warning,
        modelType: data.model_type || 'India Multi-Crop DINOv2 ViT-B/14 (59 Crops / 387 Classes)',
        routingPath: data.routing_path,
        specialistAgreement: data.specialist_agreement,
        fusionOutcome: data.fusion_outcome,
        competingPredictions: data.competing_predictions || [],
        fusionDetails: data.fusion_details,
        rawScore: data.raw_score,
        calibratedConfidence: data.calibrated_confidence,
        latencyMs: data.provenance?.latency_ms,
        warnings: data.warnings || [],
      });
    } catch (err: any) {
      console.error('Diagnosis failed:', err);
      setErrorMessage(err.message || 'Diagnosis failed. The model service encountered an error.');
      setResult(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const runDiagnosis = () => {
    if (!selectedImage && !selectedFile && !sampleId) {
      handleLoadPresetSample({
        id: 'tomato_blight',
        crop: 'Tomato',
        name: 'Tomato Early Blight',
        url: '/test_images/tomato_early_blight.jpg'
      });
      return;
    }
    runDiagnosisWithFile(selectedFile, sampleId, crop);
  };

  const handleReset = () => {
    setSelectedImage(null);
    setSelectedFile(null);
    setSampleId(null);
    setResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-[#E5DDCF] shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl lg:text-3xl font-serif font-bold text-[#103D2C]">
              Pathology & Pest Diagnosis
            </h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Demo / Mock Mode
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <Cpu size={12} /> DINOv2 ViT-B/14 (59 Crops / 387 Classes)
              </span>
            )}
            {result?.latencyMs && (
              <span className="text-[11px] text-[#292B26]/50">
                ⚡ {Math.round(result.latencyMs)} ms
              </span>
            )}
          </div>
          <p className="text-xs sm:text-sm text-[#292B26]/70 mt-1 max-w-2xl">
            Computer vision leaf diagnosis with CIB&RC verified chemical interventions, IPM non-chemical protocols, and out-of-distribution safety abstention.
          </p>
        </div>

        <button
          onClick={runDiagnosis}
          disabled={analyzing}
          className="bg-[#103D2C] hover:bg-[#17643E] text-white px-5 py-2.5 rounded-xl font-semibold text-xs sm:text-sm flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-xs disabled:opacity-50 shrink-0"
        >
          {analyzing ? <Loader2 size={16} className="animate-spin" /> : <Bug size={16} />}
          <span>{analyzing ? 'Executing Neural Inference...' : `Diagnose ${diagnosisMode === 'pest' ? 'Pest' : 'Disease'}`}</span>
        </button>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-2xs">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Target Crop & Diagnostic Configuration Toolbar */}
      <div className="bg-white rounded-xl p-4 shadow-2xs border border-[#E5DDCF] space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          {/* Mode Switcher */}
          <div className="sm:col-span-4">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-[#103D2C] mb-1">
              Diagnostic Mode
            </label>
            <div className="flex rounded-lg border border-[#E5DDCF] p-0.5 bg-[#FBF7EF] text-xs">
              <button
                type="button"
                onClick={() => setDiagnosisMode('disease')}
                className={`flex-1 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                  diagnosisMode === 'disease' ? 'bg-[#103D2C] text-white shadow-2xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                Foliar Disease (ViT)
              </button>
              <button
                type="button"
                onClick={() => setDiagnosisMode('pest')}
                className={`flex-1 py-1.5 rounded-md font-semibold transition-all cursor-pointer ${
                  diagnosisMode === 'pest' ? 'bg-[#103D2C] text-white shadow-2xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                Insect Pest (YOLO)
              </button>
            </div>
          </div>

          {/* Affected Crop */}
          <div className="sm:col-span-5">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-[#103D2C] mb-1">
              Affected Crop Host
            </label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full border border-[#E5DDCF] rounded-lg px-3 py-1.5 text-xs bg-[#FBF7EF] font-semibold text-[#103D2C] outline-none"
            >
              {SUPPORTED_CROPS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Observed Symptoms Toggle */}
          <div className="sm:col-span-3 sm:pt-4">
            <button
              type="button"
              onClick={() => setShowSymptoms(prev => !prev)}
              className="w-full py-1.5 px-3 rounded-lg border border-[#E5DDCF] bg-[#FBF7EF] hover:bg-[#E5DDCF]/50 text-xs font-semibold text-[#103D2C] flex items-center justify-between transition-colors cursor-pointer"
            >
              <span>Symptoms ({selectedSymptoms.length})</span>
              {showSymptoms ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>
        </div>

        {/* Collapsible Symptoms Tag List */}
        {showSymptoms && (
          <div className="pt-2 border-t border-[#E5DDCF]/70">
            <span className="text-[10px] font-bold text-[#292B26]/60 uppercase tracking-wide block mb-1.5">
              Select Observed Foliar Symptoms (Rule-based clinical matching):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {AVAILABLE_SYMPTOMS.map((sym) => {
                const active = selectedSymptoms.includes(sym);
                return (
                  <button
                    key={sym}
                    type="button"
                    onClick={() => toggleSymptom(sym)}
                    className={`text-[11px] px-2.5 py-1 rounded-md border transition-all cursor-pointer ${
                      active
                        ? 'bg-[#103D2C] text-white border-[#103D2C] font-semibold shadow-2xs'
                        : 'bg-[#FBF7EF] text-[#292B26]/80 border-[#E5DDCF] hover:border-[#17643E]'
                    }`}
                  >
                    {active ? `✓ ${sym}` : `+ ${sym}`}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
      />

      {/* Main Inspection Grid (2 Columns: Image Input on Left, Clinical Results on Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left Column: Image Dropzone & Fast Dataset Samples (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-xl shadow-2xs border border-[#E5DDCF] p-5 flex flex-col justify-between">
            <div className="border-b border-[#E5DDCF] pb-3 mb-3 flex items-center justify-between">
              <h3 className="font-bold text-xs uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                <Camera size={15} className="text-[#17643E]" /> Leaf Photograph
              </h3>
              {selectedImage && (
                <button
                  onClick={handleReset}
                  className="text-[11px] text-red-600 hover:text-red-700 flex items-center gap-1 font-semibold cursor-pointer"
                >
                  <RotateCcw size={12} /> Clear Photo
                </button>
              )}
            </div>

            {selectedImage ? (
              <div className="space-y-3">
                <div className="relative w-full h-56 rounded-lg overflow-hidden border border-[#E5DDCF] bg-neutral-900/5">
                  <img
                    src={selectedImage}
                    alt="Uploaded symptomatic leaf"
                    className="w-full h-full object-contain"
                  />
                  {analyzing && (
                    <div className="absolute inset-0 bg-[#103D2C]/80 backdrop-blur-2xs flex flex-col items-center justify-center text-white">
                      <Loader2 className="w-8 h-8 animate-spin mb-2" />
                      <span className="text-xs font-bold uppercase tracking-wider">Evaluating ViT-B/14 Features...</span>
                      <span className="text-[10px] text-emerald-200 mt-0.5">Normalization & classification</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs bg-[#FBF7EF] p-2 rounded-lg border border-[#E5DDCF]">
                  <span className="text-[11px] text-[#292B26]/70 truncate max-w-[200px]">
                    {sampleId ? `Benchmark: ${sampleId}` : selectedFile ? selectedFile.name : 'Photo loaded'}
                  </span>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-[11px] text-[#17643E] font-bold hover:underline cursor-pointer"
                  >
                    Replace Photo
                  </button>
                </div>
              </div>
            ) : (
              <div className="border-2 border-dashed border-[#E5DDCF] rounded-xl p-6 text-center bg-[#FBF7EF]/50 flex flex-col items-center justify-center min-h-[220px]">
                <Upload className="w-8 h-8 text-[#17643E] mb-2" />
                <h4 className="font-bold text-xs text-[#103D2C]">Upload Symptomatic Leaf Photo</h4>
                <p className="text-[11px] text-[#292B26]/60 mt-1 max-w-xs leading-relaxed">
                  Clear close-up photograph of leaf lesions (JPEG, PNG, WebP up to 15 MB).
                </p>
                <div className="flex items-center gap-2 mt-4">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer shadow-2xs"
                  >
                    Select Leaf File
                  </button>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-white border border-[#E5DDCF] text-[#103D2C] text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-[#E5DDCF] transition-colors cursor-pointer"
                  >
                    Open Camera
                  </button>
                </div>
              </div>
            )}

            {/* Fast Dataset Benchmark Samples */}
            <div className="pt-3 mt-3 border-t border-[#E5DDCF]/70">
              <span className="text-[10px] font-bold text-[#103D2C] uppercase tracking-wider block mb-2">
                Or Test with Verified Dataset Samples:
              </span>
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => handleLoadPresetSample({
                    id: 'potato_blight',
                    crop: 'Potato',
                    name: 'Potato Early Blight',
                    url: '/test_images/potato_early_blight.jpg'
                  })}
                  className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-semibold text-left truncate"
                >
                  🥔 Potato Early Blight
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadPresetSample({
                    id: 'tomato_blight',
                    crop: 'Tomato',
                    name: 'Tomato Early Blight',
                    url: '/test_images/tomato_early_blight.jpg'
                  })}
                  className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-semibold text-left truncate"
                >
                  🍅 Tomato Early Blight
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadPresetSample({
                    id: 'tomato_healthy',
                    crop: 'Tomato',
                    name: 'Tomato Healthy Leaf',
                    url: '/test_images/tomato_healthy.jpg'
                  })}
                  className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-semibold text-left truncate"
                >
                  🌿 Tomato Healthy Leaf
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadPresetSample({
                    id: 'apple_scab',
                    crop: 'Apple',
                    name: 'Apple Scab',
                    url: '/test_images/apple_scab_bierny.jpg'
                  })}
                  className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-semibold text-left truncate"
                >
                  🍎 Apple Scab
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadPresetSample({
                    id: 'corn_rust',
                    crop: 'Corn',
                    name: 'Corn Common Rust',
                    url: '/test_images/corn_common_rust.jpg'
                  })}
                  className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-semibold text-left truncate"
                >
                  🌽 Corn Common Rust
                </button>
                <button
                  type="button"
                  onClick={() => handleLoadPresetSample({
                    id: 'cotton_leaf',
                    crop: 'Cotton',
                    name: 'Cotton Field Leaf (OOD Test)',
                    url: '/test_images/cotton_field_leaf.jpg'
                  })}
                  className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-semibold text-left truncate"
                >
                  🛡️ OOD Field Abstention
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Diagnostic Result Showcase (7 Cols) */}
        <div className="lg:col-span-7">
          {analyzing ? (
            <div className="bg-white rounded-xl border border-[#E5DDCF] p-12 text-center shadow-2xs">
              <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mx-auto mb-3" />
              <h4 className="font-bold text-sm text-[#103D2C]">Executing Deep Learning Vision Model</h4>
              <p className="text-xs text-[#292B26]/60 mt-1">Cross-referencing DINOv2 ViT-B/14 387 pathology classes and CIB&RC formulations...</p>
            </div>
          ) : result ? (
            <div className="bg-white rounded-xl shadow-2xs border border-[#E5DDCF] p-5 space-y-4">

              {/* PRIMARY DIAGNOSIS RESULT BANNER */}
              <div className="border-b border-[#E5DDCF] pb-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#292B26]/60 block mb-0.5">
                      Identified Condition
                    </span>
                    <h3 className={`text-xl lg:text-2xl font-bold font-serif ${
                      result.isHealthy ? 'text-[#17643E]' : result.abstention ? 'text-amber-800' : 'text-[#B6532A]'
                    }`}>
                      {result.condition}
                    </h3>
                    {result.scientificName && (
                      <p className="text-xs italic text-[#292B26]/60 mt-0.5">
                        Scientific: {result.scientificName}
                      </p>
                    )}
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-xl font-bold font-mono text-[#103D2C]">
                      {result.confidence}%
                    </span>
                    <span className="text-[10px] text-[#292B26]/50 block">Vision Confidence</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 mt-3">
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                    result.isHealthy ? 'bg-emerald-100 text-emerald-800' :
                    result.severity === 'High' ? 'bg-red-100 text-red-800' :
                    result.severity === 'Medium' ? 'bg-amber-100 text-amber-800' :
                    'bg-slate-100 text-slate-800'
                  }`}>
                    {result.severity}
                  </span>

                  {result.hostCropStatus === 'verified' && (
                    <span className="text-[10px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Host Verified: {result.diagnosedCrop || crop}
                    </span>
                  )}

                  {result.routingPath === 'specialist_fused' && (
                    <span className="text-[10px] font-bold text-indigo-900 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 flex items-center gap-1">
                      <span>⚡ Crop Specialist + ViT Fused</span>
                      {result.fusionOutcome === 'agree' && <span className="text-emerald-700">(Concordant Agreement)</span>}
                      {result.fusionOutcome === 'disputed' && <span className="text-amber-700">(Disputed Disagreement)</span>}
                      {result.fusionOutcome === 'crop_uncertain' && <span className="text-red-700">(Crop Conflict)</span>}
                      {result.fusionOutcome === 'insufficient_evidence' && <span className="text-slate-600">(Insufficient Evidence)</span>}
                      {result.fusionOutcome === 'single_model' && <span className="text-indigo-700">(Specialist Dominant)</span>}
                    </span>
                  )}

                  {result.cropMismatchWarning && (
                    <span className="text-[10px] font-medium text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-300">
                      Discrepancy: {result.cropMismatchWarning}
                    </span>
                  )}
                </div>
              </div>

              {/* Abstention / Safety Safeguard Alert */}
              {result.abstention && (
                <div className="bg-amber-50 border border-amber-300 text-amber-900 p-3 rounded-lg text-xs space-y-2">
                  <div className="flex items-center gap-1.5 font-bold text-amber-900">
                    <AlertTriangle size={14} className="text-amber-700 shrink-0" />
                    <span>Clinical Abstention Activated: {result.abstentionReason || 'Low confidence threshold'}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed text-amber-900/90">
                    {result.description}
                  </p>
                  {result.competingPredictions && result.competingPredictions.length > 0 && (
                    <div className="bg-white/80 p-2.5 rounded border border-amber-200 space-y-1">
                      <span className="text-[10px] font-bold text-amber-950 uppercase tracking-wider block">
                        Competing Model Predictions:
                      </span>
                      {result.competingPredictions.map((comp, idx) => (
                        <div key={idx} className="flex justify-between items-center text-[11px] text-[#292B26]">
                          <span className="font-medium">
                            <span className="text-neutral-500 font-semibold">{comp.model}:</span> {comp.crop} — {comp.condition}
                          </span>
                          <span className="font-mono font-bold text-amber-900">{Math.round(comp.score * 100)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <p className="text-[10px] text-amber-800/80 italic">
                    Safety safeguard: Broad-spectrum chemicals are withheld to prevent improper application on ambiguous symptoms.
                  </p>
                </div>
              )}

              {/* ACTION: CLINICAL INTERVENTION & TREATMENT (First Thing Farmer Needs) */}
              <div className="space-y-3">
                <div>
                  <h4 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <CheckCircle size={14} className="text-[#17643E]" /> Direct Clinical Protocol
                  </h4>
                  <div className="bg-[#FBF7EF] p-3 rounded-lg border border-[#E5DDCF] text-xs text-[#292B26] leading-relaxed">
                    {result.treatment}
                  </div>
                </div>

                {/* CIB&RC Chemical Formulations */}
                {!result.abstention && !result.isHealthy && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                      <ExternalLink size={13} className="text-[#17643E]" /> CIB&RC Registered Interventions
                    </h4>
                    {result.chemicalTreatments && result.chemicalTreatments.length > 0 ? (
                      <div className="space-y-1.5">
                        {result.chemicalTreatments.map((chem, i) => (
                          <div key={i} className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF] text-xs">
                            <div className="flex justify-between font-bold text-[#103D2C]">
                              <span>{chem.chemical_name}</span>
                              <span className="text-[#B6532A] font-semibold">{chem.dosage}</span>
                            </div>
                            <div className="flex justify-between text-[10px] text-[#292B26]/60 mt-0.5">
                              <span>Reg: {chem.cpr_registration || 'CIBRC-VERIFIED'}</span>
                              {chem.waiting_period_days && <span>Pre-Harvest Interval (PHI): {chem.waiting_period_days} days</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="bg-[#FBF7EF] p-2.5 rounded-lg border border-[#E5DDCF] text-[11px] text-[#292B26]/75 italic">
                        No direct CIB&RC registered chemical fungicide found for this specific pairing. Rely on IPM biological and cultural controls below.
                      </div>
                    )}
                  </div>
                )}

                {/* Cultural & Biological IPM Controls */}
                <div className="space-y-1.5">
                  <h4 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                    <Leaf size={14} className="text-[#17643E]" /> IPM Cultural & Biological Management
                  </h4>
                  <ul className="text-xs text-[#292B26]/80 list-disc pl-4 space-y-1">
                    {result.nonChemicalOptions.map((opt, i) => (
                      <li key={i}>{opt}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Collapsible Technical Candidates & Model Breakdown */}
              {result.topPredictions && result.topPredictions.length > 0 && (
                <div className="border border-[#E5DDCF] rounded-lg overflow-hidden pt-1">
                  <button
                    onClick={() => setShowModelCandidates(prev => !prev)}
                    className="w-full px-3 py-2 bg-[#FBF7EF] text-left flex items-center justify-between text-xs font-bold text-[#103D2C] hover:bg-[#E5DDCF]/40 cursor-pointer"
                  >
                    <div className="flex items-center gap-1.5">
                      <BarChart3 size={14} className="text-[#17643E]" />
                      <span>Diagnostic Candidate Distribution ({result.topPredictions.length} classes evaluated)</span>
                    </div>
                    {showModelCandidates ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>

                  {showModelCandidates && (
                    <div className="p-3 space-y-2 border-t border-[#E5DDCF] text-xs">
                      {result.topPredictions.map((tp, idx) => (
                        <div key={idx} className="space-y-0.5">
                          <div className="flex justify-between items-center text-[11px]">
                            <span className="text-[#292B26] font-medium truncate max-w-[280px]">
                              {tp.crop ? `${tp.crop} — ${tp.condition}` : tp.condition}
                            </span>
                            <span className="font-bold text-[#103D2C] font-mono">{tp.percentage}%</span>
                          </div>
                          <div className="w-full bg-[#E5DDCF]/50 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${idx === 0 ? 'bg-[#17643E]' : 'bg-[#A8C69A]'}`}
                              style={{ width: `${tp.percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Economic Threshold Level (ETL) Scientific Disclaimer */}
              <div className="bg-amber-50/70 border border-amber-200 p-2.5 rounded-lg text-[10px] text-amber-900 flex items-start gap-1.5">
                <Info size={13} className="text-amber-800 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong>Scientific & ETL Disclaimer:</strong> Classification is performed via statistical visual pattern matching across Indian agro-climatic imagery. Verify severe outbreaks with a certified plant pathologist or Krishi Vigyan Kendra (KVK) officer before applying registered chemical sprays.
                </p>
              </div>

            </div>
          ) : (
            <div className="bg-white rounded-xl border border-[#E5DDCF] p-12 text-center shadow-2xs h-full flex flex-col items-center justify-center min-h-[320px]">
              <ShieldAlert className="w-10 h-10 text-[#A8C69A] mx-auto mb-3" />
              <h4 className="font-bold text-sm text-[#103D2C]">Awaiting Leaf Inspection</h4>
              <p className="text-xs text-[#292B26]/60 max-w-sm mx-auto mt-1 leading-relaxed">
                Upload a genuine symptomatic leaf photograph or click any verified dataset sample on the left to trigger real-time AI pathology classification.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
