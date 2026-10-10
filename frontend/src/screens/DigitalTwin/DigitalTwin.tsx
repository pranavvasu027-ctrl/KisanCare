import React, { useState, useEffect } from 'react';
import { Map, Leaf, Droplets, Thermometer, Wind, AlertTriangle, Layers, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

export default function DigitalTwin() {
  const [farmData, setFarmData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetchFarmData();
  }, []);

  const fetchFarmData = async () => {
    setLoading(true);
    try {
      const res = await api.getFarmDetails('FARM-001');
      setFarmData(res);
      setIsDemo(res.isDemo);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto flex flex-col h-full">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Digital Twin</h1>
          <p className="text-[#292B26]/70 mt-1">Live simulation and monitoring of your farm's health.</p>
        </div>
        <div className="flex gap-2 items-center">
          {isDemo && <span className="bg-orange-100 text-orange-700 text-xs font-bold px-2 py-1 rounded-full uppercase tracking-wider">Demo Mode</span>}
          <select className="border border-[#E5DDCF] bg-white rounded-lg px-4 py-2 font-medium text-[#103D2C] outline-none">
            <option>All Fields</option>
            <option>Field 1</option>
            <option>Field 2</option>
          </select>
          <button onClick={fetchFarmData} className="bg-[#FBF7EF] border border-[#E5DDCF] text-[#103D2C] px-4 py-2 rounded-lg flex items-center gap-2 font-medium hover:bg-white">
            <Layers size={18} />
            Map Layers
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
        {/* Map View (Spans 3 cols) */}
        <div className="lg:col-span-3 bg-white rounded-2xl border border-[#E5DDCF] overflow-hidden shadow-sm relative min-h-[500px]">
          <img src="https://images.unsplash.com/photo-1590055531615-f16d36ffe8ea?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80" alt="Satellite Map" className="absolute inset-0 w-full h-full object-cover mix-blend-overlay" />
          
          <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 800">
            {/* Field 1 */}
            <polygon points="100,200 400,150 500,450 150,550" fill="rgba(23, 100, 62, 0.4)" stroke="#A8C69A" strokeWidth="3" className="hover:fill-rgba(23, 100, 62, 0.6) transition-all cursor-pointer" />
            <text x="300" y="350" fill="white" fontSize="24" fontWeight="bold" textAnchor="middle" className="pointer-events-none drop-shadow-md">Field 1</text>
            
            {/* Field 2 - Stress alert */}
            <polygon points="550,100 900,200 850,500 450,400" fill="rgba(182, 83, 42, 0.5)" stroke="#B6532A" strokeWidth="3" className="hover:fill-rgba(182, 83, 42, 0.7) transition-all cursor-pointer" />
            <text x="680" y="300" fill="white" fontSize="24" fontWeight="bold" textAnchor="middle" className="pointer-events-none drop-shadow-md">Field 2</text>
            
            {/* Tooltip mockup for Field 2 */}
            <g transform="translate(680, 220)">
              <rect x="-80" y="-40" width="160" height="30" rx="4" fill="white" className="shadow-lg" />
              <text x="0" y="-20" fill="#B6532A" fontSize="12" fontWeight="bold" textAnchor="middle">Water Stress Detected</text>
            </g>
          </svg>

          {/* Map Controls */}
          <div className="absolute top-4 right-4 bg-white/90 backdrop-blur rounded-lg shadow-sm border border-[#E5DDCF] p-2 flex flex-col gap-2">
            <button className="w-8 h-8 flex items-center justify-center text-[#103D2C] hover:bg-[#FBF7EF] rounded">+</button>
            <button className="w-8 h-8 flex items-center justify-center text-[#103D2C] hover:bg-[#FBF7EF] rounded">-</button>
            <div className="w-8 border-b border-[#E5DDCF]"></div>
            <button className="w-8 h-8 flex items-center justify-center text-[#103D2C] hover:bg-[#FBF7EF] rounded" title="NDVI"><Leaf size={16} /></button>
            <button className="w-8 h-8 flex items-center justify-center text-[#103D2C] hover:bg-[#FBF7EF] rounded" title="Moisture"><Droplets size={16} /></button>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-[#E5DDCF] shadow-sm p-5">
            <h3 className="font-bold text-[#103D2C] mb-4 border-b border-[#E5DDCF] pb-2">Field 2 Details</h3>
            
            {loading ? (
              <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-[#17643E]" /></div>
            ) : (
              <>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-[#292B26]/70">Crop</span>
                    <span className="font-bold text-[#103D2C]">{farmData?.crop?.current_crop || 'Cotton'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-[#292B26]/70">Stage</span>
                    <span className="font-semibold text-[#17643E] bg-[#A8C69A]/20 px-2 py-0.5 rounded-full text-xs">Flowering</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-[#292B26]/70">Soil Moisture</span>
                    <span className="font-bold text-[#B6532A]">14% (Low)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-[#292B26]/70">Est. Yield</span>
                    <span className="font-bold text-[#103D2C]">1.2 t/ac</span>
                  </div>
                </div>
                
                <div className="mt-6 bg-[#FBF7EF] p-4 rounded-xl border border-[#B6532A]/30">
                  <div className="flex items-start gap-2 mb-2">
                    <AlertTriangle size={16} className="text-[#B6532A] mt-0.5" />
                    <h4 className="font-bold text-[#B6532A] text-sm">Action Required</h4>
                  </div>
                  <p className="text-xs text-[#292B26]/70">Apply 40mm of irrigation within 48 hours to prevent yield loss during flowering.</p>
                </div>
              </>
            )}
          </div>
          
          <div className="bg-white rounded-2xl border border-[#E5DDCF] shadow-sm p-5">
            <h3 className="font-bold text-[#103D2C] mb-4 border-b border-[#E5DDCF] pb-2">Micro-Climate</h3>
            
            {loading ? (
              <div className="flex justify-center py-6"><Loader2 className="w-6 h-6 animate-spin text-[#17643E]" /></div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center bg-[#FBF7EF] p-3 rounded-lg">
                  <Thermometer size={16} className="mx-auto text-[#17643E] mb-1" />
                  <div className="text-lg font-bold text-[#103D2C]">{farmData?.climate?.temperature || 32}°C</div>
                  <div className="text-[10px] text-[#292B26]/60">Temp</div>
                </div>
                <div className="text-center bg-[#FBF7EF] p-3 rounded-lg">
                  <Wind size={16} className="mx-auto text-[#17643E] mb-1" />
                  <div className="text-lg font-bold text-[#103D2C]">{farmData?.climate?.humidity || 62}%</div>
                  <div className="text-[10px] text-[#292B26]/60">Humidity</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
