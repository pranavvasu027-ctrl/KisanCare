import React, { useState, useRef } from 'react';
import {
  Camera, Upload, CheckCircle2, AlertTriangle,
  HelpCircle, RefreshCw, X, Loader2, ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';

type CropOption = 'Cotton' | 'Soybean';

interface FarmerGuidance {
  status: 'healthy' | 'disease_detected' | 'unable_to_determine';
  status_label: string;
  disease_name: string;
  confidence_percent: number | null;
  confidence_display: string;
  recommended_steps: string[];
  crop: CropOption;
  is_healthy: boolean;
  is_abstaining: boolean;
}

const VALID_COTTON_CLASSES = new Set([
  'Bacterial Blight',
  'Cotton Leaf Curl Virus',
  'Fusarium Wilt',
  'Healthy Foliage',
]);

const VALID_SOYBEAN_CLASSES = new Set([
  'Downy Mildew',
  'Frogeye Leaf Spot',
  'Healthy Foliage',
  'Soybean Mosaic Virus',
  'Asian Soybean Rust',
  'Brown Spot (Septoria)',
]);

export default function DiseaseDetection() {
  // Input 1: Crop Selection (Cotton or Soybean only)
  const [selectedCrop, setSelectedCrop] = useState<CropOption>('Cotton');

  // Input 2: Leaf Photo
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Diagnosis State
  const [analyzing, setAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [diagnosis, setDiagnosis] = useState<FarmerGuidance | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelected = (file: File) => {
    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage('The photo size is too large (over 15MB). Please upload a smaller photo.');
      return;
    }
    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    setErrorMessage(null);
    setDiagnosis(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelected(file);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setDiagnosis(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const runDiagnosis = async () => {
    if (!selectedFile) {
      setErrorMessage('Please take or upload a leaf photo first.');
      return;
    }

    setErrorMessage(null);
    setAnalyzing(true);
    setDiagnosis(null);

    try {
      const response = await api.detectDisease(selectedCrop, [], {
        file: selectedFile,
        locationState: 'Maharashtra',
        growthStage: 'vegetative',
        imageType: 'leaf',
      });

      // Defensively extract data payload regardless of response wrapping
      const raw = response?.data;
      const data = (raw && raw.farmer_guidance)
        ? raw
        : (raw && raw.data && raw.data.farmer_guidance)
          ? raw.data
          : (raw?.data || raw || {});

      const validClasses = selectedCrop === 'Cotton' ? VALID_COTTON_CLASSES : VALID_SOYBEAN_CLASSES;

      if (data.farmer_guidance) {
        const fg = data.farmer_guidance;
        const isRecognized = validClasses.has(fg.disease_name);

        if (fg.is_abstaining || !isRecognized) {
          setDiagnosis({
            status: 'unable_to_determine',
            status_label: 'Unable to Determine Reliably',
            disease_name: 'Unable to identify the disease reliably. Please upload a clearer leaf photo.',
            confidence_percent: null,
            confidence_display: 'Confidence too low for safe identification',
            recommended_steps: [
              'Take a close-up photo in good natural daylight, focusing on the leaf lesion or discolored area.',
              'Avoid blurry photos, distant foliage, or strong shadow/glare in the frame.',
              'Strictly avoid applying chemical pesticides or fungicides without a verified diagnosis.',
              'If symptoms are spreading, take a fresh leaf sample to your nearest Krishi Vigyan Kendra (KVK) or State Agricultural Extension Officer.',
            ],
            crop: selectedCrop,
            is_healthy: false,
            is_abstaining: true,
          });
        } else {
          setDiagnosis(fg);
        }
      } else {
        // Fallback parser if API returned legacy format
        const rawCondition = typeof data.condition === 'string' ? data.condition.trim() : '';
        const isValidClass = validClasses.has(rawCondition);
        const isHealthy = isValidClass && (rawCondition === 'Healthy Foliage' || data.is_healthy);
        const isAbstain = data.abstention || !isValidClass || !rawCondition;
        const confVal = typeof data.confidence_percent === 'number' ? data.confidence_percent : null;

        if (isAbstain || !isValidClass || confVal === null || confVal < 45) {
          setDiagnosis({
            status: 'unable_to_determine',
            status_label: 'Unable to Determine Reliably',
            disease_name: 'Unable to identify the disease reliably. Please upload a clearer leaf photo.',
            confidence_percent: null,
            confidence_display: 'Confidence too low for safe identification',
            recommended_steps: [
              'Take a close-up photo in good natural daylight, focusing on the leaf lesion or discolored area.',
              'Avoid blurry photos, distant foliage, or strong shadow/glare in the frame.',
              'Strictly avoid applying chemical pesticides or fungicides without a verified diagnosis.',
              'If symptoms are spreading, take a fresh leaf sample to your nearest Krishi Vigyan Kendra (KVK) or State Agricultural Extension Officer.',
            ],
            crop: selectedCrop,
            is_healthy: false,
            is_abstaining: true,
          });
        } else {
          setDiagnosis({
            status: isHealthy ? 'healthy' : 'disease_detected',
            status_label: isHealthy ? 'Healthy Leaf' : 'Likely Disease Detected',
            disease_name: rawCondition,
            confidence_percent: confVal,
            confidence_display: `${confVal}% (Model confidence score)`,
            recommended_steps: data.preventive_management || [
              'Maintain field sanitation and proper spacing.',
              'Consult your local Krishi Vigyan Kendra (KVK) or extension officer with a physical leaf sample.',
            ],
            crop: selectedCrop,
            is_healthy: isHealthy,
            is_abstaining: false,
          });
        }
      }
    } catch (err: any) {
      console.error('Diagnosis request failed:', err);
      setErrorMessage(err.message || 'Diagnosis failed. Please check your photo and try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FBF7EF] py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-xl mx-auto space-y-6">

        {/* Simple Farmer-Friendly Header */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C]">
            Crop Disease Detection
          </h1>
          <p className="text-sm text-[#292B26]/75 max-w-md mx-auto">
            Choose your crop and upload a leaf photo to check for diseases and get safe guidance.
          </p>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div className="bg-red-50 border border-red-300 text-red-900 p-4 rounded-xl text-sm flex items-start gap-3 shadow-sm">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold block">Notice</span>
              <p>{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Main Simple Farmer Form Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 sm:p-6 space-y-6">

          {/* INPUT 1: SELECT CROP */}
          <div>
            <label className="block text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">
              Step 1: Select Your Crop
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => { setSelectedCrop('Cotton'); setDiagnosis(null); }}
                className={`py-3.5 px-4 rounded-xl border text-center transition-all cursor-pointer font-bold text-base flex flex-col items-center gap-1 ${
                  selectedCrop === 'Cotton'
                    ? 'border-[#103D2C] bg-[#103D2C] text-white shadow-sm ring-2 ring-[#103D2C]/20'
                    : 'border-[#E5DDCF] bg-[#FBF7EF] text-[#103D2C] hover:border-[#103D2C]'
                }`}
              >
                <span className="text-2xl">☁️</span>
                <span>Cotton</span>
              </button>

              <button
                type="button"
                onClick={() => { setSelectedCrop('Soybean'); setDiagnosis(null); }}
                className={`py-3.5 px-4 rounded-xl border text-center transition-all cursor-pointer font-bold text-base flex flex-col items-center gap-1 ${
                  selectedCrop === 'Soybean'
                    ? 'border-[#103D2C] bg-[#103D2C] text-white shadow-sm ring-2 ring-[#103D2C]/20'
                    : 'border-[#E5DDCF] bg-[#FBF7EF] text-[#103D2C] hover:border-[#103D2C]'
                }`}
              >
                <span className="text-2xl">🌱</span>
                <span>Soybean</span>
              </button>
            </div>
          </div>

          {/* INPUT 2: UPLOAD LEAF PHOTO */}
          <div>
            <label className="block text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">
              Step 2: Upload Leaf Photo
            </label>

            {/* Hidden File and Camera Inputs */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleInputChange}
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
            />
            <input
              type="file"
              ref={cameraInputRef}
              onChange={handleInputChange}
              accept="image/*"
              capture="environment"
              className="hidden"
            />

            {!previewUrl ? (
              <div className="border-2 border-dashed border-[#E5DDCF] hover:border-[#103D2C] rounded-2xl p-6 text-center bg-[#FBF7EF]/50 transition-colors">
                <div className="w-12 h-12 bg-[#103D2C]/10 text-[#103D2C] rounded-full flex items-center justify-center mx-auto mb-3">
                  <Camera className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-[#103D2C] text-base mb-1">
                  Add Leaf Photo
                </h3>
                <p className="text-xs text-[#292B26]/60 mb-4">
                  Take a clear, close-up photo of the affected leaf in good light.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    className="w-full sm:w-auto px-5 py-2.5 bg-[#103D2C] hover:bg-[#17643E] text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-2 cursor-pointer shadow-sm transition-colors"
                  >
                    <Camera size={16} /> Take Photo
                  </button>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full sm:w-auto px-5 py-2.5 bg-white border border-[#E5DDCF] hover:bg-[#FBF7EF] text-[#103D2C] text-sm font-semibold rounded-xl flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-2xs"
                  >
                    <Upload size={16} /> Choose from Gallery
                  </button>
                </div>
              </div>
            ) : (
              /* Photo Preview with Replace Option */
              <div className="space-y-3">
                <div className="relative rounded-xl overflow-hidden border border-[#E5DDCF] bg-black/5 h-64 flex items-center justify-center">
                  <img
                    src={previewUrl}
                    alt="Selected leaf preview"
                    className="max-h-full max-w-full object-contain"
                  />
                  {analyzing && (
                    <div className="absolute inset-0 bg-[#103D2C]/80 backdrop-blur-xs flex flex-col items-center justify-center text-white p-4 text-center">
                      <Loader2 className="w-8 h-8 animate-spin mb-2 text-[#A8C69A]" />
                      <span className="font-bold text-sm">Analyzing {selectedCrop} Leaf...</span>
                      <span className="text-xs text-emerald-200 mt-1">Checking for signs of foliar disease</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-[#292B26]/70 truncate max-w-[200px]">
                    Photo ready: {selectedFile?.name || 'Leaf Image'}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-3 py-1.5 bg-[#FBF7EF] border border-[#E5DDCF] text-[#103D2C] rounded-lg font-medium hover:bg-[#E5DDCF] cursor-pointer"
                    >
                      Replace Photo
                    </button>
                    <button
                      type="button"
                      onClick={handleReset}
                      className="p-1.5 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg cursor-pointer"
                      title="Remove photo"
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ONE PROMINENT DETECT DISEASE BUTTON */}
          <button
            type="button"
            onClick={runDiagnosis}
            disabled={analyzing || !selectedFile}
            className={`w-full py-3.5 px-6 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md ${
              analyzing || !selectedFile
                ? 'bg-[#103D2C]/40 text-white cursor-not-allowed'
                : 'bg-[#103D2C] hover:bg-[#17643E] text-white hover:shadow-lg active:scale-[0.99]'
            }`}
          >
            {analyzing ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                <span>Analyzing Leaf...</span>
              </>
            ) : (
              <>
                <span>Detect Disease</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>

        {/* RESULTS SECTION DIRECTLY ON THE SAME PAGE */}
        {diagnosis && (
          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 sm:p-6 space-y-5 animate-in fade-in duration-200">

            {/* 1. Status Banner */}
            <div className={`p-4 rounded-xl flex items-start gap-3 border ${
              diagnosis.status === 'healthy'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                : diagnosis.status === 'unable_to_determine'
                ? 'bg-amber-50 border-amber-200 text-amber-950'
                : 'bg-orange-50 border-orange-200 text-orange-950'
            }`}>
              {diagnosis.status === 'healthy' ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
              ) : diagnosis.status === 'unable_to_determine' ? (
                <HelpCircle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-orange-600 shrink-0 mt-0.5" />
              )}
              <div>
                <span className="text-xs font-bold uppercase tracking-wider block opacity-75">
                  Diagnosis Result
                </span>
                <span className="text-lg font-bold block">
                  {diagnosis.status_label}
                </span>
              </div>
            </div>

            {/* 2. Disease Name & Confidence */}
            <div className="space-y-2 border-b border-[#E5DDCF] pb-4">
              <div>
                <span className="text-xs font-bold text-[#103D2C] uppercase tracking-wider block">
                  Condition:
                </span>
                <h3 className={`text-xl font-bold mt-0.5 ${
                  diagnosis.status === 'healthy'
                    ? 'text-emerald-700'
                    : diagnosis.status === 'unable_to_determine'
                    ? 'text-[#292B26]/80 text-base font-normal'
                    : 'text-[#B6532A]'
                }`}>
                  {diagnosis.disease_name}
                </h3>
              </div>

              {/* Confidence: Show only when meaningful and appropriately calibrated */}
              <div>
                <span className="text-xs font-bold text-[#103D2C] uppercase tracking-wider block">
                  Confidence:
                </span>
                <p className="text-sm font-medium text-[#292B26]/80 mt-0.5">
                  {diagnosis.confidence_display}
                </p>
                {diagnosis.status !== 'unable_to_determine' && (
                  <span className="text-[11px] text-[#292B26]/50 block">
                    Model confidence score. Outbreaks should be verified with a local Krishi Vigyan Kendra (KVK) or State Agricultural Extension Officer before applying any chemical treatment.
                  </span>
                )}
              </div>
            </div>

            {/* 3. Recommended Next Steps */}
            <div className="space-y-3">
              <span className="text-xs font-bold text-[#103D2C] uppercase tracking-wider block">
                Recommended Next Steps:
              </span>
              <ul className="space-y-2 text-sm text-[#292B26]">
                {diagnosis.recommended_steps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-[#103D2C]/10 text-[#103D2C] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="leading-relaxed">{step}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 4. Retake Photo / Try Another Image Button */}
            <div className="pt-3 border-t border-[#E5DDCF]">
              <button
                type="button"
                onClick={handleReset}
                className="w-full py-2.5 px-4 bg-[#FBF7EF] hover:bg-[#E5DDCF] border border-[#E5DDCF] text-[#103D2C] text-sm font-semibold rounded-xl flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-2xs"
              >
                <RefreshCw size={15} /> Retake / Try Another Photo
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
