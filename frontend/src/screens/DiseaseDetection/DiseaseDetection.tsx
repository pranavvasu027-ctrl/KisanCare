import React, { useState, useRef } from 'react';
import {
  Camera, Upload, CheckCircle2, AlertTriangle,
  HelpCircle, RefreshCw, X, Loader2, ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';

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

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
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

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setErrorMessage('Please upload or take a leaf photo first.');
      return;
    }

    setAnalyzing(true);
    setErrorMessage(null);
    setDiagnosis(null);

    try {
      const response = await api.detectDisease(selectedCrop, [], {
        file: selectedFile,
        locationState: 'Maharashtra',
        growthStage: 'vegetative',
        imageType: 'leaf',
      });

      const resData = response.data;
      if (!resData) {
        throw new Error('No diagnostic data returned by server.');
      }

      // Check if backend returned structured farmer guidance
      const guidance = resData.farmer_guidance || (resData.data && resData.data.farmer_guidance);

      if (guidance) {
        const isCotton = selectedCrop === 'Cotton';
        const validSet = isCotton ? VALID_COTTON_CLASSES : VALID_SOYBEAN_CLASSES;
        const diseaseName = guidance.disease_name;

        // Ensure disease name matches genuine specialist classes or clean abstention
        if (guidance.status === 'unable_to_determine' || !validSet.has(diseaseName)) {
          if (guidance.status !== 'healthy') {
            setDiagnosis({
              status: 'unable_to_determine',
              status_label: 'Unable to Determine Reliably',
              disease_name: 'Uncertain foliar pattern',
              confidence_percent: null,
              confidence_display: 'Confidence too low',
              recommended_steps: [
                'Take a clearer, closer photo in bright natural daylight.',
                'Ensure the leaf fills at least 70% of the camera frame.',
                'Avoid extreme glare, shadows, or blurry camera focus.',
                'Consult your local Krishi Vigyan Kendra (KVK) or extension officer with a physical leaf sample.',
              ],
              crop: selectedCrop,
              is_healthy: false,
              is_abstaining: true,
            });
            return;
          }
        }

        setDiagnosis({
          status: guidance.status,
          status_label: guidance.status_label,
          disease_name: guidance.disease_name,
          confidence_percent: guidance.confidence_percent,
          confidence_display: guidance.confidence_display,
          recommended_steps: guidance.recommended_steps || [],
          crop: selectedCrop,
          is_healthy: guidance.is_healthy,
          is_abstaining: guidance.is_abstaining,
        });
      } else {
        // Fallback for direct condition extraction
        const condition = resData.condition || (resData.data && resData.data.condition) || 'Healthy Foliage';
        const confidence = typeof resData.confidence_percent === 'number'
          ? resData.confidence_percent
          : Math.round(((resData.confidence || resData.probability || 0.85) as number) * 100);

        const isHealthy = condition.toLowerCase().includes('healthy');

        setDiagnosis({
          status: isHealthy ? 'healthy' : 'disease_detected',
          status_label: isHealthy ? 'Healthy Foliage' : 'Disease Detected',
          disease_name: condition,
          confidence_percent: confidence,
          confidence_display: `${confidence}% confidence`,
          recommended_steps: isHealthy
            ? ['Maintain regular crop monitoring and balanced nutrient management.']
            : ['Consult your local agricultural extension officer for verified field treatment advice.'],
          crop: selectedCrop,
          is_healthy: isHealthy,
          is_abstaining: false,
        });
      }
    } catch (err: any) {
      console.error('Diagnosis error:', err);
      setErrorMessage(
        err.message || 'Unable to analyze the leaf photo. Please check your internet connection and try again.'
      );
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-4xl mx-auto space-y-6">
      {/* Seasonal Crop Care Workflow Stepper */}
      <WorkflowStepper currentStageId={3} />

      {/* Main Container */}
      <div className="max-w-xl mx-auto space-y-6">

        {/* Header */}
        <div className="text-center space-y-1">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#103D2C] text-white shadow-xs mb-2">
            <span className="text-xl">🌿</span>
          </div>
          <h1 className="text-2xl font-serif font-bold text-[#103D2C]">
            Plant Disease Diagnosis
          </h1>
          <p className="text-xs text-[#292B26]/70 max-w-sm mx-auto">
            Specialized deep neural diagnosis strictly for <strong>Cotton</strong> and <strong>Soybean</strong> crops.
          </p>
        </div>

        {/* Error Notification */}
        {errorMessage && (
          <div className="bg-red-50 border border-red-300 text-red-900 p-4 rounded-xl text-sm flex items-start gap-3 shadow-sm">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div className="space-y-1 flex-1">
              <span className="font-bold block">Inspection Notice</span>
              <p className="text-xs text-red-800 leading-relaxed">{errorMessage}</p>
            </div>
            <button
              type="button"
              onClick={() => setErrorMessage(null)}
              className="text-red-500 hover:text-red-800 cursor-pointer"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Card: 2 Farmer Inputs */}
        <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 shadow-xs space-y-5">

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
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className="border-2 border-dashed border-[#E5DDCF] hover:border-[#103D2C] rounded-2xl p-6 text-center bg-[#FBF7EF]/50 transition-colors"
              >
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
                    <div className="absolute inset-0 bg-[#103D2C]/40 backdrop-blur-xs flex flex-col items-center justify-center text-white gap-2 p-4 text-center">
                      <Loader2 className="w-8 h-8 animate-spin" />
                      <span className="font-bold text-sm">Analyzing leaf condition...</span>
                      <span className="text-xs text-white/80">Evaluating {selectedCrop} foliar patterns</span>
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
                      onClick={() => cameraInputRef.current?.click()}
                      className="text-[#103D2C] font-semibold hover:underline cursor-pointer flex items-center gap-1"
                    >
                      <Camera size={13} /> Retake
                    </button>
                    <span className="text-[#E5DDCF]">|</span>
                    <button
                      type="button"
                      onClick={handleReset}
                      className="text-red-600 font-semibold hover:underline cursor-pointer flex items-center gap-1"
                    >
                      <X size={13} /> Remove
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ANALYZE BUTTON */}
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!selectedFile || analyzing}
            className={`w-full py-3.5 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all cursor-pointer shadow-sm ${
              !selectedFile || analyzing
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed border border-gray-300'
                : 'bg-[#17643E] hover:bg-[#103D2C] text-white hover:shadow-md'
            }`}
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Diagnosing Leaf Photo...</span>
              </>
            ) : (
              <>
                <span>Get Instant Diagnosis</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>

        {/* DIAGNOSIS RESULT CARD (ON SAME PAGE) */}
        {diagnosis && (
          <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 shadow-xs space-y-4 animate-in fade-in duration-300">

            {/* 1. Header Banner */}
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 ${
                diagnosis.status === 'healthy'
                  ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
                  : diagnosis.status === 'disease_detected'
                  ? 'bg-amber-50/80 border-amber-300 text-amber-950'
                  : 'bg-gray-50 border-gray-300 text-gray-900'
              }`}
            >
              <div className="shrink-0 mt-0.5">
                {diagnosis.status === 'healthy' && (
                  <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                )}
                {diagnosis.status === 'disease_detected' && (
                  <AlertTriangle className="w-6 h-6 text-amber-600" />
                )}
                {diagnosis.status === 'unable_to_determine' && (
                  <HelpCircle className="w-6 h-6 text-gray-500" />
                )}
              </div>

              <div className="space-y-1 flex-1">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-xs font-bold uppercase tracking-wider opacity-80">
                    {diagnosis.crop} • {diagnosis.status_label}
                  </span>
                  {diagnosis.confidence_display && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white/80 border border-current">
                      {diagnosis.confidence_display}
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-bold">
                  {diagnosis.disease_name}
                </h3>
              </div>
            </div>

            {/* 2. Recommended Next Steps */}
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

            {/* 3. Retake Photo / Try Another Image Button */}
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

      {/* Seasonal Workflow Navigation Footer */}
      <WorkflowFooter
        currentStageNumber={3}
        currentStageName="In-Season Crop Care"
        completedActionMessage={
          diagnosis
            ? `Diagnosis complete for ${diagnosis.crop} (${diagnosis.disease_name})! Next: Simulate harvest yield and cost adjustments.`
            : null
        }
        prevStep={{ label: "Irrigation & Climate", path: "/irrigation" }}
        nextStep={{
          label: "What-If Simulator",
          labelMr: "नफा व जोखीम सिम्युलेटर",
          path: "/simulator",
          description: "Simulate management adjustments, drought tolerance, and yield impact"
        }}
        alternativeNextStep={{
          label: "Farm Economics",
          path: "/economics"
        }}
      />
    </div>
  );
}
