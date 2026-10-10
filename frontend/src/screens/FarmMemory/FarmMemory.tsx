import React from 'react';
import { History, Calendar, Sprout, TrendingUp, Search } from 'lucide-react';

export default function FarmMemory() {
  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Memory</h1>
          <p className="text-[#292B26]/70 mt-1">Historical data, past performance, and season logs.</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="p-6 border-b border-[#E5DDCF] flex gap-4">
          <div className="flex-1 bg-[#FBF7EF] rounded-lg border border-[#E5DDCF] p-4 flex gap-4 items-center cursor-pointer hover:bg-[#E5DDCF]/50">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm">
              <Calendar className="text-[#103D2C]" />
            </div>
            <div>
              <div className="text-sm font-bold text-[#103D2C]">Kharif 2025</div>
              <div className="text-xs text-[#292B26]/60">Soybean • 2.6 t/ac • ₹42k Profit</div>
            </div>
          </div>
          <div className="flex-1 bg-white rounded-lg border border-[#E5DDCF] p-4 flex gap-4 items-center cursor-pointer hover:bg-[#FBF7EF]">
            <div className="w-12 h-12 bg-[#FBF7EF] rounded-full flex items-center justify-center">
              <Calendar className="text-[#292B26]/40" />
            </div>
            <div>
              <div className="text-sm font-bold text-[#292B26]">Rabi 2024-25</div>
              <div className="text-xs text-[#292B26]/60">Wheat • 1.8 t/ac • ₹28k Profit</div>
            </div>
          </div>
        </div>

        <div className="p-6">
          <h3 className="font-bold text-[#103D2C] mb-4">Season Details: Kharif 2025</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="border border-[#E5DDCF] p-4 rounded-xl">
              <p className="text-xs text-[#292B26]/60 mb-1">Crop Planted</p>
              <div className="text-lg font-bold text-[#103D2C]">Soybean (JS 335)</div>
            </div>
            <div className="border border-[#E5DDCF] p-4 rounded-xl">
              <p className="text-xs text-[#292B26]/60 mb-1">Total Yield</p>
              <div className="text-lg font-bold text-[#103D2C]">2.6 tonnes/ac</div>
            </div>
            <div className="border border-[#E5DDCF] p-4 rounded-xl">
              <p className="text-xs text-[#292B26]/60 mb-1">Profitability</p>
              <div className="text-lg font-bold text-[#17643E]">₹42,000/ac</div>
            </div>
          </div>

          <h3 className="font-bold text-[#103D2C] mb-4">Key Learnings & Notes</h3>
          <ul className="space-y-3">
            <li className="bg-[#FBF7EF] p-3 rounded-lg text-sm text-[#292B26]/80 flex gap-2">
              <Sprout className="w-5 h-5 text-[#17643E] shrink-0" /> JS 335 variety performed well despite a mid-season dry spell.
            </li>
            <li className="bg-[#FBF7EF] p-3 rounded-lg text-sm text-[#292B26]/80 flex gap-2">
              <TrendingUp className="w-5 h-5 text-[#17643E] shrink-0" /> Waiting 2 extra weeks before selling increased revenue by 8%.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
