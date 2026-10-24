import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard, Map, Sprout, TestTube, Bug, Droplets,
  LineChart, TrendingUp, FlaskConical, Lightbulb, History,
  Bot, Landmark, FileText, Settings, Leaf, Package, Compass, Tractor
} from 'lucide-react';

interface NavItem {
  name: string;
  nameKey?: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
}

interface NavGroup {
  stage?: string;
  stageMr?: string;
  items: NavItem[];
}

const Sidebar = () => {
  const { t } = useTranslation();

  const navGroups: NavGroup[] = [
    {
      items: [
        { nameKey: 'nav.overview', name: 'Overview', path: '/', icon: <LayoutDashboard size={18} /> },
      ]
    },
    {
      stage: '1. Farm & Soil',
      stageMr: 'शेत व माती',
      items: [
        { nameKey: 'nav.myFarms', name: 'My Farms', path: '/farm-setup', icon: <Map size={18} /> },
        { nameKey: 'nav.digitalTwin', name: 'Digital Twin', path: '/digital-twin', icon: <Leaf size={18} /> },
        { nameKey: 'nav.soilIntelligence', name: 'Soil Intelligence', path: '/soil', icon: <TestTube size={18} /> },
      ]
    },
    {
      stage: '2. Crop Planning',
      stageMr: 'पीक नियोजन',
      items: [
        { nameKey: 'nav.cropIntelligence', name: 'Crop Intelligence', path: '/crop-recommendation', icon: <Sprout size={18} /> },
        { nameKey: 'nav.cropComparison', name: 'Crop Comparison', path: '/crop-comparison', icon: <Compass size={18} /> },
      ]
    },
    {
      stage: '3. Crop Care',
      stageMr: 'हंगामी निगा',
      items: [
        { nameKey: 'nav.irrigationClimate', name: 'Irrigation & Climate', path: '/irrigation', icon: <Droplets size={18} /> },
        { nameKey: 'nav.diseasePest', name: 'Disease & Pest', path: '/disease', icon: <Bug size={18} /> },
        { nameKey: 'nav.fertilizerAdvisory', name: 'Fertilizer Advisory', path: '/fertilizer', icon: <FlaskConical size={18} /> },
        { nameKey: 'nav.recommendations', name: 'Recommendations', path: '/recommendations', icon: <Lightbulb size={18} /> },
      ]
    },
    {
      stage: '4. Simulation & ROI',
      stageMr: 'नफा व जोखीम',
      items: [
        { nameKey: 'nav.whatIfSimulator', name: 'What-If Simulator', path: '/simulator', icon: <FlaskConical size={18} /> },
        { nameKey: 'nav.farmEconomics', name: 'Farm Economics', path: '/economics', icon: <LineChart size={18} /> },
      ]
    },
    {
      stage: '5. Market & Machinery',
      stageMr: 'बाजार व अवजारे',
      items: [
        { nameKey: 'nav.rentals', name: 'Farm Equipment Rentals', path: '/rentals', icon: <Tractor size={18} /> },
        { nameKey: 'nav.marketIntelligence', name: 'Market Intelligence', path: '/market', icon: <TrendingUp size={18} /> },
        { nameKey: 'nav.postHarvest', name: 'Post-Harvest Loss', path: '/post-harvest', icon: <Package size={18} /> },
      ]
    },
    {
      stage: 'Support & Records',
      stageMr: 'मदत व नोंदी',
      items: [
        { nameKey: 'nav.kisanCareAi', name: 'KisanCare AI', path: '/copilot', icon: <Bot size={18} /> },
        { nameKey: 'nav.governmentSchemes', name: 'Government Schemes', path: '/schemes', icon: <Landmark size={18} /> },
        { nameKey: 'nav.farmMemory', name: 'Farm Memory', path: '/memory', icon: <History size={18} /> },
        { nameKey: 'nav.documents', name: 'Documents', path: '/documents', icon: <FileText size={18} /> },
      ]
    }
  ];

  return (
    <aside className="w-64 bg-[#0A2E22] text-white flex flex-col h-full overflow-y-auto shrink-0 select-none border-r border-[#154636]">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#154636]/80 bg-gradient-to-b from-[#0F3B2C] to-[#0A2E22]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-md shadow-emerald-950/40 border border-emerald-400/30">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-heading font-extrabold text-white tracking-tight flex items-center gap-1.5">
              KISAN<span className="text-emerald-400 font-light">care</span>
            </h1>
            <div className="flex items-center gap-1 text-[10px] text-emerald-300/80 font-medium tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Maha AgriStack &bull; DPI
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 px-3 py-3 space-y-4">
        {navGroups.map((group, gIdx) => (
          <div key={gIdx} className="space-y-1">
            {group.stage && (
              <div className="px-3 pt-2 pb-1 flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-emerald-300/70">
                <span>{group.stage}</span>
                <span className="font-normal text-[9px] text-emerald-200/50">{group.stageMr}</span>
              </div>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center space-x-3 px-3 py-2 rounded-xl transition-all text-xs ${
                        isActive
                          ? 'bg-emerald-600 text-white font-bold shadow-md shadow-emerald-900/40 ring-1 ring-emerald-400/40'
                          : 'text-emerald-100/70 hover:bg-[#124231] hover:text-white'
                      }`
                    }
                  >
                    <span className="shrink-0">{item.icon}</span>
                    <span className="truncate">{item.nameKey ? t(item.nameKey, item.name) : item.name}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Mini Farmer Registry Card in Footer */}
      <div className="p-3 border-t border-[#154636] bg-[#07241A] space-y-2">
        <div className="p-2.5 rounded-xl bg-emerald-950/60 border border-emerald-800/60 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-800/60 border border-emerald-600/40 flex items-center justify-center shrink-0">
            <Landmark className="w-4 h-4 text-emerald-300" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1">
              <span className="text-[10px] font-bold text-emerald-300 truncate">MH Farmer Registry</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            </div>
            <p className="text-[9px] text-emerald-200/70 font-mono truncate">ID: MH-AKL-884920</p>
          </div>
        </div>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center space-x-3 px-3 py-2 rounded-xl transition-colors text-xs ${
              isActive
                ? 'bg-emerald-600 text-white font-semibold'
                : 'text-emerald-100/70 hover:bg-[#124231] hover:text-white'
            }`
          }
        >
          <Settings size={18} />
          <span>{t('nav.settings', 'Settings & Preferences')}</span>
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;
