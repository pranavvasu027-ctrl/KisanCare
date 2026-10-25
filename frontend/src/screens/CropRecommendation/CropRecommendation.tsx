import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { translateDynamic } from '../../i18n/translateHelper';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2,
  Sprout, Droplets, MapPin, Calendar, ShieldAlert, Sparkles,
  RefreshCw, ArrowRight, Info, FileQuestion, Leaf, Check,
  Filter, FlaskConical, Layers, TrendingUp, ChevronRight
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../services/supabase';
import { useFarmerProfile } from '../../context/FarmerProfileContext';

interface FieldOption {
  id: string;
  name: string;
  area: number;
  crop: string;
}

interface RecommendedCropItem {
  crop: string;
  rank: number;
  suitability_label: string;
  reason: string;
  local_considerations: string;
  water_advisory?: string;
  warning?: string;
  is_regionally_verified: boolean;
}

interface CropRecommendationResult {
  success: boolean;
  district: string;
  season: string;
  climate_source: string;
  applied_ph?: number;
  is_ph_baseline_applied?: boolean;
  extracted_nutrients?: {
    nitrogen?: number;
    phosphorus?: number;
    potassium?: number;
    ph?: number;
  };
  recommendations: RecommendedCropItem[];
  general_advisory?: string;
  warnings: string[];
}

