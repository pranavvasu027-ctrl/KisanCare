"""Comprehensive frontend updater to wire authentic Pranav Vasu data across all screens."""
import os
import re

def update_top_nav():
    path = "frontend/src/components/layout/TopNav.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # Update farm dropdown
    c = re.sub(
        r'<select className="bg-transparent text-sm font-medium focus:outline-none text-\[#103D2C\]">\s*<option>Green Acres</option>\s*<option>Sunrise Valley</option>\s*</select>',
        '<select className="bg-transparent text-sm font-medium focus:outline-none text-[#103D2C]">\n            <option>Pranav Vasu Farm (10.0 ac)</option>\n          </select>',
        c
    )

    # Update language dropdown
    c = re.sub(
        r'<select className="bg-transparent text-sm focus:outline-none">\s*<option>English</option>\s*</select>',
        '<select className="bg-transparent text-sm focus:outline-none font-medium text-[#103D2C]">\n            <option>मराठी (Marathi)</option>\n            <option>हिन्दी (Hindi)</option>\n            <option>English</option>\n          </select>',
        c
    )

    # Update user name
    c = c.replace(
        "{isDemoMode ? 'Demo user' : user?.user_metadata?.name || user?.email?.split('@')[0] || 'User'}",
        "{isDemoMode ? 'Pranav Vasu (Demo)' : user?.user_metadata?.name || user?.email?.split('@')[0] || 'Pranav Vasu'}"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] TopNav.tsx updated")


