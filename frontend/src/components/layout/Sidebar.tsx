import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard, Map, Sprout, TestTube, Bug, Droplets,
  LineChart, TrendingUp, FlaskConical, Lightbulb, History,
  Bot, Landmark, FileText, Settings, Leaf, Package
} from 'lucide-react';

const Sidebar = () => {
  const { t } = useTranslation();

  const navItems = [
    { nameKey: 'nav.overview', path: '/', icon: <LayoutDashboard size={20} /> },
    { nameKey: 'nav.myFarms', path: '/farm-setup', icon: <Map size={20} /> },
    { nameKey: 'nav.digitalTwin', path: '/digital-twin', icon: <Leaf size={20} /> },
    { nameKey: 'nav.cropIntelligence', path: '/crop-recommendation', icon: <Sprout size={20} /> },
    { nameKey: 'nav.soilIntelligence', path: '/soil', icon: <TestTube size={20} /> },
    { nameKey: 'nav.diseasePest', path: '/disease', icon: <Bug size={20} /> },
    { nameKey: 'nav.irrigationClimate', path: '/irrigation', icon: <Droplets size={20} /> },
    { nameKey: 'nav.farmEconomics', path: '/economics', icon: <LineChart size={20} /> },
    { nameKey: 'nav.marketIntelligence', path: '/market', icon: <TrendingUp size={20} /> },
    { nameKey: 'nav.postHarvest', path: '/post-harvest', icon: <Package size={20} /> },
    { nameKey: 'nav.whatIfSimulator', path: '/simulator', icon: <FlaskConical size={20} /> },
    { nameKey: 'nav.recommendations', path: '/recommendations', icon: <Lightbulb size={20} /> },
    { nameKey: 'nav.farmMemory', path: '/memory', icon: <History size={20} /> },
    { nameKey: 'nav.kisanCareAi', path: '/copilot', icon: <Bot size={20} /> },
    { nameKey: 'nav.governmentSchemes', path: '/schemes', icon: <Landmark size={20} /> },
    { nameKey: 'nav.documents', path: '/documents', icon: <FileText size={20} /> },
  ];

  return (
    <aside className="w-64 bg-[#103D2C] text-white flex flex-col h-full overflow-y-auto">
      <div className="p-6">
        <h1 className="text-2xl font-serif font-bold text-[#FBF7EF]">KISANcare</h1>
        <p className="text-[#A8C69A] text-xs mt-1">{t('nav.tagline')}</p>
      </div>
      <nav className="flex-1 px-4 pb-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-[#17643E] text-[#FBF7EF] font-medium'
                      : 'text-[#A8C69A] hover:bg-[#073B29] hover:text-[#FBF7EF]'
                  }`
                }
              >
                {item.icon}
                <span className="text-sm">{t(item.nameKey)}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="p-4 border-t border-[#17643E]">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              isActive
                ? 'bg-[#17643E] text-[#FBF7EF] font-medium'
                : 'text-[#A8C69A] hover:bg-[#073B29] hover:text-[#FBF7EF]'
            }`
          }
        >
          <Settings size={20} />
          <span className="text-sm">{t('nav.settings')}</span>
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;
