import React from 'react';
import { Bug, Camera, Upload, ShieldAlert, CheckCircle } from 'lucide-react';

export default function DiseaseDetection() {
  return (
    <div className="p-4 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="text-center max-w-2xl mx-auto mb-8">
        <div className="w-16 h-16 bg-[#17643E]/10 text-[#17643E] rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Bug size={32} />
        </div>
        <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Disease & Pest Detection</h1>
        <p className="text-[#292B26]/70 mt-2">Upload a photo of an affected leaf to identify the disease and get treatment recommendations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 text-center border-dashed border-2">
          <div className="py-12 flex flex-col items-center justify-center">
            <Upload className="w-12 h-12 text-[#A8C69A] mb-4" />
            <h3 className="font-bold text-[#103D2C] mb-1">Upload Image</h3>
            <p className="text-xs text-[#292B26]/50 mb-6">JPG, PNG up to 10MB</p>
            <div className="flex gap-4">
              <button className="bg-[#FBF7EF] text-[#103D2C] border border-[#E5DDCF] px-4 py-2 rounded-lg font-medium hover:bg-[#E5DDCF] flex items-center gap-2">
                Browse Files
              </button>
              <button className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E] flex items-center gap-2">
                <Camera size={18} /> Take Photo
              </button>
            </div>
          </div>
        </div>

        <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#E5DDCF] p-6 flex flex-col justify-center">
          <h3 className="font-bold text-[#103D2C] mb-4 flex items-center gap-2">
            <ShieldAlert className="text-[#B6532A]" /> Example Result
          </h3>
          <div className="bg-white p-4 rounded-xl border border-[#E5DDCF]">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-bold text-lg text-[#B6532A]">Soybean Rust</h4>
              <span className="bg-[#17643E]/10 text-[#17643E] text-xs font-bold px-2 py-1 rounded">94% Match</span>
            </div>
            <p className="text-sm text-[#292B26]/70 mb-4">A fungal disease causing tan to dark brown lesions on leaves, leading to premature defoliation.</p>
            
            <h5 className="text-xs font-bold text-[#103D2C] uppercase tracking-wider mb-2">Recommended Action</h5>
            <ul className="text-sm text-[#292B26]/80 space-y-2">
              <li className="flex gap-2"><CheckCircle size={16} className="text-[#17643E] shrink-0" /> Apply appropriate fungicide (e.g., Tebuconazole)</li>
              <li className="flex gap-2"><CheckCircle size={16} className="text-[#17643E] shrink-0" /> Ensure good canopy ventilation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
