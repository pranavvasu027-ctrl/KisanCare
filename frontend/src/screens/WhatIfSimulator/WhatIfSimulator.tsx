import React from 'react';
import { FlaskConical, Play, Save, RotateCcw, TrendingDown, TrendingUp, BarChart2 } from 'lucide-react';

export default function WhatIfSimulator() {
  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">What-If Simulator</h1>
          <p className="text-[#292B26]/70 mt-1">Simulate changes in farming practices and predict outcomes.</p>
        </div>
        <div className="flex gap-2">
          <button className="bg-white text-[#103D2C] border border-[#E5DDCF] px-4 py-2 rounded-lg font-medium hover:bg-[#FBF7EF] flex items-center gap-2">
            <Save size={18} /> Save Scenario
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        
        {/* Controls Panel */}
        <div className="lg:col-span-4 bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 flex flex-col">
          <h3 className="font-bold text-[#103D2C] mb-4 pb-2 border-b border-[#E5DDCF]">Scenario Parameters</h3>
          
          <div className="space-y-5 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Crop Selection</label>
              <select className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none">
                <option>Soybean</option>
                <option>Cotton</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Irrigation Schedule</label>
              <select className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none">
                <option>Optimal (As recommended)</option>
                <option>Reduced (-20%)</option>
                <option>Rainfed only</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Fertilizer Strategy</label>
              <select className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none">
                <option>Standard NPK</option>
                <option>Organic + Biofertilizers</option>
                <option>High Yield (Chemical)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Weather Assumption</label>
              <select className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none">
                <option>Normal Monsoon</option>
                <option>Drought (-30% rain)</option>
                <option>Excess Rain (+20%)</option>
              </select>
            </div>
            
            <div className="pt-4 mt-2 border-t border-[#E5DDCF]">
              <label className="block text-sm font-medium text-[#292B26] mb-3">Expected Market Price</label>
              <input type="range" min="3000" max="6000" defaultValue="4500" className="w-full accent-[#17643E]" />
              <div className="flex justify-between text-xs text-[#292B26]/60 mt-1">
                <span>₹3,000/qtl</span>
                <span className="font-bold text-[#103D2C]">₹4,500/qtl</span>
                <span>₹6,000/qtl</span>
              </div>
            </div>
          </div>
          
          <div className="pt-4 border-t border-[#E5DDCF] mt-4 flex gap-2">
            <button className="flex-1 bg-[#FBF7EF] text-[#292B26] border border-[#E5DDCF] rounded-lg py-2 font-medium hover:bg-[#E5DDCF] flex items-center justify-center gap-2">
              <RotateCcw size={16} /> Reset
            </button>
            <button className="flex-[2] bg-[#103D2C] text-white rounded-lg py-2 font-medium hover:bg-[#17643E] flex items-center justify-center gap-2 shadow-sm">
              <Play size={16} /> Run Simulation
            </button>
          </div>
        </div>
        
        {/* Results Panel */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#17643E]/5 rounded-2xl border border-[#17643E]/20 p-5 relative overflow-hidden">
              <h4 className="text-sm font-bold text-[#103D2C] mb-1">Baseline Prediction</h4>
              <p className="text-xs text-[#292B26]/60 mb-4">Current farming practices</p>
              <div className="text-3xl font-bold text-[#103D2C] mb-1">₹38,500 <span className="text-sm font-normal">/ ac</span></div>
              <div className="text-sm text-[#292B26]/70">Est. Yield: 2.6 t/ac</div>
            </div>
            
            <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 relative overflow-hidden shadow-sm">
              <h4 className="text-sm font-bold text-[#103D2C] mb-1">Simulated Outcome</h4>
              <p className="text-xs text-[#292B26]/60 mb-4">With adjusted parameters</p>
              <div className="text-3xl font-bold text-[#17643E] mb-1 flex items-center gap-2">
                ₹44,200 <span className="text-sm font-normal text-[#292B26]">/ ac</span>
              </div>
              <div className="flex justify-between items-end">
                <div className="text-sm text-[#292B26]/70">Est. Yield: 2.9 t/ac</div>
                <div className="text-sm font-bold text-[#17643E] bg-[#17643E]/10 px-2 py-1 rounded flex items-center gap-1">
                  <TrendingUp size={14} /> +14.8%
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-[#103D2C]">Comparison Chart</h3>
              <div className="flex gap-4 text-xs font-medium">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#E5DDCF]"></span> Baseline</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#17643E]"></span> Simulated</span>
              </div>
            </div>
            
            <div className="flex-1 flex items-end justify-around pb-4 border-b border-[#E5DDCF] px-4">
              {/* Fake Bar Chart */}
              <div className="w-16 flex gap-1 items-end h-full relative">
                <div className="w-full bg-[#E5DDCF] rounded-t-sm" style={{ height: '60%' }}></div>
                <div className="w-full bg-[#17643E] rounded-t-sm" style={{ height: '75%' }}></div>
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-[#292B26]/70">Yield</span>
              </div>
              
              <div className="w-16 flex gap-1 items-end h-full relative">
                <div className="w-full bg-[#E5DDCF] rounded-t-sm" style={{ height: '40%' }}></div>
                <div className="w-full bg-[#17643E] rounded-t-sm" style={{ height: '48%' }}></div>
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-[#292B26]/70">Cost</span>
              </div>
              
              <div className="w-16 flex gap-1 items-end h-full relative">
                <div className="w-full bg-[#E5DDCF] rounded-t-sm" style={{ height: '55%' }}></div>
                <div className="w-full bg-[#17643E] rounded-t-sm" style={{ height: '85%' }}></div>
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-[#292B26]/70">Profit</span>
              </div>
              
              <div className="w-16 flex gap-1 items-end h-full relative">
                <div className="w-full bg-[#E5DDCF] rounded-t-sm" style={{ height: '70%' }}></div>
                <div className="w-full bg-[#B6532A] rounded-t-sm" style={{ height: '30%' }}></div>
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-[#292B26]/70">Risk</span>
              </div>
            </div>
            
            <div className="mt-8 bg-[#FBF7EF] p-4 rounded-xl border border-[#A8C69A]/30">
              <h4 className="font-bold text-[#103D2C] text-sm mb-2">AI Insights</h4>
              <p className="text-sm text-[#292B26]/80 leading-relaxed">
                By optimizing irrigation and using organic fertilizers, your profit increases by <strong>14.8%</strong> while reducing overall risk. Water usage decreases significantly, making the crop more resilient to potential dry spells.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
