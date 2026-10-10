import React from 'react';
import { TestTube, Upload, MapPin, Activity, Check, AlertTriangle } from 'lucide-react';

export default function SoilIntelligence() {
  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Soil Intelligence</h1>
          <p className="text-[#292B26]/70 mt-1">Manage soil health reports and nutrient guidance.</p>
        </div>
        <button className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E] flex items-center gap-2">
          <Upload size={18} /> Upload Report
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-[#103D2C] flex items-center gap-2"><TestTube className="text-[#17643E]"/> Nutrient Profile</h3>
              <span className="text-xs font-semibold bg-[#FBF7EF] px-2 py-1 rounded text-[#292B26]/60">Field 1 (Black Cotton)</span>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="border border-[#E5DDCF] rounded-xl p-4 text-center">
                <div className="text-xs text-[#292B26]/60 mb-1">Nitrogen (N)</div>
                <div className="text-2xl font-bold text-[#103D2C]">Low</div>
                <div className="w-full bg-[#F2E8D5] h-1.5 rounded-full mt-2"><div className="bg-[#B6532A] h-1.5 rounded-full w-1/4"></div></div>
              </div>
              <div className="border border-[#E5DDCF] rounded-xl p-4 text-center">
                <div className="text-xs text-[#292B26]/60 mb-1">Phosphorus (P)</div>
                <div className="text-2xl font-bold text-[#103D2C]">Med</div>
                <div className="w-full bg-[#F2E8D5] h-1.5 rounded-full mt-2"><div className="bg-[#17643E] h-1.5 rounded-full w-1/2"></div></div>
              </div>
              <div className="border border-[#E5DDCF] rounded-xl p-4 text-center">
                <div className="text-xs text-[#292B26]/60 mb-1">Potassium (K)</div>
                <div className="text-2xl font-bold text-[#103D2C]">High</div>
                <div className="w-full bg-[#F2E8D5] h-1.5 rounded-full mt-2"><div className="bg-[#17643E] h-1.5 rounded-full w-3/4"></div></div>
              </div>
              <div className="border border-[#E5DDCF] rounded-xl p-4 text-center">
                <div className="text-xs text-[#292B26]/60 mb-1">pH Level</div>
                <div className="text-2xl font-bold text-[#103D2C]">7.2</div>
                <div className="text-[10px] text-[#17643E] mt-1 font-bold">Optimal</div>
              </div>
            </div>
          </div>

          <div className="bg-[#FBF7EF] rounded-2xl p-6 border border-[#E5DDCF]">
            <h3 className="font-bold text-[#103D2C] mb-4">Fertilizer Guidance (for Soybean)</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-[#E5DDCF]">
                <Check className="w-5 h-5 text-[#17643E] mt-0.5" />
                <div>
                  <p className="font-bold text-sm text-[#103D2C]">Apply Urea: 25 kg/acre</p>
                  <p className="text-xs text-[#292B26]/70">To address Nitrogen deficiency during vegetative stage.</p>
                </div>
              </div>
              <div className="flex items-start gap-3 bg-white p-3 rounded-lg border border-[#E5DDCF]">
                <AlertTriangle className="w-5 h-5 text-[#B6532A] mt-0.5" />
                <div>
                  <p className="font-bold text-sm text-[#103D2C]">Reduce MOP Application</p>
                  <p className="text-xs text-[#292B26]/70">Potassium levels are already high. Save costs by skipping MOP this season.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
          <h3 className="font-bold text-[#103D2C] mb-4">Past Reports</h3>
          <div className="space-y-4">
            {[1,2,3].map((i) => (
              <div key={i} className="flex justify-between items-center p-3 border border-[#E5DDCF] rounded-lg hover:bg-[#FBF7EF] cursor-pointer">
                <div>
                  <p className="text-sm font-bold text-[#103D2C]">Kharif 202{6-i}</p>
                  <p className="text-xs text-[#292B26]/60 flex items-center gap-1"><MapPin size={10}/> Field 1</p>
                </div>
                <span className="text-xs text-[#17643E] font-medium">View PDF</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
