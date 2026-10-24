import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../services/api';
import { translateDynamic } from '../../i18n/translateHelper';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import {
  Leaf, Activity, Sprout, Bug, Droplets, TrendingUp, ShieldCheck,
  BarChart2, Lightbulb, History, Settings, Sun, CloudRain, Check,
  Wind, MapPin, Plus, ArrowRight, AlertTriangle, ChevronRight, Map,
  FileText, MessageSquare, QrCode, Landmark, Award, Sparkles, ExternalLink,
  Calendar, Layers, CheckCircle2
} from 'lucide-react';

const StatCard = ({ title, value, change, isPositive, icon: Icon, suffix = '', subtitle = '' }: any) => {
  const { t } = useTranslation();
  return (
    <div className="agri-card p-5 agri-card-hover flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-800 shrink-0 shadow-2xs">
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-xs font-semibold text-[#19241B]/60 uppercase tracking-wider mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-heading font-extrabold text-[#103D2C]">{value}</span>
            {suffix && <span className="text-xs font-semibold text-[#19241B]/60">{suffix}</span>}
          </div>
          {subtitle && <p className="text-[11px] text-emerald-700 font-medium mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {change !== undefined && change !== 0 && (
        <div className="flex flex-col items-end">
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-0.5 ${isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
            {isPositive ? '↑' : '↓'} {Math.abs(change)}%
          </span>
          <span className="text-[10px] text-[#19241B]/40 mt-1">{t('common.vsLastSeason', 'vs last season')}</span>
        </div>
      )}
    </div>
  );
};

const AlertRow = ({ title, desc, severity, onClick }: { title: string, desc: string, severity: 'High' | 'Medium' | 'Low', onClick?: () => void }) => {
  const { t } = useTranslation();
  const severityKey = severity === 'High' ? 'common.high' : severity === 'Medium' ? 'common.moderate' : 'common.low';

  return (
    <div onClick={onClick} className="flex items-start justify-between p-4 border-b border-[#E6ECE3] last:border-0 hover:bg-emerald-50/40 transition-colors cursor-pointer group">
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 p-2 rounded-xl shrink-0 ${severity === 'High' ? 'bg-red-50 text-red-600 border border-red-100' : severity === 'Medium' ? 'bg-amber-50 text-amber-600 border border-amber-100' : 'bg-blue-50 text-blue-600 border border-blue-100'}`}>
          {severity === 'High' ? <Droplets className="w-4 h-4" /> : severity === 'Medium' ? <CloudRain className="w-4 h-4" /> : <Bug className="w-4 h-4" />}
        </div>
        <div>
          <h4 className="text-xs font-bold text-[#19241B] group-hover:text-emerald-800 transition-colors">{title}</h4>
          <p className="text-[11px] text-[#19241B]/70 mt-0.5 leading-relaxed">{desc}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 pl-3">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${severity === 'High' ? 'bg-red-100 text-red-800' : severity === 'Medium' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-800'}`}>
          {t(severityKey, severity)}
        </span>
        <ChevronRight className="w-4 h-4 text-[#19241B]/30 group-hover:translate-x-0.5 transition-transform" />
      </div>
    </div>
  );
};

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
    <div className="p-4 lg:p-8 space-y-8 max-w-[1440px] mx-auto">

      {/* 1. AGRI-STACK OFFICIAL HERO BANNER WITH REAL FARM PHOTOGRAPHY */}
      <div className="relative rounded-3xl overflow-hidden shadow-lg border border-[#D5E2D1] bg-[#072F22] min-h-[300px] flex items-center">
        {/* Cinematic Backdrop Image */}
        <div className="absolute inset-0">
          <img
            src="/images/hero-farm.jpg"
            alt="Maha AgriStack Precision Farmland"
            className="w-full h-full object-cover object-center"
          />
          {/* Subtle dark gradient overlay ensuring high contrast readability */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#05261B]/95 via-[#083827]/85 to-[#083827]/40"></div>
        </div>

        {/* Hero Content */}
        <div className="relative z-10 w-full px-6 py-8 lg:px-10 lg:py-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
          
          {/* Left: Farmer Welcome & Government AgriStack Credentials */}
          <div className="max-w-2xl text-white space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 backdrop-blur-md border border-emerald-400/30 text-emerald-300 text-xs font-semibold shadow-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Maharashtra AgriStack &bull; Unified Farmer Registry (FR)</span>
            </div>

            <div>
              <h1 className="text-3xl lg:text-5xl font-heading font-extrabold text-white tracking-tight leading-tight">
                Namaskar, <span className="text-emerald-300">{farmerName}</span>!
              </h1>
              <p className="text-emerald-100/80 text-sm lg:text-base mt-2 leading-relaxed">
                Your verified 7/12 land records, laboratory soil health cards, and meteorological crop advisories are active for Kharif 2024.
              </p>
            </div>

            {/* Quick Metadata Chips */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              <span className="px-3 py-1 rounded-xl bg-white/10 backdrop-blur-md border border-white/15 text-white flex items-center gap-1.5 font-medium">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" /> Takli Bu, Akola &bull; गट क्र. 142/1, 142/2
              </span>
              <span className="px-3 py-1 rounded-xl bg-white/10 backdrop-blur-md border border-white/15 text-white flex items-center gap-1.5 font-medium">
                <Layers className="w-3.5 h-3.5 text-amber-300" /> 10.0 Acres Registered (Regur Black Soil)
              </span>
              <span className="px-3 py-1 rounded-xl bg-emerald-500/20 backdrop-blur-md border border-emerald-400/30 text-emerald-200 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Aadhaar e-KYC Verified
              </span>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={() => navigate('/digital-twin')}
                className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-[#05261B] text-xs font-bold transition-all shadow-md shadow-emerald-950/30 flex items-center gap-2 cursor-pointer"
              >
                <Leaf className="w-4 h-4" /> Open Digital Farm Twin
              </button>
              <button
                onClick={() => navigate('/copilot')}
                className="px-5 py-2.5 rounded-xl bg-white/15 hover:bg-white/25 backdrop-blur-md border border-white/25 text-white text-xs font-bold transition-all flex items-center gap-2 cursor-pointer"
              >
                <MessageSquare className="w-4 h-4 text-emerald-300" /> Ask KisanCare AI
              </button>
            </div>
          </div>

          {/* Right: Digital Farmer Registry ID Card (Official Maha AgriStack Look) */}
          <div className="lg:w-84 shrink-0 bg-white/95 backdrop-blur-md rounded-2xl p-5 shadow-2xl border border-white/40 text-[#19241B]">
            {/* Tricolor Accent Header */}
            <div className="h-1.5 w-full rounded-full bg-gradient-to-r from-amber-500 via-white to-emerald-600 mb-3"></div>

            <div className="flex items-center justify-between pb-3 border-b border-[#E6ECE3]">
              <div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-emerald-800 block">Govt. of Maharashtra</span>
                <span className="text-xs font-heading font-extrabold text-[#103D2C]">Farmer Registry Card</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Active
              </span>
            </div>

            <div className="flex items-center gap-3.5 py-3">
              <div className="relative">
                <img
                  src="/images/farmer-profile.jpg"
                  alt="Farmer Avatar"
                  className="w-14 h-14 rounded-xl object-cover border-2 border-emerald-600 shadow-xs"
                />
                <span className="absolute -bottom-1 -right-1 p-0.5 rounded-full bg-emerald-600 text-white">
                  <ShieldCheck className="w-3 h-3" />
                </span>
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-bold text-[#103D2C] leading-tight truncate">{farmerName}</h4>
                <p className="text-[10px] font-mono text-[#19241B]/70 mt-0.5">ID: MH-AKL-884920</p>
                <p className="text-[10px] text-emerald-700 font-medium">Taluka: Akola &bull; Dist: Akola</p>
              </div>
            </div>

            <div className="bg-[#F8FAF7] rounded-xl p-2.5 border border-[#E6ECE3] space-y-1.5 text-[11px]">
              <div className="flex justify-between items-center">
                <span className="text-[#19241B]/60">Total Landholding:</span>
                <span className="font-bold text-[#103D2C]">10.0 Acres</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#19241B]/60">7/12 गट क्रमांक:</span>
                <span className="font-mono font-semibold text-[#103D2C]">142/1, 142/2</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#19241B]/60">Primary Kharif Crop:</span>
                <span className="font-semibold text-emerald-800">Cotton (Godavari)</span>
              </div>
            </div>

            <div className="mt-3 pt-2.5 border-t border-[#E6ECE3] flex items-center justify-between text-[10px]">
              <span className="text-[#19241B]/50 flex items-center gap-1">
                <QrCode className="w-3.5 h-3.5 text-emerald-700" /> QR Verified
              </span>
              <button
                onClick={() => navigate('/farm-setup')}
                className="text-emerald-800 font-bold hover:underline flex items-center gap-0.5 cursor-pointer"
              >
                Inspect 7/12 Records <ChevronRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 2. SEASONAL LIFECYCLE WORKFLOW STEPPER */}
      <div className="agri-card p-6 bg-white">
        <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-base font-heading font-bold text-[#103D2C] flex items-center gap-2">
              <Calendar className="w-5 h-5 text-emerald-600" />
              Continuous Farming Season Lifecycle &bull; खरीप हंगाम २०२४
            </h3>
            <p className="text-xs text-[#19241B]/60 mt-0.5">
              Step through your seasonal milestones sequentially: from soil preparation to market trading.
            </p>
          </div>
          <span className="text-[11px] font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 w-max">
            Active Stage: Crop Care &amp; Monitoring
          </span>
        </div>
        <WorkflowStepper currentStageId={3} />
      </div>

      {/* 3. VISUAL STORY CARDS WITH REAL IMAGERY: SOIL INTELLIGENCE & HARVEST LIFECYCLE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Visual Card 1: Soil Intelligence & Root Stratum */}
        <div className="agri-card overflow-hidden agri-card-hover group flex flex-col justify-between">
          <div className="relative h-56 overflow-hidden">
            <img
              src="/images/soil-roots.jpg"
              alt="Soil organic structure and root profile"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0A2E22] via-[#0A2E22]/30 to-transparent"></div>
            <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-white/90 backdrop-blur-md text-[#103D2C] text-xs font-bold border border-white/50 flex items-center gap-1.5 shadow-xs">
              <Leaf className="w-3.5 h-3.5 text-emerald-600" /> Soil Health Card
            </div>
            <div className="absolute bottom-4 left-4 right-4 text-white">
              <h4 className="text-lg font-heading font-extrabold text-white leading-snug">
                Deep Black Cotton Soil (Regur) &bull; Soil Health Profile
              </h4>
              <p className="text-xs text-emerald-100/90 mt-1 line-clamp-1">
                Lab Tested pH 7.8 &bull; Available NPK: 140:60:40 kg/ha &bull; High Organic Matter
              </p>
            </div>
          </div>

          <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-2.5 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3]">
                <span className="text-[10px] text-[#19241B]/50 block font-medium">Moisture</span>
                <span className="text-sm font-bold text-emerald-800">74%</span>
                <span className="text-[9px] text-emerald-700 block font-semibold mt-0.5">Adequate</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3]">
                <span className="text-[10px] text-[#19241B]/50 block font-medium">Soil Organic C</span>
                <span className="text-sm font-bold text-[#103D2C]">0.54%</span>
                <span className="text-[9px] text-amber-700 block font-semibold mt-0.5">Moderate</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3]">
                <span className="text-[10px] text-[#19241B]/50 block font-medium">{t('dashboard.soilHealth', 'Soil Health')}</span>
                <span className="text-sm font-bold text-emerald-700">78 / 100</span>
                <span className="text-[9px] text-emerald-700 block font-semibold mt-0.5">{t('common.good', 'Good')}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-[#E6ECE3]">
              <span className="text-xs text-[#19241B]/70 font-medium">
                Recommendation: Split application of Nitrogen before flowering.
              </span>
              <button
                onClick={() => navigate('/soil')}
                className="px-4 py-2 rounded-xl bg-[#103D2C] hover:bg-emerald-800 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
              >
                Inspect Soil <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Visual Card 2: Crop Harvest & Yield Intelligence */}
        <div className="agri-card overflow-hidden agri-card-hover group flex flex-col justify-between">
          <div className="relative h-56 overflow-hidden">
            <img
              src="/images/crop-harvest.jpg"
              alt="Harvest intelligence"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0A2E22] via-[#0A2E22]/30 to-transparent"></div>
            <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-white/90 backdrop-blur-md text-[#103D2C] text-xs font-bold border border-white/50 flex items-center gap-1.5 shadow-xs">
              <Sprout className="w-3.5 h-3.5 text-amber-600" /> Kharif Yield Forecast
            </div>
            <div className="absolute bottom-4 left-4 right-4 text-white">
              <h4 className="text-lg font-heading font-extrabold text-white leading-snug">
                Cotton (Godavari) &amp; Soybean Intercrop
              </h4>
              <p className="text-xs text-amber-100/90 mt-1 line-clamp-1">
                Day 115 of 160 &bull; Boll Development Stage &bull; Rainfed parcel
              </p>
            </div>
          </div>

          <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-2.5 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3]">
                <span className="text-[10px] text-[#19241B]/50 block font-medium">{t('dashboard.expectedYield', 'Target Yield')}</span>
                <span className="text-sm font-bold text-[#103D2C]">10.0 qtl/ac</span>
                <span className="text-[9px] text-emerald-700 block font-semibold mt-0.5">{t('dashboard.benchmark', 'Benchmark')}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3]">
                <span className="text-[10px] text-[#19241B]/50 block font-medium">{t('dashboard.expectedRevenue', 'Est. Revenue')}</span>
                <span className="text-sm font-bold text-emerald-800">₹4,00,000</span>
                <span className="text-[9px] text-emerald-700 block font-semibold mt-0.5">@ ₹8,000/qtl</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3]">
                <span className="text-[10px] text-[#19241B]/50 block font-medium">Water Stress</span>
                <span className="text-sm font-bold text-amber-700">{t('common.moderate', 'Moderate')}</span>
                <span className="text-[9px] text-amber-700 block font-semibold mt-0.5">Need Irrig.</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-[#E6ECE3]">
              <span className="text-xs text-[#19241B]/70 font-medium">
                Occasional supplementary irrigation recommended from 200m farm pond.
              </span>
              <button
                onClick={() => navigate('/crop-comparison')}
                className="px-4 py-2 rounded-xl bg-[#103D2C] hover:bg-emerald-800 text-white text-xs font-bold transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
              >
                {t('dashboard.compareCrops', 'Compare Crops')} <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 4. METRICS & REAL-TIME WEATHER OBSERVATION */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('dashboard.farmHealthScore', 'Farm Health Score')}
          value="78"
          suffix="/ 100"
          change={6}
          isPositive={true}
          icon={Activity}
          subtitle={t('dashboard.cropCondition', 'Good crop condition')}
        />
        <StatCard
          title={t('dashboard.expectedYield', 'Projected Yield')}
          value="10.0"
          suffix="qtl/ac"
          change={0}
          isPositive={true}
          icon={Leaf}
          subtitle="Cotton (Godavari)"
        />
        <StatCard
          title="Mandi Price (Akot)"
          value="₹8,000"
          suffix="/ qtl"
          change={1.5}
          isPositive={true}
          icon={TrendingUp}
          subtitle="Above MSP (₹7,121)"
        />

        {/* Real-Time Meteorological Station Widget */}
        <div className="agri-card p-5 bg-gradient-to-br from-emerald-50/50 to-white flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 block">{t('dashboard.weatherClimate', 'Weather Observation')}</span>
              <span className="text-xs text-[#19241B]/60 flex items-center gap-1 mt-0.5">
                <MapPin className="w-3 h-3 text-emerald-700" /> Takli Bu, Akola
              </span>
            </div>
            <Sun className="w-6 h-6 text-amber-500 animate-spin-slow" />
          </div>

          <div className="my-2 flex items-baseline gap-2">
            <span className="text-3xl font-heading font-extrabold text-[#103D2C]">
              {weather?.temperature ? `${weather.temperature}°C` : '33.1°C'}
            </span>
            <span className="text-xs font-medium text-[#19241B]/70">
              {translateDynamic(weather?.weather_condition || 'Partly Cloudy', currentLang)}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-1 pt-2 border-t border-[#E6ECE3] text-center text-[10px]">
            <div>
              <span className="text-[#19241B]/50 block">{t('dashboard.humidity', 'Humidity')}</span>
              <span className="font-bold text-[#103D2C]">{weather?.humidity ? `${weather.humidity}%` : '35%'}</span>
            </div>
            <div className="border-x border-[#E6ECE3]">
              <span className="text-[#19241B]/50 block">{t('dashboard.wind', 'Wind')}</span>
              <span className="font-bold text-[#103D2C]">{weather?.wind_speed_kmh ? `${weather.wind_speed_kmh}k` : '5.7k'}</span>
            </div>
            <div>
              <span className="text-[#19241B]/50 block">{t('dashboard.rainProb', 'Rain Prob.')}</span>
              <span className="font-bold text-emerald-700">{weather?.rainfall_probability || '15%'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. ROW: PRIORITY ALERTS, AGRI-STACK SCHEMES, AND QUICK ACTIONS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Column 1: Priority Alerts */}
        <div className="agri-card flex flex-col">
          <div className="p-5 border-b border-[#E6ECE3] flex justify-between items-center bg-[#F8FAF7] rounded-t-2xl">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <h3 className="font-heading font-bold text-sm text-[#103D2C]">{t('dashboard.priorityAlerts', 'Priority Alerts & Advisories')}</h3>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
              3 Active
            </span>
          </div>
          <div className="divide-y divide-[#E6ECE3] flex-1">
            <AlertRow
              onClick={() => navigate('/irrigation')}
              title={t('dashboard.waterStressAlertTitle', 'Water Stress in Field A')}
              desc={t('dashboard.waterStressAlertDesc', 'Critical drought stress at boll development stage in rainfed Cotton parcel')}
              severity="High"
            />
            <AlertRow
              onClick={() => navigate('/irrigation')}
              title={t('dashboard.suppIrrigationAlertTitle', 'Supplementary Irrigation Window')}
              desc={t('dashboard.suppIrrigationAlertDesc', '100–500m water source available for occasional protective irrigation')}
              severity="Medium"
            />
            <AlertRow
              onClick={() => navigate('/soil')}
              title={t('dashboard.soilLabPendingTitle', 'Soil Lab Report Pending')}
              desc={t('dashboard.soilLabPendingDesc', 'Reported pH 7.6–8.5 (black cotton soil); NPK lab report pending upload')}
              severity="Low"
            />
          </div>
        </div>

        {/* Column 2: Maharashtra AgriStack Schemes & Direct Benefit Transfer */}
        <div className="agri-card flex flex-col p-5 space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-[#E6ECE3]">
            <div className="flex items-center gap-2">
              <Landmark className="w-4 h-4 text-emerald-700" />
              <h3 className="font-heading font-bold text-sm text-[#103D2C]">AgriStack Schemes &amp; DBT</h3>
            </div>
            <button
              onClick={() => navigate('/schemes')}
              className="text-xs font-bold text-emerald-800 hover:underline flex items-center gap-0.5 cursor-pointer"
            >
              All Schemes <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-200/80 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-emerald-950">PM-KISAN (16th Installment)</h4>
                <p className="text-[11px] text-emerald-800 mt-0.5">₹2,000 Credited to Aadhaar-linked Bank A/C</p>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-200 text-emerald-900">Credited</span>
            </div>

            <div className="p-3 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3] flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-[#103D2C]">PM Fasal Bima Yojana (PMFBY)</h4>
                <p className="text-[11px] text-[#19241B]/60 mt-0.5">Kharif 2024 Cotton &bull; Sum Insured: ₹1,50,000</p>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">Active</span>
            </div>

            <div className="p-3 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3] flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-[#103D2C]">KUSUM Solar Ag-Pump Scheme</h4>
                <p className="text-[11px] text-[#19241B]/60 mt-0.5">5 HP Solar Pump Subsidy &bull; 90% Govt. grant</p>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">Sanctioned</span>
            </div>
          </div>

          <div className="pt-2 text-[11px] text-[#19241B]/60 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Single-window verification powered by Farmer ID MH-AKL-884920</span>
          </div>
        </div>

        {/* Column 3: Quick Navigation Modules */}
        <div className="agri-card p-5 flex flex-col justify-between space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E6ECE3]">
            <Sparkles className="w-4 h-4 text-emerald-700" />
            <h3 className="font-heading font-bold text-sm text-[#103D2C]">AI &amp; Simulation Shortcuts</h3>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div
              onClick={() => navigate('/simulator')}
              className="p-3.5 rounded-xl bg-[#F8FAF7] hover:bg-emerald-50 border border-[#E6ECE3] hover:border-emerald-300 transition-all cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                <Settings className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-[#103D2C] group-hover:text-emerald-900">{t('dashboard.runWhatIf', 'What-If Shock')}</h4>
              <p className="text-[10px] text-[#19241B]/60 mt-0.5">Drought / excess rain ROI</p>
            </div>

            <div
              onClick={() => navigate('/disease')}
              className="p-3.5 rounded-xl bg-[#F8FAF7] hover:bg-emerald-50 border border-[#E6ECE3] hover:border-emerald-300 transition-all cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                <Bug className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-[#103D2C] group-hover:text-amber-900">Leaf Disease AI</h4>
              <p className="text-[10px] text-[#19241B]/60 mt-0.5">Instant crop scan diagnosis</p>
            </div>

            <div
              onClick={() => navigate('/market')}
              className="p-3.5 rounded-xl bg-[#F8FAF7] hover:bg-emerald-50 border border-[#E6ECE3] hover:border-emerald-300 transition-all cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-800 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                <BarChart2 className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-[#103D2C] group-hover:text-blue-900">Mandi Forecast</h4>
              <p className="text-[10px] text-[#19241B]/60 mt-0.5">Akot / Amravati spot prices</p>
            </div>

            <div
              onClick={() => navigate('/copilot')}
              className="p-3.5 rounded-xl bg-[#F8FAF7] hover:bg-emerald-50 border border-[#E6ECE3] hover:border-emerald-300 transition-all cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                <MessageSquare className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-[#103D2C] group-hover:text-emerald-900">{t('dashboard.askAi', 'KisanCare AI')}</h4>
              <p className="text-[10px] text-[#19241B]/60 mt-0.5">Voice &amp; regional chat</p>
            </div>
          </div>

          <button
            onClick={() => navigate('/economics')}
            className="w-full py-2.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-900 font-bold text-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
          >
            Review Farm Cost &amp; Profit Ledger <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
