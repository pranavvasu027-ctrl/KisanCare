import React, { useState, useRef } from 'react';
import { Bug, Camera, Upload, ShieldAlert, CheckCircle, Loader2, RotateCcw, AlertTriangle } from 'lucide-react';

export default function DiseaseDetection() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<{
    disease: string;
    scientificName: string;
    confidence: number;
    severity: 'Low' | 'Medium' | 'High';
    description: string;
    actions: string[];
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setSelectedImage(url);
      runDiagnosis();
    }
  };

  const runDiagnosis = () => {
    setAnalyzing(true);
    setResult(null);
    setTimeout(() => {
      setResult({
        disease: 'Soybean Rust',
        scientificName: 'Phakopsora pachyrhizi',
        confidence: 94,
        severity: 'Medium',
        description: 'A fungal disease causing tan to dark brown polygonal lesions on leaves, leading to premature defoliation and severe pod fill reduction.',
        actions: [
          'Apply triazole or strobilurin-based fungicide (e.g., Tebuconazole 25.9% EC @ 1ml/L).',
          'Ensure adequate plant spacing to facilitate airflow and canopy drying.',
          'Avoid overhead sprinkler irrigation during warm, humid conditions.',
          'Schedule a follow-up inspection in 7 days to assess spore containment.'
        ]
      });
      setAnalyzing(false);
    }, 1200);
  };

  const handleLoadSample = () => {
    setSelectedImage('https://images.unsplash.com/photo-1599940824399-b87987ceb72a?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80');
    runDiagnosis();
  };

  const handleReset = () => {
    setSelectedImage(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="text-center max-w-2xl mx-auto mb-6">
        <div className="w-16 h-16 bg-[#17643E]/10 text-[#17643E] rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Bug size={32} />
        </div>
        <div className="flex items-center justify-center gap-2">
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Disease & Pest Detection</h1>
          <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
            Sample Vision Model
          </span>
        </div>
        <p className="text-[#292B26]/70 mt-2">
          Upload or capture a photo of an affected leaf to identify symptoms and get treatment recommendations.
        </p>
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
            <div className="space-y-4 w-full">
              <div className="relative w-full h-56 rounded-xl overflow-hidden border border-[#E5DDCF] bg-black/5">
                <img
                  src={selectedImage}
                  alt="Uploaded leaf"
                  className="w-full h-full object-cover"
                />
                {analyzing && (
                  <div className="absolute inset-0 bg-[#103D2C]/60 backdrop-blur-xs flex flex-col items-center justify-center text-white">
                    <Loader2 className="w-8 h-8 animate-spin mb-2" />
                    <span className="text-xs font-bold uppercase tracking-wider">Analyzing leaf patterns...</span>
                  </div>
                )}
              </div>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs bg-[#FBF7EF] border border-[#E5DDCF] text-[#103D2C] px-3 py-1.5 rounded-lg hover:bg-[#E5DDCF]"
                >
                  Change Image
                </button>
                <button
                  onClick={handleReset}
                  className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1 py-1.5"
                >
                  <RotateCcw size={14} /> Clear
                </button>
              </div>
            </div>
          ) : (
            <div className="py-8 flex flex-col items-center justify-center">
              <Upload className="w-12 h-12 text-[#A8C69A] mb-4" />
              <h3 className="font-bold text-[#103D2C] mb-1">Upload Leaf Photo</h3>
              <p className="text-xs text-[#292B26]/50 mb-6">Supports JPG, PNG up to 10MB</p>
              <div className="flex flex-wrap justify-center gap-3 mb-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF] px-4 py-2 rounded-lg font-medium hover:bg-[#E5DDCF] flex items-center gap-2 cursor-pointer"
                >
                  Browse Files
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E] flex items-center gap-2 cursor-pointer"
                >
                  <Camera size={18} /> Take Photo
                </button>
              </div>
              <button
                onClick={handleLoadSample}
                className="text-xs text-[#17643E] hover:underline font-semibold"
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
              <h4 className="font-bold text-[#103D2C]">Analyzing Disease Features</h4>
              <p className="text-xs text-[#292B26]/60 mt-1">Cross-referencing crop pathology database...</p>
            </div>
          ) : result ? (
            <div className="space-y-4">
              <div className="bg-white p-5 rounded-xl border border-[#E5DDCF] shadow-xs">
                <div className="flex justify-between items-start mb-1">
                  <div>
                    <h4 className="font-bold text-xl text-[#B6532A]">{result.disease}</h4>
                    <p className="text-xs italic text-[#292B26]/60">{result.scientificName}</p>
                  </div>
                  <span className="bg-[#17643E]/10 text-[#17643E] text-xs font-bold px-2.5 py-1 rounded-full border border-[#17643E]/20">
                    {result.confidence}% Match
                  </span>
                </div>
                <div className="my-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider bg-orange-100 text-orange-800 px-2 py-0.5 rounded">
                    Severity: {result.severity}
                  </span>
                </div>
                <p className="text-xs text-[#292B26]/75 leading-relaxed mb-4">
                  {result.description}
                </p>

                <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <CheckCircle size={14} className="text-[#17643E]" /> Recommended Action Plan
                </h5>
                <ul className="text-xs text-[#292B26]/80 space-y-2">
                  {result.actions.map((act, i) => (
                    <li key={i} className="flex gap-2 items-start">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#17643E] mt-1.5 shrink-0"></span>
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="bg-white p-6 rounded-xl border border-[#E5DDCF] text-center">
              <ShieldAlert className="w-10 h-10 text-[#A8C69A] mx-auto mb-3" />
              <h4 className="font-bold text-[#103D2C] mb-1">Awaiting Leaf Inspection</h4>
              <p className="text-xs text-[#292B26]/60">
                Upload or capture a leaf photo on the left to see instant diagnostic classification and treatment guidance.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