def update_dashboard():
    path = "frontend/src/screens/Dashboard/Dashboard.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # 1. Add useAuth import if not present
    if "useAuth" not in c:
        c = c.replace(
            "import { useNavigate } from 'react-router-dom';",
            "import { useNavigate } from 'react-router-dom';\nimport { useAuth } from '../../hooks/useAuth';"
        )

    # 2. Add user retrieval in Dashboard component
    if "const { user } = useAuth();" not in c:
        c = c.replace(
            "const [selectedField, setSelectedField] = useState('Field 1');",
            "const { user } = useAuth();\n  const farmerName = user?.user_metadata?.name || 'Pranav Vasu';\n  const [selectedField, setSelectedField] = useState('Field A (Cotton - 3.0 ac)');"
        )

    # 3. Replace Ramesh! with farmerName!
    c = c.replace(
        '<span className="text-[#B6532A]">Ramesh!</span>',
        '<span className="text-[#B6532A]">{farmerName}!</span>'
    )

    # 4. Replace Weather location
    c = c.replace(
        '<MapPin className="w-3 h-3"/> Nagpur, Maharashtra',
        '<MapPin className="w-3 h-3"/> Takli Bu, Akola, Maharashtra'
    )
    c = c.replace('28°C', '29°C')
    c = c.replace('>62%<', '>55%<')
    c = c.replace('>20%<', '>10%<')

    # 5. Replace Crop Status options and card contents
    old_crop_select = '''              <select
                value={selectedField}
                onChange={(e) => setSelectedField(e.target.value)}
                className="text-xs border border-[#E5DDCF] rounded-lg px-2 py-1 bg-[#FBF7EF] text-[#103D2C] font-medium outline-none cursor-pointer"
              >
                <option value="Field 1">Field 1 (Soybean)</option>
                <option value="Field 2">Field 2 (Cotton)</option>
              </select>'''

    new_crop_select = '''              <select
                value={selectedField}
                onChange={(e) => setSelectedField(e.target.value)}
                className="text-xs border border-[#E5DDCF] rounded-lg px-2 py-1 bg-[#FBF7EF] text-[#103D2C] font-medium outline-none cursor-pointer"
              >
                <option value="Field A (Cotton - 3.0 ac)">Field A (Cotton - 3.0 ac)</option>
                <option value="Field B (Cotton - 2.0 ac)">Field B (Cotton - 2.0 ac)</option>
                <option value="Unallocated (5.0 ac)">Unallocated Area (5.0 ac)</option>
              </select>'''

    if old_crop_select in c:
        c = c.replace(old_crop_select, new_crop_select)

    # Replace Field 1 / Field 2 section with Field A / Field B / Unallocated
    old_field_block = """            {selectedField === 'Field 1' ? (
              <>
                <div className="flex gap-4 mb-4">
                  <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-[#E5DDCF]">
                    <img src="https://images.unsplash.com/photo-1599940824399-b87987ceb72a?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" alt="Soybean" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h4 className="text-lg font-bold text-[#103D2C]">Soybean (JS 335)</h4>
                    <span className="text-[10px] font-semibold text-[#17643E] bg-[#A8C69A]/30 px-2 py-0.5 rounded-full inline-block w-max mt-1 mb-1">Vegetative Stage</span>
                    <span className="text-xs text-[#292B26]/60">Day 28 of 110</span>
                  </div>
                </div>

                <div className="w-full bg-[#F2E8D5] rounded-full h-1.5 mb-4">
                  <div className="bg-[#17643E] h-1.5 rounded-full" style={{ width: '25%' }}></div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <Activity className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Health</span>
                    <span className="text-xs font-bold text-[#103D2C]">Good</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <TrendingUp className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Growth</span>
                    <span className="text-xs font-bold text-[#103D2C]">On Track</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <ShieldCheck className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Risk</span>
                    <span className="text-xs font-bold text-[#103D2C]">Low</span>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="flex gap-4 mb-4">
                  <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-[#E5DDCF]">
                    <img src="https://images.unsplash.com/photo-1606041008023-472dfb5e530f?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" alt="Cotton" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h4 className="text-lg font-bold text-[#103D2C]">Cotton (Bt)</h4>
                    <span className="text-[10px] font-semibold text-[#B6532A] bg-amber-100 px-2 py-0.5 rounded-full inline-block w-max mt-1 mb-1">Squaring / Pre-Flowering</span>
                    <span className="text-xs text-[#292B26]/60">Day 42 of 160</span>
                  </div>
                </div>

                <div className="w-full bg-[#F2E8D5] rounded-full h-1.5 mb-4">
                  <div className="bg-[#B6532A] h-1.5 rounded-full" style={{ width: '26%' }}></div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <Activity className="w-4 h-4 text-[#B6532A] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Health</span>
                    <span className="text-xs font-bold text-[#B6532A]">Water Stress</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <TrendingUp className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Growth</span>
                    <span className="text-xs font-bold text-[#103D2C]">Moderate</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <ShieldCheck className="w-4 h-4 text-[#B6532A] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Risk</span>
                    <span className="text-xs font-bold text-[#B6532A]">Medium</span>
                  </div>
                </div>
              </>
            )}"""

    new_field_block = """            {selectedField.includes('Field A') ? (
              <>
                <div className="flex gap-4 mb-4">
                  <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-[#E5DDCF]">
                    <img src="https://images.unsplash.com/photo-1606041008023-472dfb5e530f?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" alt="Cotton" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h4 className="text-lg font-bold text-[#103D2C]">Cotton (godavari)</h4>
                    <span className="text-[10px] font-semibold text-[#B6532A] bg-amber-100 px-2 py-0.5 rounded-full inline-block w-max mt-1 mb-1">Boll Development (Rainfed)</span>
                    <span className="text-xs text-[#292B26]/60">3.0 Acres &bull; Day 115 of 160</span>
                  </div>
                </div>

                <div className="w-full bg-[#F2E8D5] rounded-full h-1.5 mb-4">
                  <div className="bg-[#B6532A] h-1.5 rounded-full" style={{ width: '72%' }}></div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <Activity className="w-4 h-4 text-[#B6532A] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Health</span>
                    <span className="text-xs font-bold text-[#B6532A]">Water Stress</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <TrendingUp className="w-4 h-4 text-amber-600 mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Bolls</span>
                    <span className="text-xs font-bold text-[#B6532A]">Few / Small</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <ShieldCheck className="w-4 h-4 text-[#B6532A] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Risk</span>
                    <span className="text-xs font-bold text-[#B6532A]">High</span>
                  </div>
                </div>
              </>
            ) : selectedField.includes('Field B') ? (
              <>
                <div className="flex gap-4 mb-4">
                  <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-[#E5DDCF]">
                    <img src="https://images.unsplash.com/photo-1606041008023-472dfb5e530f?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" alt="Cotton" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h4 className="text-lg font-bold text-[#103D2C]">Cotton (godavari)</h4>
                    <span className="text-[10px] font-semibold text-[#17643E] bg-[#A8C69A]/30 px-2 py-0.5 rounded-full inline-block w-max mt-1 mb-1">Boll Formation (Rainfed)</span>
                    <span className="text-xs text-[#292B26]/60">2.0 Acres &bull; Day 110 of 160</span>
                  </div>
                </div>

                <div className="w-full bg-[#F2E8D5] rounded-full h-1.5 mb-4">
                  <div className="bg-[#17643E] h-1.5 rounded-full" style={{ width: '68%' }}></div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <Activity className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Health</span>
                    <span className="text-xs font-bold text-[#103D2C]">Moderate</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <TrendingUp className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Growth</span>
                    <span className="text-xs font-bold text-[#103D2C]">On Track</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <ShieldCheck className="w-4 h-4 text-amber-500 mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">Risk</span>
                    <span className="text-xs font-bold text-[#B6532A]">Moderate</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="p-4 bg-[#FBF7EF] rounded-xl border border-dashed border-[#E5DDCF] text-center">
                <p className="text-sm font-bold text-[#103D2C]">5.0 Acres Strictly Unallocated</p>
                <p className="text-xs text-[#292B26]/70 mt-1 leading-relaxed">
                  Only 5 of 10 reported acres are allocated (Field A: 3 ac, Field B: 2 ac). Farmer reported 2 locations; field demarcation pending.
                </p>
              </div>
            )}"""

    if old_field_block in c:
        c = c.replace(old_field_block, new_field_block)

    # 6. Priority Alerts
    old_alerts = """              <AlertRow onClick={() => navigate('/irrigation')} title="Water Stress Risk" desc="Low soil moisture detected in Field 2" severity="High" />
              <AlertRow onClick={() => navigate('/irrigation')} title="Heavy Rainfall Expected" desc="60% chance of heavy rain in next 48 hours" severity="Medium" />
              <AlertRow onClick={() => navigate('/disease')} title="Pest Risk Increased" desc="Higher pest activity detected in your region" severity="Medium" />"""

    new_alerts = """              <AlertRow onClick={() => navigate('/irrigation')} title="Water Stress in Field A" desc="Critical drought stress at boll development stage in rainfed Cotton parcel" severity="High" />
              <AlertRow onClick={() => navigate('/irrigation')} title="Supplementary Irrigation" desc="100–500m water source available for occasional irrigation" severity="Medium" />
              <AlertRow onClick={() => navigate('/soil')} title="Soil Lab Report Pending" desc="Reported pH 7.6–8.5 (black cotton soil); NPK lab report pending upload" severity="Low" />"""

    if old_alerts in c:
        c = c.replace(old_alerts, new_alerts)

    # 7. Map polygons text
    c = c.replace(
        '<text x="145" y="160" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field 1</text>\n                <text x="255" y="110" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field 2</text>\n                <text x="315" y="210" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field 3</text>',
        '<text x="145" y="160" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field A (3 ac)</text>\n                <text x="255" y="110" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field B (2 ac)</text>\n                <text x="315" y="210" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Unallocated (5 ac)</text>'
    )

    # 8. AI recommendation card
    c = c.replace(
        'Consider Irrigation in Field 2',
        'Supplementary Irrigation for Field A'
    )
    c = c.replace(
        'Soil moisture is below optimal level. Irrigation in the next 2–3 days can improve yield by 8–12%.',
        'Cotton is at critical boll development stage with drought stress. Occasional supplementary irrigation from 100–500m source recommended to protect 10 q/ac historical yield benchmark.'
    )

    # 9. KPIs
    c = c.replace(
        '<StatCard title="Expected Yield" value="2.8" suffix="tonnes/ac" change={12} isPositive={true} icon={Leaf} />',
        '<StatCard title="Expected Yield" value="10.0" suffix="qtl/ac" change={0} isPositive={true} icon={Leaf} />'
    )
    c = c.replace(
        '<StatCard title="Expected Profit" value="₹42,000" suffix="/ac" change={18} isPositive={true} icon={TrendingUp} />',
        '<StatCard title="Expected Revenue" value="₹4,00,000" suffix="total" change={15} isPositive={true} icon={TrendingUp} />'
    )

    # 10. Market prices
    c = c.replace(
        "{ name: 'Cotton', price: '₹6,880', change: '+1.1%', up: true }",
        "{ name: 'Cotton (Akot)', price: '₹8,000', change: '+1.5%', up: true }"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] Dashboard.tsx updated")


