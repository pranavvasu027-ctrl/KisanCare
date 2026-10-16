import React, { useState, useRef } from 'react';
import {
  Bug, Camera, Upload, ShieldAlert, CheckCircle, Loader2,
  RotateCcw, AlertCircle, ShieldCheck, Sprout, Info, Leaf
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

export default function DiseaseDetection() {
  const [diagnosisMode, setDiagnosisMode] = useState<'disease' | 'pest'>('disease');
  const [crop, setCrop] = useState('Soybean');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>(['Yellow leaves', 'Stunted growth']);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<{
    condition: string;
    scientificName?: string;
    confidence: number;
    severity: 'Low' | 'Medium' | 'High';
    description?: string;
    treatment: string;
    preventiveManagement: string[];
    nonChemicalOptions: string[];
    modelType?: string;
  } | null>(null);

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
      const url = URL.createObjectURL(file);
      setSelectedImage(url);
      runDiagnosis();
    }
  };

  const runDiagnosis = async () => {
    setErrorMessage(null);

    if (selectedSymptoms.length === 0) {
      setErrorMessage('Please select at least one observed symptom or field damage indicator before running diagnosis.');
      setResult(null);
      return;
    }

    setAnalyzing(true);
    try {
      let response: any;
      if (diagnosisMode === 'pest') {
        response = await api.detectPest(crop, selectedSymptoms);
      } else {
        response = await api.detectDisease(crop, selectedSymptoms);
      }

      const data = response.data;
      setIsDemo(response.isDemo);

      const conditionName = data.prediction || (diagnosisMode === 'pest' ? 'Insect Pest' : 'Pathological Condition');

      // Map scientific names accurately based on condition rather than generic combined strings
      const getScientificTaxonomy = (cond: string, cropName: string): string => {
        const lower = cond.toLowerCase();
        if (lower.includes('powdery mildew')) return 'Podosphaera xanthii / Erysiphe diffusa';
        if (lower.includes('nitrogen') || lower.includes('root rot')) return 'Abiotic N-Chlorosis / Fusarium spp. / Rhizoctonia solani';
        if (lower.includes('leaf spot')) return 'Cercospora sojina (Frogeye) / Septoria glycines';
        if (lower.includes('rust')) return 'Phakopsora pachyrhizi (Asian Soybean Rust)';
        if (lower.includes('caterpillar') || lower.includes('beetle')) return 'Spodoptera litura (Tobacco cutworm) / Chrysodeixis acuta';
        if (lower.includes('aphid')) return cropName === 'Cotton' ? 'Aphis gossypii (Cotton aphid)' : 'Aphis glycines (Soybean aphid)';
        if (lower.includes('healthy') || lower.includes('no major pest')) return 'No active foliar pathogen detected';
        return `${cropName} foliar pathology classification`;
      };

      // Structured Preventive & Non-Chemical Guidance
      const preventiveList = [
        'Maintain recommended inter-row and plant spacing to facilitate sunlight penetration and canopy aeration.',
        'Adopt deep summer plowing to expose resting pupae and fungal sclerotia to solar heat.',
        'Rotate with non-host cereal or pulse crops to break pathogen/pest life cycles.',
        'Eradicate volunteer host weeds on field bunds and drainage perimeters.'
      ];

      const nonChemicalList = diagnosisMode === 'pest'
        ? [
            'Install yellow sticky traps (15–20 per acre) for sucking pests or pheromone traps for pod borers.',
            'Spray cold-pressed Neem seed kernel extract (NSKE 5%) or Azadirachtin 1500 ppm at first sign of infestation.',
            'Encourage natural biological predators including ladybird beetles, hoverflies, and Chrysoperla.'
          ]
        : [
            'Apply bio-fungicides such as Trichoderma viride or Pseudomonas fluorescens as seed/soil treatment.',
            'Remove and safely destroy heavily infected lower leaves to restrict spore dispersal.',
            'Avoid excessive evening sprinkler irrigation that leaves leaf surface wet overnight.'
          ];

      setResult({
        condition: conditionName,
        scientificName: getScientificTaxonomy(conditionName, crop),
        confidence: Math.round((data.confidence ?? 0.85) * 100),
        severity: (data.confidence ?? 0.85) > 0.8 ? 'High' : 'Medium',
        description: `Evaluated using ${data.model_type || 'diagnostic rules'} based on symptoms (${selectedSymptoms.join(', ')}) recorded for ${crop}.`,
        treatment: data.treatment || 'Consult local agricultural extension officer.',
        preventiveManagement: preventiveList,
        nonChemicalOptions: nonChemicalList,
        modelType: data.model_type || (diagnosisMode === 'pest' ? 'Rule-based Pest Model' : 'Rule-based Disease Model')
      });
    } catch (err: any) {
      console.error('Diagnosis failed:', err);
      setErrorMessage(`Diagnosis failed: ${err.message || String(err)}`);
      setResult(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleLoadSample = () => {
    setSelectedImage('https://images.unsplash.com/photo-1599940824399-b87987ceb72a?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80');
    runDiagnosis();
  };

  const handleReset = () => {
    setSelectedImage(null);
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
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Disease & Pest Detection</h1>
          {isDemo ? (
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
              Demo / Mock Mode
            </span>
          ) : (
            <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
              Rule-Based Expert Engine
            </span>
          )}
        </div>
        <p className="text-[#292B26]/70 mt-2 text-sm">
          Diagnose crop pathogens, foliar diseases, and insect pests with integrated preventive management and biological controls.
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
            <span className="text-xs font-bold text-[#103D2C] uppercase tracking-wider">Diagnostic Mode:</span>
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
                Foliar Disease
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
                Insect Pest
              </button>
            </div>
          </div>
          <span className="text-[11px] text-[#292B26]/60">
            {diagnosisMode === 'disease' ? 'Foliar pathogens & fungal spots' : 'Chewing & sucking pest damage'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">Affected Crop</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 text-sm bg-[#FBF7EF] font-medium text-[#103D2C]"
            >
              <option value="Soybean">Soybean</option>
              <option value="Cotton">Cotton</option>
              <option value="Wheat">Wheat</option>
              <option value="Rice">Rice</option>
              <option value="Tomato">Tomato</option>
              <option value="Onion">Onion</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={runDiagnosis}
              disabled={analyzing}
              className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 shadow-xs"
            >
              {analyzing ? <Loader2 size={16} className="animate-spin" /> : <Bug size={16} />}
              <span>{analyzing ? 'Analyzing Diagnosis...' : `Run ${diagnosisMode === 'pest' ? 'Pest' : 'Disease'} Diagnosis`}</span>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">
            Observed Symptoms / Field Signs
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
                  {active ? `✓ ${sym}` : `+ ${sym}`}
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
        accept="image/*"
        className="hidden"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left: Upload Area */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 text-center border-dashed border-2 flex flex-col items-center justify-center min-h-[340px]">
          {selectedImage ? (
            <div className="space-y-3 w-full">
              <div className="relative w-full h-52 rounded-xl overflow-hidden border border-[#E5DDCF] bg-black/5">
                <img
                  src={selectedImage}
                  alt="Uploaded leaf"
                  className="w-full h-full object-cover"
                />
                {analyzing && (
                  <div className="absolute inset-0 bg-[#103D2C]/60 backdrop-blur-xs flex flex-col items-center justify-center text-white">
                    <Loader2 className="w-8 h-8 animate-spin mb-2" />
                    <span className="text-xs font-bold uppercase tracking-wider">Evaluating clinical rules...</span>
                  </div>
                )}
              </div>
              <div className="text-[11px] text-[#292B26]/70 bg-[#FBF7EF] p-2 rounded-lg border border-[#E5DDCF] flex items-center justify-center gap-1.5">
                <Info size={13} className="text-[#17643E] shrink-0" />
                <span>Visual field record attached. Diagnosis evaluates selected clinical symptoms.</span>
              </div>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs bg-[#FBF7EF] border border-[#E5DDCF] text-[#103D2C] px-3 py-1.5 rounded-lg hover:bg-[#E5DDCF] cursor-pointer"
                >
                  Change Image
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
            <div className="py-6 flex flex-col items-center justify-center max-w-sm">
              <Upload className="w-10 h-10 text-[#A8C69A] mb-3" />
              <h3 className="font-bold text-[#103D2C] mb-1">Field Reference Photo</h3>
              <p className="text-[11px] text-[#292B26]/60 mb-4 leading-relaxed">
                Attach a field leaf photo as a visual record. Note: Computer vision image classification is not active on this backend; diagnosis evaluates selected clinical symptoms via the rule-based expert engine.
              </p>
              <div className="flex flex-wrap justify-center gap-3 mb-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF] px-4 py-2 rounded-lg font-medium hover:bg-[#E5DDCF] flex items-center gap-2 cursor-pointer text-xs"
                >
                  Browse Files
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E] flex items-center gap-2 cursor-pointer text-xs"
                >
                  <Camera size={16} /> Take Photo
                </button>
              </div>
              <button
                onClick={handleLoadSample}
                className="text-xs text-[#17643E] hover:underline font-semibold cursor-pointer"
              >
                Or test with sample leaf photo
              </button>
            </div>
          )}
        </div>

        {/* Right: Diagnosis Result */}
        <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#E5DDCF] p-6 flex flex-col justify-center min-h-[340px]">
          {analyzing ? (
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mx-auto mb-3" />
              <h4 className="font-bold text-[#103D2C]">Analyzing Clinical Signs</h4>
              <p className="text-xs text-[#292B26]/60 mt-1">Cross-referencing crop pathology rules...</p>
            </div>
          ) : result ? (
            <div className="space-y-4">
              <div className="bg-white p-5 rounded-xl border border-[#E5DDCF] shadow-xs space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-xl text-[#B6532A]">{result.condition}</h4>
                    {result.scientificName && <p className="text-xs italic text-[#292B26]/60">{result.scientificName}</p>}
                  </div>
                  <div className="text-right">
                    <span className="bg-[#17643E]/10 text-[#17643E] text-xs font-bold px-2.5 py-1 rounded-full border border-[#17643E]/20 inline-block">
                      Rule Match Score: {result.confidence}%
                    </span>
                    <span className="text-[10px] text-[#292B26]/50 block mt-0.5">
                      Symptom matrix alignment (heuristic)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-orange-100 text-orange-800 px-2 py-0.5 rounded">
                    Severity: {result.severity}
                  </span>
                  {result.modelType && (
                    <span className="text-[10px] font-medium text-[#292B26]/60">
                      Engine: {result.modelType}
                    </span>
                  )}
                </div>

                {result.description && (
                  <p className="text-xs text-[#292B26]/75 leading-relaxed">
                    {result.description}
                  </p>
                )}

                {/* Treatment from Model */}
                <div className="pt-2 border-t border-[#E5DDCF]/60">
                  <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <CheckCircle size={14} className="text-[#17643E]" /> Direct Clinical Protocol
                  </h5>
                  <div className="bg-[#FBF7EF] p-3 rounded-lg border border-[#E5DDCF] text-xs text-[#292B26]">
                    {result.treatment}
                  </div>
                </div>

                {/* Non-Chemical Management Options */}
                <div className="pt-2 border-t border-[#E5DDCF]/60 space-y-1.5">
                  <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider flex items-center gap-1.5">
                    <Leaf size={14} className="text-[#17643E]" /> Non-Chemical & Biological Controls
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
                    <ShieldCheck size={14} className="text-[#17643E]" /> Preventive Field Practices
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
                    <span className="font-bold block">Economic Threshold Level (ETL) & Diagnostic Disclaimer:</span>
                    <p className="leading-relaxed">
                      Diagnoses are evaluated by a rule-based expert symptom matcher. Match scores reflect clinical symptom matrix alignment, not a calibrated Bayesian probability. Verify severe pathogen outbreaks with a certified plant pathologist or Krishi Vigyan Kendra (KVK) officer before applying chemical interventions.
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
                Select your symptoms above or upload a leaf photo to trigger real-time crop disease or insect pest analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
