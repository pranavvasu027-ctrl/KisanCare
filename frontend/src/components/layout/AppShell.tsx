import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNav from './TopNav';

const AppShell = () => {
  return (
    <div className="flex h-screen bg-[#FBF7EF] overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 w-full overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppShell;
