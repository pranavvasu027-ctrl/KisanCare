import React from 'react';
import { ArrowRight, Leaf, TrendingUp, Droplets, ShieldAlert, BarChart2 } from 'lucide-react';

export default function CropComparison() {
  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Crop Comparison</h1>
          <p className="text-[#292B26]/70 mt-1">Side-by-side analysis of candidate crops for your farm.</p>
        </div>
        <button className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E]">Run Simulator</button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="grid grid-cols-3 border-b border-[#E5DDCF]">
          <div className="p-6 bg-[#FBF7EF]">
            <h3 className="font-bold text-[#292B26]/60 uppercase tracking-wider text-xs mb-2">Metrics</h3>
          </div>
          <div className="p-6 text-center border-l border-[#E5DDCF]">
            <h2 className="text-xl font-bold text-[#103D2C] mb-1">Soybean (JS 335)</h2>
            <span className="bg-[#17643E]/10 text-[#17643E] text-[10px] font-bold px-2 py-0.5 rounded-full">Recommended</span>
          </div>
          <div className="p-6 text-center border-l border-[#E5DDCF]">
            <h2 className="text-xl font-bold text-[#103D2C] mb-1">Cotton (Bt)</h2>
            <span className="bg-[#292B26]/10 text-[#292B26]/60 text-[10px] font-bold px-2 py-0.5 rounded-full">Alternative</span>
          </div>
        </div>

        <div className="grid grid-cols-3 divide-x divide-[#E5DDCF] border-b border-[#E5DDCF]">
          <div className="p-5 flex items-center gap-3">
            <TrendingUp className="text-[#A8C69A] w-5 h-5" />
            <span className="font-medium text-[#292B26]">Expected Yield</span>
          </div>
          <div className="p-5 text-center font-bold text-[#103D2C]">2.8 t/ac</div>
          <div className="p-5 text-center font-bold text-[#103D2C]">1.2 t/ac</div>
        </div>

        <div className="grid grid-cols-3 divide-x divide-[#E5DDCF] border-b border-[#E5DDCF]">
          <div className="p-5 flex items-center gap-3">
            <BarChart2 className="text-[#A8C69A] w-5 h-5" />
            <span className="font-medium text-[#292B26]">Cultivation Cost</span>
          </div>
          <div className="p-5 text-center font-bold text-[#103D2C]">₹12,000 /ac</div>
          <div className="p-5 text-center font-bold text-[#103D2C]">₹18,500 /ac</div>
        </div>

        <div className="grid grid-cols-3 divide-x divide-[#E5DDCF] border-b border-[#E5DDCF] bg-[#17643E]/5">
          <div className="p-5 flex items-center gap-3">
            <Leaf className="text-[#17643E] w-5 h-5" />
            <span className="font-bold text-[#103D2C]">Expected Profit</span>
          </div>
          <div className="p-5 text-center font-bold text-[#17643E] text-lg">₹42,000 /ac</div>
          <div className="p-5 text-center font-bold text-[#103D2C] text-lg">₹38,000 /ac</div>
        </div>

        <div className="grid grid-cols-3 divide-x divide-[#E5DDCF] border-b border-[#E5DDCF]">
          <div className="p-5 flex items-center gap-3">
            <Droplets className="text-[#A8C69A] w-5 h-5" />
            <span className="font-medium text-[#292B26]">Water Requirement</span>
          </div>
          <div className="p-5 text-center text-[#292B26]">Medium (450-700mm)</div>
          <div className="p-5 text-center text-[#B6532A] font-medium">High (700-1200mm)</div>
        </div>

        <div className="grid grid-cols-3 divide-x divide-[#E5DDCF]">
          <div className="p-5 flex items-center gap-3">
            <ShieldAlert className="text-[#A8C69A] w-5 h-5" />
            <span className="font-medium text-[#292B26]">Overall Risk</span>
          </div>
          <div className="p-5 text-center text-[#17643E] font-medium">Low</div>
          <div className="p-5 text-center text-[#B6532A] font-medium">Moderate</div>
        </div>
      </div>
    </div>
  );
}