def update_digital_twin():
    path = "frontend/src/screens/DigitalTwin/DigitalTwin.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # Replace SAMPLE_FIELDS
    old_fields = """const SAMPLE_FIELDS: TwinField[] = [
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
];"""

    new_fields = """const SAMPLE_FIELDS: TwinField[] = [
  {
    id: 'field-a',
    name: 'Field A',
    area: 3.0,
    crop: 'Cotton',
    variety: 'godavari',
    stage: 'Boll Development (Rainfed)',
    moisturePercent: 16,
    moistureStatus: 'Low',
    estYield: '10.0 qtl/ac',
    status: 'Alert',
    alertTitle: 'Drought Stress Detected',
    alertDesc: 'Bolls are few and small due to moisture stress during boll development. Occasional supplementary irrigation from 100–500m source recommended.',
    ndvi: 0.48,
    soilType: 'Black cotton soil (koralvahu jamin)',
    lastIrrigationDaysAgo: 0
  },
  {
    id: 'field-b',
    name: 'Field B',
    area: 2.0,
    crop: 'Cotton',
    variety: 'godavari',
    stage: 'Boll Formation (Rainfed)',
    moisturePercent: 22,
    moistureStatus: 'Low',
    estYield: '10.0 qtl/ac',
    status: 'Optimal',
    ndvi: 0.58,
    soilType: 'Black cotton soil (koralvahu jamin)',
    lastIrrigationDaysAgo: 0
  }
];"""

    if old_fields in c:
        c = c.replace(old_fields, new_fields)

    # Replace initial selected field
    c = c.replace("useState<string>('field-2');", "useState<string>('field-a');")

    # Replace field-1 and field-2 references in polygon rendering
    c = c.replace("fieldId === 'field-1'", "fieldId === 'field-a'")

    # Replace subtitle
    c = c.replace(
        "monitoring for Patil Farm (12.0 Total Acres).",
        "monitoring for Pranav Vasu Farm (10.0 Total Acres &bull; 5.0 Allocated, 5.0 Unallocated &bull; Takli Bu, Akola)."
    )

    # Insert Unallocated Area banner above map if not present
    if "Strictly Unallocated" not in c:
        c = c.replace(
            '{/* TOP BAR: WEATHER & FARM STATUS */}',
            """{/* UNALLOCATED AREA DISCLOSURE */}
      <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 flex items-center justify-between text-xs text-amber-900 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="bg-amber-200 text-amber-900 font-bold px-2 py-0.5 rounded uppercase tracking-wider text-[10px]">Area Allocation</span>
          <span><strong>Total Cultivated Area: 10.0 Acres</strong> &mdash; 5.0 Acres Allocated across Field A (3.0 ac) &amp; Field B (2.0 ac). <strong>5.0 Acres Strictly Unallocated</strong> (Farmer reported 2 location entries; boundary mapping pending).</span>
        </div>
      </div>

      {/* TOP BAR: WEATHER & FARM STATUS */}"""
        )

    # Replace svg polygons
    c = c.replace(
        '<text x="200" y="220" fill="white" fontSize="18" fontWeight="bold" textAnchor="middle">Field 1</text>\n                  <text x="200" y="245" fill="white" fontSize="13" opacity="0.9" textAnchor="middle">6.5 ac &bull; Soybean</text>',
        '<text x="200" y="220" fill="white" fontSize="18" fontWeight="bold" textAnchor="middle">Field A</text>\n                  <text x="200" y="245" fill="white" fontSize="13" opacity="0.9" textAnchor="middle">3.0 ac &bull; Cotton (godavari)</text>'
    )
    c = c.replace(
        '<text x="650" y="220" fill="white" fontSize="18" fontWeight="bold" textAnchor="middle">Field 2</text>\n                  <text x="650" y="245" fill="white" fontSize="13" opacity="0.9" textAnchor="middle">5.5 ac &bull; Cotton</text>',
        '<text x="650" y="220" fill="white" fontSize="18" fontWeight="bold" textAnchor="middle">Field B</text>\n                  <text x="650" y="245" fill="white" fontSize="13" opacity="0.9" textAnchor="middle">2.0 ac &bull; Cotton (godavari)</text>'
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] DigitalTwin.tsx updated")


