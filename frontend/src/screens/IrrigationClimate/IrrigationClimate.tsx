import React from 'react';
import { Droplets, CloudRain, Sun, Wind, AlertTriangle, Calendar } from 'lucide-react';

export default function IrrigationClimate() {
  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Irrigation & Climate</h1>
          <p className="text-[#292B26]/70 mt-1">Weather forecasts and precise irrigation scheduling.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#103D2C] text-white rounded-3xl p-8 relative overflow-hidden">
            <div className="absolute right-0 top-0 bottom-0 opacity-10 pointer-events-none">
              <Sun className="w-64 h-64 -translate-y-10 translate-x-10" />
            </div>
            <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-8">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Sun className="text-yellow-400" />
                  <span className="text-xl font-medium text-[#FBF7EF]">Partly Cloudy</span>
                </div>
                <div className="text-6xl font-bold font-serif mb-2">28°C</div>
                <p className="text-[#A8C69A]">Nagpur, Maharashtra</p>
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                <div>
                  <div className="text-[#A8C69A] text-xs">Humidity</div>
                  <div className="font-bold text-lg">62%</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Wind</div>
                  <div className="font-bold text-lg">12 km/h</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Rain Chance</div>
                  <div className="font-bold text-lg">20%</div>
                </div>
                <div>
                  <div className="text-[#A8C69A] text-xs">Evapotranspiration</div>
                  <div className="font-bold text-lg">4.2 mm/d</div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-4">7-Day Forecast</h3>
            <div className="flex justify-between items-end overflow-x-auto gap-4 custom-scrollbar pb-2">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => (
                <div key={day} className="flex flex-col items-center gap-2 min-w-[60px]">
                  <span className="text-xs font-bold text-[#292B26]/60">{day}</span>
                  {i === 2 || i === 3 ? <CloudRain className="text-blue-500 w-6 h-6" /> : <Sun className="text-yellow-500 w-6 h-6" />}
                  <span className="text-sm font-bold text-[#103D2C]">{30 - i}°</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-4 flex items-center gap-2"><Droplets className="text-[#17643E]" /> Irrigation Schedule</h3>
            
            <div className="bg-white rounded-xl border border-[#E5DDCF] p-4 mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-[#103D2C]">Field 1 (Soybean)</span>
                <span className="text-xs bg-[#B6532A]/10 text-[#B6532A] px-2 py-1 rounded-full font-bold">Needs Water</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-[#292B26]/80 mb-2">
                <Calendar size={14} /> Schedule: Today, 5:00 PM
              </div>
              <p className="text-xs text-[#292B26]/60">Apply 20mm (approx 2 hrs drip)</p>
            </div>

            <div className="bg-white rounded-xl border border-[#E5DDCF] p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-[#103D2C]">Field 2 (Cotton)</span>
                <span className="text-xs bg-[#17643E]/10 text-[#17643E] px-2 py-1 rounded-full font-bold">Optimal</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-[#292B26]/80 mb-2">
                <Calendar size={14} /> Next: Thursday
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <h3 className="font-bold text-[#103D2C] mb-2 flex items-center gap-2"><AlertTriangle className="text-[#B6532A]" /> Climate Risk</h3>
            <p className="text-sm text-[#292B26]/70 mb-4">High temperatures expected late next week. Ensure adequate soil moisture to prevent heat stress.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
