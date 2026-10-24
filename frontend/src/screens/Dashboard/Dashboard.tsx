import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../services/api';
import { translateDynamic } from '../../i18n/translateHelper';
import {
  Leaf, Activity, Sprout, Bug, Droplets, TrendingUp, ShieldCheck,
  BarChart2, Lightbulb, History, Settings, Sun, CloudRain, Check,
  Wind, MapPin, Plus, ArrowRight, AlertTriangle, ChevronRight, Map, FileText, MessageSquare
} from 'lucide-react';

const StatCard = ({ title, value, change, isPositive, icon: Icon, suffix = '' }: any) => {
  const { t } = useTranslation();
  return (
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
      {change !== undefined && change !== null && (
        <div className="flex flex-col items-end">
          <span className={`text-sm font-bold flex items-center gap-1 ${isPositive ? 'text-[#17643E]' : 'text-[#B6532A]'}`}>
            {isPositive ? '↑' : '↓'} {Math.abs(change)}%
          </span>
          <span className="text-xs text-[#292B26]/40 mt-1">{t('common.vsLastSeason')}</span>
        </div>
      )}
    </div>
  );
};

const AlertRow = ({ title, desc, severity, onClick }: { title: string, desc: string, severity: 'High' | 'Medium' | 'Low', onClick?: () => void }) => {
  const { t } = useTranslation();
  const severityKey = severity === 'High' ? 'common.high' : severity === 'Medium' ? 'common.moderate' : 'common.low';

  return (
    <div onClick={onClick} className="flex items-start justify-between p-4 border-b border-[#E5DDCF] last:border-0 hover:bg-[#FBF7EF] transition-colors cursor-pointer group">
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
          {t(severityKey)}
        </span>
        <ChevronRight className="w-4 h-4 text-[#292B26]/30" />
      </div>
    </div>
  );
};