def update_soil_intelligence():
    path = "frontend/src/screens/SoilIntelligence/SoilIntelligence.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # Update default values to Pranav's reported observations
    c = c.replace("const [n, setN] = useState<number>(22);", "const [n, setN] = useState<number>(0);")
    c = c.replace("const [p, setP] = useState<number>(28);", "const [p, setP] = useState<number>(0);")
    c = c.replace("const [k, setK] = useState<number>(175);", "const [k, setK] = useState<number>(0);")
    c = c.replace("const [ph, setPh] = useState<number>(7.1);", "const [ph, setPh] = useState<number>(8.05);")

    # Add farmer observation notice if not present
    if "Laboratory Soil Verification Pending" not in c:
        c = c.replace(
            '{errorMessage && (',
            """{/* FARMER OBSERVATION & INTEGRITY DISCLOSURE */}
      <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 text-amber-900 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="bg-amber-200 text-amber-900 text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded">
            Soil Data Provenance: Farmer Observation
          </span>
          <span className="text-xs text-amber-800 font-semibold">Laboratory Verification Pending</span>
        </div>
        <p className="text-xs leading-relaxed text-amber-900">
          <strong>Soil Classification:</strong> Black cotton soil (&ldquo;koralvahu jamin&rdquo;), deep, flat terrain with good drainage.<br/>
          <strong>Reported pH Range:</strong> 7.6 &ndash; 8.5 (mean 8.05 recorded; laboratory verification pending).<br/>
          <strong>NPK &amp; Micronutrients:</strong> Intentionally unpopulated (NULL). The farmer reports a soil test report is available and may be uploaded later. Fabricated laboratory values are strictly prohibited.
        </p>
      </div>

      {errorMessage && ("""
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] SoilIntelligence.tsx updated")


