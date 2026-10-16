import React, { useState } from 'react';
import { History, Calendar, Sprout, TrendingUp } from 'lucide-react';

interface SeasonRecord {
  season: string;
  crop: string;
  yield: string;
  profit: string;
  learnings: string[];
}

const seasonRecords: Record<string, SeasonRecord> = {
  'Kharif 2025': {
    season: 'Kharif 2025',
    crop: 'Soybean (JS 335)',
    yield: '2.6 tonnes/ac',
    profit: '₹42,000/ac',
    learnings: [
      'JS 335 variety performed well despite a mid-season 14-day dry spell.',
      'Waiting 2 extra weeks before selling increased revenue by 8% due to late-season demand.'
    ]
  },
  'Rabi 2024-25': {
    season: 'Rabi 2024-25',
    crop: 'Wheat (GW 322)',
    yield: '1.8 tonnes/ac',
    profit: '₹28,000/ac',
    learnings: [
      'Timely second irrigation at CRI (Crown Root Initiation) stage prevented lodging.',
      'Sold 60% of produce at local APMC; retained remainder for seed bank.'
    ]
  }
};

export default function FarmMemory() {
  const [selectedSeason, setSelectedSeason] = useState<string>('Kharif 2025');
  const record = seasonRecords[selectedSeason] || seasonRecords['Kharif 2025'];

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Memory</h1>
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
              Sample Historical Logs
            </span>
          </div>
          <p className="text-[#292B26]/70 mt-1">Historical data, past performance, and season logs.</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="p-6 border-b border-[#E5DDCF] flex flex-col sm:flex-row gap-4">
          <div
            onClick={() => setSelectedSeason('Kharif 2025')}
            className={`flex-1 rounded-lg border p-4 flex gap-4 items-center cursor-pointer transition-all ${
              selectedSeason === 'Kharif 2025'
                ? 'bg-[#FBF7EF] border-[#17643E] ring-1 ring-[#17643E]/20'
                : 'bg-white border-[#E5DDCF] hover:bg-[#FBF7EF]'
            }`}
          >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-xs ${
              selectedSeason === 'Kharif 2025' ? 'bg-[#17643E] text-white' : 'bg-[#FBF7EF] text-[#292B26]/50'
            }`}>
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-[#103D2C]">Kharif 2025</div>
              <div className="text-xs text-[#292B26]/60">Soybean • 2.6 t/ac • ₹42k Profit</div>
            </div>
          </div>

          <div
            onClick={() => setSelectedSeason('Rabi 2024-25')}
            className={`flex-1 rounded-lg border p-4 flex gap-4 items-center cursor-pointer transition-all ${
              selectedSeason === 'Rabi 2024-25'
                ? 'bg-[#FBF7EF] border-[#17643E] ring-1 ring-[#17643E]/20'
                : 'bg-white border-[#E5DDCF] hover:bg-[#FBF7EF]'
            }`}
          >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-xs ${
              selectedSeason === 'Rabi 2024-25' ? 'bg-[#17643E] text-white' : 'bg-[#FBF7EF] text-[#292B26]/50'
            }`}>
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-[#103D2C]">Rabi 2024-25</div>
              <div className="text-xs text-[#292B26]/60">Wheat • 1.8 t/ac • ₹28k Profit</div>
            </div>
          </div>
        </div>

        <div className="p-6">
          <h3 className="font-bold text-[#103D2C] mb-4">Season Details: {record.season}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
              <p className="text-xs text-[#292B26]/60 mb-1">Crop Planted</p>
              <div className="text-lg font-bold text-[#103D2C]">{record.crop}</div>
            </div>
            <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
              <p className="text-xs text-[#292B26]/60 mb-1">Total Yield</p>
              <div className="text-lg font-bold text-[#103D2C]">{record.yield}</div>
            </div>
            <div className="border border-[#E5DDCF] p-4 rounded-xl bg-[#FBF7EF]/50">
              <p className="text-xs text-[#292B26]/60 mb-1">Profitability</p>
              <div className="text-lg font-bold text-[#17643E]">{record.profit}</div>
            </div>
          </div>

          <h3 className="font-bold text-[#103D2C] mb-4">Key Learnings & Notes</h3>
          <ul className="space-y-3">
            {record.learnings.map((item, i) => (
              <li key={i} className="bg-[#FBF7EF] p-3 rounded-lg text-sm text-[#292B26]/80 flex gap-2">
                <Sprout className="w-5 h-5 text-[#17643E] shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
