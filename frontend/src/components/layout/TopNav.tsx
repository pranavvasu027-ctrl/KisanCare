import React from 'react';
import { Search, Bell, ShieldCheck, MapPin, Globe, LogOut, Sparkles } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const TopNav = () => {
  const { signOut, user, role, isDemoMode } = useAuth();
  const farmerName = isDemoMode ? 'Pranav Vasu' : user?.user_metadata?.name || user?.email?.split('@')[0] || 'Pranav Vasu';

  return (
    <header className="h-16 bg-white/95 backdrop-blur-md border-b border-[#E6ECE3] flex items-center justify-between px-6 shrink-0 z-30 sticky top-0 shadow-[0_1px_4px_rgba(16,61,44,0.03)]">
      {/* Search & Farm Selector */}
      <div className="flex items-center gap-4 flex-1 max-w-2xl">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search farm plots, soil tests, crop advisories, schemes..."
            className="w-full pl-10 pr-12 py-2 bg-[#F8FAF7] border border-[#E6ECE3] rounded-xl text-xs text-[#19241B] placeholder:text-[#19241B]/40 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-600 transition-all"
          />
          <Search className="absolute left-3.5 top-2.5 text-[#19241B]/40" size={16} />
          <kbd className="absolute right-3 top-2.5 px-1.5 py-0.5 text-[10px] font-mono text-[#19241B]/40 bg-white border border-[#E6ECE3] rounded shadow-2xs">⌘K</kbd>
        </div>

        {/* AgriStack Verified Pill */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-200/80 rounded-xl text-emerald-900 shadow-2xs">
          <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
          <div className="text-left leading-tight">
            <span className="text-[10px] font-bold block tracking-wider uppercase text-emerald-800">AgriStack ID: MH-AKL-884920</span>
            <span className="text-[9px] text-emerald-700 font-medium">e-KYC &amp; 7/12 Land Linked &bull; Maha FR</span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {isDemoMode && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-amber-50 text-amber-900 border border-amber-300 shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            DEMO MODE
          </span>
        )}

        {/* Selected Farm Parcel */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-[#F8FAF7] border border-[#E6ECE3] rounded-xl">
          <MapPin className="w-3.5 h-3.5 text-emerald-700" />
          <div className="text-left text-xs">
            <span className="text-[10px] block text-[#19241B]/50 font-medium">Active Plot</span>
            <select className="bg-transparent font-semibold text-[#103D2C] focus:outline-none text-xs cursor-pointer p-0">
              <option>Takli Bu, Akola (10.0 Ac)</option>
              <option>Field A &bull; Cotton (3.0 Ac)</option>
              <option>Field B &bull; Cotton (2.0 Ac)</option>
            </select>
          </div>
        </div>

        {/* Language Selector */}
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-[#F8FAF7] border border-[#E6ECE3] rounded-xl text-xs text-[#103D2C]">
          <Globe className="w-3.5 h-3.5 text-emerald-700" />
          <select className="bg-transparent text-xs font-semibold focus:outline-none cursor-pointer">
            <option>मराठी (MR)</option>
            <option>English (EN)</option>
            <option>हिन्दी (HI)</option>
          </select>
        </div>

        {/* Notifications */}
        <button className="relative w-9 h-9 rounded-xl bg-[#F8FAF7] border border-[#E6ECE3] hover:bg-emerald-50 text-[#19241B]/70 hover:text-emerald-800 flex items-center justify-center transition-colors">
          <Bell size={17} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-amber-500 rounded-full ring-2 ring-white"></span>
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-2 border-l border-[#E6ECE3]">
          <div className="relative">
            <img
              src="/images/farmer-profile.jpg"
              alt={farmerName}
              className="w-9 h-9 rounded-xl object-cover border-2 border-emerald-600 shadow-2xs"
            />
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-white rounded-full"></span>
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-bold text-[#103D2C] leading-tight">{farmerName}</span>
            <span className="text-[10px] text-emerald-700 font-semibold flex items-center gap-1">
              <Sparkles className="w-2.5 h-2.5" /> Verified Farmer
            </span>
          </div>
          <button
            onClick={signOut}
            title={isDemoMode ? "Demo mode has no session to sign out" : "Sign out"}
            disabled={isDemoMode}
            className="w-8 h-8 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 flex items-center justify-center transition-colors ml-1"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default TopNav;

