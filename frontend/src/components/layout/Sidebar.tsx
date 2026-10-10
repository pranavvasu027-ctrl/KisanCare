import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Map, Sprout, TestTube, Bug, Droplets, 
  LineChart, TrendingUp, FlaskConical, Lightbulb, History, 
  Bot, Landmark, FileText, Settings, Leaf
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { name: 'Overview', path: '/', icon: <LayoutDashboard size={20} /> },
    { name: 'My Farms', path: '/farm-setup', icon: <Map size={20} /> },
    { name: 'Digital Twin', path: '/digital-twin', icon: <Leaf size={20} /> },
    { name: 'Crop Intelligence', path: '/crop-recommendation', icon: <Sprout size={20} /> },
    { name: 'Soil Intelligence', path: '/soil', icon: <TestTube size={20} /> },
    { name: 'Disease & Pest', path: '/disease', icon: <Bug size={20} /> },
    { name: 'Irrigation & Climate', path: '/irrigation', icon: <Droplets size={20} /> },
    { name: 'Farm Economics', path: '/economics', icon: <LineChart size={20} /> },
    { name: 'Market Intelligence', path: '/market', icon: <TrendingUp size={20} /> },
    { name: 'What-If Simulator', path: '/simulator', icon: <FlaskConical size={20} /> },
    { name: 'Recommendations', path: '/recommendations', icon: <Lightbulb size={20} /> },
    { name: 'Farm Memory', path: '/memory', icon: <History size={20} /> },
    { name: 'KisanCare AI', path: '/copilot', icon: <Bot size={20} /> },
    { name: 'Government Schemes', path: '/schemes', icon: <Landmark size={20} /> },
    { name: 'Documents', path: '/documents', icon: <FileText size={20} /> },
  ];

  return (
    <aside className="w-64 bg-[#103D2C] text-white flex flex-col h-full overflow-y-auto">
      <div className="p-6">
        <h1 className="text-2xl font-serif font-bold text-[#FBF7EF]">KISANcare</h1>
        <p className="text-[#A8C69A] text-xs mt-1">Smarter Farms • Better Tomorrows</p>
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
                <span className="text-sm">{item.name}</span>
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
          <span className="text-sm">Settings</span>
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;
