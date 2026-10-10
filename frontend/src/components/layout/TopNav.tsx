import React from 'react';
import { Search, Bell, User, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const TopNav = () => {
  const { signOut, user, role } = useAuth();

  return (
    <header className="h-16 bg-[#FBF7EF] border-b border-[#E5DDCF] flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center space-x-4 flex-1">
        <div className="relative w-96">
          <input 
            type="text" 
            placeholder="Search farms, fields, features..." 
            className="w-full pl-10 pr-4 py-2 bg-white border border-[#E5DDCF] rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-[#A8C69A]"
          />
          <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
        </div>
      </div>
      
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2 border-r border-[#E5DDCF] pr-6">
          <span className="text-sm text-gray-500">Current Farm:</span>
          <select className="bg-transparent text-sm font-medium focus:outline-none text-[#103D2C]">
            <option>Green Acres</option>
            <option>Sunrise Valley</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2 border-r border-[#E5DDCF] pr-6">
          <select className="bg-transparent text-sm focus:outline-none">
            <option>English</option>
          </select>
        </div>

        <button className="text-gray-500 hover:text-[#103D2C] relative">
          <Bell size={20} />
          <span className="absolute -top-1 -right-1 bg-[#B6532A] w-2 h-2 rounded-full"></span>
        </button>
        
        <div className="flex items-center space-x-3 ml-2 border-l border-[#E5DDCF] pl-4">
          <div className="flex flex-col text-right">
            <span className="text-sm font-medium text-[#103D2C]">{user?.email?.split('@')[0] || 'User'}</span>
            <span className="text-xs text-gray-500">{role || 'Farmer'}</span>
          </div>
          <button 
            onClick={signOut}
            title="Log out"
            className="flex items-center space-x-2 w-8 h-8 rounded-full bg-red-100 hover:bg-red-200 flex items-center justify-center text-red-700 transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default TopNav;
