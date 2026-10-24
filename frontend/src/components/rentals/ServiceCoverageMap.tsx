import React, { useState } from 'react';
import { MapPin, Navigation, Info, ShieldCheck, Tractor, Compass } from 'lucide-react';
import { RentalListing } from '../../types/rental';

interface ServiceCoverageMapProps {
  listings: RentalListing[];
  onSelectListing: (listing: RentalListing) => void;
  farmLocationName?: string;
}

export default function ServiceCoverageMap({
  listings,
  onSelectListing,
  farmLocationName = 'Shioni, Akola Road'
}: ServiceCoverageMapProps) {
  const [selectedHub, setSelectedHub] = useState<string | null>(null);

  // Vidarbha Hubs Coordinates translated to SVG canvas (width: 700, height: 420)
  // Centered around Akola (20.7002, 77.0082)
  const hubs = [
    { name: 'Akola City (Central CHC)', taluka: 'Akola', x: 350, y: 210, radius: 85, color: '#17643E' },
    { name: 'Murtizapur Hub', taluka: 'Murtizapur', x: 520, y: 220, radius: 70, color: '#B6532A' },
    { name: 'Telhara Agri Syndicate', taluka: 'Telhara', x: 280, y: 100, radius: 65, color: '#2B6CB0' },
    { name: 'Balapur Rural Transport', taluka: 'Balapur', x: 200, y: 230, radius: 75, color: '#6B46C1' },
    { name: 'Barshitakli Krushi Yantra', taluka: 'Barshitakli', x: 390, y: 320, radius: 65, color: '#D69E2E' },
  ];

  // Farm Location (Shioni, ~8km from Akola Central)
  const farmPos = { x: 375, y: 195 };

  return (
    <div className="bg-white rounded-3xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-serif font-bold text-base text-[#103D2C]">
              Regional Service Coverage & Machinery Hubs
            </h3>
            <span className="text-[10px] font-bold text-[#17643E] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Akola & Vidarbha Zone
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Real-time coverage radiuses from registered Custom Hiring Centers & local tractor cooperatives.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-600 bg-[#FBF7EF] px-3 py-1.5 rounded-xl border border-[#E5DDCF]">
          <Navigation size={13} className="text-[#103D2C]" />
          <span>Active Farm: <strong>{farmLocationName}</strong></span>
        </div>
      </div>

      {/* SVG Map Container */}
      <div className="relative bg-[#FBF7EF] border border-[#E5DDCF] rounded-2xl overflow-hidden p-2 flex items-center justify-center">
        <svg viewBox="0 0 700 420" className="w-full h-auto max-h-[380px] select-none">
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 30" fill="none" stroke="#E5DDCF" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="700" height="420" fill="url(#grid)" />

          {/* District boundary outline (Stylized Vidarbha / Akola district) */}
          <path
            d="M 120 180 Q 240 50 450 60 Q 620 90 640 250 Q 580 380 380 390 Q 180 370 120 180 Z"
            fill="#F4EBD9"
            fillOpacity="0.4"
            stroke="#D8CCB7"
            strokeWidth="1.5"
            strokeDasharray="4 2"
          />

          {/* Radius circles for hubs */}
          {hubs.map((hub) => (
            <g key={hub.name}>
              <circle
                cx={hub.x}
                cy={hub.y}
                r={hub.radius}
                fill={hub.color}
                fillOpacity={selectedHub === hub.taluka ? 0.22 : 0.08}
                stroke={hub.color}
                strokeWidth={selectedHub === hub.taluka ? 2 : 1}
                strokeDasharray={selectedHub === hub.taluka ? 'none' : '3 3'}
                className="transition-all duration-300"
              />
              {/* Hub Center Marker */}
              <circle
                cx={hub.x}
                cy={hub.y}
                r={selectedHub === hub.taluka ? 8 : 6}
                fill={hub.color}
                stroke="#FFFFFF"
                strokeWidth="2"
                className="cursor-pointer hover:scale-125 transition-transform"
                onClick={() => setSelectedHub(hub.taluka)}
              />
              <text
                x={hub.x}
                y={hub.y - 12}
                textAnchor="middle"
                fontSize="11"
                fontWeight="bold"
                fill="#103D2C"
              >
                {hub.taluka}
              </text>
            </g>
          ))}

          {/* Farmer's Farm Marker */}
          <g>
            <circle cx={farmPos.x} cy={farmPos.y} r="14" fill="#B6532A" fillOpacity="0.25" className="animate-ping" />
            <circle cx={farmPos.x} cy={farmPos.y} r="8" fill="#B6532A" stroke="#FFFFFF" strokeWidth="2" />
            <text
              x={farmPos.x}
              y={farmPos.y + 20}
              textAnchor="middle"
              fontSize="11"
              fontWeight="bold"
              fill="#B6532A"
            >
              ★ Your Farm
            </text>
          </g>
        </svg>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm p-3 rounded-xl border border-[#E5DDCF] text-[11px] space-y-1.5 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#B6532A]"></span>
            <span>Your Farm Location (Akola)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#17643E]"></span>
            <span>CHC Machinery Hub (25-35 km Service Radius)</span>
          </div>
        </div>
      </div>

      {/* Hub Listings quick list */}
      {selectedHub && (
        <div className="bg-[#FBF7EF] p-4 rounded-2xl border border-[#E5DDCF] space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-bold text-[#103D2C]">
              Machinery Available in {selectedHub} Taluka:
            </span>
            <button
              onClick={() => setSelectedHub(null)}
              className="text-gray-400 hover:text-gray-600 font-semibold"
            >
              Clear Filter
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            {listings
              .filter(l => l.taluka.toLowerCase() === selectedHub.toLowerCase())
              .map(l => (
                <div
                  key={l.id}
                  onClick={() => onSelectListing(l)}
                  className="bg-white p-2.5 rounded-xl border border-[#E5DDCF] hover:border-[#17643E] cursor-pointer flex items-center justify-between text-xs transition-colors"
                >
                  <div className="font-semibold text-gray-800 line-clamp-1">{l.title}</div>
                  <span className="font-bold text-[#17643E] shrink-0 ml-2">₹{l.price}/{l.billing_unit.replace('per_', '')}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
