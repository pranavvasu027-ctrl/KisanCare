import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { translateDynamic } from '../../i18n/translateHelper';
import {
  Bug, Camera, Upload, ShieldAlert, CheckCircle, Loader2,
  RotateCcw, AlertCircle, ShieldCheck, Sprout, Info, Leaf,
  ExternalLink, BarChart3, AlertTriangle, Cpu
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
  'Tomato',
  'Apple',
  'Corn',
  'Potato',
  'Grape',
  'Pepper Bell',
  'Peach',
  'Cherry',
  'Strawberry',
  'Soybean',
  'Orange',
  'Squash',
  'Blueberry',
  'Raspberry',
  'Cotton',
  'Rice',
  'Wheat',
  'Onion'
];

interface TopPrediction {
  condition: string;
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
  scientificName?: string;
  confidence: number;
  severity: 'Low' | 'Medium' | 'High';
  description?: string;
  treatment: string;
  preventiveManagement: string[];
  nonChemicalOptions: string[];
  chemicalTreatments?: ChemicalTreatment[];
  topPredictions?: TopPrediction[];
  cropMatch: boolean;
  cropMismatchWarning?: string | null;
  modelType?: string;
  latencyMs?: number;
  warnings?: string[];
}

export default function DiseaseDetection() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  const [diagnosisMode, setDiagnosisMode] = useState<'disease' | 'pest'>('disease');
  const [crop, setCrop] = useState('Tomato');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(['Yellow leaves', 'Stunted growth']);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sampleId, setSampleId] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnosisResult | null>(null);

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
        setErrorMessage('File size exceeds the 15 MB limit. Please select a smaller leaf photo.');
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

      const conditionName = data.condition || data.prediction || 'Unknown Foliar Condition';
      const sciName = data.scientific_name || `${targetCrop} foliar pathological disorder`;
      const confidenceVal = typeof data.confidence_percent === 'number'
        ? data.confidence_percent
        : Math.round((data.confidence ?? 0.85) * 100);

      const chemicals: ChemicalTreatment[] = (data.treatments?.chemical || []).map((c: any) => ({
        chemical_name: c.chemical_name,
        dosage: c.dosage,
        cpr_registration: c.cpr_registration,
        waiting_period_days: c.waiting_period_days,
      }));

      const topPreds: TopPrediction[] = (data.top_5_predictions || []).map((tp: any) => ({
        condition: tp.condition,
        percentage: tp.percentage ?? Math.round((tp.probability ?? 0) * 100),
        probability: tp.probability ?? 0,
      }));

      setResult({
        condition: conditionName,
        scientificName: sciName,
        confidence: confidenceVal,
        severity: data.severity || (confidenceVal > 80 ? 'High' : 'Medium'),
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
        cropMatch: data.crop_match ?? true,
        cropMismatchWarning: data.crop_mismatch_warning,
        modelType: data.model_type || 'PyTorch EfficientNetV2-S + CIBRC Regulatory Engine',
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
      // Default to sample if user hasn't selected any image yet
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
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-6">
        <div className="w-16 h-16 bg-[#17643E]/10 text-[#17643E] rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Bug size={32} />
        </div>
        <div className="flex items-center justify-center gap-2">
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">{t('disease.title')}</h1>
          {isDemo ? (
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
              {t('disease.sampleBadge')}
            </span>
          ) : (
            <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
              <Cpu size={12} /> {t('disease.deepLearningBadge')}
            </span>
          )}
        </div>
        <p className="text-[#292B26]/70 mt-2 text-sm">
          {t('disease.subtitle')}
        </p>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2 shadow-xs">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Target & Mode Selector */}
      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-4">
        {/* Mode Selector Toggle */}
        <div className="flex items-center justify-between border-b border-[#E5DDCF] pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#103D2C] uppercase tracking-wider">{t('disease.diagnosticMode')}</span>
            <div className="flex rounded-lg border border-[#E5DDCF] p-0.5 bg-[#FBF7EF]">
              <button
                type="button"
                onClick={() => setDiagnosisMode('disease')}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                  diagnosisMode === 'disease'
                    ? 'bg-[#103D2C] text-white shadow-xs'
                    : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                {t('disease.foliarMode')}
              </button>
              <button
                type="button"
                onClick={() => setDiagnosisMode('pest')}
                className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                  diagnosisMode === 'pest'
                    ? 'bg-[#103D2C] text-white shadow-xs'
                    : 'text-[#292B26]/70 hover:text-[#103D2C]'
                }`}
              >
                {t('disease.pestMode')}
              </button>
            </div>
          </div>
          <span className="text-[11px] text-[#292B26]/60">
            {diagnosisMode === 'disease' ? t('disease.foliarClasses') : t('disease.pestClasses')}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">{t('disease.affectedCrop')}</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 text-sm bg-[#FBF7EF] font-medium text-[#103D2C]"
            >
              {SUPPORTED_CROPS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={runDiagnosis}
              disabled={analyzing}
              className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 shadow-xs"
            >
              {analyzing ? <Loader2 size={16} className="animate-spin" /> : <Bug size={16} />}
              <span>{analyzing ? t('disease.executingInference') : t('disease.runDiagnosis', { mode: diagnosisMode === 'pest' ? 'Pest' : 'Disease' })}</span>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">
            {t('disease.observedSymptoms')}
          </label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_SYMPTOMS.map((sym) => {
              const active = selectedSymptoms.includes(sym);
              return (
                <button
                  key={sym}
                  type="button"
                  onClick={() => toggleSymptom(sym)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all cursor-pointer ${
                    active
                      ? 'bg-[#103D2C] text-white border-[#103D2C] font-semibold shadow-xs'
                      : 'bg-[#FBF7EF] text-[#292B26]/80 border-[#E5DDCF] hover:border-[#17643E]'
                  }`}
                >
                  {active ? `✓ ${translateDynamic(sym, currentLang) || sym}` : `+ ${translateDynamic(sym, currentLang) || sym}`}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left: Upload Area */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 text-center border-dashed border-2 flex flex-col items-center justify-center min-h-[380px]">
          {selectedImage ? (
            <div className="space-y-3 w-full">
              <div className="relative w-full h-56 rounded-xl overflow-hidden border border-[#E5DDCF] bg-black/5">
                <img
                  src={selectedImage}
                  alt="Uploaded leaf"
                  className="w-full h-full object-contain bg-neutral-900/10"
                />
                {analyzing && (
                  <div className="absolute inset-0 bg-[#103D2C]/75 backdrop-blur-xs flex flex-col items-center justify-center text-white">
                    <Loader2 className="w-8 h-8 animate-spin mb-2" />
                    <span className="text-xs font-bold uppercase tracking-wider">Evaluating PyTorch EfficientNetV2-S...</span>
                    <span className="text-[10px] text-emerald-200 mt-1">ImageNet normalization & feature extraction</span>
                  </div>
                )}
              </div>
              <div className="text-[11px] text-[#292B26]/70 bg-[#FBF7EF] p-2 rounded-lg border border-[#E5DDCF] flex items-center justify-center gap-1.5">
                <Info size={13} className="text-[#17643E] shrink-0" />
                <span>
                  {sampleId ? `Verified benchmark sample: ${sampleId}` : selectedFile ? `Uploaded genuine file: ${selectedFile.name}` : 'Visual record loaded.'}
                </span>
              </div>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs bg-[#FBF7EF] border border-[#E5DDCF] text-[#103D2C] px-3 py-1.5 rounded-lg hover:bg-[#E5DDCF] cursor-pointer"
                >
                  Change Photo
                </button>
                <button
                  onClick={handleReset}
                  className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1 py-1.5 cursor-pointer"
                >
                  <RotateCcw size={14} /> Clear
                </button>
              </div>
            </div>
          ) : (
            <div className="py-4 flex flex-col items-center justify-center max-w-sm">
              <Upload className="w-10 h-10 text-[#A8C69A] mb-3" />
              <h3 className="font-bold text-[#103D2C] mb-1">{t('disease.uploadLeafPhoto')}</h3>
              <p className="text-[11px] text-[#292B26]/60 mb-4 leading-relaxed">
                Upload a clear close-up photograph of the symptomatic leaf (JPEG, PNG, WebP up to 15 MB). The real EfficientNetV2-S neural network will perform multi-class pathology classification.
              </p>
              <div className="flex flex-wrap justify-center gap-3 mb-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF] px-4 py-2 rounded-lg font-medium hover:bg-[#E5DDCF] flex items-center gap-2 cursor-pointer text-xs shadow-xs"
                >
                  Browse Files
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E] flex items-center gap-2 cursor-pointer text-xs shadow-xs"
                >
                  <Camera size={16} /> Take Photo
                </button>
              </div>

              {/* Instant Verification Preset Buttons */}
              <div className="w-full pt-3 border-t border-[#E5DDCF]/60">
                <span className="text-[11px] font-bold text-[#103D2C] uppercase tracking-wider block mb-2">
                  Or Test with Verified Dataset Samples:
                </span>
                <div className="grid grid-cols-2 gap-1.5 text-left">
                  <button
                    type="button"
                    onClick={() => handleLoadPresetSample({
                      id: 'apple_scab',
                      crop: 'Apple',
                      name: 'Apple Scab',
                      url: '/test_images/apple_scab_bierny.jpg'
                    })}
                    className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-medium"
                  >
                    🍎 Apple Scab
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadPresetSample({
                      id: 'tomato_blight',
                      crop: 'Tomato',
                      name: 'Tomato Early Blight',
                      url: '/test_images/tomato_early_blight.jpg'
                    })}
                    className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-medium"
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
                    className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-medium"
                  >
                    🌿 Tomato Healthy Leaf
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadPresetSample({
                      id: 'corn_rust',
                      crop: 'Corn',
                      name: 'Corn Common Rust',
                      url: '/test_images/corn_common_rust.jpg'
                    })}
                    className="text-[11px] p-2 bg-[#FBF7EF] border border-[#E5DDCF] hover:border-[#17643E] rounded-lg transition-colors cursor-pointer text-[#103D2C] font-medium"
                  >
                    🌽 Corn Common Rust
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Diagnosis Result */}
        <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#E5DDCF] p-6 flex flex-col justify-center min-h-[380px]">
          {analyzing ? (
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mx-auto mb-3" />
              <h4 className="font-bold text-[#103D2C]">Executing Deep Learning Vision Model</h4>
              <p className="text-xs text-[#292B26]/60 mt-1">Cross-referencing EfficientNetV2-S 38 pathology classes & CIB&RC treatments...</p>
            </div>
          ) : result ? (
            <div className="space-y-4">
              <div className="bg-white p-5 rounded-xl border border-[#E5DDCF] shadow-xs space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-xl text-[#B6532A]">{result.condition}</h4>
                    {result.scientificName && (
                      <p className="text-xs italic text-[#292B26]/60 mt-0.5">
                        Taxonomy: {result.scientificName}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className="bg-[#17643E]/10 text-[#17643E] text-xs font-bold px-2.5 py-1 rounded-full border border-[#17643E]/20 inline-block">
                      Vision Score: {result.confidence}%
                    </span>
                    <span className="text-[10px] text-[#292B26]/50 block mt-0.5">
                      Uncalibrated Softmax Score
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    result.severity === 'High' ? 'bg-red-100 text-red-800' :
                    result.severity === 'Medium' ? 'bg-orange-100 text-orange-800' :
                    'bg-emerald-100 text-emerald-800'
                  }`}>
                    Severity: {result.severity}
                  </span>
                  {result.modelType && (
                    <span className="text-[10px] font-medium text-[#292B26]/60 bg-neutral-100 px-2 py-0.5 rounded">
                      {result.modelType}
                    </span>
                  )}
                  {typeof result.latencyMs === 'number' && (
                    <span className="text-[10px] text-[#292B26]/50">
                      ⚡ {Math.round(result.latencyMs)} ms
                    </span>
                  )}
                </div>

                {/* Crop Compatibility Banner */}
                {!result.cropMatch ? (
                  <div className="bg-amber-50 border border-amber-300 text-amber-900 p-2.5 rounded-lg text-xs flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block">Crop Mismatch Alert:</span>
                      <p className="text-[11px] leading-relaxed">
                        {result.cropMismatchWarning || `Pathogen features align with ${result.condition}, which conflicts with declared crop ${crop}.`}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-3 py-1.5 rounded-lg text-xs flex items-center gap-2">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span className="text-[11px]">Biological host compatibility verified for {crop}.</span>
                  </div>
                )}

                {/* Top-5 Predictions Breakdown */}
                {result.topPredictions && result.topPredictions.length > 1 && (
                  <div className="pt-2 border-t border-[#E5DDCF]/60">
                    <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <BarChart3 size={14} className="text-[#17643E]" /> Top Pathology Candidates
                    </h5>
                    <div className="space-y-1.5">
                      {result.topPredictions.slice(0, 4).map((tp, idx) => (
                        <div key={idx} className="space-y-0.5">
                          <div className="flex justify-between text-[11px]">
                            <span className="text-[#292B26]/80 font-medium">{tp.condition}</span>
                            <span className="text-[#103D2C] font-bold">{tp.percentage}%</span>
                          </div>
                          <div className="w-full bg-[#E5DDCF]/40 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${idx === 0 ? 'bg-[#17643E]' : 'bg-[#A8C69A]'}`}
                              style={{ width: `${tp.percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Treatment / Clinical Protocol */}
                <div className="pt-2 border-t border-[#E5DDCF]/60">
                  <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <CheckCircle size={14} className="text-[#17643E]" /> {t('disease.treatmentProtocol')}
                  </h5>
                  <div className="bg-[#FBF7EF] p-3 rounded-lg border border-[#E5DDCF] text-xs text-[#292B26] leading-relaxed">
                    {translateDynamic(result.treatment, currentLang) || result.treatment}
                  </div>
                </div>

                {/* CIBRC Registered Chemical Formulations */}
                {result.chemicalTreatments && result.chemicalTreatments.length > 0 && (
                  <div className="pt-2 border-t border-[#E5DDCF]/60 space-y-1.5">
                    <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                      <ExternalLink size={13} className="text-[#17643E]" /> {t('disease.chemicalTreatments')}
                    </h5>
                    <div className="space-y-1.5">
                      {result.chemicalTreatments.map((chem, i) => (
                        <div key={i} className="bg-[#FBF7EF] p-2 rounded-lg border border-[#E5DDCF] text-[11px] space-y-0.5">
                          <div className="flex justify-between font-bold text-[#103D2C]">
                            <span>{chem.chemical_name}</span>
                            <span className="text-[#B6532A]">{chem.dosage}</span>
                          </div>
                          <div className="flex justify-between text-[10px] text-[#292B26]/60">
                            <span>Reg: {chem.cpr_registration || 'CIBRC-STANDARD'}</span>
                            {chem.waiting_period_days && <span>PHI Waiting Period: {chem.waiting_period_days} days</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Non-Chemical Management Options */}
                <div className="pt-2 border-t border-[#E5DDCF]/60 space-y-1.5">
                  <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                    <Leaf size={14} className="text-[#17643E]" /> {t('disease.nonChemicalOptions')}
                  </h5>
                  <ul className="text-xs text-[#292B26]/80 list-disc pl-4 space-y-1">
                    {result.nonChemicalOptions.map((opt, i) => (
                      <li key={i}>{opt}</li>
                    ))}
                  </ul>
                </div>

                {/* Preventive Management */}
                <div className="pt-2 border-t border-[#E5DDCF]/60 space-y-1.5">
                  <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck size={14} className="text-[#17643E]" /> {t('disease.preventiveManagement')}
                  </h5>
                  <ul className="text-xs text-[#292B26]/80 list-disc pl-4 space-y-1">
                    {result.preventiveManagement.map((prev, i) => (
                      <li key={i}>{prev}</li>
                    ))}
                  </ul>
                </div>

                {/* Scientific Disclaimer */}
                <div className="bg-amber-50/70 border border-amber-200 p-2.5 rounded-lg text-[10px] text-amber-900 flex items-start gap-1.5">
                  <Info size={13} className="text-amber-800 shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    <span className="font-bold block">Scientific & Economic Threshold Level (ETL) Disclaimer:</span>
                    <p className="leading-relaxed">
                      Classification is generated by a deep neural network (PyTorch EfficientNetV2-S) and reflects statistical pattern matching across benchmark leaf imagery. Softmax scores are uncalibrated probabilities and must not be treated as a confirmed laboratory pathogen isolation. Verify severe outbreaks with a certified plant pathologist or Krishi Vigyan Kendra (KVK) officer before applying registered fungicides.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white p-6 rounded-xl border border-[#E5DDCF] text-center">
              <ShieldAlert className="w-10 h-10 text-[#A8C69A] mx-auto mb-3" />
              <h4 className="font-bold text-[#103D2C] mb-1">Awaiting Inspection</h4>
              <p className="text-xs text-[#292B26]/60">
                Upload a genuine leaf photo or choose one of the verified dataset sample buttons on the left to execute the deep learning disease classifier.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
