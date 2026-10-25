import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { changeLanguage } from '../i18n';
import { supabase } from '../services/supabase';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';
import { IS_DEMO_MODE } from '../config/demo';
import { MAHARASHTRA_GEOGRAPHY } from '../data/maharashtraGeography';
import {
  Leaf, Sprout, TrendingUp, ShieldCheck, Droplets, Bug,
  ArrowRight, ArrowLeft, Check, CheckCircle2, AlertCircle,
  MapPin, Phone, Lock, Eye, EyeOff, Mail, Compass, Navigation,
  Plus, Trash2, Edit3, Loader2, Sparkles, Tractor, User, RefreshCw
} from 'lucide-react';

export interface FieldEntry {
  id: string;
  field_name: string;
  area: string;
  area_unit: string;
  soil_type: string;
  irrigation_method: string;
  current_crop: string;
  previous_crop: string;
}

const STORAGE_DRAFT_KEY = 'kisancare_onboarding_draft';

// Flattened list of Maharashtra districts
const MAHARASHTRA_DISTRICTS = Object.values(MAHARASHTRA_GEOGRAPHY).flatMap(
  (div) => Object.keys(div.districts)
).sort();

export default function Onboarding({ onComplete }: { onComplete?: () => void }) {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { t, i18n } = useTranslation();

  // Screen / Journey Step: 1 = Welcome, 2 = Account/Auth, 3 = Profile, 4 = Farm Setup, 5 = Field Setup, 6 = Review, 7 = Save/Complete
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [returnToReview, setReturnToReview] = useState<boolean>(false);

  // Screen 1: Welcome & Language
  const [selectedLanguage, setSelectedLanguage] = useState<'en' | 'hi' | 'mr'>('en');

  // Screen 2: Account & Authentication
  const [authMode, setAuthMode] = useState<'signup' | 'signin'>('signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);
  const [isDemoUser, setIsDemoUser] = useState(false);

  // Screen 3: Farmer Profile
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [stateName, setStateName] = useState('Maharashtra');
  const [district, setDistrict] = useState('Akola');
  const [village, setVillage] = useState('Takli Bu');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState<'Male' | 'Female' | 'Other' | ''>('');
  const [farmingExperience, setFarmingExperience] = useState('5-15 years');
  const [farmerCategory, setFarmerCategory] = useState('Small (1-2 ha)');

  // Screen 4: Farm Setup
  const [farmName, setFarmName] = useState('');
  const [totalArea, setTotalArea] = useState('10.0');
  const [areaUnit, setAreaUnit] = useState<'acre' | 'hectare'>('acre');
  const [landOwnership, setLandOwnership] = useState('Owned');
  const [irrigationSource, setIrrigationSource] = useState('Borewell / Tube Well');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [isCapturingGps, setIsCapturingGps] = useState(false);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);

  // Screen 5: Field Setup (One or more fields)
  const [fields, setFields] = useState<FieldEntry[]>([
    {
      id: 'field-1',
      field_name: 'Field 1 (North Parcel)',
      area: '6.0',
      area_unit: 'acre',
      soil_type: 'Black Cotton (Regur)',
      irrigation_method: 'Drip',
      current_crop: 'Cotton',
      previous_crop: 'Soybean'
    },
    {
      id: 'field-2',
      field_name: 'Field 2 (South Parcel)',
      area: '4.0',
      area_unit: 'acre',
      soil_type: 'Medium Black Loam',
      irrigation_method: 'Rainfed',
      current_crop: 'Soybean',
      previous_crop: 'Wheat'
    }
  ]);
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);

  // Screen 6 & 7: Save & Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionProgress, setSubmissionProgress] = useState<string | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [submissionSuccess, setSubmissionSuccess] = useState<any | null>(null);

  // Field-level error messages
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // 1. Restore saved onboarding draft from localStorage on initial mount
  useEffect(() => {
    try {
      const savedDraft = localStorage.getItem(STORAGE_DRAFT_KEY);
      if (savedDraft) {
        const d = JSON.parse(savedDraft);
        if (d.fullName) setFullName(d.fullName);
        if (d.phone) setPhone(d.phone);
        if (d.stateName) setStateName(d.stateName);
        if (d.district) setDistrict(d.district);
        if (d.village) setVillage(d.village);
        if (d.age) setAge(d.age);
        if (d.gender) setGender(d.gender);
        if (d.farmingExperience) setFarmingExperience(d.farmingExperience);
        if (d.farmerCategory) setFarmerCategory(d.farmerCategory);
        if (d.farmName) setFarmName(d.farmName);
        if (d.totalArea) setTotalArea(d.totalArea);
        if (d.areaUnit) setAreaUnit(d.areaUnit);
        if (d.landOwnership) setLandOwnership(d.landOwnership);
        if (d.irrigationSource) setIrrigationSource(d.irrigationSource);
        if (d.latitude) setLatitude(d.latitude);
        if (d.longitude) setLongitude(d.longitude);
        if (Array.isArray(d.fields) && d.fields.length > 0) setFields(d.fields);
        if (d.selectedLanguage) {
          setSelectedLanguage(d.selectedLanguage);
          changeLanguage(d.selectedLanguage);
        }
      }
    } catch {
      // ignore draft parse error
    }
  }, []);

  // 2. Persist in-progress onboarding state to localStorage whenever form data changes
  useEffect(() => {
    if (currentStep > 1 && !submissionSuccess) {
      try {
        const draft = {
          fullName, phone, stateName, district, village, age, gender,
          farmingExperience, farmerCategory, farmName, totalArea, areaUnit,
          landOwnership, irrigationSource, latitude, longitude, fields,
          selectedLanguage
        };
        localStorage.setItem(STORAGE_DRAFT_KEY, JSON.stringify(draft));
      } catch {
        // ignore localStorage quota error
      }
    }
  }, [
    currentStep, fullName, phone, stateName, district, village, age, gender,
    farmingExperience, farmerCategory, farmName, totalArea, areaUnit,
    landOwnership, irrigationSource, latitude, longitude, fields,
    selectedLanguage, submissionSuccess
  ]);

  // 3. Auto-suggest Farm Name when farmer enters full name
  useEffect(() => {
    if (fullName.trim() && !farmName) {
      setFarmName(`${fullName.trim()}'s Farm`);
    }
  }, [fullName]);

  // Handle Language Change
  const handleLanguageChange = (lang: 'en' | 'hi' | 'mr') => {
    setSelectedLanguage(lang);
    changeLanguage(lang);
  };

  // Screen 2: Authentication Handlers
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthSuccess(null);
    setFieldErrors({});

    const errors: Record<string, string> = {};
    if (!email.trim() || !email.includes('@')) {
      errors.email = 'Please enter a valid email address.';
    }
    if (!password || password.length < 6) {
      errors.password = 'Password must be at least 6 characters.';
    }
    if (authMode === 'signup' && password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setAuthLoading(true);
    try {
      if (authMode === 'signup') {
        const { data, error } = await supabase.auth.signUp({
          email: email.trim().toLowerCase(),
          password,
          options: {
            data: {
              name: fullName || 'Farmer'
            }
          }
        });
        if (error) {
          if (error.message.toLowerCase().includes('already registered')) {
            setAuthError('An account with this email already exists. Please switch to "Sign In".');
          } else {
            setAuthError(error.message);
          }
          setAuthLoading(false);
          return;
        }
        setAuthSuccess('Account created successfully! Proceeding to Profile setup.');
        setTimeout(() => {
          setAuthLoading(false);
          goToStep(3);
        }, 800);
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: email.trim().toLowerCase(),
          password
        });
        if (error) {
          setAuthError(error.message);
          setAuthLoading(false);
          return;
        }
        setAuthSuccess('Signed in successfully! Loading your farmer profile.');
        setTimeout(() => {
          setAuthLoading(false);
          goToStep(3);
        }, 800);
      }
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed. Please verify credentials or try Demo Mode.');
      setAuthLoading(false);
    }
  };

  const handleDemoBypass = () => {
    setIsDemoUser(true);
    setAuthSuccess('Demo farmer session activated. Proceeding to profile setup.');
    setTimeout(() => goToStep(3), 400);
  };

  // Step Validation & Navigation
  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};

    if (step === 3) {
      if (!fullName.trim()) errors.fullName = 'Full Name is required.';
      if (!phone.trim()) {
        errors.phone = 'Mobile Phone Number is required.';
      } else if (!/^[0-9+ -]{8,15}$/.test(phone.trim())) {
        errors.phone = 'Please enter a valid phone number (e.g. 9876543210).';
      }
      if (!district.trim()) errors.district = 'District is required.';
      if (!village.trim()) errors.village = 'Village / Locality is required.';
    }

    if (step === 4) {
      if (!farmName.trim()) errors.farmName = 'Farm Name or Identifier is required.';
      const areaNum = parseFloat(totalArea);
      if (isNaN(areaNum) || areaNum <= 0) {
        errors.totalArea = 'Total land area must be a valid positive number.';
      }
    }

    if (step === 5) {
      if (fields.length === 0) {
        errors.fields = 'You must configure at least one field for your farm.';
      } else {
        fields.forEach((f, idx) => {
          if (!f.field_name.trim()) {
            errors[`field_${idx}_name`] = `Field #${idx + 1} must have a name.`;
          }
          const fArea = parseFloat(f.area);
          if (isNaN(fArea) || fArea <= 0) {
            errors[`field_${idx}_area`] = `Field #${idx + 1} area must be a positive number.`;
          }
        });
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const goToStep = (stepNum: number) => {
    setFieldErrors({});
    setCurrentStep(stepNum);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNext = () => {
    if (!validateStep(currentStep)) return;

    if (returnToReview) {
      setReturnToReview(false);
      goToStep(6);
      return;
    }

    goToStep(Math.min(7, currentStep + 1));
  };

  const handleBack = () => {
    setFieldErrors({});
    if (returnToReview) {
      setReturnToReview(false);
      goToStep(6);
      return;
    }
    goToStep(Math.max(1, currentStep - 1));
  };

  const handleEditSection = (targetStep: number) => {
    setReturnToReview(true);
    goToStep(targetStep);
  };

  // GPS Geolocation Handler
  const handleCaptureGps = () => {
    if (!navigator.geolocation) {
      setGpsStatus('Geolocation is not supported by your mobile device.');
      return;
    }
    setIsCapturingGps(true);
    setGpsStatus('Accessing GPS satellites...');

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsCapturingGps(false);
        const lat = pos.coords.latitude.toFixed(6);
        const lon = pos.coords.longitude.toFixed(6);
        setLatitude(lat);
        setLongitude(lon);
        setGpsStatus(`GPS coordinates captured: ${lat}, ${lon} (±${Math.round(pos.coords.accuracy)}m)`);
      },
      (err) => {
        setIsCapturingGps(false);
        setGpsStatus(`Unable to acquire GPS location: ${err.message}. You can enter coordinates or proceed with village location.`);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
    );
  };

  // Field Management Helpers
  const handleAddField = () => {
    const nextIdx = fields.length + 1;
    const farmAreaNum = parseFloat(totalArea) || 10;
    const allocatedSoFar = fields.reduce((acc, f) => acc + (parseFloat(f.area) || 0), 0);
    const remaining = Math.max(0, farmAreaNum - allocatedSoFar);
    const suggestedArea = remaining > 0 ? remaining.toFixed(1) : '1.0';

    const newField: FieldEntry = {
      id: `field-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      field_name: `Field ${nextIdx}`,
      area: suggestedArea,
      area_unit: areaUnit,
      soil_type: 'Black Cotton (Regur)',
      irrigation_method: 'Drip',
      current_crop: 'Cotton',
      previous_crop: 'Soybean'
    };
    setFields([...fields, newField]);
    setEditingFieldId(newField.id);
  };

  const handleRemoveField = (idToRemove: string) => {
    if (fields.length <= 1) {
      alert('Every farm must have at least one field.');
      return;
    }
    setFields(fields.filter(f => f.id !== idToRemove));
    if (editingFieldId === idToRemove) {
      setEditingFieldId(null);
    }
  };

  const handleUpdateField = (id: string, updates: Partial<FieldEntry>) => {
    setFields(fields.map(f => f.id === id ? { ...f, ...updates } : f));
  };

  // Screen 7: Save & Complete Onboarding Persistence
  const handleSaveAndComplete = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setSubmissionError(null);
    setSubmissionProgress('Validating onboarding data schema...');

    try {
      // 1. Prepare Request Payload
      const areaNum = parseFloat(totalArea);
      const parsedFields = fields.map(f => ({
        field_name: f.field_name.trim(),
        area: parseFloat(f.area) || 1.0,
        area_unit: f.area_unit || areaUnit,
        soil_type: f.soil_type || 'Black Cotton (Regur)',
        irrigation_method: f.irrigation_method || 'Drip',
        current_crop: f.current_crop || 'Cotton',
        previous_crop: f.previous_crop || 'Soybean'
      }));

      const onboardingPayload = {
        farmer_id: user?.id || `farmer-${Date.now()}`,
        name: fullName.trim(),
        phone: phone.trim(),
        state: stateName.trim(),
        district: district.trim(),
        village: village.trim(),
        preferred_language: selectedLanguage,
        farming_experience: farmingExperience,
        farmer_category: farmerCategory,
        farm_name: farmName.trim(),
        total_area: areaNum,
        area_unit: areaUnit,
        latitude: latitude ? parseFloat(latitude) : null,
        longitude: longitude ? parseFloat(longitude) : null,
        irrigation_source: irrigationSource,
        land_ownership: landOwnership,
        fields: parsedFields
      };

      setSubmissionProgress('Connecting to KisanCare Backend API...');
      let backendResult: any = null;

      try {
        backendResult = await api.submitOnboarding(onboardingPayload);
      } catch (apiErr: any) {
        console.warn('Backend /api/v1/onboarding call failed or running in client-direct mode:', apiErr);
      }

      // 2. Direct Supabase Client Synchronization (if user is authenticated)
      if (user && isAuthenticated && !isDemoUser) {
        setSubmissionProgress('Persisting profile & farm to Supabase PostgreSQL database...');
        try {
          // A. Profile
          await supabase.from('profiles').upsert({
            user_id: user.id,
            name: fullName.trim(),
            phone: phone.trim(),
            state: stateName.trim(),
            district: district.trim(),
            village: village.trim(),
            preferred_language: selectedLanguage,
            farming_experience: farmingExperience,
            farmer_category: farmerCategory,
            role: 'farmer'
          }, { onConflict: 'user_id' });

          // B. Farm
          const farmLocation = `${village.trim()}, ${district.trim()}, ${stateName.trim()}`;
          const { data: createdFarm, error: farmErr } = await supabase.from('farms').insert({
            user_id: user.id,
            farm_name: farmName.trim(),
            location: farmLocation,
            total_area: areaNum,
            area_unit: areaUnit,
            land_ownership: landOwnership,
            latitude: latitude ? parseFloat(latitude) : null,
            longitude: longitude ? parseFloat(longitude) : null,
            status: 'ACTIVE'
          }).select().single();

          if (!farmErr && createdFarm) {
            const activeFarmId = createdFarm.id;
            localStorage.setItem('kisancare_active_farm_id', activeFarmId);

            // C. Fields & Seasons
            for (const f of parsedFields) {
              const { data: createdField } = await supabase.from('fields').insert({
                farm_id: activeFarmId,
                field_name: f.field_name,
                area: f.area,
                area_unit: f.area_unit,
                soil_description: f.soil_type,
                status: 'ACTIVE'
              }).select().single();

              if (createdField) {
                await supabase.from('seasons').insert({
                  field_id: createdField.id,
                  season_name: 'Kharif 2024',
                  crop: f.current_crop,
                  previous_crop: f.previous_crop,
                  status: 'ACTIVE'
                });
              }
            }
          }
        } catch (dbErr: any) {
          console.warn('Direct Supabase write warning:', dbErr);
        }
      }

      // 3. Set Active Session Metadata
      const savedFarmId = backendResult?.farm_id || localStorage.getItem('kisancare_active_farm_id') || `farm-${Date.now()}`;
      localStorage.setItem('kisancare_active_farm_id', savedFarmId);
      localStorage.setItem('kisancare_farmer_name', fullName.trim());
      localStorage.setItem('kisancare_farm_name', farmName.trim());
      localStorage.setItem('kisancare_farm_location', `${village.trim()}, ${district.trim()}`);
      localStorage.setItem('kisancare_farm_area', `${totalArea} ${areaUnit}`);

      // Clear draft since onboarding succeeded
      localStorage.removeItem(STORAGE_DRAFT_KEY);

      setSubmissionProgress(null);
      setSubmissionSuccess({
        farm_id: savedFarmId,
        farm_name: farmName.trim(),
        farmer_name: fullName.trim(),
        total_area: `${totalArea} ${areaUnit}`,
        fields_count: fields.length,
        is_mock: backendResult?.is_mock ?? (!isAuthenticated)
      });
      setIsSubmitting(false);
    } catch (err: any) {
      setIsSubmitting(false);
      setSubmissionProgress(null);
      setSubmissionError(err.message || 'Failed to complete farmer onboarding. Please check connection and retry.');
    }
  };

  const handleFinishToDashboard = () => {
    if (onComplete) {
      onComplete();
    } else {
      navigate('/');
    }
  };

  // Total allocated area calculation
  const totalAllocated = fields.reduce((sum, f) => sum + (parseFloat(f.area) || 0), 0);
  const farmAreaNumber = parseFloat(totalArea) || 0;
  const isAreaExceeded = farmAreaNumber > 0 && totalAllocated > farmAreaNumber;

  // Step Labels for Header Progress Bar
  const stepTitles = [
    'Welcome',
    'Authentication',
    'Farmer Profile',
    'Farm Setup',
    'Field Setup',
    'Review Summary',
    'Complete'
  ];

  return (
    <div className="min-h-screen bg-[#FBF7EF] flex flex-col justify-between text-[#292B26] font-sans">
      
      {/* TOP HEADER & STEPPER */}
      <header className="bg-white border-b border-[#E5DDCF] sticky top-0 z-30 shadow-xs">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          
          {/* Logo Treatment */}
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => goToStep(1)}>
            <div className="w-9 h-9 rounded-xl bg-[#103D2C] flex items-center justify-center text-white shadow-xs">
              <Sprout className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <span className="text-xl font-bold font-serif tracking-tight text-[#103D2C]">
                KISAN<span className="text-[#B6532A] font-normal">care</span>
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-semibold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                Farmer Onboarding
              </span>
            </div>
          </div>

          {/* Language Quick Selector */}
          <div className="flex items-center gap-1.5 bg-[#FBF7EF] p-1 rounded-xl border border-[#E5DDCF]">
            {(['en', 'hi', 'mr'] as const).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => handleLanguageChange(lang)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-all ${
                  selectedLanguage === lang
                    ? 'bg-[#103D2C] text-white shadow-2xs'
                    : 'text-[#292B26]/70 hover:text-[#103D2C] hover:bg-white'
                }`}
              >
                {lang === 'en' ? 'EN' : lang === 'hi' ? 'हिंदी' : 'मराठी'}
              </button>
            ))}
          </div>
        </div>

        {/* Step Progress Bar */}
        <div className="max-w-4xl mx-auto px-4 pb-2.5 pt-1">
          <div className="flex items-center justify-between mb-1.5 text-xs">
            <span className="font-semibold text-emerald-900">
              Step {currentStep} of 7: <span className="font-bold text-[#103D2C]">{stepTitles[currentStep - 1]}</span>
            </span>
            <span className="text-[11px] text-[#292B26]/60 font-medium">
              {Math.round((currentStep / 7) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-[#E5DDCF] h-2 rounded-full overflow-hidden">
            <div
              className="bg-[#103D2C] h-full transition-all duration-300 rounded-full"
              style={{ width: `${(currentStep / 7) * 100}%` }}
            />
          </div>
        </div>
      </header>

      {/* MAIN ONBOARDING CONTENT CONTAINER */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-6">

        {/* =================================================================== */}
        {/* SCREEN 1 — WELCOME                                                 */}
        {/* =================================================================== */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Hero Card */}
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-50 rounded-full -mr-16 -mt-16 -z-0 opacity-70 pointer-events-none" />
              
              <div className="relative z-10">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-4">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Maharashtra Digital Agriculture Initiative</span>
                </div>

                <h1 className="text-3xl sm:text-4xl font-serif font-extrabold text-[#103D2C] leading-tight mb-3">
                  Welcome to <span className="text-[#B6532A]">KISANcare</span>
                </h1>
                <p className="text-base sm:text-lg text-[#292B26]/80 leading-relaxed max-w-2xl">
                  Your personalized farming copilot. Connect your land, get real-time crop recommendations, track mandi prices, detect leaf diseases, and rent certified farm machinery.
                </p>

                {/* Cultural Marathi/Hindi welcoming note */}
                <div className="mt-4 p-3.5 rounded-2xl bg-[#FBF7EF] border border-[#E5DDCF] flex items-center gap-3">
                  <Leaf className="w-5 h-5 text-emerald-700 shrink-0" />
                  <p className="text-xs text-emerald-900 font-serif italic">
                    "मातीशी नाते, उद्याच्या समृद्धीसाठी" &bull; किसान की उन्नति, देश की प्रगति
                  </p>
                </div>
              </div>
            </div>

            {/* Value Propositions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                {
                  icon: Sprout,
                  title: 'Smart Crop Recommendation',
                  desc: 'Machine learning advisory tailored to your soil fertility, water source, and district climate.'
                },
                {
                  icon: TrendingUp,
                  title: 'Mandi Price Forecasts',
                  desc: 'Real-time Agmarknet arrivals and 7-day predictive pricing for Cotton, Soybean, and Tur.'
                },
                {
                  icon: Bug,
                  title: 'Disease & Pest Detection',
                  desc: 'Early symptom diagnosis and zero-chemical integrated pest management (IPM) guidance.'
                },
                {
                  icon: Tractor,
                  title: 'Farm Equipment Rental',
                  desc: 'Rent harvesters, rotavators, and tractors from verified Custom Hiring Centers in Maharashtra.'
                }
              ].map((feat, idx) => {
                const Icon = feat.icon;
                return (
                  <div key={idx} className="bg-white p-5 rounded-2xl border border-[#E5DDCF] shadow-2xs flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-[#103D2C] shrink-0">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#103D2C]">{feat.title}</h3>
                      <p className="text-xs text-[#292B26]/70 mt-1 leading-normal">{feat.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Primary Action Buttons */}
            <div className="bg-white p-6 rounded-2xl border border-[#E5DDCF] space-y-3 shadow-sm">
              <button
                type="button"
                onClick={() => goToStep(2)}
                className="w-full py-4 px-6 rounded-xl bg-[#103D2C] hover:bg-[#164B35] text-white text-base font-bold shadow-md shadow-emerald-950/20 flex items-center justify-center gap-2 cursor-pointer transition-all active:scale-[0.99]"
              >
                <span>Get Started — Onboard My Farm</span>
                <ArrowRight className="w-5 h-5" />
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthMode('signin');
                  goToStep(2);
                }}
                className="w-full py-3.5 px-6 rounded-xl bg-white hover:bg-[#F2E8D5] text-[#103D2C] border border-[#E5DDCF] text-sm font-bold flex items-center justify-center gap-2 cursor-pointer transition-all"
              >
                <span>Already have a KisanCare account? Sign In</span>
              </button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* SCREEN 2 — ACCOUNT AND AUTHENTICATION                               */}
        {/* =================================================================== */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm">
              
              {/* Header */}
              <div className="mb-6">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-2">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Secure Farmer Authentication</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C]">
                  {authMode === 'signup' ? 'Create Your KisanCare Account' : 'Sign In to Your Account'}
                </h2>
                <p className="text-sm text-[#292B26]/70 mt-1">
                  {authMode === 'signup'
                    ? 'Register your account to securely save and access your farm records across devices.'
                    : 'Enter your credentials to resume your verified farming dashboard.'}
                </p>
              </div>

              {/* Mode Toggle Tabs */}
              <div className="flex border border-[#E5DDCF] p-1 rounded-xl bg-[#FBF7EF] mb-6">
                <button
                  type="button"
                  onClick={() => { setAuthMode('signup'); setAuthError(null); }}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                    authMode === 'signup' ? 'bg-[#103D2C] text-white shadow-2xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                  }`}
                >
                  Create New Account
                </button>
                <button
                  type="button"
                  onClick={() => { setAuthMode('signin'); setAuthError(null); }}
                  className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                    authMode === 'signin' ? 'bg-[#103D2C] text-white shadow-2xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                  }`}
                >
                  Sign In Existing
                </button>
              </div>

              {/* Error Banner */}
              {authError && (
                <div className="mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Authentication Notice:</span> {authError}
                  </div>
                </div>
              )}

              {/* Success Banner */}
              {authSuccess && (
                <div className="mb-5 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold">{authSuccess}</span>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleAuthSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Email Address <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="w-5 h-5 text-[#292B26]/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="e.g. ramesh.patil@example.com"
                      className={`w-full pl-11 pr-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                        fieldErrors.email ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                      }`}
                      required
                    />
                  </div>
                  {fieldErrors.email && (
                    <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                      <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.email}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Password (Min 6 Characters) <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="w-5 h-5 text-[#292B26]/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter a secure password"
                      className={`w-full pl-11 pr-11 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                        fieldErrors.password ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                      }`}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#292B26]/40 hover:text-[#103D2C]"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {fieldErrors.password && (
                    <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                      <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.password}
                    </p>
                  )}
                </div>

                {authMode === 'signup' && (
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                      Confirm Password <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Lock className="w-5 h-5 text-[#292B26]/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Re-enter password to confirm"
                        className={`w-full pl-11 pr-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                          fieldErrors.confirmPassword ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                        }`}
                        required
                      />
                    </div>
                    {fieldErrors.confirmPassword && (
                      <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                        <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.confirmPassword}
                      </p>
                    )}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full mt-2 py-3.5 px-6 rounded-xl bg-[#103D2C] hover:bg-[#164B35] text-white text-sm font-bold shadow-md shadow-emerald-950/20 flex items-center justify-center gap-2 cursor-pointer transition-all disabled:opacity-50"
                >
                  {authLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>{authMode === 'signup' ? 'Creating Account...' : 'Signing In...'}</span>
                    </>
                  ) : (
                    <>
                      <span>{authMode === 'signup' ? 'Create Account & Continue' : 'Sign In & Continue'}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Demo Mode / Offline Option */}
              <div className="mt-6 pt-5 border-t border-[#E5DDCF] text-center">
                <p className="text-xs text-[#292B26]/60 mb-2">
                  Testing on phone without live Supabase credentials?
                </p>
                <button
                  type="button"
                  onClick={handleDemoBypass}
                  className="py-2.5 px-4 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold transition-all flex items-center justify-center gap-2 mx-auto cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-700" />
                  <span>Continue in Demonstration Mode (No Auth Required)</span>
                </button>
              </div>

            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* SCREEN 3 — FARMER PROFILE                                          */}
        {/* =================================================================== */}
        {currentStep === 3 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm">
              
              <div className="mb-6">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-2">
                  <User className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Farmer Identity & Details</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C]">
                  Personal Profile
                </h2>
                <p className="text-sm text-[#292B26]/70 mt-1">
                  Tell us who you are so your agricultural reports and advisory can be addressed accurately.
                </p>
              </div>

              <div className="space-y-4">
                {/* Full Name */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Farmer Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Ramesh Patil"
                    className={`w-full px-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                      fieldErrors.fullName ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                    }`}
                  />
                  {fieldErrors.fullName && (
                    <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                      <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.fullName}
                    </p>
                  )}
                </div>

                {/* Phone Number */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Mobile Phone Number <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Phone className="w-5 h-5 text-[#292B26]/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="e.g. 9876543210"
                      className={`w-full pl-11 pr-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                        fieldErrors.phone ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                      }`}
                    />
                  </div>
                  {fieldErrors.phone && (
                    <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                      <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.phone}
                    </p>
                  )}
                </div>

                {/* State & District Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                      State <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={stateName}
                      onChange={(e) => setStateName(e.target.value)}
                      className="w-full px-4 py-3 bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-sm outline-none focus:bg-white focus:border-[#103D2C]"
                    >
                      <option value="Maharashtra">Maharashtra</option>
                      <option value="Gujarat">Gujarat</option>
                      <option value="Madhya Pradesh">Madhya Pradesh</option>
                      <option value="Karnataka">Karnataka</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                      District <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={district}
                      onChange={(e) => setDistrict(e.target.value)}
                      className={`w-full px-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                        fieldErrors.district ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                      }`}
                    >
                      {MAHARASHTRA_DISTRICTS.map((dist) => (
                        <option key={dist} value={dist}>{dist}</option>
                      ))}
                    </select>
                    {fieldErrors.district && (
                      <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                        <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.district}
                      </p>
                    )}
                  </div>
                </div>

                {/* Village / Locality */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Village / Locality <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <MapPin className="w-5 h-5 text-[#292B26]/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={village}
                      onChange={(e) => setVillage(e.target.value)}
                      placeholder="e.g. Takli Bu or Shirpur"
                      className={`w-full pl-11 pr-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                        fieldErrors.village ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                      }`}
                    />
                  </div>
                  {fieldErrors.village && (
                    <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                      <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.village}
                    </p>
                  )}
                </div>

                {/* Optional Agronomic Background */}
                <div className="pt-3 border-t border-[#E5DDCF]">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#103D2C] block mb-3">
                    Farming Experience & Profile (Optional)
                  </span>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-[#292B26]/70 mb-1">Farming Experience</label>
                      <select
                        value={farmingExperience}
                        onChange={(e) => setFarmingExperience(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-xs outline-none focus:bg-white"
                      >
                        <option value="< 5 years">Less than 5 years</option>
                        <option value="5-15 years">5 to 15 years</option>
                        <option value="15+ years">More than 15 years</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs text-[#292B26]/70 mb-1">Farmer Category</label>
                      <select
                        value={farmerCategory}
                        onChange={(e) => setFarmerCategory(e.target.value)}
                        className="w-full px-3.5 py-2.5 bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-xs outline-none focus:bg-white"
                      >
                        <option value="Marginal (< 1 ha)">Marginal (Less than 1 hectare)</option>
                        <option value="Small (1-2 ha)">Small (1 to 2 hectares)</option>
                        <option value="Medium (2-10 ha)">Medium (2 to 10 hectares)</option>
                        <option value="Large (> 10 ha)">Large (More than 10 hectares)</option>
                      </select>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* SCREEN 4 — FARM SETUP                                              */}
        {/* =================================================================== */}
        {currentStep === 4 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm">
              
              <div className="mb-6">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-2">
                  <Compass className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Farm Property & Boundaries</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C]">
                  Farm Setup
                </h2>
                <p className="text-sm text-[#292B26]/70 mt-1">
                  Configure your primary farm holding, land measurements, and water access.
                </p>
              </div>

              <div className="space-y-4">
                {/* Farm Name */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Farm Name / Identifier <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={farmName}
                    onChange={(e) => setFarmName(e.target.value)}
                    placeholder="e.g. Ramesh Patil Farm or Wavar Gut 142"
                    className={`w-full px-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                      fieldErrors.farmName ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                    }`}
                  />
                  {fieldErrors.farmName && (
                    <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                      <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.farmName}
                    </p>
                  )}
                </div>

                {/* Total Area & Unit Pill Toggle */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                      Total Land Area <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={totalArea}
                      onChange={(e) => setTotalArea(e.target.value)}
                      placeholder="e.g. 10.0"
                      className={`w-full px-4 py-3 bg-[#FBF7EF] border rounded-xl text-sm outline-none focus:bg-white transition-colors ${
                        fieldErrors.totalArea ? 'border-red-400 focus:border-red-600' : 'border-[#E5DDCF] focus:border-[#103D2C]'
                      }`}
                    />
                    {fieldErrors.totalArea && (
                      <p className="text-red-600 text-xs mt-1 flex items-center gap-1 font-medium">
                        <AlertCircle className="w-3.5 h-3.5" /> {fieldErrors.totalArea}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                      Measurement Unit <span className="text-red-500">*</span>
                    </label>
                    <div className="flex border border-[#E5DDCF] p-1 rounded-xl bg-[#FBF7EF] h-[46px] items-center">
                      <button
                        type="button"
                        onClick={() => setAreaUnit('acre')}
                        className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                          areaUnit === 'acre' ? 'bg-[#103D2C] text-white shadow-2xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                        }`}
                      >
                        Acres (एकर)
                      </button>
                      <button
                        type="button"
                        onClick={() => setAreaUnit('hectare')}
                        className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                          areaUnit === 'hectare' ? 'bg-[#103D2C] text-white shadow-2xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
                        }`}
                      >
                        Hectares (हेक्टर)
                      </button>
                    </div>
                  </div>
                </div>

                {/* Irrigation Availability */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Primary Irrigation Source
                  </label>
                  <select
                    value={irrigationSource}
                    onChange={(e) => setIrrigationSource(e.target.value)}
                    className="w-full px-4 py-3 bg-[#FBF7EF] border border-[#E5DDCF] rounded-xl text-sm outline-none focus:bg-white focus:border-[#103D2C]"
                  >
                    <option value="Borewell / Tube Well">Borewell / Tube Well (विहीर / बोअरवेल)</option>
                    <option value="Canal Irrigation">Canal Irrigation (कालवा पाणी)</option>
                    <option value="Drip System">Drip System Installed (ठिबक सिंचन)</option>
                    <option value="Farm Pond / River">Farm Pond / River (शेततळे / नदी)</option>
                    <option value="Rainfed Only">Rainfed Only / Jirayat (कोरडवाहू)</option>
                  </select>
                </div>

                {/* Land Ownership */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#103D2C] mb-1.5">
                    Land Ownership Type
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {['Owned', 'Leased', 'Shared'].map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setLandOwnership(type)}
                        className={`py-2.5 px-3 rounded-xl border text-xs font-semibold transition-all ${
                          landOwnership === type
                            ? 'bg-[#103D2C] text-white border-[#103D2C] shadow-2xs'
                            : 'bg-[#FBF7EF] text-[#292B26]/80 border-[#E5DDCF] hover:bg-white'
                        }`}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>

                {/* GPS Coordinates Section */}
                <div className="p-4 rounded-2xl bg-[#FBF7EF] border border-[#E5DDCF] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#103D2C] flex items-center gap-1.5">
                        <Navigation className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Farm Geolocation (Optional)</span>
                      </h4>
                      <p className="text-[11px] text-[#292B26]/60">
                        Enables precision weather alerts & satellite soil health mapping.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleCaptureGps}
                      disabled={isCapturingGps}
                      className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                    >
                      {isCapturingGps ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Navigation className="w-3.5 h-3.5" />}
                      <span>Capture GPS</span>
                    </button>
                  </div>

                  {gpsStatus && (
                    <p className="text-xs text-emerald-800 bg-white p-2.5 rounded-lg border border-emerald-200">
                      {gpsStatus}
                    </p>
                  )}

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[10px] text-[#292B26]/60 block mb-0.5">Latitude:</span>
                      <input
                        type="text"
                        value={latitude}
                        onChange={(e) => setLatitude(e.target.value)}
                        placeholder="e.g. 20.7002"
                        className="w-full px-3 py-2 bg-white border border-[#E5DDCF] rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-[#292B26]/60 block mb-0.5">Longitude:</span>
                      <input
                        type="text"
                        value={longitude}
                        onChange={(e) => setLongitude(e.target.value)}
                        placeholder="e.g. 77.0082"
                        className="w-full px-3 py-2 bg-white border border-[#E5DDCF] rounded-lg text-xs"
                      />
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* SCREEN 5 — FIELD SETUP                                              */}
        {/* =================================================================== */}
        {currentStep === 5 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm">
              
              <div className="mb-6">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-2">
                  <Leaf className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Parcel & Crop Allocation</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C]">
                  Field Setup
                </h2>
                <p className="text-sm text-[#292B26]/70 mt-1">
                  Divide your farm into one or more fields. Add soil types and crops for each parcel.
                </p>
              </div>

              {/* Area Allocation Tracker Meter */}
              <div className="p-4 rounded-2xl bg-[#FBF7EF] border border-[#E5DDCF] mb-6 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#103D2C]">
                    Total Farm Allocation:
                  </span>
                  <span className={`font-bold ${isAreaExceeded ? 'text-red-600' : 'text-emerald-800'}`}>
                    {totalAllocated.toFixed(1)} of {farmAreaNumber.toFixed(1)} {areaUnit}s
                  </span>
                </div>
                <div className="w-full bg-[#E5DDCF] h-2.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 rounded-full ${
                      isAreaExceeded ? 'bg-red-500' : 'bg-emerald-600'
                    }`}
                    style={{
                      width: `${farmAreaNumber > 0 ? Math.min(100, (totalAllocated / farmAreaNumber) * 100) : 0}%`
                    }}
                  />
                </div>
                {isAreaExceeded && (
                  <p className="text-xs text-red-600 font-medium flex items-center gap-1 mt-1">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    Allocated field area exceeds total farm area ({totalAllocated.toFixed(1)} &gt; {farmAreaNumber} {areaUnit}s). Please adjust field sizes.
                  </p>
                )}
              </div>

              {/* Fields List */}
              <div className="space-y-4">
                {fields.map((field, idx) => {
                  const isEditing = editingFieldId === field.id || editingFieldId === null;
                  return (
                    <div
                      key={field.id}
                      className="rounded-2xl border border-[#E5DDCF] p-4 bg-white shadow-2xs space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-[#103D2C] text-white text-xs font-bold flex items-center justify-center">
                            {idx + 1}
                          </span>
                          <span className="font-bold text-sm text-[#103D2C]">
                            {field.field_name || `Field #${idx + 1}`}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                            {field.area} {field.area_unit}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => setEditingFieldId(isEditing && editingFieldId === field.id ? '' : field.id)}
                            className="p-1.5 text-[#292B26]/60 hover:text-[#103D2C] rounded-lg hover:bg-gray-100"
                            title="Toggle edit details"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          {fields.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveField(field.id)}
                              className="p-1.5 text-red-500 hover:text-red-700 rounded-lg hover:bg-red-50"
                              title="Delete field"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Summary Tags */}
                      <div className="flex flex-wrap gap-2 text-[11px] text-[#292B26]/70">
                        <span className="px-2 py-0.5 rounded-md bg-[#FBF7EF] border border-[#E5DDCF]">
                          Crop: <strong className="text-emerald-800">{field.current_crop || 'Not specified'}</strong>
                        </span>
                        <span className="px-2 py-0.5 rounded-md bg-[#FBF7EF] border border-[#E5DDCF]">
                          Soil: <strong>{field.soil_type || 'Unspecified'}</strong>
                        </span>
                        <span className="px-2 py-0.5 rounded-md bg-[#FBF7EF] border border-[#E5DDCF]">
                          Irrigation: <strong>{field.irrigation_method}</strong>
                        </span>
                      </div>

                      {/* Editable Form Details */}
                      {isEditing && (
                        <div className="pt-3 border-t border-[#E5DDCF] space-y-3 animate-in fade-in duration-200">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="block text-[11px] font-bold text-[#103D2C] mb-1">
                                Field Name <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="text"
                                value={field.field_name}
                                onChange={(e) => handleUpdateField(field.id, { field_name: e.target.value })}
                                placeholder="e.g. North Parcel"
                                className="w-full px-3 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs"
                              />
                            </div>
                            <div>
                              <label className="block text-[11px] font-bold text-[#103D2C] mb-1">
                                Parcel Area ({areaUnit}) <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="number"
                                step="0.1"
                                min="0.1"
                                value={field.area}
                                onChange={(e) => handleUpdateField(field.id, { area: e.target.value })}
                                placeholder="e.g. 5.0"
                                className="w-full px-3 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div>
                              <label className="block text-[11px] text-[#292B26]/70 mb-1">
                                Current / Planned Crop
                              </label>
                              <select
                                value={field.current_crop}
                                onChange={(e) => handleUpdateField(field.id, { current_crop: e.target.value })}
                                className="w-full px-3 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs"
                              >
                                <option value="Cotton">Cotton (कापूस)</option>
                                <option value="Soybean">Soybean (सोयाबीन)</option>
                                <option value="Tur / Red Gram">Tur / Red Gram (तूर)</option>
                                <option value="Wheat">Wheat (गहू)</option>
                                <option value="Gram / Chana">Gram / Chana (हरभरा)</option>
                                <option value="Onion">Onion (कांदा)</option>
                                <option value="Sugarcane">Sugarcane (ऊस)</option>
                                <option value="Other">Other Crop</option>
                              </select>
                            </div>

                            <div>
                              <label className="block text-[11px] text-[#292B26]/70 mb-1">
                                Soil Type (Skippable)
                              </label>
                              <select
                                value={field.soil_type}
                                onChange={(e) => handleUpdateField(field.id, { soil_type: e.target.value })}
                                className="w-full px-3 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs"
                              >
                                <option value="Black Cotton (Regur)">Black Cotton / Regur (काळी माती)</option>
                                <option value="Medium Black Loam">Medium Black Loam (मध्यम काळी)</option>
                                <option value="Red Soil">Red Soil (तांबडी माती)</option>
                                <option value="Sandy Loam">Sandy Loam (वालुकामय)</option>
                                <option value="Clay Loam">Clay Loam (चोपणी)</option>
                                <option value="Alluvial">Alluvial / Riverine</option>
                                <option value="Not Tested / Unknown">Not Tested / Unknown (माहित नाही)</option>
                              </select>
                            </div>

                            <div>
                              <label className="block text-[11px] text-[#292B26]/70 mb-1">
                                Irrigation Method
                              </label>
                              <select
                                value={field.irrigation_method}
                                onChange={(e) => handleUpdateField(field.id, { irrigation_method: e.target.value })}
                                className="w-full px-3 py-2 bg-[#FBF7EF] border border-[#E5DDCF] rounded-lg text-xs"
                              >
                                <option value="Drip">Drip Irrigation (ठिबक)</option>
                                <option value="Sprinkler">Sprinkler (तुषार)</option>
                                <option value="Flood / Furrow">Flood / Furrow (पाट पाणी)</option>
                                <option value="Rainfed">Rainfed (पावसावर)</option>
                              </select>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Add Field Button */}
              <button
                type="button"
                onClick={handleAddField}
                className="mt-4 w-full py-3 px-4 rounded-xl border-2 border-dashed border-emerald-300 hover:border-emerald-500 bg-emerald-50/50 hover:bg-emerald-50 text-emerald-800 text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>+ Add Another Field / Parcel</span>
              </button>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* SCREEN 6 — REVIEW INFORMATION                                       */}
        {/* =================================================================== */}
        {currentStep === 6 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm">
              
              <div className="mb-6">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-2">
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Final Step Before Registration</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C]">
                  Review Information
                </h2>
                <p className="text-sm text-[#292B26]/70 mt-1">
                  Please verify your details. Click "Edit" on any section if changes are needed.
                </p>
              </div>

              <div className="space-y-4">
                {/* 1. Farmer Profile Summary */}
                <div className="p-4 rounded-2xl bg-[#FBF7EF] border border-[#E5DDCF]">
                  <div className="flex items-center justify-between pb-2 border-b border-[#E5DDCF] mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Farmer Profile</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handleEditSection(3)}
                      className="text-xs font-bold text-emerald-800 hover:underline flex items-center gap-1"
                    >
                      <Edit3 className="w-3 h-3" /> Edit
                    </button>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-[#292B26]/60 block">Full Name:</span>
                      <strong className="text-[#103D2C]">{fullName || 'Not specified'}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Mobile Phone:</span>
                      <strong>{phone || 'Not specified'}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Location:</span>
                      <strong>{village}, {district}, {stateName}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Preferred Language:</span>
                      <strong>{selectedLanguage === 'mr' ? 'मराठी' : selectedLanguage === 'hi' ? 'हिंदी' : 'English'}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Experience:</span>
                      <strong>{farmingExperience}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Category:</span>
                      <strong>{farmerCategory}</strong>
                    </div>
                  </div>
                </div>

                {/* 2. Farm Setup Summary */}
                <div className="p-4 rounded-2xl bg-[#FBF7EF] border border-[#E5DDCF]">
                  <div className="flex items-center justify-between pb-2 border-b border-[#E5DDCF] mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                      <Compass className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Farm Properties</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handleEditSection(4)}
                      className="text-xs font-bold text-emerald-800 hover:underline flex items-center gap-1"
                    >
                      <Edit3 className="w-3 h-3" /> Edit
                    </button>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-[#292B26]/60 block">Farm Name:</span>
                      <strong className="text-[#103D2C]">{farmName || 'Unnamed Farm'}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Total Area:</span>
                      <strong className="text-emerald-800">{totalArea} {areaUnit}s</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Ownership:</span>
                      <strong>{landOwnership}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">Irrigation Source:</span>
                      <strong>{irrigationSource}</strong>
                    </div>
                    <div>
                      <span className="text-[#292B26]/60 block">GPS Coordinates:</span>
                      <strong>{latitude && longitude ? `${latitude}, ${longitude}` : 'Not Captured'}</strong>
                    </div>
                  </div>
                </div>

                {/* 3. Fields Summary */}
                <div className="p-4 rounded-2xl bg-[#FBF7EF] border border-[#E5DDCF]">
                  <div className="flex items-center justify-between pb-2 border-b border-[#E5DDCF] mb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#103D2C] flex items-center gap-1.5">
                      <Leaf className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Configured Fields ({fields.length} parcels &bull; {totalAllocated.toFixed(1)} {areaUnit}s)</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => handleEditSection(5)}
                      className="text-xs font-bold text-emerald-800 hover:underline flex items-center gap-1"
                    >
                      <Edit3 className="w-3 h-3" /> Edit
                    </button>
                  </div>
                  <div className="space-y-2">
                    {fields.map((f, i) => (
                      <div key={f.id} className="p-2.5 rounded-xl bg-white border border-[#E5DDCF] flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-[#103D2C] text-white text-[10px] font-bold flex items-center justify-center">
                            {i + 1}
                          </span>
                          <div>
                            <span className="font-bold text-[#103D2C]">{f.field_name}</span>
                            <span className="text-[#292B26]/60 ml-2">({f.area} {f.area_unit})</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-[11px]">
                          <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
                            {f.current_crop}
                          </span>
                          <span className="text-[#292B26]/60 hidden sm:inline">
                            {f.soil_type}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Statutory Farmer Acknowledgement */}
                <div className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200 text-xs text-emerald-900 flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
                  <p>
                    I confirm that the above farm details and landholding figures are accurate. My data remains private and farmer-owned under KisanCare security guidelines.
                  </p>
                </div>

              </div>
            </div>
          </div>
        )}

        {/* =================================================================== */}
        {/* SCREEN 7 — SAVE AND COMPLETE ONBOARDING                             */}
        {/* =================================================================== */}
        {currentStep === 7 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#E5DDCF] shadow-sm text-center">

              {!submissionSuccess ? (
                <div>
                  <div className="w-16 h-16 rounded-3xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-[#103D2C] mx-auto mb-4">
                    {isSubmitting ? (
                      <Loader2 className="w-8 h-8 animate-spin text-emerald-700" />
                    ) : (
                      <Sprout className="w-8 h-8 text-emerald-700" />
                    )}
                  </div>

                  <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#103D2C] mb-2">
                    {isSubmitting ? 'Registering Your Farm...' : 'Ready to Connect Your Farm'}
                  </h2>
                  <p className="text-sm text-[#292B26]/70 max-w-md mx-auto mb-6">
                    {isSubmitting
                      ? submissionProgress || 'Communicating with KisanCare database and ML models...'
                      : 'Click below to finalize your registration and initialize your Digital Farm Twin.'}
                  </p>

                  {/* Submission Error Banner with Retry */}
                  {submissionError && (
                    <div className="mb-6 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs text-left">
                      <div className="flex items-start gap-2.5">
                        <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                        <div>
                          <strong className="block text-sm mb-1">Registration Could Not Complete:</strong>
                          <p>{submissionError}</p>
                          <button
                            type="button"
                            onClick={handleSaveAndComplete}
                            className="mt-3 px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 transition-colors flex items-center gap-1.5 cursor-pointer"
                          >
                            <RefreshCw className="w-3.5 h-3.5" />
                            <span>Retry Submission</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {!isSubmitting && !submissionError && (
                    <button
                      type="button"
                      onClick={handleSaveAndComplete}
                      className="py-4 px-8 rounded-2xl bg-[#103D2C] hover:bg-[#164B35] text-white text-base font-bold shadow-lg shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 mx-auto cursor-pointer"
                    >
                      <Check className="w-5 h-5" />
                      <span>Confirm & Register My Farm</span>
                    </button>
                  )}
                </div>
              ) : (
                /* Confirmed Success State */
                <div className="space-y-6">
                  <div className="w-20 h-20 rounded-full bg-emerald-100 border-4 border-emerald-500/20 flex items-center justify-center text-emerald-700 mx-auto">
                    <CheckCircle2 className="w-10 h-10 text-emerald-600" />
                  </div>

                  <div>
                    <span className="inline-block px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold mb-2">
                      Farm Registration Confirmed &bull; Active
                    </span>
                    <h2 className="text-3xl font-serif font-extrabold text-[#103D2C]">
                      Welcome to KisanCare, {submissionSuccess.farmer_name}!
                    </h2>
                    <p className="text-sm text-[#292B26]/70 mt-2 max-w-lg mx-auto">
                      Your farm <strong className="text-[#103D2C]">"{submissionSuccess.farm_name}"</strong> with {submissionSuccess.fields_count} parcels ({submissionSuccess.total_area}) has been registered in the KisanCare system.
                    </p>
                  </div>

                  {/* Registered Details Pill */}
                  <div className="bg-[#FBF7EF] border border-[#E5DDCF] rounded-2xl p-4 max-w-md mx-auto text-xs space-y-2 text-left">
                    <div className="flex justify-between">
                      <span className="text-[#292B26]/60">Assigned Farm ID:</span>
                      <span className="font-mono font-bold text-[#103D2C]">{submissionSuccess.farm_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#292B26]/60">Location:</span>
                      <span className="font-bold">{village}, {district}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#292B26]/60">Data Persistence:</span>
                      <span className="font-bold text-emerald-700">
                        {submissionSuccess.is_mock ? 'Verified Local Session (Demo Mode)' : 'Database Confirmed'}
                      </span>
                    </div>
                  </div>

                  {/* SCREEN 8 — DASHBOARD NAVIGATION ACTION */}
                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={handleFinishToDashboard}
                      className="w-full max-w-md py-4 px-6 rounded-2xl bg-[#103D2C] hover:bg-[#164B35] text-white text-base font-bold shadow-lg shadow-emerald-950/20 transition-all flex items-center justify-center gap-2 mx-auto cursor-pointer"
                    >
                      <span>Enter Farm Dashboard</span>
                      <ArrowRight className="w-5 h-5" />
                    </button>
                    <p className="text-[11px] text-[#292B26]/50 mt-2">
                      Access Crop Recommendation, Market Prices, Disease AI, and Equipment Rental.
                    </p>
                  </div>
                </div>
              )}

            </div>
          </div>
        )}

      </main>

      {/* STICKY BOTTOM NAVIGATION BAR (for Steps 2 to 6) */}
      {currentStep >= 2 && currentStep <= 6 && (
        <footer className="bg-white border-t border-[#E5DDCF] sticky bottom-0 z-30 py-3 shadow-md">
          <div className="max-w-3xl mx-auto px-4 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleBack}
              className="py-3 px-5 rounded-xl border border-[#E5DDCF] bg-white hover:bg-[#FBF7EF] text-[#292B26] text-xs font-bold flex items-center gap-2 cursor-pointer transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <button
              type="button"
              onClick={handleNext}
              className="flex-1 py-3 px-6 rounded-xl bg-[#103D2C] hover:bg-[#164B35] text-white text-xs font-bold shadow-md shadow-emerald-950/10 flex items-center justify-center gap-2 cursor-pointer transition-all"
            >
              <span>{returnToReview ? 'Save Changes & Review' : currentStep === 6 ? 'Save & Complete' : 'Continue'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </footer>
      )}

    </div>
  );
}