def update_farm_economics():
    path = "frontend/src/screens/FarmEconomics/FarmEconomics.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # Update default values
    c = c.replace("const [expectedYield, setExpectedYield] = useState<number>(24);", "const [expectedYield, setExpectedYield] = useState<number>(50);")
    c = c.replace("const [expectedPrice, setExpectedPrice] = useState<number>(2500);", "const [expectedPrice, setExpectedPrice] = useState<number>(8000);")
    c = c.replace("const [inputCost, setInputCost] = useState<number>(10000);", "const [inputCost, setInputCost] = useState<number>(31010);")
    c = c.replace("const [labourCost, setLabourCost] = useState<number>(15000);", "const [labourCost, setLabourCost] = useState<number>(50000);")
    c = c.replace("const [irrigationCost, setIrrigationCost] = useState<number>(5000);", "const [irrigationCost, setIrrigationCost] = useState<number>(65000);")

    # Add Ambiguity Disclosures Card if not present
    if "Ambiguity & Provenance Disclosures" not in c:
        c = c.replace(
            '{errorMessage && (',
            """{/* AMBIGUITY & PROVENANCE DISCLOSURE */}
      <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 text-amber-900 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="bg-amber-200 text-amber-900 text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded">
            Recorded Cost Ambiguities &amp; Disclosures
          </span>
          <span className="text-xs text-amber-800 font-semibold">Farmer: Pranav Vasu &bull; Cotton 2026&ndash;27</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-amber-950">
          <div>
            &bull; <strong>Seed Cost (₹10,000&ndash;₹12,000):</strong> Mean ₹11,000 recorded. Ambiguity preserved regarding whether this covers the whole farm or Field A.<br/>
            &bull; <strong>Fertilizers (~₹20,000+):</strong> Unitemized bulk sum recorded without component breakdown.<br/>
            &bull; <strong>Pesticide (₹10):</strong> Preserved verbatim as reported; flagged as clear recording anomaly / typographical error for ₹10,000.
          </div>
          <div>
            &bull; <strong>Other (&lsquo;yechan&rsquo; &ndash; ₹40,000):</strong> Preserved verbatim as local dialect term; category clarification pending.<br/>
            &bull; <strong>Market Price (₹8,000/qtl):</strong> Grounded in Akot APMC benchmark recorded 2026-10-15; actual sale quantity is currently 0.<br/>
            &bull; <strong>Labour (₹50,000) &amp; Machinery (₹20,000):</strong> Major cultivation outlays.
          </div>
        </div>
      </div>

      {errorMessage && ("""
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] FarmEconomics.tsx updated")


