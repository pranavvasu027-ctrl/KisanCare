import React, { useState, useEffect } from 'react';
import Onboarding from './screens/Onboarding';

function App() {
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [twin, setTwin] = useState<any>(null);
  const [simulation, setSimulation] = useState<any>(null);

  const fetchTwin = async () => {
    try {
      const res = await fetch('/api/v1/farms/F001/digital-twin');
      const data = await res.json();
      setTwin(data);
    } catch (e) {
      console.error(e);
    }
  };

  const runSim = async () => {
    try {
      const res = await fetch('/api/v1/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ farm_id: 'F001', changes: { rainfall_change_percent: -20 } })
      });
      const data = await res.json();
      setSimulation(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchTwin();
  }, []);

  if (showOnboarding) {
    return <Onboarding />;
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-green-700">KisanCare Dashboard</h1>
        <button onClick={() => setShowOnboarding(true)} className="text-sm text-gray-500 underline">Back to Login</button>
      </div>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-xl font-semibold mb-4">Digital Twin State</h2>
        {twin ? (
          <pre className="bg-gray-100 p-4 rounded">{JSON.stringify(twin, null, 2)}</pre>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">What-If Simulator</h2>
        <p className="mb-4 text-gray-600">Simulate -20% rainfall impact</p>
        <button 
          onClick={runSim}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Run Simulation
        </button>

        {simulation && (
          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 border rounded">
              <h3 className="font-bold text-gray-700 mb-2">Baseline</h3>
              <p>Yield: {simulation.baseline.yield}</p>
              <p>Profit: ₹{simulation.baseline.profit}</p>
              <p>Risk: {simulation.baseline.risk}</p>
            </div>
            <div className="p-4 bg-red-50 border border-red-200 rounded">
              <h3 className="font-bold text-red-700 mb-2">Scenario</h3>
              <p>Yield: {simulation.scenario.yield}</p>
              <p>Profit: ₹{simulation.scenario.profit}</p>
              <p>Risk: {simulation.scenario.risk}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
