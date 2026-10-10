import React from 'react';
import { 
  Leaf, Activity, Sprout, Bug, Droplets, TrendingUp, ShieldCheck,
  BarChart2, Lightbulb, History, Settings, Sun, CloudRain, Check,
  Wind, MapPin, Plus, ArrowRight, AlertTriangle, ChevronRight, Map, FileText, MessageSquare
} from 'lucide-react';

const StatCard = ({ title, value, change, isPositive, icon: Icon, suffix = '' }: any) => (
  <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] flex items-center justify-between">
    <div className="flex items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-[#F2E8D5] flex items-center justify-center text-[#103D2C]">
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm font-medium text-[#292B26]/60 mb-1">{title}</p>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-[#103D2C]">{value}</span>
          {suffix && <span className="text-sm font-medium text-[#292B26]/60">{suffix}</span>}
        </div>
      </div>
    </div>
    {change && (
      <div className="flex flex-col items-end">
        <span className={`text-sm font-bold flex items-center gap-1 ${isPositive ? 'text-[#17643E]' : 'text-[#B6532A]'}`}>
          {isPositive ? '↑' : '↓'} {Math.abs(change)}%
        </span>
        <span className="text-xs text-[#292B26]/40 mt-1">vs last season</span>
      </div>
    )}
  </div>
);

