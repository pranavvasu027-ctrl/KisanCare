import React from 'react';
import { Lightbulb, CheckCircle2, AlertTriangle, ArrowRight, ThumbsUp, ThumbsDown } from 'lucide-react';

export default function AiRecommendation() {
  return (
    <div className="p-4 lg:p-8 max-w-4xl mx-auto space-y-6">
      <div className="mb-6">
        <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Explainable Recommendation</h1>
        <p className="text-[#292B26]/70 mt-1">Understanding the AI's logic behind this advice.</p>
      </div>

      <div className="bg-white rounded-3xl shadow-sm border border-[#E5DDCF] overflow-hidden">
        <div className="bg-[#17643E] p-6 text-white flex items-start gap-4">
          <div className="bg-white/20 p-3 rounded-2xl">
            <Lightbulb className="w-8 h-8 text-white" />
          </div>
          <div>
            <span className="text-[#A8C69A] text-sm font-semibold uppercase tracking-wider mb-1 block">Priority Action</span>
            <h2 className="text-2xl font-bold">Consider Irrigation in Field 2 within 48 Hours</h2>
            <p className="text-white/80 mt-2 max-w-2xl">Soil moisture is below optimal levels during a critical growth stage. Irrigating now can prevent yield loss.</p>
          </div>
        </div>

        <div className="p-6 lg:p-8 space-y-8">
          <div>
            <h3 className="text-lg font-bold text-[#103D2C] mb-4 flex items-center gap-2">
              <CheckCircle2 className="text-[#17643E] w-5 h-5" /> Why is this recommended?
            </h3>
            <div className="bg-[#FBF7EF] rounded-xl p-5 space-y-3 border border-[#E5DDCF]">
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#103D2C] mt-2 shrink-0"></div>
                <p className="text-[#292B26]/80 text-sm"><strong className="text-[#103D2C]">Soil Moisture (Model 2):</strong> Currently at 14%. Optimal for Cotton at flowering stage is 22-25%.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#103D2C] mt-2 shrink-0"></div>
                <p className="text-[#292B26]/80 text-sm"><strong className="text-[#103D2C]">Weather Forecast:</strong> No rain expected in the next 7 days. High temperatures will increase evaporation.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-[#103D2C] mt-2 shrink-0"></div>
                <p className="text-[#292B26]/80 text-sm"><strong className="text-[#103D2C]">Yield Impact:</strong> Stress during flowering can reduce boll retention, potentially lowering yield by 8-12%.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-md font-bold text-[#103D2C] mb-3">Expected Benefits</h3>
              <div className="border border-[#A8C69A] rounded-xl p-4 bg-[#A8C69A]/10 text-sm text-[#103D2C] space-y-2">
                <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[#17643E]" /> Secure expected yield</div>
                <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[#17643E]" /> Maintain plant vigor</div>
                <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-[#17643E]" /> Better nutrient uptake</div>
              </div>
            </div>
            <div>
              <h3 className="text-md font-bold text-[#103D2C] mb-3">Costs & Risks</h3>
              <div className="border border-[#E5DDCF] rounded-xl p-4 bg-white text-sm text-[#292B26]/80 space-y-2">
                <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-[#B6532A]" /> Pumping electricity cost</div>
                <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-[#B6532A]" /> Water resource usage</div>
              </div>
            </div>
          </div>

          <div className="border-t border-[#E5DDCF] pt-6 flex justify-between items-center">
            <div className="text-sm text-[#292B26]/60">Was this recommendation helpful?</div>
            <div className="flex gap-2">
              <button className="p-2 border border-[#E5DDCF] rounded-lg text-[#292B26]/60 hover:text-[#17643E] hover:bg-[#FBF7EF]"><ThumbsUp size={18} /></button>
              <button className="p-2 border border-[#E5DDCF] rounded-lg text-[#292B26]/60 hover:text-[#B6532A] hover:bg-[#FBF7EF]"><ThumbsDown size={18} /></button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
