import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNav from './TopNav';
import { useAuth } from '../../hooks/useAuth';

const AppShell = () => {
  const { isDemoMode } = useAuth();

  return (
    <div className="flex h-screen bg-[#FBF7EF] overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 w-full overflow-hidden">
        {isDemoMode && (
          <div className="bg-amber-500 text-stone-900 px-6 py-1.5 text-xs font-semibold flex items-center justify-between border-b border-amber-600 shadow-sm shrink-0 z-20">
            <div className="flex items-center gap-2">
              <span className="bg-amber-900 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">
                DEMO MODE
              </span>
              <span>Authentication bypassed &mdash; Viewing with demonstration farm data (Pranav Vasu &bull; 10.0 Acres &bull; Takli Bu, Akola)</span>
            </div>
            <span className="text-[11px] text-amber-950 font-normal hidden md:inline">
              Sample Data Only &bull; Changes are not written to Supabase
            </span>
          </div>
        )}
        <TopNav />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppShell;
