import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { IS_DEMO_MODE } from './config/demo';

// Pages
import Login from './screens/Auth/Login';
import Onboarding from './screens/Onboarding';
import Dashboard from './screens/Dashboard/Dashboard';
import FarmSetup from './screens/FarmSetup/FarmSetup';
import DigitalTwin from './screens/DigitalTwin/DigitalTwin';
import CropRecommendation from './screens/CropRecommendation/CropRecommendation';
import CropComparison from './screens/CropComparison/CropComparison';
import WhatIfSimulator from './screens/WhatIfSimulator/WhatIfSimulator';
import AiRecommendation from './screens/AiRecommendation/AiRecommendation';
import SoilIntelligence from './screens/SoilIntelligence/SoilIntelligence';
import DiseaseDetection from './screens/DiseaseDetection/DiseaseDetection';
import IrrigationClimate from './screens/IrrigationClimate/IrrigationClimate';
import FarmEconomics from './screens/FarmEconomics/FarmEconomics';
import MarketIntelligence from './screens/MarketIntelligence/MarketIntelligence';
import FarmMemory from './screens/FarmMemory/FarmMemory';
import Copilot from './screens/Copilot/Copilot';
import GovernmentSchemes from './screens/GovernmentSchemes/GovernmentSchemes';
import Documents from './screens/Documents/Documents';
import Settings from './screens/Settings/Settings';
import PostHarvestLoss from './screens/PostHarvestLoss/PostHarvestLoss';
import RentalMarketplace from './screens/Rentals/RentalMarketplace';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { session, loading, isDemoMode } = useAuth();

  if (isDemoMode) {
    return <>{children}</>;
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-[#FBF7EF]">Loading...</div>;
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/onboarding" element={<Onboarding />} />

          <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="farm-setup" element={<FarmSetup />} />
            <Route path="digital-twin" element={<DigitalTwin />} />
            <Route path="crop-recommendation" element={<CropRecommendation />} />
            <Route path="crop-comparison" element={<CropComparison />} />
            <Route path="post-harvest" element={<PostHarvestLoss />} />
            <Route path="simulator" element={<WhatIfSimulator />} />
            <Route path="recommendations" element={<AiRecommendation />} />
            <Route path="soil" element={<SoilIntelligence />} />
            <Route path="soil-intelligence" element={<SoilIntelligence />} />
            <Route path="disease" element={<DiseaseDetection />} />
            <Route path="irrigation" element={<IrrigationClimate />} />
            <Route path="economics" element={<FarmEconomics />} />
            <Route path="market" element={<MarketIntelligence />} />
            <Route path="memory" element={<FarmMemory />} />
            <Route path="copilot" element={<Copilot />} />
            <Route path="schemes" element={<GovernmentSchemes />} />
            <Route path="documents" element={<Documents />} />
            <Route path="settings" element={<Settings />} />

            {/* Agricultural Equipment, Vehicle & Labour Rental Marketplace */}
            <Route path="rentals" element={<RentalMarketplace />} />
            <Route path="rentals/:section" element={<RentalMarketplace />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
