import React, { useState, useEffect } from 'react';
import { FlaskConical, Play, Save, RotateCcw, TrendingDown, TrendingUp, BarChart2, Loader2, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';

export default function WhatIfSimulator() {
  const [crop, setCrop] = useState('Cotton');
  const [irrigation, setIrrigation] = useState('Optimal (As recommended)');
  const [fertilizerStrategy, setFertilizerStrategy] = useState('Standard NPK');
  const [weatherAssumption, setWeatherAssumption] = useState('Normal Monsoon');
  const [marketPrice, setMarketPrice] = useState<number>(8000);

  const [loading, setLoading] = useState<boolean>(false);
  const [isDemo, setIsDemo] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    executeSimulation();
  }, [crop, irrigation, fertilizerStrategy, weatherAssumption, marketPrice]);

  const executeSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      // Map controls to changes payload
      let rainfallChange = 0;
      if (weatherAssumption === 'Drought (-30% rain)') rainfallChange = -30;
      if (weatherAssumption === 'Excess Rain (+20%)') rainfallChange = 20;

      let inputCost = 30000;
      if (fertilizerStrategy === 'Organic + Biofertilizers') inputCost = 34000;
      if (fertilizerStrategy === 'High Yield (Chemical)') inputCost = 40000;

      const res = await api.runSimulation('52120432-c948-4026-87c4-7e2c481a7bf5', {
        crop,
        rainfall_change_percent: rainfallChange,
        input_cost: inputCost,
        expected_price: marketPrice,
        irrigation_strategy: irrigation
      });

      setResult(res.data);
      setIsDemo(res.isDemo);
    } catch (err: any) {
      console.error('Simulation execution failed:', err);
      setError(`Simulation engine notice: ${err.message || String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const baseline = result?.baseline || { yield: 24, cost: 30000, revenue: 60000, profit: 30000, risk: 0.35 };
  const scenario = result?.scenario || { yield: 26, cost: 34000, revenue: 65000, profit: 31000, risk: 0.30 };
  const profitDiff = result?.differences?.profit_diff ?? (scenario.profit - baseline.profit);
  const profitDiffPercent = baseline.profit > 0 ? Math.round((profitDiff / baseline.profit) * 1000) / 10 : 0;

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto h-full flex flex-col space-y-6">
      <WorkflowStepper currentStageId={4} />

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">What-If Simulator</h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Simulation
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                Live Simulation Engine
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">Simulate changes in farming practices and predict economic outcomes.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={executeSimulation}
            disabled={loading}
            className="bg-[#103D2C] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#17643E] transition-colors flex items-center gap-2 text-sm shadow-sm disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play size={16} />} Run Simulation
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        {/* Controls Panel */}
        <div className="lg:col-span-4 bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 flex flex-col">
          <h3 className="font-bold text-[#103D2C] mb-4 pb-2 border-b border-[#E5DDCF]">Scenario Parameters</h3>

          <div className="space-y-5 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Crop Selection</label>
              <select
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none cursor-pointer"
              >
                <option value="Soybean">Soybean</option>
                <option value="Cotton">Cotton</option>
                <option value="Wheat">Wheat</option>
                <option value="Rice">Rice</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Irrigation Schedule</label>
              <select
                value={irrigation}
                onChange={(e) => setIrrigation(e.target.value)}
                className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none cursor-pointer"
              >
                <option value="Optimal (As recommended)">Optimal (As recommended)</option>
                <option value="Reduced (-20%)">Reduced (-20%)</option>
                <option value="Rainfed only">Rainfed only</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Fertilizer Strategy</label>
              <select
                value={fertilizerStrategy}
                onChange={(e) => setFertilizerStrategy(e.target.value)}
                className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none cursor-pointer"
              >
                <option value="Standard NPK">Standard NPK</option>
                <option value="Organic + Biofertilizers">Organic + Biofertilizers</option>
                <option value="High Yield (Chemical)">High Yield (Chemical)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#292B26] mb-1">Weather Assumption</label>
              <select
                value={weatherAssumption}
                onChange={(e) => setWeatherAssumption(e.target.value)}
                className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm outline-none cursor-pointer"
              >
                <option value="Normal Monsoon">Normal Monsoon</option>
                <option value="Drought (-30% rain)">Drought (-30% rain)</option>
                <option value="Excess Rain (+20%)">Excess Rain (+20%)</option>
              </select>
            </div>

            <div className="pt-4 mt-2 border-t border-[#E5DDCF]">
              <label className="block text-sm font-medium text-[#292B26] mb-3">Expected Market Price</label>
              <input
                type="range"
                min="2000"
                max="7000"
                step="100"
                value={marketPrice}
                onChange={(e) => setMarketPrice(Number(e.target.value))}
                className="w-full accent-[#17643E]"
              />
              <div className="flex justify-between text-xs text-[#292B26]/60 mt-1">
                <span>₹2,000/qtl</span>
                <span className="font-bold text-[#103D2C]">₹{marketPrice.toLocaleString('en-IN')}/qtl</span>
                <span>₹7,000/qtl</span>
              </div>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-[#17643E]/5 rounded-2xl border border-[#17643E]/20 p-5 relative overflow-hidden">
              <h4 className="text-sm font-bold text-[#103D2C] mb-1">Baseline Prediction</h4>
              <p className="text-xs text-[#292B26]/60 mb-4">Standard baseline practices</p>
              <div className="text-3xl font-bold text-[#103D2C] mb-1">
                ₹{Math.round(baseline.profit).toLocaleString('en-IN')} <span className="text-sm font-normal">/ ac</span>
              </div>
              <div className="text-sm text-[#292B26]/70">Est. Yield: {baseline.yield} qtl/ac</div>
            </div>

            <div className="bg-white rounded-2xl border border-[#E5DDCF] p-5 relative overflow-hidden shadow-sm">
              <h4 className="text-sm font-bold text-[#103D2C] mb-1">Simulated Outcome</h4>
              <p className="text-xs text-[#292B26]/60 mb-4">With adjusted scenario parameters</p>
              <div className="text-3xl font-bold text-[#17643E] mb-1 flex items-center gap-2">
                ₹{Math.round(scenario.profit).toLocaleString('en-IN')} <span className="text-sm font-normal text-[#292B26]">/ ac</span>
              </div>
              <div className="flex justify-between items-end">
                <div className="text-sm text-[#292B26]/70">Est. Yield: {scenario.yield} qtl/ac</div>
                <div className={`text-sm font-bold px-2 py-1 rounded flex items-center gap-1 ${profitDiff >= 0 ? 'text-[#17643E] bg-[#17643E]/10' : 'text-[#B6532A] bg-red-50'
                  }`}>
                  {profitDiff >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {profitDiff >= 0 ? `+${profitDiffPercent}%` : `${profitDiffPercent}%`}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-5 flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-[#103D2C]">Comparison Summary</h3>
              <div className="flex gap-4 text-xs font-medium">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#E5DDCF]"></span> Baseline</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[#17643E]"></span> Scenario</span>
              </div>
            </div>

            <div className="space-y-4 py-2 border-b border-[#E5DDCF]">
              <div className="flex justify-between text-sm py-1 border-b border-[#E5DDCF]/50">
                <span className="text-[#292B26]/70">Expected Revenue</span>
                <span className="font-bold text-[#103D2C]">
                  ₹{Math.round(baseline.revenue).toLocaleString('en-IN')} → ₹{Math.round(scenario.revenue).toLocaleString('en-IN')}
                </span>
              </div>
              <div className="flex justify-between text-sm py-1 border-b border-[#E5DDCF]/50">
                <span className="text-[#292B26]/70">Total Input & Labour Cost</span>
                <span className="font-bold text-[#103D2C]">
                  ₹{Math.round(baseline.cost).toLocaleString('en-IN')} → ₹{Math.round(scenario.cost).toLocaleString('en-IN')}
                </span>
              </div>
              <div className="flex justify-between text-sm py-1 border-b border-[#E5DDCF]/50">
                <span className="text-[#292B26]/70">Net Profit Difference</span>
                <span className={`font-bold ${profitDiff >= 0 ? 'text-[#17643E]' : 'text-[#B6532A]'}`}>
                  {profitDiff >= 0 ? `+₹${Math.round(profitDiff).toLocaleString('en-IN')}` : `-₹${Math.round(Math.abs(profitDiff)).toLocaleString('en-IN')}`}
                </span>
              </div>
              <div className="flex justify-between text-sm py-1">
                <span className="text-[#292B26]/70">Simulated Risk Score</span>
                <span className="font-bold text-[#103D2C]">
                  {Math.round((scenario.risk ?? 0.3) * 100)}% ({scenario.risk > 0.4 ? 'Elevated' : 'Moderate'})
                </span>
              </div>
            </div>

            <div className="mt-6 bg-[#FBF7EF] p-4 rounded-xl border border-[#A8C69A]/30">
              <h4 className="font-bold text-[#103D2C] text-sm mb-2 flex items-center gap-1.5">
                <CheckCircle2 size={16} className="text-[#17643E]" /> Simulation Engine Analysis
              </h4>
              <ul className="text-xs text-[#292B26]/80 space-y-1">
                {result?.explanation?.map((item: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-[#17643E] font-bold">•</span>
                    <span>{item}</span>
                  </li>
                )) || (
                    <li>Adjusting weather or fertilizer inputs recalculates harvest yield and net margins through the backend simulation model.</li>
                  )}
              </ul>
            </div>
          </div>
        </div>
      </div>

      <WorkflowFooter
        currentStageNumber={4}
        currentStageName="Simulation & ROI"
        completedActionMessage={result ? `Simulation evaluated! Yield: ${scenario.yield} qtl/ac (${profitDiff >= 0 ? '+' : ''}${profitDiffPercent}% profit impact). Next: View detailed farm cost breakdown.` : null}
        prevStep={{ label: "Disease & Pest Care", path: "/disease" }}
        nextStep={{
          label: "Farm Economics & Budgeting",
          labelMr: "शेती नफा गणित",
          path: "/economics",
          description: "Analyze production costs, break-even prices, and return on investment"
        }}
        alternativeNextStep={{
          label: "Mandi Market Prices",
          path: "/market"
        }}
      />
    </div>
  );
}
