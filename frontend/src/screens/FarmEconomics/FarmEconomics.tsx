import React from 'react';
import { IndianRupee, TrendingUp, TrendingDown, PieChart, BarChart } from 'lucide-react';

export default function FarmEconomics() {
  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Economics</h1>
        <p className="text-[#292B26]/70 mt-1">Track costs, expected revenue, and overall profitability.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-[#E5DDCF]">
          <p className="text-sm text-[#292B26]/60 mb-2">Total Cultivation Cost</p>
          <div className="text-3xl font-bold text-[#B6532A] mb-2">₹1,24,000</div>
          <p className="text-xs text-[#292B26]/50">Season to date</p>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-[#E5DDCF]">
          <p className="text-sm text-[#292B26]/60 mb-2">Expected Revenue</p>
          <div className="text-3xl font-bold text-[#17643E] mb-2">₹3,80,000</div>
          <p className="text-xs text-[#292B26]/50">Based on current market trends</p>
        </div>
        <div className="bg-[#103D2C] text-white p-6 rounded-2xl shadow-sm">
          <p className="text-sm text-[#A8C69A] mb-2">Expected Profit</p>
          <div className="text-3xl font-bold text-white mb-2">₹2,56,000</div>
          <div className="text-xs text-[#A8C69A] flex items-center gap-1"><TrendingUp size={12} /> +12% from last year</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-[#103D2C] flex items-center gap-2"><PieChart size={18} /> Cost Breakdown</h3>
          </div>
          <div className="space-y-4">
            {[
              { name: 'Seeds', val: '₹24,000', pct: '19%', color: 'bg-[#17643E]' },
              { name: 'Fertilizers', val: '₹35,000', pct: '28%', color: 'bg-[#A8C69A]' },
              { name: 'Labor', val: '₹40,000', pct: '32%', color: 'bg-[#B6532A]' },
              { name: 'Machinery/Irrigation', val: '₹25,000', pct: '21%', color: 'bg-[#E5DDCF]' },
            ].map(item => (
              <div key={item.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-[#292B26]">{item.name}</span>
                  <span className="font-bold text-[#103D2C]">{item.val} ({item.pct})</span>
                </div>
                <div className="w-full bg-[#FBF7EF] h-2 rounded-full">
                  <div className={`${item.color} h-2 rounded-full`} style={{ width: item.pct }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-[#103D2C] flex items-center gap-2"><BarChart size={18} /> Profit History</h3>
          </div>
          <div className="flex items-end justify-between h-48 border-b border-[#E5DDCF] pb-2 px-2">
            {[2021, 2022, 2023, 2024, 2025].map((year, i) => (
              <div key={year} className="flex flex-col items-center gap-2 w-12">
                <div className="w-full bg-[#17643E] rounded-t-sm" style={{ height: `${40 + i * 15}%` }}></div>
                <span className="text-xs text-[#292B26]/60">{year}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