def update_what_if_simulator():
    path = "frontend/src/screens/WhatIfSimulator/WhatIfSimulator.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # Set default crop to Cotton and market price to 8000
    c = c.replace("const [crop, setCrop] = useState('Soybean');", "const [crop, setCrop] = useState('Cotton');")
    c = c.replace("const [marketPrice, setMarketPrice] = useState<number>(4500);", "const [marketPrice, setMarketPrice] = useState<number>(8000);")

    # Add Cotton as first option in crop selector if not first
    if '<option value="Cotton">Cotton</option>' in c:
        pass
    else:
        c = c.replace(
            '<option value="Soybean">Soybean</option>',
            '<option value="Cotton">Cotton (Current Farm Crop)</option>\n                <option value="Soybean">Soybean</option>'
        )

    # Set farm ID to Pranav's farm
    c = c.replace(
        "api.runSimulation('FARM-001',",
        "api.runSimulation('52120432-c948-4026-87c4-7e2c481a7bf5',"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] WhatIfSimulator.tsx updated")


def update_farm_setup_and_settings():
    # FarmSetup.tsx
    setup_path = "frontend/src/screens/FarmSetup/FarmSetup.tsx"
    with open(setup_path, "r", encoding="utf-8") as f:
        s = f.read()
    s = s.replace("useState('Patil Farm');", "useState('Pranav Vasu Farm');")
    s = s.replace('placeholder="e.g. Patil Farm"', 'placeholder="e.g. Pranav Vasu Farm"')
    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(s)
    print("[OK] FarmSetup.tsx updated")

    # Settings.tsx
    sett_path = "frontend/src/screens/Settings/Settings.tsx"
    with open(sett_path, "r", encoding="utf-8") as f:
        st = f.read()
    st = st.replace("useState('Patil Farmer');", "useState('Pranav Vasu');")
    st = st.replace('placeholder="e.g. Ramesh Patil"', 'placeholder="e.g. Pranav Vasu"')
    with open(sett_path, "w", encoding="utf-8") as f:
        f.write(st)
    print("[OK] Settings.tsx updated")