const AlertRow = ({ title, desc, severity }: { title: string, desc: string, severity: 'High' | 'Medium' | 'Low' }) => (
  <div className="flex items-start justify-between p-4 border-b border-[#E5DDCF] last:border-0 hover:bg-[#FBF7EF] transition-colors cursor-pointer group">
    <div className="flex items-start gap-3">
      <div className={`mt-1 p-1.5 rounded-full ${severity === 'High' ? 'bg-red-100 text-red-600' : severity === 'Medium' ? 'bg-orange-100 text-orange-600' : 'bg-blue-100 text-blue-600'}`}>
        {severity === 'High' ? <Droplets className="w-4 h-4" /> : severity === 'Medium' ? <CloudRain className="w-4 h-4" /> : <Bug className="w-4 h-4" />}
      </div>
      <div>
        <h4 className="text-sm font-bold text-[#292B26] group-hover:text-[#103D2C]">{title}</h4>
        <p className="text-xs text-[#292B26]/70 mt-1">{desc}</p>
      </div>
    </div>
    <div className="flex items-center gap-3">
      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${severity === 'High' ? 'bg-red-100 text-red-700' : severity === 'Medium' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'}`}>
        {severity}
      </span>
      <ChevronRight className="w-4 h-4 text-[#292B26]/30" />
    </div>
  </div>
);

const QuickActionCard = ({ icon: Icon, title, desc }: any) => (
  <div className="bg-[#FBF7EF] rounded-xl p-5 border border-[#E5DDCF] hover:shadow-md transition-all cursor-pointer group flex flex-col h-full">
    <div className="w-10 h-10 rounded-lg bg-[#103D2C] text-white flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
      <Icon className="w-5 h-5" />
    </div>
    <h4 className="text-sm font-bold text-[#103D2C] mb-2">{title}</h4>
    <p className="text-xs text-[#292B26]/70 flex-1">{desc}</p>
    <div className="mt-4 flex justify-end">
      <ArrowRight className="w-4 h-4 text-[#103D2C] opacity-0 group-hover:opacity-100 transition-opacity transform group-hover:translate-x-1" />
    </div>
  </div>
);

export default function Dashboard() {
  return (
    <div className="p-4 lg:p-8">
      <div className="max-w-[1400px] mx-auto space-y-6">
        
        {/* HERO BANNER */}
        <div className="relative bg-[#F2E8D5] rounded-3xl overflow-hidden shadow-sm border border-[#E5DDCF] min-h-[220px] flex items-center px-8 lg:px-12">
          <div className="absolute right-0 top-0 bottom-0 w-1/2 md:w-2/3 lg:w-3/4">
            <img 
              src="https://images.unsplash.com/photo-1592982537447-6f2a6a0c5989?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80" 
              alt="Landscape" 
              className="w-full h-full object-cover mix-blend-overlay opacity-60"
              style={{ maskImage: 'linear-gradient(to right, transparent, black 40%)', WebkitMaskImage: 'linear-gradient(to right, transparent, black 40%)' }}
            />
          </div>
          <div className="relative z-10 max-w-lg py-8">
            <h2 className="text-3xl lg:text-4xl font-bold text-[#103D2C] font-serif mb-2">
              Good Morning, <span className="text-[#B6532A]">Ramesh!</span>
            </h2>
            <p className="text-[#292B26]/80 text-lg">Here's what's happening on your farm today.</p>
          </div>
          <div className="hidden lg:block absolute right-12 top-12 max-w-xs text-right z-10">
            <p className="text-[#103D2C] font-serif text-xl italic font-medium">"Better decisions today<br/>for a healthier tomorrow."</p>
          </div>
        </div>

        {/* ROW 1: SCORE, WEATHER, CROP STATUS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Farm Health Score */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2">
                <Leaf className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">Farm Health Score</h3>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-[#17643E] flex items-center justify-end gap-1">↑ 6%</span>
                <span className="text-[10px] text-[#292B26]/50">vs last week</span>
              </div>
            </div>
            
            <div className="flex items-center gap-8">
              <div className="relative w-28 h-28 shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="transparent" stroke="#F2E8D5" strokeWidth="12" />
                  <circle cx="50" cy="50" r="40" fill="transparent" stroke="#17643E" strokeWidth="12" strokeDasharray="251.2" strokeDashoffset={251.2 * (1 - 0.78)} strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold text-[#103D2C]">78</span>
                  <span className="text-xs font-semibold text-[#17643E]">Good</span>
                </div>
              </div>
              
              <div className="flex-1 space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-2 text-[#292B26]/70"><span className="w-1.5 h-1.5 rounded-full bg-[#17643E]"></span> Crop condition</span>
                  <span className="font-semibold text-[#103D2C]">Good</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-2 text-[#292B26]/70"><span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> Soil health</span>
                  <span className="font-semibold text-[#103D2C]">Moderate</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-2 text-[#292B26]/70"><span className="w-1.5 h-1.5 rounded-full bg-[#17643E]"></span> Water</span>
                  <span className="font-semibold text-[#103D2C]">Good</span>
                </div>
              </div>
            </div>
          </div>

          {/* Weather Today */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Sprout className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">Weather Today</h3>
              </div>
            </div>
            
            <div className="flex items-center gap-4 mb-6">
              <Sun className="w-12 h-12 text-yellow-500 fill-current" />
              <div>
                <div className="text-3xl font-bold text-[#103D2C]">28°C</div>
                <div className="text-sm font-medium text-[#292B26]/70">Partly Cloudy</div>
                <div className="text-xs text-[#292B26]/50 flex items-center gap-1 mt-1"><MapPin className="w-3 h-3"/> Nagpur, Maharashtra</div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 border-t border-[#E5DDCF] pt-4">
              <div className="text-center">
                <Droplets className="w-4 h-4 mx-auto text-[#292B26]/40 mb-1" />
                <div className="text-[10px] text-[#292B26]/60">Humidity</div>
                <div className="text-sm font-bold text-[#103D2C]">62%</div>
              </div>
              <div className="text-center border-l border-r border-[#E5DDCF]">
                <Wind className="w-4 h-4 mx-auto text-[#292B26]/40 mb-1" />
                <div className="text-[10px] text-[#292B26]/60">Wind</div>
                <div className="text-sm font-bold text-[#103D2C]">12 km/h</div>
              </div>
              <div className="text-center">
                <CloudRain className="w-4 h-4 mx-auto text-[#292B26]/40 mb-1" />
                <div className="text-[10px] text-[#292B26]/60">Rain Chance</div>
                <div className="text-sm font-bold text-[#103D2C]">20%</div>
              </div>
            </div>
          </div>

          {/* Crop Status */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Leaf className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">Crop Status</h3>
              </div>
              <select className="text-xs border border-[#E5DDCF] rounded-lg px-2 py-1 bg-[#FBF7EF] text-[#103D2C] font-medium outline-none">
                <option>Field 1</option>
                <option>Field 2</option>
              </select>
            </div>
            
            <div className="flex gap-4 mb-4">
              <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-[#E5DDCF]">
                <img src="https://images.unsplash.com/photo-1599940824399-b87987ceb72a?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" alt="Soybean" className="w-full h-full object-cover" />
              </div>
              <div className="flex flex-col justify-center">
                <h4 className="text-lg font-bold text-[#103D2C]">Soybean</h4>
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
          </div>
        </div>

        {/* ROW 2: ALERTS, MAP, RECOMMENDATION */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] flex flex-col">
            <div className="p-5 border-b border-[#E5DDCF] flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-[#B6532A]" />
                  <h3 className="font-bold text-[#103D2C]">Priority Alerts</h3>
                </div>
                <p className="text-xs text-[#B6532A] mt-1 font-medium">3 items need attention</p>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto max-h-[300px]">
              <AlertRow title="Water Stress Risk" desc="Low soil moisture detected in Field 2" severity="High" />
              <AlertRow title="Heavy Rainfall Expected" desc="60% chance of heavy rain in next 48 hours" severity="Medium" />
              <AlertRow title="Pest Risk Increased" desc="Higher pest activity detected in your region" severity="Medium" />
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Map className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">My Farm Overview</h3>
              </div>
            </div>
            <div className="relative flex-1 bg-[#A8C69A]/20 rounded-xl overflow-hidden border border-[#E5DDCF] min-h-[220px]">
              <img src="https://images.unsplash.com/photo-1590055531615-f16d36ffe8ea?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" alt="Map" className="w-full h-full object-cover mix-blend-overlay" />
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 300" preserveAspectRatio="none">
                <polygon points="50,150 180,50 240,250 120,280" fill="rgba(23, 100, 62, 0.6)" stroke="white" strokeWidth="2" />
                <polygon points="190,40 320,80 290,170 195,145" fill="rgba(182, 83, 42, 0.4)" stroke="white" strokeWidth="2" />
                <polygon points="300,180 340,100 390,160 330,280 250,260" fill="rgba(168, 198, 154, 0.5)" stroke="white" strokeWidth="2" />
                <text x="145" y="160" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field 1</text>
                <text x="255" y="110" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field 2</text>
                <text x="315" y="210" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field 3</text>
              </svg>
            </div>
          </div>

          <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#A8C69A]/50 p-6 flex flex-col relative overflow-hidden">
            <div className="relative z-10 flex-1 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="w-5 h-5 text-[#B6532A]" />
                <h3 className="font-bold text-[#103D2C]">AI Recommendation</h3>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-[#E5DDCF] mb-4 flex-1">
                <div className="flex items-start gap-3 mb-2">
                  <div className="p-1.5 bg-[#A8C69A]/20 rounded-full text-[#17643E]">
                    <Check className="w-4 h-4" />
                  </div>
                  <h4 className="font-bold text-[#103D2C] text-sm">Consider Irrigation in Field 2</h4>
                </div>
                <p className="text-sm text-[#292B26]/70 leading-relaxed ml-10">
                  Soil moisture is below optimal level. Irrigation in the next 2–3 days can improve yield by 8–12%.
                </p>
              </div>
              <button className="w-full bg-[#103D2C] text-white rounded-xl py-3 text-sm font-semibold hover:bg-[#17643E] transition-colors flex justify-center items-center gap-2">
                View Details <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

        </div>

        {/* ROW 3: KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Expected Yield" value="2.8" suffix="tonnes/ac" change={12} isPositive={true} icon={Leaf} />
          <StatCard title="Expected Profit" value="₹42,000" suffix="/ac" change={18} isPositive={true} icon={TrendingUp} />
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                <Droplets className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-[#292B26]/60 mb-1">Water Usage</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-[#103D2C]">65%</span>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] flex flex-col justify-center">
            <div className="flex items-center gap-4 mb-2">
              <div className="w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center text-orange-500 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-[#292B26]/60">Overall Risk</p>
                <span className="text-sm font-bold text-[#103D2C]">Low to Moderate</span>
              </div>
            </div>
          </div>
        </div>

        {/* ROW 4: QUICK ACTIONS & MORE */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-[#B6532A]" />
              <h3 className="font-bold text-[#103D2C]">Quick Actions</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 h-36">
              <QuickActionCard icon={FileText} title="View Digital Twin" desc="Explore your farm in detail." />
              <QuickActionCard icon={Sprout} title="Compare Crops" desc="Find the best crop for your field." />
              <QuickActionCard icon={Settings} title="Run What-If" desc="See how changes affect yield." />
              <QuickActionCard icon={MessageSquare} title="Ask AI" desc="Get answers to farming questions." />
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-[#17643E]" />
                  <h3 className="font-bold text-[#103D2C] text-sm">Market Prices</h3>
                </div>
              </div>
              <div className="space-y-3">
                {[
                  { name: 'Soybean', price: '₹4,650', change: '+2.3%', up: true },
                  { name: 'Cotton', price: '₹6,880', change: '+1.1%', up: true },
                  { name: 'Tur', price: '₹7,200', change: '-1.5%', up: false },
                  { name: 'Wheat', price: '₹2,340', change: '+0.8%', up: true }
                ].map(item => (
                  <div key={item.name} className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#292B26] w-16">{item.name}</span>
                    <span className="text-[#292B26]/70">{item.price} <span className="text-[9px]">/ qtl</span></span>
                    <span className={`font-semibold w-12 text-right ${item.up ? 'text-[#17643E]' : 'text-[#B6532A]'}`}>{item.up ? '↑' : '↓'} {item.change.replace('+','').replace('-','')}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 flex-1">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-[#17643E]" />
                  <h3 className="font-bold text-[#103D2C] text-sm">Recent Activity</h3>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-[#17643E] mt-1.5 shrink-0"></div>
                  <div>
                    <p className="text-xs font-medium text-[#292B26]">Field 1 satellite data updated</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-[#A8C69A] mt-1.5 shrink-0"></div>
                  <div>
                    <p className="text-xs font-medium text-[#292B26]">Soil report added for Field 2</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
