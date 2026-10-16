import React, { useState, useEffect } from 'react';
import {
  Map, Leaf, Droplets, Thermometer, Wind, AlertTriangle, Layers,
  Loader2, CheckCircle2, Info, ZoomIn, ZoomOut, Compass
} from 'lucide-react';
import { api } from '../../services/api';

export interface TwinField {
  id: string;
  name: string;
  area: number;
  crop: string;
  variety: string;
  stage: string;
  moisturePercent: number;
  moistureStatus: 'Low' | 'Adequate' | 'High';
  estYield: string;
  status: 'Optimal' | 'Alert';
  alertTitle?: string;
  alertDesc?: string;
  ndvi: number;
  soilType: string;
  lastIrrigationDaysAgo: number;
}

const SAMPLE_FIELDS: TwinField[] = [
  {
    id: 'field-1',
    name: 'Field 1 (North Parcel)',
    area: 6.5,
    crop: 'Soybean',
    variety: 'JS 335',
    stage: 'Vegetative / Pod Development',
    moisturePercent: 38,
    moistureStatus: 'Adequate',
    estYield: '2.4 t/ac',
    status: 'Optimal',
    ndvi: 0.74,
    soilType: 'Medium Black Clay',
    lastIrrigationDaysAgo: 5
  },
  {
    id: 'field-2',
    name: 'Field 2 (South Parcel)',
    area: 5.5,
    crop: 'Cotton',
    variety: 'Bt Cotton (Bollgard II)',
    stage: 'Flowering & Square Formation',
    moisturePercent: 14,
    moistureStatus: 'Low',
    estYield: '1.1 t/ac',
    status: 'Alert',
    alertTitle: 'Water Stress Detected',
    alertDesc: 'Apply 40mm of supplementary irrigation within 48 hours to avert boll/square shedding during flowering.',
    ndvi: 0.46,
    soilType: 'Shallow Red Loam',
    lastIrrigationDaysAgo: 11
  }
];