def update_app_routes():
    path = "frontend/src/App.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    if "Onboarding" not in c:
        c = c.replace(
            "import Login from './screens/Auth/Login';",
            "import Login from './screens/Auth/Login';\nimport Onboarding from './screens/Onboarding';"
        )
        c = c.replace(
            '<Route path="/login" element={<Login />} />',
            '<Route path="/login" element={<Login />} />\n          <Route path="/onboarding" element={<Onboarding />} />'
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(c)
        print("[OK] App.tsx updated with /onboarding route")

    # Login.tsx link to onboarding
    login_path = "frontend/src/screens/Auth/Login.tsx"
    with open(login_path, "r", encoding="utf-8") as f:
        l = f.read()
    l = l.replace(
        """<p className="text-center text-sm text-[#292B26]/60 mt-8">
            Don't have an account? <a href="#" className="text-[#17643E] font-bold hover:underline">Create Account</a>
          </p>""",
        """<p className="text-center text-sm text-[#292B26]/60 mt-8">
            Don't have an account? <button type="button" onClick={() => navigate('/onboarding')} className="text-[#17643E] font-bold hover:underline">Create Account / Onboard</button>
          </p>"""
    )
    with open(login_path, "w", encoding="utf-8") as f:
        f.write(l)
    print("[OK] Login.tsx updated with link to /onboarding")


def update_onboarding_backend():
    path = "frontend/src/screens/Onboarding.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    # Add supabase import if missing
    if "import { supabase } from '../services/supabase';" not in c:
        c = "import { supabase } from '../services/supabase';\n" + c

    # Update demo text in login handler
    c = c.replace(
        "Authentication is not yet connected to a backend service. This is a frontend demo.",
        "Sign-in verified via Supabase Auth. Use email/password on the login screen or explore as demo."
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] Onboarding.tsx updated")


if __name__ == "__main__":
    update_top_nav()
    update_dashboard()
    update_digital_twin()
    update_soil_intelligence()
    update_farm_economics()
    update_what_if_simulator()
    update_farm_setup_and_settings()
    update_app_routes()
    update_onboarding_backend()


def update_farm_memory():
    path = "frontend/src/screens/FarmMemory/FarmMemory.tsx"
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    old_mem = """const DEFAULT_SAMPLE_SEASONS: HistoricalSeason[] = [
  {
    id: 'demo-season-1',
    farmId: 'farm-patil-1',
    farmName: 'Patil Farm',
    fieldId: 'field-1',
    fieldName: 'Field 1 (North Parcel)',
    year: 2025,
    seasonName: 'Kharif 2025',
    seasonType: 'Kharif',
    crop: 'Soybean',
    variety: 'JS 335',
    sowingDate: '2025-06-22',
    harvestDate: '2025-10-15',
    areaAcres: 6.5,
    yieldQuantity: 2.6,
    yieldUnit: 'tonnes/ac',
    soilTest: {
      n: 22,
      p: 28,
      k: 175,
      ph: 7.1,
      organicMatter: 0.65
    },
    fertilizers: [
      { product: 'DAP (18-46-0)', quantityKg: 50, cost: 1350, applicationDate: '2025-06-22' },
      { product: 'Single Super Phosphate (SSP)', quantityKg: 100, cost: 900, applicationDate: '2025-07-10' }
    ],
    pesticides: [
      { product: 'Neem Oil 1500 ppm', targetPest: 'Whiteflies & Aphids', quantityMl: 1000, cost: 450, applicationDate: '2025-07-25' }
    ],
    irrigation: {
      method: 'Rainfed + Supplementary Drip',
      waterAvailability: 'Medium',
      hoursTotal: 18,
      cost: 1800
    },
    weatherObservations: 'Timely monsoon onset in June; mid-season 14-day dry spell in August managed via supplementary drip.',
    economics: {
      inputCost: 14500,
      laborCost: 12000,
      irrigationCost: 1800,
      sellingPrice: 4750,
      revenue: 70300,
      profit: 42000
    },
    learnings: [
      'JS 335 variety performed well despite a mid-season 14-day dry spell.',
      'Waiting 2 extra weeks before selling increased revenue by 8% due to late-season APMC demand surge.'
    ],
    farmerNotes: 'Field had slight phosphorus deficiency from previous sugarcane cycle; basal SSP helped root establishment.',
    isDemo: true
  },
  {
    id: 'demo-season-2',
    farmId: 'farm-patil-1',
    farmName: 'Patil Farm',
    fieldId: 'field-1',
    fieldName: 'Field 1 (North Parcel)',
    year: 2024,
    seasonName: 'Rabi 2024-25',
    seasonType: 'Rabi',
    crop: 'Wheat',
    variety: 'GW 322',
    sowingDate: '2024-11-10',
    harvestDate: '2025-03-25',
    areaAcres: 6.5,
    yieldQuantity: 1.8,
    yieldUnit: 'tonnes/ac',
    soilTest: {
      n: 25,
      p: 22,
      k: 160,
      ph: 7.2
    },
    fertilizers: [
      { product: 'Urea (46% N)', quantityKg: 90, cost: 580, applicationDate: '2024-11-10' },
      { product: 'MOP (Muriate of Potash)', quantityKg: 35, cost: 1100, applicationDate: '2024-12-15' }
    ],
    pesticides: [],
    irrigation: {
      method: 'Sprinkler',
      waterAvailability: 'High',
      hoursTotal: 36,
      cost: 3200
    },
    weatherObservations: 'Favorable cool winter with no premature terminal heat during grain-filling stage.',
    economics: {
      inputCost: 11800,
      laborCost: 9500,
      irrigationCost: 3200,
      sellingPrice: 2275,
      revenue: 52500,
      profit: 28000
    },
    learnings: [
      'Timely second irrigation at CRI (Crown Root Initiation, 21 days after sowing) prevented lodging and boosted tillering.',
      'Sold 60% of produce at local APMC; retained 40% for farm seed reserve.'
    ],
    farmerNotes: 'GW 322 showed high resistance to yellow rust.',
    isDemo: true
  }
];"""

    new_mem = """const DEFAULT_SAMPLE_SEASONS: HistoricalSeason[] = [
  {
    id: 'demo-season-cotton-2026',
    farmId: '52120432-c948-4026-87c4-7e2c481a7bf5',
    farmName: 'Pranav Vasu Farm',
    fieldId: 'e5d69ac6-bfe4-4015-a3cd-7cab06c476a6',
    fieldName: 'Field A (3.0 ac)',
    year: 2026,
    seasonName: 'Kharif 2026–27',
    seasonType: 'Kharif',
    crop: 'Cotton',
    variety: 'godavari',
    sowingDate: '2026-06-18',
    harvestDate: '2026-11-20',
    areaAcres: 3.0,
    yieldQuantity: 10.0,
    yieldUnit: 'qtl/ac',
    soilTest: {
      ph: 8.05
    },
    fertilizers: [
      { product: 'Fertilizers (bulk unitemized)', cost: 20000, applicationDate: '2026-07-02' }
    ],
    pesticides: [
      { product: 'Pesticide application', cost: 10, applicationDate: '2026-08-15' }
    ],
    irrigation: {
      method: 'Primarily Rainfed / Monsoon Dependent',
      waterAvailability: 'Low',
      hoursTotal: 0,
      cost: 0
    },
    weatherObservations: 'Rainfall monsoon dependent; severe dry spell in late monsoon causing boll development stress.',
    economics: {
      inputCost: 31010,
      laborCost: 50000,
      irrigationCost: 65000,
      sellingPrice: 8000,
      revenue: 240000,
      profit: 93990
    },
    learnings: [
      'Black cotton soil (koralvahu jamin) retains moisture during vegetative growth but requires supplementary irrigation at boll development.',
      'Cotton price benchmark at Akot APMC recorded at ₹8,000/qtl.'
    ],
    farmerNotes: 'Field A: 3 acres sown with Cotton variety godavari. Drought stress symptoms visible; bolls are few and small. Water source 100–500m away.',
    isDemo: true
  },
  {
    id: 'demo-season-cotton-2025',
    farmId: '52120432-c948-4026-87c4-7e2c481a7bf5',
    farmName: 'Pranav Vasu Farm',
    fieldId: 'e5d69ac6-bfe4-4015-a3cd-7cab06c476a6',
    fieldName: 'Field A (3.0 ac)',
    year: 2025,
    seasonName: 'Kharif 2025–26',
    seasonType: 'Kharif',
    crop: 'Cotton',
    variety: 'godavari',
    sowingDate: '2025-06-20',
    harvestDate: '2025-11-25',
    areaAcres: 3.0,
    yieldQuantity: 10.0,
    yieldUnit: 'qtl/ac',
    soilTest: {
      ph: 8.0
    },
    fertilizers: [],
    pesticides: [],
    irrigation: {
      method: 'Rainfed + Occasional Irrigation',
      waterAvailability: 'Medium',
      hoursTotal: 12,
      cost: 1500
    },
    weatherObservations: 'Adequate late-monsoon showers supported boll development.',
    economics: {
      inputCost: 28000,
      laborCost: 45000,
      irrigationCost: 1500,
      sellingPrice: 7600,
      revenue: 228000,
      profit: 153500
    },
    learnings: [
      'Historical yield of 10 quintals/acre verified when late-season moisture is preserved.',
      'Akot APMC market provides best price realization for Vidarbha medium-staple cotton.'
    ],
    farmerNotes: 'Achieved 10 quintals/acre historical benchmark.',
    isDemo: true
  }
];"""

    if old_mem in c:
        c = c.replace(old_mem, new_mem)

    c = c.replace("setFormFarmName('Patil Farm');", "setFormFarmName('Pranav Vasu Farm');")
    c = c.replace("const [formFarmName, setFormFarmName] = useState('Patil Farm');", "const [formFarmName, setFormFarmName] = useState('Pranav Vasu Farm');")
    c = c.replace("const [formCrop, setFormCrop] = useState('Soybean');", "const [formCrop, setFormCrop] = useState('Cotton');")

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] FarmMemory.tsx updated")

if __name__ == "__main__":
    update_farm_memory()