interface ManualCropItem {
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

type LangOption = 'en' | 'mr' | 'hi';

const LABELS: Record<LangOption, {
  title: string;
  subtitle: string;
  uploadTitle: string;
  uploadSubtitle: string;
  supportedFormats: string;
  browseBtn: string;
  demoPrompt: string;
  trySampleBtn: string;
  analyzingTitle: string;
  analyzingSubtitle: string;
  resultsTitle: string;
  rankLabel: string;
  whyRecommended: string;
  localNotes: string;
  waterNotice: string;
  regionalWarning: string;
  testAnotherBtn: string;
  errorTitle: string;
  errorAction: string;
  disclaimer: string;
}> = {
  en: {
    title: 'Crop Recommendation',
    subtitle: 'Upload your soil laboratory report (Soil Health Card) to receive the top 3 crops suitable for your soil and local climate.',
    uploadTitle: 'Upload Soil Laboratory Report',
    uploadSubtitle: 'Drag & drop your soil test PDF or photo here, or browse from your device',
    supportedFormats: 'Supports PDF, JPG, JPEG, and PNG (Max 5MB)',
    browseBtn: 'Choose Soil Report File',
    demoPrompt: 'Don\'t have a file ready?',
    trySampleBtn: 'Load Sample Soil Health Report',
    analyzingTitle: 'Analyzing Soil Report...',
    analyzingSubtitle: 'Extracting soil parameters via OCR and matching with Maharashtra regional agro-climate history.',
    resultsTitle: 'Top 3 Recommended Crops',
    rankLabel: 'Rank',
    whyRecommended: 'Why Recommended',
    localNotes: 'Regional Agronomic Fit',
    waterNotice: 'Water & Irrigation Advisory',
    regionalWarning: 'Regional Evidence Note',
    testAnotherBtn: 'Upload Another Soil Report',
    errorTitle: 'Unable to Generate Recommendation',
    errorAction: 'Please check your document and try again.',
    disclaimer: 'Recommendations are based on scientific soil-crop matching and Maharashtra historical cultivation records. Always verify with your local Krishi Vigyan Kendra (KVK) before final seed procurement.'
  },
  mr: {
    title: 'पीक शिफारस',
    subtitle: 'तुमच्या जमिनीचा माती परीक्षण अहवाल (Soil Health Card) अपलोड करा आणि तुमच्या मातीसाठी व हवामानासाठी योग्य अशी ३ सर्वोत्तम पिके जाणून घ्या.',
    uploadTitle: 'माती परीक्षण अहवाल अपलोड करा',
    uploadSubtitle: 'माती परीक्षणाची PDF किंवा फोटो येथे ड्रॅग करा किंवा डिव्हाइसवरून निवडा',
    supportedFormats: 'PDF, JPG, JPEG आणि PNG समर्थित (कमाल ५ MB)',
    browseBtn: 'अहवाल फाईल निवडा',
    demoPrompt: 'तुमच्याकडे फाईल नाही का?',
    trySampleBtn: 'नमुना माती अहवाल वापरा',
    analyzingTitle: 'माती अहवालाचे विश्लेषण सुरू आहे...',
    analyzingSubtitle: 'OCR द्वारे मातीतील घटक वाचून महाराष्ट्रातील हवामान नोंदींशी पडताळणी केली जात आहे.',
    resultsTitle: 'सर्वोत्तम ३ शिफारस केलेली पिके',
    rankLabel: 'क्रमांक',
    whyRecommended: 'शिफारस करण्याचे कारण',
    localNotes: 'स्थानिक शेती अनुकूलता',
    waterNotice: 'पाणी व सिंचन सल्ला',
    regionalWarning: 'प्रादेशिक पुरावा नोंद',
    testAnotherBtn: 'दुसरा माती अहवाल तपासा',
    errorTitle: 'पीक शिफारस व्युत्पन्न करता आली नाही',
    errorAction: 'कृपया दस्तऐवज तपासा आणि पुन्हा प्रयत्न करा.',
    disclaimer: 'शिफारशी वैज्ञानिक माती-पीक जुळवणी आणि महाराष्ट्रातील ऐतिहासिक कृषी नोंदींवर आधारित आहेत. बियाणे खरेदीपूर्वी स्थानिक कृषी विज्ञान केंद्राचा (KVK) सल्ला घ्या.'
  },
  hi: {
    title: 'फसल सिफारिश',
    subtitle: 'अपनी मिट्टी परीक्षण रिपोर्ट (Soil Health Card) अपलोड करें और अपनी मिट्टी व स्थानीय मौसम के लिए 3 सबसे उपयुक्त फसलें जानें।',
    uploadTitle: 'मिट्टी परीक्षण रिपोर्ट अपलोड करें',
    uploadSubtitle: 'मिट्टी परीक्षण की PDF या फोटो यहाँ ड्रैग करें या डिवाइस से चुनें',
    supportedFormats: 'PDF, JPG, JPEG और PNG समर्थित (अधिकतम 5 MB)',
    browseBtn: 'रिपोर्ट फ़ाइल चुनें',
    demoPrompt: 'क्या आपके पास फ़ाइल नहीं है?',
    trySampleBtn: 'नमूना मृदा रिपोर्ट लोड करें',
    analyzingTitle: 'मिट्टी रिपोर्ट का विश्लेषण हो रहा है...',
    analyzingSubtitle: 'OCR द्वारा पोषक तत्वों का विश्लेषण और महाराष्ट्र के मौसम इतिहास से मिलान किया जा रहा है।',
    resultsTitle: 'शीर्ष 3 अनुशंसित फसलें',
    rankLabel: 'रैंक',
    whyRecommended: 'अनुशंसा का कारण',
    localNotes: 'क्षेत्रीय कृषि अनुकूलता',
    waterNotice: 'जल एवं सिंचाई सलाह',
    regionalWarning: 'क्षेत्रीय साक्ष्य सूचना',
    testAnotherBtn: 'दूसरी मिट्टी रिपोर्ट अपलोड करें',
    errorTitle: 'सिफारिश तैयार नहीं की जा सकी',
    errorAction: 'कृपया दस्तावेज़ की जांच करें और पुनः प्रयास करें।',
    disclaimer: 'सिफारिशें वैज्ञानिक मृदा-फसल मिलान और महाराष्ट्र के ऐतिहासिक आंकड़ों पर आधारित हैं। अंतिम निर्णय से पहले स्थानीय कृषि विज्ञान केंद्र (KVK) से परामर्श लें।'
  }
};

export default function CropRecommendation() {
  const { t: tI18n, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  const navigate = useNavigate();
  const { user } = useAuth();
  const { profile } = useFarmerProfile();
  const isAuthenticated = Boolean(user);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<'upload' | 'manual'>('upload');
  const [lang, setLang] = useState<LangOption>('en');
  const t = LABELS[lang];

  // ---------------------------------------------------------------------------
  // UPLOAD-FIRST PIPELINE STATE (PR #13 CORE)
  // ---------------------------------------------------------------------------
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<CropRecommendationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [customPh, setCustomPh] = useState<string>('7.2');
  const [autoAppliedPh, setAutoAppliedPh] = useState<number | null>(null);
  const [elapsedSec, setElapsedSec] = useState<number>(0);
  const [loadingStage, setLoadingStage] = useState<number>(1);

  // Progressive live loading tracker
  useEffect(() => {
    let timer: any = null;
    if (loading) {
      setElapsedSec(0);
      setLoadingStage(1);
      timer = setInterval(() => {
        setElapsedSec((prev) => {
          const next = prev + 1;
          if (next >= 16) setLoadingStage(4);
          else if (next >= 8) setLoadingStage(3);
          else if (next >= 3) setLoadingStage(2);
          return next;
        });
      }, 1000);
    } else {
      setElapsedSec(0);
      setLoadingStage(1);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [loading]);

  const STAGE_DESCRIPTIONS: Record<LangOption, Array<{ step: number; text: string }>> = {
    en: [
      { step: 1, text: 'Scanning document layout & checking camera orientation...' },
      { step: 2, text: 'Running multi-pass neural OCR on laboratory report table...' },
      { step: 3, text: 'Extracting Nitrogen, Phosphorus, Potassium & pH parameters...' },
      { step: 4, text: 'Cross-referencing Maharashtra regional agro-climate suitability...' },
    ],
    mr: [
      { step: 1, text: 'दस्तऐवजाचे स्कॅन व दिशा तपासत आहे...' },
      { step: 2, text: 'प्रयोगशाळा तक्त्यावर न्यूरल ओसीआर प्रक्रिया सुरू आहे...' },
      { step: 3, text: 'नायट्रोजन, फॉस्फरस, पोटॅशियम व सामू (pH) मूल्ये वाचत आहे...' },
      { step: 4, text: 'महाराष्ट्रातील स्थानिक हवामान व कृषी नोंदींशी पडताळणी करत आहे...' },
    ],
    hi: [
      { step: 1, text: 'दस्तावेज़ की बनावट व कोण की जांच हो रही है...' },
      { step: 2, text: 'प्रयोगशाला तालिका पर न्यूरल ओसीआर प्रक्रिया जारी है...' },
      { step: 3, text: 'नाइट्रोजन, फास्फोरस, पोटाश व पीएच मान पढ़े जा रहे हैं...' },
      { step: 4, text: 'महाराष्ट्र के क्षेत्रीय मौसम आंकड़ों से मिलान किया जा रहा है...' },
    ],
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const processFile = async (file: File, phOverride?: number) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'jpg', 'jpeg', 'png'].includes(ext || '')) {
      setErrorMessage('Unsupported file format. Please upload a PDF, JPG, JPEG, or PNG document.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 5MB limit. Please upload a compressed or standard document.');
      return;
    }

    setSelectedFile(file);
    setLoading(true);
    setErrorMessage(null);
    setResult(null);

    try {
      const response = await api.recommendCropsFromReport(file, undefined, undefined, undefined, phOverride, 7.4);
      if (response && response.success && response.recommendations && response.recommendations.length > 0) {
        setResult(response);
        setAutoAppliedPh(response.is_ph_baseline_applied ? (response.applied_ph || 7.4) : (phOverride || null));
      } else {
        setErrorMessage(
          'Could not generate reliable recommendations from this report. Please ensure the document is clear and contains available Nitrogen, Phosphorus, Potassium, and pH.'
        );
      }
    } catch (err: any) {
      const msg = err.message || '';
      setErrorMessage(
        msg || 'An unexpected error occurred while processing the report. Please try another clear document.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const res = await fetch('/demo-assets/soil-report-kharif-2025.pdf');
      if (!res.ok) {
        throw new Error('Sample soil report could not be loaded from demo assets.');
      }
      const blob = await res.blob();
      const sampleFile = new File([blob], 'soil-report-kharif-2025.pdf', { type: 'application/pdf' });
      await processFile(sampleFile);
    } catch (err: any) {
      setErrorMessage(err.message || 'Could not load the sample soil report.');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setErrorMessage(null);
    setAutoAppliedPh(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const getSuitabilityBadge = (label: string) => {
    const lower = label.toLowerCase();
    if (lower.includes('highly')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
          <CheckCircle2 size={13} />
          <span>{label}</span>
        </span>
      );
    }
    if (lower.includes('moderate')) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
          <Info size={13} />
          <span>{label}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-stone-100 text-stone-800">
        <AlertCircle size={13} />
        <span>{label}</span>
      </span>
    );
  };

  // ---------------------------------------------------------------------------

  // Sync state from active farmer profile and soil report
  useEffect(() => {
    if (profile) {
      if (profile.soil_report) {
        setNitrogen(profile.soil_report.nitrogen ?? 210);
        setPhosphorus(profile.soil_report.phosphorus ?? 32);
        setPotassium(profile.soil_report.potassium ?? 320);
        setSoilPh(profile.soil_report.ph ?? 7.8);
      }
      if (profile.weather) {
        setDistrict(profile.weather.district || 'Akola');
      }
    }
  }, [profile]);

  // MANUAL FIELD PARAMETERS STATE (FROM MAIN)
  // ---------------------------------------------------------------------------
  const [fields, setFields] = useState<FieldOption[]>([
    { id: 'field-1', name: 'Field 1 (North Parcel)', area: 6.5, crop: 'Soybean' },
    { id: 'field-2', name: 'Field 2 (South Parcel)', area: 5.5, crop: 'Cotton' }
  ]);
  const [selectedFieldId, setSelectedFieldId] = useState<string>('field-1');
  const [soilType, setSoilType] = useState('Black Cotton Soil / Medium Clay');
  const [soilPh, setSoilPh] = useState<number>(6.5);
  const [nitrogen, setNitrogen] = useState<number>(90);
  const [phosphorus, setPhosphorus] = useState<number>(45);
  const [potassium, setPotassium] = useState<number>(55);
  const [district, setDistrict] = useState<string>('Akola');
  const [season, setSeason] = useState<string>('Kharif');
  const [temperature, setTemperature] = useState<number>(27.5);
  const [humidity, setHumidity] = useState<number>(75);
  const [rainfall, setRainfall] = useState<number>(850);
  const [waterAvailability, setWaterAvailability] = useState<'Low' | 'Medium' | 'High'>('Medium');
  const [manualLoading, setManualLoading] = useState<boolean>(false);
  const [manualRecs, setManualRecs] = useState<ManualCropItem[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<ManualCropItem | null>(null);

  const fetchManualRecommendations = async () => {
    setManualLoading(true);
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
        top_k: 5
      });
      if (Array.isArray(response.data)) {
        setManualRecs(response.data);
      }
    } catch (err: any) {
      console.warn('Manual crop prediction failed:', err);
    } finally {
      setManualLoading(false);
    }
  };

  const selectedField = fields.find((f) => f.id === selectedFieldId) || fields[0];

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Workflow Navigation Stepper */}
      <WorkflowStepper currentStageId={2} />

      {/* Top Header & Localization */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#E5DDCF] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-[#103D2C] flex items-center gap-2">
            <Sprout className="text-[#17643E]" size={26} />
            <span>{t.title}</span>
          </h1>
          <p className="text-xs text-[#292B26]/70 mt-1 max-w-xl leading-relaxed">
            {t.subtitle}
          </p>
        </div>

        {/* Mode & Language Selector */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          <div className="flex items-center bg-white border border-[#E5DDCF] rounded-lg p-0.5 text-xs shadow-2xs">
            <button
              type="button"
              onClick={() => setLang('en')}
              className={`px-3 py-1 rounded font-medium transition-colors cursor-pointer ${
                lang === 'en' ? 'bg-[#103D2C] text-white' : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLang('mr')}
              className={`px-3 py-1 rounded font-medium transition-colors cursor-pointer ${
                lang === 'mr' ? 'bg-[#103D2C] text-white' : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              मराठी
            </button>
            <button
              type="button"
              onClick={() => setLang('hi')}
              className={`px-3 py-1 rounded font-medium transition-colors cursor-pointer ${
                lang === 'hi' ? 'bg-[#103D2C] text-white' : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              हिन्दी
            </button>
          </div>
        </div>
      </div>

      
      {/* Active Farmer Profile & Soil Report Linkage Banner */}
      {profile && (
        <div className="bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 border border-emerald-300 rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs text-emerald-950 shadow-2xs mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#103D2C] text-white flex items-center justify-center shrink-0 shadow-sm">
              <Sprout className="w-5 h-5 text-emerald-300" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-[#103D2C]">
                  Linked to {profile.name}'s Farm Profile &amp; Soil Report
                </span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-200/90 text-emerald-900 text-[10px] font-extrabold uppercase tracking-wider">
                  AgriStack Synced
                </span>
              </div>
              <p className="text-[11px] text-emerald-800 mt-0.5">
                Farm: <strong>{profile.farm_name}</strong> &bull; GPS: <strong>{profile.weather?.district || district}</strong> ({profile.weather?.latitude?.toFixed(2)}°N, {profile.weather?.longitude?.toFixed(2)}°E) &bull; Soil NPK: <strong className="text-[#103D2C]">{profile.soil_report?.nitrogen}-{profile.soil_report?.phosphorus}-{profile.soil_report?.potassium}</strong> kg/ha &bull; pH: <strong>{profile.soil_report?.ph}</strong>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('/onboarding')}
            className="px-3 py-1.5 bg-white border border-emerald-300 hover:bg-emerald-100 text-[#103D2C] font-bold rounded-xl text-xs transition-colors shadow-2xs shrink-0 flex items-center gap-1.5 cursor-pointer"
          >
            <FlaskConical className="w-3.5 h-3.5 text-[#17643E]" />
            <span>Update Profile / Soil NPK</span>
          </button>
        </div>
      )}

      {/* Mode Switcher Tabs */}
      <div className="flex border-b border-[#E5DDCF] gap-6 text-xs sm:text-sm font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab('upload')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
            activeTab === 'upload'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-[#292B26]/60 hover:text-[#103D2C]'
          }`}
        >
          <UploadCloud size={16} />
          <span>Upload Soil Health Report (PDF/Photo)</span>
          <span className="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded-full font-bold">
            Neural OCR
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('manual')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
            activeTab === 'manual'
              ? 'border-[#103D2C] text-[#103D2C]'
              : 'border-transparent text-[#292B26]/60 hover:text-[#103D2C]'
          }`}
        >
          <FlaskConical size={16} />
          <span>Manual Field Parameters & Sliders</span>
        </button>
      </div>

      {/* ===================================================================== */}
      {/* TAB 1: UPLOAD SOIL REPORT (PR #13 CORE PIPELINE)                      */}
      {/* ===================================================================== */}
      {activeTab === 'upload' && (
        <div className="max-w-4xl mx-auto space-y-6">
          {/* UPLOAD AREA */}
          {!loading && !result && (
            <div className="space-y-4">
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all bg-white ${
                  dragActive ? 'border-[#17643E] bg-emerald-50/40 scale-[1.005]' : 'border-[#E5DDCF] hover:border-[#103D2C]/40'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileChange}
                  className="hidden"
                  id="soil-report-upload-input"
                />

                <div className="w-16 h-16 rounded-full bg-[#FBF7EF] border border-[#E5DDCF] flex items-center justify-center mx-auto mb-4 text-[#103D2C]">
                  <UploadCloud size={30} className="text-[#17643E]" />
                </div>

                <h2 className="text-base font-bold text-[#103D2C]">
                  {t.uploadTitle}
                </h2>
                <p className="text-xs text-[#292B26]/60 mt-1 max-w-md mx-auto leading-relaxed">
                  {t.uploadSubtitle}
                </p>

                <div className="mt-5 flex flex-col sm:flex-row items-center justify-center gap-3">
                  <label
                    htmlFor="soil-report-upload-input"
                    className="inline-flex items-center gap-2 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold px-5 py-2.5 rounded-xl cursor-pointer transition-colors shadow-2xs"
                  >
                    <FileText size={15} />
                    <span>{t.browseBtn}</span>
                  </label>
                </div>

                <p className="text-[11px] text-[#292B26]/50 mt-4">
                  {t.supportedFormats}
                </p>
              </div>

              {/* Quick Demo Helper */}
              <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                <span className="text-[#292B26]/70">
                  {t.demoPrompt}
                </span>
                <button
                  type="button"
                  onClick={handleLoadSample}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#17643E] hover:text-[#103D2C] underline cursor-pointer"
                >
                  <Sparkles size={14} />
                  <span>{t.trySampleBtn}</span>
                </button>
              </div>
            </div>
          )}

          {/* LOADING / PROCESSING INDICATOR */}
          {loading && (
            <div className="bg-white border border-[#E5DDCF] rounded-2xl p-8 sm:p-10 text-center space-y-5 shadow-2xs">
              <div className="relative w-14 h-14 mx-auto flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-4 border-[#17643E]/20 border-t-[#17643E] animate-spin" />
                <Sprout size={24} className="text-[#103D2C] animate-pulse" />
              </div>

              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-[#103D2C]">
                  {t.analyzingTitle}
                </h3>
                <p className="text-xs font-semibold text-[#17643E]">
                  {STAGE_DESCRIPTIONS[lang][loadingStage - 1]?.text}
                </p>
                <p className="text-[11px] text-[#292B26]/60">
                  Processing elapsed: {elapsedSec}s &bull; Step {loadingStage} of 4
                </p>
              </div>

              {/* Dynamic Progress Bar */}
              <div className="max-w-md mx-auto space-y-1.5 pt-1">
                <div className="h-2 w-full bg-[#FBF7EF] rounded-full overflow-hidden border border-[#E5DDCF]">
                  <div
                    className="h-full bg-[#17643E] transition-all duration-500 rounded-full"
                    style={{ width: `${Math.min(95, Math.max(12, Math.round(12 + elapsedSec * 3.5)))}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-[#292B26]/50">
                  <span>Layout & OCR</span>
                  <span>NPK Extraction</span>
                  <span>Agro-climate Match</span>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-xs text-[#292B26]/60 hover:text-red-600 underline cursor-pointer"
                >
                  Cancel and select another file
                </button>
              </div>
            </div>
          )}

          {/* ACTIONABLE ERROR / LEAF REDIRECTION STATE */}
          {errorMessage && !loading && (() => {
            const cleanError = errorMessage.replace(/^API Error \(\d+\):\s*/i, '');
            const isNoDocFound = cleanError.toLowerCase().includes('no soil laboratory report detected') ||
              cleanError.toLowerCase().includes('plant/crop photo') ||
              cleanError.toLowerCase().includes('non-document') ||
              cleanError.toLowerCase().includes('unreadable even after');
            const isMissingParams = cleanError.toLowerCase().includes('essential soil parameters missing');
            const partialParts = cleanError.split('Partially readable:');
            const missingSummary = partialParts[0]?.trim();
            const readableSummary = partialParts.length > 1 ? partialParts[1]?.replace(/\.\s*KisanCare requires.*/i, '')?.trim() : null;

            if (isNoDocFound) {
              return (
                <div className="bg-white border border-[#E5DDCF] rounded-2xl p-8 sm:p-10 space-y-6 shadow-2xs text-center">
                  <div className="relative w-16 h-16 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center mx-auto text-amber-700">
                    <FileQuestion size={32} />
                    <span className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-[#103D2C] text-white flex items-center justify-center shadow-xs">
                      <Leaf size={14} className="text-emerald-400" />
                    </span>
                  </div>

                  <div className="space-y-1.5 max-w-md mx-auto">
                    <h3 className="text-base font-bold text-[#103D2C]">
                      No Soil Health Card Detected
                    </h3>
                    <p className="text-xs text-[#292B26]/75 leading-relaxed">
                      The uploaded image does not contain laboratory soil test text. It appears to be a crop leaf, plant photo, or non-document image.
                    </p>
                  </div>

                  {/* Redirection banner for plant disease detection */}
                  <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 sm:p-5 max-w-lg mx-auto text-left flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-[#103D2C]">
                        <Leaf size={14} className="text-[#17643E]" />
                        <span>Looking to diagnose a sick plant or leaf disease?</span>
                      </div>
                      <p className="text-[11px] text-[#292B26]/70 leading-relaxed">
                        Upload crop leaf photos to KisanCare AI Disease & Pest Detection for instant diagnosis and treatment plans.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate('/disease-detection')}
                      className="shrink-0 inline-flex items-center gap-1.5 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition-colors cursor-pointer shadow-2xs"
                    >
                      <span>Go to Disease AI</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>

                  <div className="pt-2 flex justify-center gap-3">
                    <button
                      type="button"
                      onClick={handleReset}
                      className="inline-flex items-center gap-1.5 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold px-5 py-2.5 rounded-xl transition-colors cursor-pointer"
                    >
                      <UploadCloud size={14} />
                      <span>Upload Soil Report (PDF/Photo)</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleLoadSample}
                      className="inline-flex items-center gap-1.5 bg-[#FBF7EF] hover:bg-emerald-50 text-[#17643E] border border-emerald-300 text-xs font-semibold px-4 py-2.5 rounded-xl transition-colors cursor-pointer"
                    >
                      <Sparkles size={14} />
                      <span>Try Sample Report</span>
                    </button>
                  </div>
                </div>
              );
            }

            return (
              <div className="bg-white border border-[#E5DDCF] rounded-2xl p-6 sm:p-8 space-y-5 shadow-2xs">
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-full bg-red-50 border border-red-200 flex items-center justify-center shrink-0 text-red-600">
                    <AlertCircle size={22} />
                  </div>
                  <div className="space-y-2 flex-1">
                    <h3 className="text-sm font-bold text-red-950">
                      {t.errorTitle}
                    </h3>
                    <p className="text-xs text-red-800 leading-relaxed font-medium">
                      {missingSummary}
                    </p>

                    {readableSummary && (
                      <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl p-3.5 space-y-1.5 mt-2">
                        <span className="text-[11px] font-semibold text-[#103D2C] uppercase tracking-wider block">
                          Successfully Verified by OCR from your Certificate:
                        </span>
                        <div className="flex flex-wrap gap-2 pt-1">
                          {readableSummary.split(',').map((param, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-[#17643E] border border-emerald-200"
                            >
                              <CheckCircle2 size={12} />
                              {param.trim()}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-2 flex flex-wrap gap-3 border-t border-[#E5DDCF]/60 pt-4">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 bg-[#103D2C] hover:bg-[#17643E] text-white text-xs font-semibold px-4 py-2 rounded-xl transition-colors cursor-pointer"
                  >
                    <RefreshCw size={13} />
                    <span>{t.testAnotherBtn}</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleLoadSample}
                    className="inline-flex items-center gap-1.5 bg-[#FBF7EF] hover:bg-emerald-50 text-[#17643E] border border-emerald-300 text-xs font-semibold px-4 py-2 rounded-xl transition-colors cursor-pointer"
                  >
                    <Sparkles size={13} />
                    <span>{t.trySampleBtn}</span>
                  </button>
                </div>
              </div>
            );
          })()}

          {/* THE 3 RECOMMENDED CROPS (Farmer-Facing Results) */}
          {result && !loading && (
            <div className="space-y-6">
              {/* Metadata Bar */}
              <div className="bg-white border border-[#E5DDCF] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
                <div className="flex items-center gap-4 text-xs text-[#292B26]/80 flex-wrap">
                  <span className="flex items-center gap-1.5 font-semibold text-[#103D2C]">
                    <MapPin size={14} className="text-[#17643E]" />
                    <span>{result.district}</span>
                  </span>
                  <span>&bull;</span>
                  <span className="flex items-center gap-1.5">
                    <Calendar size={14} className="text-[#17643E]" />
                    <span>{result.season} Season</span>
                  </span>
                  <span>&bull;</span>
                  <span className="text-[11px] text-[#292B26]/60">
                    {result.climate_source}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={handleReset}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#17643E] hover:text-[#103D2C] cursor-pointer"
                >
                  <RefreshCw size={13} />
                  <span>{t.testAnotherBtn}</span>
                </button>
              </div>

              {/* Soil Report Verification & pH Quick-Adjust Banner */}
              {(result.is_ph_baseline_applied || autoAppliedPh !== null) && selectedFile && (
                <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl p-4 sm:p-5 space-y-3 shadow-2xs">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2 text-xs font-bold text-[#103D2C]">
                      <CheckCircle2 size={16} className="text-[#17643E]" />
                      <span>Soil Laboratory Certificate Verified</span>
                    </div>
                    <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-900 px-2.5 py-0.5 rounded-full">
                      Applied pH: {autoAppliedPh || result.applied_ph || 7.4}
                    </span>
                  </div>

                  {result.extracted_nutrients && (
                    <div className="flex flex-wrap gap-2 text-xs">
                      {result.extracted_nutrients.nitrogen !== undefined && (
                        <span className="px-2.5 py-1 rounded-lg font-semibold bg-white border border-[#E5DDCF] text-[#103D2C]">
                          Nitrogen: {result.extracted_nutrients.nitrogen.toFixed(0)} kg/ha
                        </span>
                      )}
                      {result.extracted_nutrients.phosphorus !== undefined && (
                        <span className="px-2.5 py-1 rounded-lg font-semibold bg-white border border-[#E5DDCF] text-[#103D2C]">
                          Phosphorus: {result.extracted_nutrients.phosphorus.toFixed(0)} kg/ha
                        </span>
                      )}
                      {result.extracted_nutrients.potassium !== undefined && (
                        <span className="px-2.5 py-1 rounded-lg font-semibold bg-white border border-[#E5DDCF] text-[#103D2C]">
                          Potassium: {result.extracted_nutrients.potassium.toFixed(0)} kg/ha
                        </span>
                      )}
                    </div>
                  )}

                  <p className="text-[11px] text-[#292B26]/75 leading-relaxed">
                    {result.is_ph_baseline_applied
                      ? 'Your laboratory certificate tested available N, P, and K, but omitted Soil pH. Recommendations were generated using Maharashtra regional baseline pH (7.4). You can test other pH values below:'
                      : `Soil pH (${autoAppliedPh || result.applied_ph}) applied to recommendations:`}
                  </p>

                  {/* Quick pH preset buttons */}
                  <div className="flex flex-wrap items-center gap-2 pt-0.5">
                    {[5.29, 6.5, 7.0, 7.4, 8.0].map((phVal) => {
                      const isActive = (autoAppliedPh || result.applied_ph) === phVal;
                      return (
                        <button
                          key={phVal}
                          type="button"
                          onClick={() => processFile(selectedFile, phVal)}
                          className={`text-xs px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                            isActive
                              ? 'bg-[#103D2C] text-white shadow-2xs'
                              : 'bg-white border border-[#E5DDCF] text-[#103D2C] hover:border-[#17643E]'
                          }`}
                        >
                          pH {phVal} {phVal === 5.29 ? '(Row 1 value)' : phVal === 7.4 ? '(regional baseline)' : ''}
                        </button>
                      );
                    })}

                    <div className="flex items-center gap-1 bg-white border border-[#E5DDCF] rounded-lg px-2 py-1 text-xs sm:ml-auto">
                      <span className="text-[#292B26]/60 text-[11px]">Custom:</span>
                      <input
                        type="number"
                        step="0.1"
                        min="4.0"
                        max="9.5"
                        value={customPh}
                        onChange={(e) => setCustomPh(e.target.value)}
                        className="w-12 text-center font-bold text-[#103D2C] bg-[#FBF7EF] rounded px-1 text-xs border border-[#E5DDCF]"
                      />
                      <button
                        type="button"
                        onClick={() => processFile(selectedFile, parseFloat(customPh) || 7.2)}
                        className="font-semibold text-[#17643E] hover:underline cursor-pointer text-xs"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 3 Ranked Crop Cards */}
              <div className="space-y-4">
                <h2 className="text-sm font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-2">
                  <Sparkles size={16} className="text-[#17643E]" />
                  <span>{t.resultsTitle}</span>
                </h2>

                <div className="grid grid-cols-1 gap-4">
                  {result.recommendations.map((rec) => (
                    <div
                      key={rec.rank}
                      className={`bg-white rounded-2xl border transition-all p-5 sm:p-6 shadow-2xs ${
                        rec.rank === 1 ? 'border-[#17643E] ring-1 ring-[#17643E]/20' : 'border-[#E5DDCF]'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5DDCF]/60 pb-3">
                        <div className="flex items-center gap-3">
                          <span className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                            rec.rank === 1
                              ? 'bg-[#103D2C] text-white'
                              : 'bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF]'
                          }`}>
                            #{rec.rank}
                          </span>
                          <h3 className="text-lg font-bold text-[#103D2C]">
                            {rec.crop}
                          </h3>
                        </div>

                        <div>
                          {getSuitabilityBadge(rec.suitability_label)}
                        </div>
                      </div>

                      {/* Reasons & Local Context */}
                      <div className="mt-3.5 space-y-2.5 text-xs">
                        <div>
                          <span className="font-semibold text-[#103D2C] block mb-0.5">
                            {t.whyRecommended}:
                          </span>
                          <p className="text-[#292B26]/80 leading-relaxed">
                            {rec.reason}
                          </p>
                        </div>

                        <div>
                          <span className="font-semibold text-[#103D2C] block mb-0.5">
                            {t.localNotes}:
                          </span>
                          <p className="text-[#292B26]/70 leading-relaxed">
                            {rec.local_considerations}
                          </p>
                        </div>

                        {rec.water_advisory && (
                          <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-200 text-blue-900 flex items-start gap-2">
                            <Droplets size={14} className="shrink-0 mt-0.5 text-blue-600" />
                            <span className="leading-relaxed">{rec.water_advisory}</span>
                          </div>
                        )}

                        {rec.warning && (
                          <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 flex items-start gap-2">
                            <ShieldAlert size={14} className="shrink-0 mt-0.5 text-amber-700" />
                            <span className="leading-relaxed">{rec.warning}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Practical Agronomic Notice */}
              <div className="bg-[#FBF7EF] border border-[#E5DDCF] p-4 rounded-xl text-[11px] text-[#292B26]/70 leading-relaxed">
                <strong>Notice:</strong> {t.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: MANUAL FIELD PARAMETERS (PRESERVED FROM MAIN)                  */}
      {/* ===================================================================== */}
      {activeTab === 'manual' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] space-y-4 shadow-2xs">
              <h3 className="font-bold text-sm text-[#103D2C] flex items-center gap-2">
                <Layers size={16} className="text-[#17643E]" />
                <span>Field & District Selection</span>
              </h3>

              {/* Field selector */}
              <div>
                <label className="text-xs font-semibold text-[#292B26]/70 block mb-1">Target Field Parcel:</label>
                <select
                  value={selectedFieldId}
                  onChange={(e) => setSelectedFieldId(e.target.value)}
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-medium text-[#103D2C]"
                >
                  {fields.map((f) => (
                    <option key={f.id} value={f.id}>{f.name} ({f.area} acres)</option>
                  ))}
                </select>
              </div>

              {/* District dropdown mapping all 35 districts */}
              <div>
                <label className="text-xs font-semibold text-[#292B26]/70 block mb-1">Maharashtra District:</label>
                <select
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="w-full bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl px-3 py-2 text-xs font-medium text-[#103D2C]"
                >
                  {MAHARASHTRA_DISTRICTS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              {/* NPK Sliders */}
              <div className="space-y-3 pt-2">
                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#292B26]/80 mb-1">
                    <span>Nitrogen (N):</span>
                    <span className="font-mono text-[#103D2C]">{nitrogen} kg/ha</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="300"
                    value={nitrogen}
                    onChange={(e) => setNitrogen(Number(e.target.value))}
                    className="w-full accent-[#17643E]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#292B26]/80 mb-1">
                    <span>Phosphorus (P):</span>
                    <span className="font-mono text-[#103D2C]">{phosphorus} kg/ha</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="300"
                    value={phosphorus}
                    onChange={(e) => setPhosphorus(Number(e.target.value))}
                    className="w-full accent-[#17643E]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#292B26]/80 mb-1">
                    <span>Potassium (K):</span>
                    <span className="font-mono text-[#103D2C]">{potassium} kg/ha</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="800"
                    value={potassium}
                    onChange={(e) => setPotassium(Number(e.target.value))}
                    className="w-full accent-[#17643E]"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-[#292B26]/80 mb-1">
                    <span>Soil pH:</span>
                    <span className="font-mono text-[#103D2C]">{soilPh}</span>
                  </div>
                  <input
                    type="range"
                    min="4"
                    max="9.5"
                    step="0.1"
                    value={soilPh}
                    onChange={(e) => setSoilPh(Number(e.target.value))}
                    className="w-full accent-[#17643E]"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={fetchManualRecommendations}
                disabled={manualLoading}
                className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer shadow-2xs transition-colors"
              >
                {manualLoading ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
                <span>{manualLoading ? 'Evaluating Model...' : 'Calculate Recommendations'}</span>
              </button>
            </div>
          </div>

          {/* Results column */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-2xs">
              <h3 className="font-bold text-sm text-[#103D2C] mb-3 flex items-center gap-2">
                <Sparkles size={16} className="text-[#17643E]" />
                <span>Model 1 Multi-Factor Recommended Crops</span>
              </h3>

              {manualRecs.length > 0 ? (
                <div className="space-y-3">
                  {manualRecs.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-[#E5DDCF] bg-[#FBF7EF] flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-[#103D2C] text-white font-bold text-xs flex items-center justify-center">
                          #{rec.rank || idx + 1}
                        </span>
                        <div>
                          <h4 className="font-bold text-sm text-[#103D2C]">{rec.crop}</h4>
                          <span className="text-[11px] text-[#292B26]/70">
                            {rec.evidence_tier || `Verified in ${district}`}
                          </span>
                        </div>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-800">
                        {rec.region_suitability || 'High Match'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-[#292B26]/60">
                  Adjust soil sliders and click "Calculate Recommendations" to view model output.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Integrated Workflow Navigation Footer */}
      <WorkflowFooter
        currentStageNumber={2}
        currentStageName="Crop Planning & Selection"
        completedActionMessage={
          result
            ? `Top 3 crops recommended for your soil report! Compare candidates or proceed to farm economics.`
            : null
        }
        prevStep={{ label: 'Soil Intelligence', path: '/soil' }}
        nextStep={{
          label: 'Crop Comparison',
          labelMr: 'पीक तुलना',
          path: '/crop-comparison',
          description: 'Compare candidate crops side-by-side on yield, revenue, and costs'
        }}
        alternativeNextStep={{
          label: 'Run What-If Simulator',
          path: '/simulator'
        }}
      />
    </div>
  );
}