const QuickActionCard = ({ icon: Icon, title, desc, onClick }: any) => (
  <div onClick={onClick} className="bg-[#FBF7EF] rounded-xl p-5 border border-[#E5DDCF] hover:shadow-md transition-all cursor-pointer group flex flex-col h-full">
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
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';

  const farmerName = user?.user_metadata?.name || 'Pranav Vasu';
  const [selectedField, setSelectedField] = useState('Field A (Cotton - 3.0 ac)');
  const [weather, setWeather] = useState<any>(null);

  useEffect(() => {
    api.getCurrentWeather(20.7002, 77.0082).then(setWeather).catch(console.error);
  }, []);

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
              {t('dashboard.goodMorning')}, <span className="text-[#B6532A]">{farmerName}!</span>
            </h2>
            <p className="text-[#292B26]/80 text-lg">{t('dashboard.subtitle')}</p>
          </div>
          <div className="hidden lg:block absolute right-12 top-12 max-w-xs text-right z-10">
            <p className="text-[#103D2C] font-serif text-xl italic font-medium">{t('dashboard.quote')}</p>
          </div>
        </div>

        {/* ROW 1: SCORE, WEATHER, CROP STATUS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Farm Health Score */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2">
                <Leaf className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">{t('dashboard.farmHealthScore')}</h3>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-[#17643E] flex items-center justify-end gap-1">↑ 6%</span>
                <span className="text-[10px] text-[#292B26]/50">{t('dashboard.vsLastWeek')}</span>
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
                  <span className="text-xs font-semibold text-[#17643E]">{t('common.good')}</span>
                </div>
              </div>

              <div className="flex-1 space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-2 text-[#292B26]/70"><span className="w-1.5 h-1.5 rounded-full bg-[#17643E]"></span> {t('dashboard.cropCondition')}</span>
                  <span className="font-semibold text-[#103D2C]">{t('common.good')}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-2 text-[#292B26]/70"><span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> {t('dashboard.soilHealth')}</span>
                  <span className="font-semibold text-[#103D2C]">{t('common.moderate')}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="flex items-center gap-2 text-[#292B26]/70"><span className="w-1.5 h-1.5 rounded-full bg-[#17643E]"></span> {t('dashboard.water')}</span>
                  <span className="font-semibold text-[#103D2C]">{t('common.good')}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Weather Today (Verified Meteorological Observation) */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF] flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <Sun className="w-5 h-5 text-amber-500" />
                  <h3 className="font-bold text-[#103D2C]">{t('dashboard.weatherClimate')}</h3>
                </div>
                <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                  {t('dashboard.verifiedObservation')}
                </span>
              </div>

              <div className="flex items-center gap-4 mb-4">
                <Sun className="w-12 h-12 text-yellow-500 fill-current shrink-0" />
                <div>
                  <div className="text-3xl font-bold text-[#103D2C]">
                    {weather?.temperature ? `${weather.temperature}°C` : '33.1°C'}
                  </div>
                  <div className="text-sm font-medium text-[#292B26]/70">
                    {translateDynamic(weather?.weather_condition || 'Partly Cloudy', currentLang)}
                  </div>
                  <div className="text-xs text-[#292B26]/60 flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3 h-3 text-[#B6532A]"/> {weather?.location || 'Takli Bu, Akola, Maharashtra'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 border-t border-[#E5DDCF] pt-3 text-center">
                <div>
                  <Droplets className="w-4 h-4 mx-auto text-[#292B26]/40 mb-1" />
                  <div className="text-[10px] text-[#292B26]/60">{t('dashboard.humidity')}</div>
                  <div className="text-sm font-bold text-[#103D2C]">{weather?.humidity ? `${weather.humidity}%` : '35%'}</div>
                </div>
                <div className="border-l border-r border-[#E5DDCF]">
                  <Wind className="w-4 h-4 mx-auto text-[#292B26]/40 mb-1" />
                  <div className="text-[10px] text-[#292B26]/60">{t('dashboard.wind')}</div>
                  <div className="text-sm font-bold text-[#103D2C]">{weather?.wind_speed_kmh ? `${weather.wind_speed_kmh} km/h` : '5.7 km/h'}</div>
                </div>
                <div>
                  <CloudRain className="w-4 h-4 mx-auto text-[#292B26]/40 mb-1" />
                  <div className="text-[10px] text-[#292B26]/60">{t('dashboard.rainProb')}</div>
                  <div className="text-sm font-bold text-[#103D2C]">{weather?.rainfall_probability || '15%'}</div>
                </div>
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-[#E5DDCF]/60 text-[10px] text-[#292B26]/60 leading-tight">
              <span><strong>{t('dashboard.source')}:</strong> {weather?.data_source || 'Open-Meteo Agromet Station (Akola)'}</span><br/>
              <span><strong>{t('dashboard.cumulativeRainfall')}:</strong> {t('dashboard.unavailableRainGauge')}</span>
            </div>
          </div>

          {/* Crop Status */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Leaf className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">{t('dashboard.cropStatus')}</h3>
              </div>
              <select
                value={selectedField}
                onChange={(e) => setSelectedField(e.target.value)}
                className="text-xs border border-[#E5DDCF] rounded-lg px-2 py-1 bg-[#FBF7EF] text-[#103D2C] font-medium outline-none cursor-pointer"
              >
                <option value="Field A (Cotton - 3.0 ac)">{t('dashboard.fieldA')}</option>
                <option value="Field B (Cotton - 2.0 ac)">{t('dashboard.fieldB')}</option>
                <option value="Unallocated (5.0 ac)">{t('dashboard.fieldUnallocated')}</option>
              </select>
            </div>

            {selectedField.includes('Field A') ? (
              <>
                <div className="flex gap-4 mb-4">
                  <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0 border border-[#E5DDCF]">
                    <img src="https://images.unsplash.com/photo-1606041008023-472dfb5e530f?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80" alt="Cotton" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h4 className="text-lg font-bold text-[#103D2C]">{t('dashboard.cottonGodavari')}</h4>
                    <span className="text-[10px] font-semibold text-[#B6532A] bg-amber-100 px-2 py-0.5 rounded-full inline-block w-max mt-1 mb-1">
                      {t('dashboard.bollDevRainfed')}
                    </span>
                    <span className="text-xs text-[#292B26]/60">
                      3.0 {t('common.acres')} &bull; {t('dashboard.dayCount', { current: 115, total: 160 })}
                    </span>
                  </div>
                </div>

                <div className="w-full bg-[#F2E8D5] rounded-full h-1.5 mb-4">
                  <div className="bg-[#B6532A] h-1.5 rounded-full" style={{ width: '72%' }}></div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <Activity className="w-4 h-4 text-[#B6532A] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">{t('dashboard.health')}</span>
                    <span className="text-xs font-bold text-[#B6532A]">{t('common.waterStress')}</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <TrendingUp className="w-4 h-4 text-amber-600 mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">{t('dashboard.bolls')}</span>
                    <span className="text-xs font-bold text-[#B6532A]">{t('common.fewSmall')}</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <ShieldCheck className="w-4 h-4 text-[#B6532A] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">{t('dashboard.risk')}</span>
                    <span className="text-xs font-bold text-[#B6532A]">{t('common.high')}</span>
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
                    <h4 className="text-lg font-bold text-[#103D2C]">{t('dashboard.cottonGodavari')}</h4>
                    <span className="text-[10px] font-semibold text-[#17643E] bg-[#A8C69A]/30 px-2 py-0.5 rounded-full inline-block w-max mt-1 mb-1">
                      {t('dashboard.bollFormRainfed')}
                    </span>
                    <span className="text-xs text-[#292B26]/60">
                      2.0 {t('common.acres')} &bull; {t('dashboard.dayCount', { current: 110, total: 160 })}
                    </span>
                  </div>
                </div>

                <div className="w-full bg-[#F2E8D5] rounded-full h-1.5 mb-4">
                  <div className="bg-[#17643E] h-1.5 rounded-full" style={{ width: '68%' }}></div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <Activity className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">{t('dashboard.health')}</span>
                    <span className="text-xs font-bold text-[#103D2C]">{t('common.moderate')}</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <TrendingUp className="w-4 h-4 text-[#17643E] mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">{t('dashboard.growth')}</span>
                    <span className="text-xs font-bold text-[#103D2C]">{t('common.onTrack')}</span>
                  </div>
                  <div className="bg-[#FBF7EF] rounded-lg p-2 flex flex-col items-center justify-center text-center">
                    <ShieldCheck className="w-4 h-4 text-amber-500 mb-1" />
                    <span className="text-[9px] text-[#292B26]/60 mb-0.5">{t('dashboard.risk')}</span>
                    <span className="text-xs font-bold text-[#B6532A]">{t('common.moderate')}</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="p-4 bg-[#FBF7EF] rounded-xl border border-dashed border-[#E5DDCF] text-center">
                <p className="text-sm font-bold text-[#103D2C]">{t('dashboard.unallocatedNotice')}</p>
                <p className="text-xs text-[#292B26]/70 mt-1 leading-relaxed">
                  {t('dashboard.unallocatedDesc')}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ROW 2: ALERTS, MAP, RECOMMENDATION */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] flex flex-col">
            <div className="p-5 border-b border-[#E5DDCF] flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-[#B6532A]" />
                  <h3 className="font-bold text-[#103D2C]">{t('dashboard.priorityAlerts')}</h3>
                </div>
                <p className="text-xs text-[#B6532A] mt-1 font-medium">{t('dashboard.itemsNeedAttention', { count: 3 })}</p>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto max-h-[300px]">
              <AlertRow
                onClick={() => navigate('/irrigation')}
                title={t('dashboard.waterStressAlertTitle')}
                desc={t('dashboard.waterStressAlertDesc')}
                severity="High"
              />
              <AlertRow
                onClick={() => navigate('/irrigation')}
                title={t('dashboard.suppIrrigationAlertTitle')}
                desc={t('dashboard.suppIrrigationAlertDesc')}
                severity="Medium"
              />
              <AlertRow
                onClick={() => navigate('/soil')}
                title={t('dashboard.soilLabPendingTitle')}
                desc={t('dashboard.soilLabPendingDesc')}
                severity="Low"
              />
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Map className="w-5 h-5 text-[#17643E]" />
                <h3 className="font-bold text-[#103D2C]">{t('dashboard.myFarmOverview')}</h3>
              </div>
            </div>
            <div className="relative flex-1 bg-[#A8C69A]/20 rounded-xl overflow-hidden border border-[#E5DDCF] min-h-[220px]">
              <img src="https://images.unsplash.com/photo-1590055531615-f16d36ffe8ea?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" alt="Map" className="w-full h-full object-cover mix-blend-overlay" />
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 300" preserveAspectRatio="none">
                <polygon points="50,150 180,50 240,250 120,280" fill="rgba(23, 100, 62, 0.6)" stroke="white" strokeWidth="2" />
                <polygon points="190,40 320,80 290,170 195,145" fill="rgba(182, 83, 42, 0.4)" stroke="white" strokeWidth="2" />
                <polygon points="300,180 340,100 390,160 330,280 250,260" fill="rgba(168, 198, 154, 0.5)" stroke="white" strokeWidth="2" />
                <text x="145" y="160" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field A (3 ac)</text>
                <text x="255" y="110" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Field B (2 ac)</text>
                <text x="315" y="210" fill="white" fontSize="12" fontWeight="bold" textAnchor="middle">Unallocated (5 ac)</text>
              </svg>
            </div>
          </div>

          <div className="bg-[#FBF7EF] rounded-2xl shadow-sm border border-[#A8C69A]/50 p-6 flex flex-col relative overflow-hidden">
            <div className="relative z-10 flex-1 flex flex-col">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="w-5 h-5 text-[#B6532A]" />
                <h3 className="font-bold text-[#103D2C]">{t('dashboard.aiRecommendation')}</h3>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-[#E5DDCF] mb-4 flex-1">
                <div className="flex items-start gap-3 mb-2">
                  <div className="p-1.5 bg-[#A8C69A]/20 rounded-full text-[#17643E]">
                    <Check className="w-4 h-4" />
                  </div>
                  <h4 className="font-bold text-[#103D2C] text-sm">{t('dashboard.suppIrrigationRecTitle')}</h4>
                </div>
                <p className="text-sm text-[#292B26]/70 leading-relaxed ml-10">
                  {t('dashboard.suppIrrigationRecDesc')}
                </p>
              </div>
              <button
                onClick={() => navigate('/recommendations')}
                className="w-full bg-[#103D2C] text-white rounded-xl py-3 text-sm font-semibold hover:bg-[#17643E] transition-colors flex justify-center items-center gap-2"
              >
                {t('common.viewDetails')} <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

        </div>

        {/* ROW 3: KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title={t('dashboard.expectedYield')} value="10.0" suffix={t('common.qtlAc')} change={0} isPositive={true} icon={Leaf} />
          <StatCard title={t('dashboard.expectedRevenue')} value="₹4,00,000" suffix={t('dashboard.benchmark')} change={0} isPositive={true} icon={TrendingUp} />
          <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#E5DDCF] flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                <Droplets className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-[#292B26]/60 mb-0.5">{t('dashboard.waterRegime')}</p>
                <div className="flex flex-col">
                  <span className="text-lg font-bold text-[#103D2C]">{t('dashboard.primarilyRainfed')}</span>
                  <span className="text-[10px] text-amber-700 font-medium">{t('dashboard.limitedDroughtStressed')}</span>
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
                <p className="text-xs font-medium text-[#292B26]/60">{t('dashboard.overallRisk')}</p>
                <span className="text-sm font-bold text-[#103D2C]">{t('dashboard.lowToModerate')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* ROW 4: QUICK ACTIONS & MORE */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-[#B6532A]" />
              <h3 className="font-bold text-[#103D2C]">{t('dashboard.quickActions')}</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 h-36">
              <QuickActionCard
                onClick={() => navigate('/digital-twin')}
                icon={FileText}
                title={t('dashboard.viewDigitalTwin')}
                desc={t('dashboard.exploreDigitalTwinDesc')}
              />
              <QuickActionCard
                onClick={() => navigate('/crop-comparison')}
                icon={Sprout}
                title={t('dashboard.compareCrops')}
                desc={t('dashboard.findBestCropDesc')}
              />
              <QuickActionCard
                onClick={() => navigate('/simulator')}
                icon={Settings}
                title={t('dashboard.runWhatIf')}
                desc={t('dashboard.seeYieldChangesDesc')}
              />
              <QuickActionCard
                onClick={() => navigate('/copilot')}
                icon={MessageSquare}
                title={t('dashboard.askAi')}
                desc={t('dashboard.getAiAnswersDesc')}
              />
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-[#17643E]" />
                  <h3 className="font-bold text-[#103D2C] text-sm">{t('dashboard.marketPrices')}</h3>
                </div>
              </div>
              <div className="space-y-3">
                {[
                  { nameKey: 'dashboard.soybean', price: '₹4,650', change: '+2.3%', up: true },
                  { nameKey: 'dashboard.cottonAkot', price: '₹8,000', change: '+1.5%', up: true },
                  { nameKey: 'dashboard.tur', price: '₹7,200', change: '-1.5%', up: false },
                  { nameKey: 'dashboard.wheat', price: '₹2,340', change: '+0.8%', up: true }
                ].map(item => (
                  <div key={item.nameKey} className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#292B26] w-24">{t(item.nameKey)}</span>
                    <span className="text-[#292B26]/70">{item.price} <span className="text-[9px]">{t('common.perQtl')}</span></span>
                    <span className={`font-semibold w-12 text-right ${item.up ? 'text-[#17643E]' : 'text-[#B6532A]'}`}>{item.up ? '↑' : '↓'} {item.change.replace('+','').replace('-','')}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 flex-1">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-[#17643E]" />
                  <h3 className="font-bold text-[#103D2C] text-sm">{t('dashboard.recentActivity')}</h3>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-[#17643E] mt-1.5 shrink-0"></div>
                  <div>
                    <p className="text-xs font-medium text-[#292B26]">{t('dashboard.field1Satellite')}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 rounded-full bg-[#A8C69A] mt-1.5 shrink-0"></div>
                  <div>
                    <p className="text-xs font-medium text-[#292B26]">{t('dashboard.soilReportAdded')}</p>
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
