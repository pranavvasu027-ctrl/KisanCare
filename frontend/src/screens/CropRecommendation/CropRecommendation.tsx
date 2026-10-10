import React, { useState, useEffect } from 'react';
import { Sprout, Check, ChevronRight, TrendingUp, Droplets, MapPin, Search, ArrowRight, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

export default function CropRecommendation() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      // In a real app, these parameters would come from Digital Twin / Context
      const response = await api.predictCrop('NASHIK', 'Kharif', 'Medium');
      setRecommendations(response.data);
      setIsDemo(response.isDemo);
    } catch (error) {
      console.error("Failed to fetch recommendations", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Crop Intelligence</h1>
          <p className="text-[#292B26]/70 mt-1">AI-driven recommendations based on your soil and climate data.</p>
        </div>
        <div className="flex gap-2 items-center">
          {isDemo && <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded-full uppercase tracking-wider">Demo Mode</span>}
          <select className="border border-[#E5DDCF] bg-white rounded-lg px-4 py-2 font-medium text-[#103D2C] outline-none">
            <option>Kharif Season 2026</option>
            <option>Rabi Season 2026</option>
          </select>
          <button onClick={fetchRecommendations} className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E]">Generate New</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Analysis Context */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF] h-fit">
          <h3 className="font-bold text-[#103D2C] mb-4">Analysis Context</h3>
          <div className="space-y-4">
            <div className="flex gap-3">
              <MapPin className="text-[#17643E] w-5 h-5 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-[#292B26]">NASHIK (Black Cotton Soil)</p>
                <p className="text-xs text-[#292B26]/60">pH: 7.2, NPK: Medium/Low/High</p>
              </div>
            </div>
            <div className="flex gap-3">
              <Droplets className="text-[#17643E] w-5 h-5 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-[#292B26]">Water Availability</p>
                <p className="text-xs text-[#292B26]/60">Medium (Drip irrigation + Normal expected monsoon)</p>
              </div>
            </div>
            <div className="flex gap-3">
              <TrendingUp className="text-[#17643E] w-5 h-5 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-[#292B26]">Market Outlook</p>
                <p className="text-xs text-[#292B26]/60">Prices expected to remain strong</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-bold text-[#103D2C]">Top Recommendations</h3>
          
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 bg-white rounded-2xl border border-[#E5DDCF]">
               <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mb-4" />
               <p className="text-[#292B26]/70">AI models are analyzing your farm context...</p>
            </div>
          ) : (
            recommendations.map((rec, i) => (
              <div key={rec.crop} className={`bg-white rounded-2xl p-5 shadow-sm border transition-all hover:shadow-md cursor-pointer ${i === 0 ? 'border-[#17643E] ring-1 ring-[#17643E]/20' : 'border-[#E5DDCF]'}`}>
                <div className="flex justify-between items-start">
                  <div className="flex gap-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl ${i === 0 ? 'bg-[#17643E] text-white' : 'bg-[#F2E8D5] text-[#103D2C]'}`}>
                      #{i + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-lg font-bold text-[#103D2C]">{rec.crop}</h4>
                        {i === 0 && <span className="bg-[#17643E]/10 text-[#17643E] text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">Best Match</span>}
                      </div>
                      <div className="flex gap-2 mt-2">
                        {rec.tags?.map((t: string) => (
                          <span key={t} className="bg-[#FBF7EF] text-[#292B26]/70 text-xs px-2 py-0.5 rounded-md border border-[#E5DDCF]">{t}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-[#292B26]/60">Suitability</div>
                    <div className="text-2xl font-bold text-[#17643E]">{rec.score}%</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-[#E5DDCF]">
                  <div>
                    <div className="text-xs text-[#292B26]/60">Est. Yield</div>
                    <div className="font-bold text-[#292B26]">{rec.expected_yield} t/ac</div>
                  </div>
                  <div>
                    <div className="text-xs text-[#292B26]/60">Est. Profit</div>
                    <div className="font-bold text-[#292B26]">₹{rec.predicted_profit?.toLocaleString() || 'N/A'}</div>
                  </div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-xs text-[#292B26]/60">Water Req.</div>
                      <div className="font-bold text-[#292B26]">{rec.water_requirement || 'Medium'}</div>
                    </div>
                    <ChevronRight className="text-[#292B26]/30" />
                  </div>
                </div>
              </div>
            ))
          )}
          
          {!loading && (
            <div className="flex justify-center mt-6">
              <button className="text-[#17643E] font-medium hover:underline flex items-center gap-2">
                Compare selected crops <ArrowRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