export default function DigitalTwin() {
  const [farmData, setFarmData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFieldId, setSelectedFieldId] = useState<string>('field-2');
  const [activeLayer, setActiveLayer] = useState<'satellite' | 'ndvi' | 'moisture'>('satellite');
  const [zoomScale, setZoomScale] = useState<number>(1.0);

  useEffect(() => {
    fetchFarmData();
  }, []);

  const fetchFarmData = async () => {
    setLoading(true);
    try {
      const res = await api.getFarmDetails('FARM-001');
      setFarmData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const selectedField = SAMPLE_FIELDS.find(f => f.id === selectedFieldId);

  // Map Polygon styling by active layer
  const getFieldFill = (fieldId: string) => {
    const isSelected = selectedFieldId === fieldId;
    if (activeLayer === 'ndvi') {
      return fieldId === 'field-1'
        ? (isSelected ? 'rgba(34, 197, 94, 0.7)' : 'rgba(34, 197, 94, 0.5)')
        : (isSelected ? 'rgba(234, 179, 8, 0.7)' : 'rgba(234, 179, 8, 0.5)');
    }
    if (activeLayer === 'moisture') {
      return fieldId === 'field-1'
        ? (isSelected ? 'rgba(14, 165, 233, 0.7)' : 'rgba(14, 165, 233, 0.5)')
        : (isSelected ? 'rgba(239, 68, 68, 0.7)' : 'rgba(239, 68, 68, 0.5)');
    }
    // Default satellite layer
    return fieldId === 'field-1'
      ? (isSelected ? 'rgba(23, 100, 62, 0.65)' : 'rgba(23, 100, 62, 0.45)')
      : (isSelected ? 'rgba(182, 83, 42, 0.75)' : 'rgba(182, 83, 42, 0.55)');
  };

  const getFieldStroke = (fieldId: string) => {
    if (selectedFieldId === fieldId) return '#FFFFFF';
    return fieldId === 'field-1' ? '#A8C69A' : '#B6532A';
  };

  const handleZoomIn = () => setZoomScale(prev => Math.min(1.4, prev + 0.1));
  const handleZoomOut = () => setZoomScale(prev => Math.max(0.9, prev - 0.1));

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto flex flex-col h-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Digital Twin</h1>
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300 uppercase tracking-wider">
              Demo Mode • Sample Telemetry
            </span>
          </div>
          <p className="text-[#292B26]/70 mt-1 text-sm">
            Interactive virtual model and spatial field monitoring for Patil Farm (12.0 Total Acres).
          </p>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={selectedFieldId}
            onChange={(e) => setSelectedFieldId(e.target.value)}
            className="border border-[#E5DDCF] bg-white rounded-lg px-3 py-2 text-xs font-medium text-[#103D2C] outline-none shadow-xs cursor-pointer"
          >
            <option value="all">All Fields (Overview)</option>
            <option value="field-1">Field 1 (North Parcel - 6.5 ac)</option>
            <option value="field-2">Field 2 (South Parcel - 5.5 ac)</option>
          </select>

          {/* Layer switcher button */}
          <div className="flex rounded-lg border border-[#E5DDCF] bg-[#FBF7EF] p-0.5 text-xs">
            <button
              onClick={() => setActiveLayer('satellite')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                activeLayer === 'satellite' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              Satellite
            </button>
            <button
              onClick={() => setActiveLayer('ndvi')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer flex items-center gap-1 ${
                activeLayer === 'ndvi' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              <Leaf size={12} /> NDVI
            </button>
            <button
              onClick={() => setActiveLayer('moisture')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer flex items-center gap-1 ${
                activeLayer === 'moisture' ? 'bg-[#103D2C] text-white shadow-xs' : 'text-[#292B26]/70 hover:text-[#103D2C]'
              }`}
            >
              <Droplets size={12} /> Moisture
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
        {/* Map View (Spans 3 cols) */}
        <div className="lg:col-span-3 bg-white rounded-2xl border border-[#E5DDCF] overflow-hidden shadow-sm relative min-h-[520px]">
          <img
            src="https://images.unsplash.com/photo-1590055531615-f16d36ffe8ea?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80"
            alt="Satellite Map"
            className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-90"
          />

          {/* SVG Map Layer */}
          <div
            className="absolute inset-0 w-full h-full transition-transform duration-200"
            style={{ transform: `scale(${zoomScale})`, transformOrigin: 'center center' }}
          >
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 800">
              {/* Field 1 (North Parcel) */}
              <polygon
                points="100,200 400,150 500,450 150,550"
                fill={getFieldFill('field-1')}
                stroke={getFieldStroke('field-1')}
                strokeWidth={selectedFieldId === 'field-1' ? '4' : '3'}
                className="transition-all cursor-pointer"
                onClick={() => setSelectedFieldId('field-1')}
              />
              <text
                x="300"
                y="340"
                fill="white"
                fontSize="22"
                fontWeight="bold"
                textAnchor="middle"
                className="pointer-events-none drop-shadow-md font-sans"
              >
                Field 1 (North)
              </text>
              <text
                x="300"
                y="368"
                fill="white"
                fontSize="14"
                textAnchor="middle"
                className="pointer-events-none drop-shadow-md font-sans opacity-90"
              >
                Soybean • 38% Moisture
              </text>

              {/* Field 2 (South Parcel) */}
              <polygon
                points="550,100 900,200 850,500 450,400"
                fill={getFieldFill('field-2')}
                stroke={getFieldStroke('field-2')}
                strokeWidth={selectedFieldId === 'field-2' ? '4' : '3'}
                className="transition-all cursor-pointer"
                onClick={() => setSelectedFieldId('field-2')}
              />
              <text
                x="680"
                y="290"
                fill="white"
                fontSize="22"
                fontWeight="bold"
                textAnchor="middle"
                className="pointer-events-none drop-shadow-md font-sans"
              >
                Field 2 (South)
              </text>
              <text
                x="680"
                y="318"
                fill="white"
                fontSize="14"
                textAnchor="middle"
                className="pointer-events-none drop-shadow-md font-sans opacity-90"
              >
                Cotton • 14% Moisture (Low)
              </text>

              {/* Tooltip badge for Field 2 Water Stress */}
              <g transform="translate(680, 215)">
                <rect x="-85" y="-30" width="170" height="26" rx="6" fill="#B6532A" className="drop-shadow-md" />
                <text x="0" y="-13" fill="white" fontSize="11" fontWeight="bold" textAnchor="middle">
                  ⚠ Water Stress Detected
                </text>
              </g>
            </svg>
          </div>

          {/* Active Layer Label at bottom-left */}
          <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-xs text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>
              Active Layer: {activeLayer === 'satellite' ? 'Natural Satellite Color' : activeLayer === 'ndvi' ? 'NDVI Vegetation Index (Simulated)' : 'Soil Moisture Heatmap (Simulated)'}
            </span>
          </div>

          {/* Floating Map Controls on top-right */}
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-xs rounded-xl shadow-sm border border-[#E5DDCF] p-1.5 flex flex-col gap-1.5 z-10">
            <button
              onClick={handleZoomIn}
              className="w-8 h-8 flex items-center justify-center text-[#103D2C] hover:bg-[#FBF7EF] rounded-lg cursor-pointer transition-colors"
              title="Zoom In"
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={handleZoomOut}
              className="w-8 h-8 flex items-center justify-center text-[#103D2C] hover:bg-[#FBF7EF] rounded-lg cursor-pointer transition-colors"
              title="Zoom Out"
            >
              <ZoomOut size={16} />
            </button>
            <div className="w-full border-b border-[#E5DDCF]"></div>
            <button
              onClick={() => setActiveLayer('ndvi')}
              className={`w-8 h-8 flex items-center justify-center rounded-lg cursor-pointer transition-colors ${
                activeLayer === 'ndvi' ? 'bg-[#17643E] text-white' : 'text-[#103D2C] hover:bg-[#FBF7EF]'
              }`}
              title="NDVI Canopy Health"
            >
              <Leaf size={16} />
            </button>
            <button
              onClick={() => setActiveLayer('moisture')}
              className={`w-8 h-8 flex items-center justify-center rounded-lg cursor-pointer transition-colors ${
                activeLayer === 'moisture' ? 'bg-[#17643E] text-white' : 'text-[#103D2C] hover:bg-[#FBF7EF]'
              }`}
              title="Soil Moisture Heatmap"
            >
              <Droplets size={16} />
            </button>
          </div>
        </div>

        {/* Sidebar Info Panels */}
        <div className="space-y-6">
          {/* Field Details Card */}
          <div className="bg-white rounded-2xl border border-[#E5DDCF] shadow-sm p-5 space-y-4">
            <div className="border-b border-[#E5DDCF] pb-2 flex justify-between items-center">
              <h3 className="font-bold text-[#103D2C] text-sm">
                {selectedField ? selectedField.name : 'All Fields (Farm Overview)'}
              </h3>
              <span className="text-[10px] text-[#292B26]/50">
                {selectedField ? `${selectedField.area} ac` : '12.0 ac Total'}
              </span>
            </div>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-[#17643E]" />
              </div>
            ) : selectedField ? (
              <div className="space-y-3.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Cultivated Crop</span>
                  <span className="font-bold text-[#103D2C]">
                    {selectedField.crop} <span className="font-normal text-[11px] text-[#292B26]/60">({selectedField.variety})</span>
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Phenological Stage</span>
                  <span className="font-semibold text-[#17643E] bg-[#A8C69A]/20 px-2.5 py-0.5 rounded-full text-[11px]">
                    {selectedField.stage}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Soil Moisture (0–30cm)</span>
                  <span className={`font-bold ${selectedField.moisturePercent < 20 ? 'text-[#B6532A]' : 'text-[#17643E]'}`}>
                    {selectedField.moisturePercent}% ({selectedField.moistureStatus})
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Estimated Yield (Sample)</span>
                  <span className="font-bold text-[#103D2C]">{selectedField.estYield}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Canopy NDVI (Index)</span>
                  <span className="font-bold text-[#103D2C]">{selectedField.ndvi.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Soil Type</span>
                  <span className="font-medium text-[#292B26]">{selectedField.soilType}</span>
                </div>

                {/* Field-specific Alert/Action Box */}
                {selectedField.status === 'Alert' ? (
                  <div className="mt-4 bg-[#FBF7EF] p-3.5 rounded-xl border border-[#B6532A]/30 space-y-1.5">
                    <div className="flex items-start gap-1.5">
                      <AlertTriangle size={15} className="text-[#B6532A] shrink-0 mt-0.5" />
                      <h4 className="font-bold text-[#B6532A] text-xs">{selectedField.alertTitle}</h4>
                    </div>
                    <p className="text-[11px] text-[#292B26]/75 leading-relaxed">
                      {selectedField.alertDesc}
                    </p>
                  </div>
                ) : (
                  <div className="mt-4 bg-emerald-50/70 p-3.5 rounded-xl border border-emerald-200 space-y-1">
                    <div className="flex items-center gap-1.5 text-emerald-900 font-bold text-xs">
                      <CheckCircle2 size={14} className="text-emerald-700" />
                      <span>Vegetation Vigor Optimal</span>
                    </div>
                    <p className="text-[11px] text-emerald-900/80 leading-relaxed">
                      Root-zone soil moisture is adequate. No moisture stress or canopy deficit detected.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              /* All Fields Overview */
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Total Cultivated Area</span>
                  <span className="font-bold text-[#103D2C]">12.0 Acres</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Active Fields</span>
                  <span className="font-bold text-[#103D2C]">2 Parcels</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Average Farm Moisture</span>
                  <span className="font-bold text-amber-700">26.0% (Mixed)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#292B26]/70">Active Warnings</span>
                  <span className="font-bold text-[#B6532A]">1 Alert (Field 2)</span>
                </div>
                <p className="text-[11px] text-[#292B26]/60 pt-2 border-t border-[#E5DDCF]">
                  Select Field 1 or Field 2 to inspect parcel-specific micro-telemetry and action items.
                </p>
              </div>
            )}
          </div>

          {/* Micro-Climate Panel */}
          <div className="bg-white rounded-2xl border border-[#E5DDCF] shadow-sm p-5 space-y-3">
            <div className="border-b border-[#E5DDCF] pb-2 flex justify-between items-center">
              <h3 className="font-bold text-[#103D2C] text-sm">Micro-Climate (Sample)</h3>
              <span className="text-[10px] text-[#292B26]/50">Nashik District</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF]">
                <Thermometer size={16} className="mx-auto text-[#17643E] mb-1" />
                <div className="text-base font-bold text-[#103D2C]">32°C</div>
                <div className="text-[10px] text-[#292B26]/60">Air Temp</div>
              </div>
              <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF]">
                <Wind size={16} className="mx-auto text-[#17643E] mb-1" />
                <div className="text-base font-bold text-[#103D2C]">58%</div>
                <div className="text-[10px] text-[#292B26]/60">Rel. Humidity</div>
              </div>
              <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF]">
                <Compass size={16} className="mx-auto text-[#17643E] mb-1" />
                <div className="text-base font-bold text-[#103D2C]">12 km/h</div>
                <div className="text-[10px] text-[#292B26]/60">Wind (WNW)</div>
              </div>
              <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF]">
                <Droplets size={16} className="mx-auto text-[#17643E] mb-1" />
                <div className="text-base font-bold text-[#103D2C]">0 mm</div>
                <div className="text-[10px] text-[#292B26]/60">Rain (72h)</div>
              </div>
            </div>

            <div className="bg-[#FBF7EF] p-2.5 rounded-xl border border-[#E5DDCF] text-[10px] text-[#292B26]/70 leading-relaxed">
              <span className="font-bold text-[#103D2C] block">Data Provenance:</span>
              Demonstration digital twin with synthetic field parameters. Does not represent live hardware telemetry or real-world sensor logs.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
