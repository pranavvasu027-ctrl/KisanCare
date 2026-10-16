import React, { useState, useEffect } from 'react';
import { IndianRupee, TrendingUp, TrendingDown, PieChart, BarChart, Loader2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function FarmEconomics() {
  const [expectedYield, setExpectedYield] = useState<number>(24);
  const [expectedPrice, setExpectedPrice] = useState<number>(2500);
  const [inputCost, setInputCost] = useState<number>(10000);
  const [labourCost, setLabourCost] = useState<number>(15000);
  const [irrigationCost, setIrrigationCost] = useState<number>(5000);

  const [economics, setEconomics] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isDemo, setIsDemo] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    runEconomicsCalculation();
  }, [expectedYield, expectedPrice, inputCost, labourCost, irrigationCost]);

  const runEconomicsCalculation = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await api.calculateEconomics({
        expected_yield: expectedYield,
        expected_price: expectedPrice,
        input_cost: inputCost,
        labour_cost: labourCost,
        irrigation_cost: irrigationCost
      });
      setEconomics(response.data);
      setIsDemo(response.isDemo);
    } catch (err: any) {
      console.error('Failed to calculate economics:', err);
      setErrorMessage(`Economics Calculation Notice: ${err.message || String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const totalCost = economics?.total_cost ?? (inputCost + labourCost + irrigationCost);
  const seedsCost = Math.round(inputCost * 0.45);
  const fertCost = Math.round(inputCost * 0.55);

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Farm Economics</h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Sample Economics Data
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                Live Economics Engine
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">Track costs, expected revenue, and overall profitability.</p>
        </div>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Interactive Economic Parameter Inputs */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF]">
        <h3 className="font-bold text-sm text-[#103D2C] uppercase tracking-wider mb-4">Economic Model Parameters</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-medium text-[#292B26] mb-1">Expected Yield (Quintals)</label>
            <input
              type="number"
              min="1"
              value={expectedYield}
              onChange={(e) => setExpectedYield(Number(e.target.value))}
              className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-1.5 text-sm font-semibold text-[#103D2C]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#292B26] mb-1">Expected Price (₹/Qtl)</label>
            <input
              type="number"
              min="100"
              step="50"
              value={expectedPrice}
              onChange={(e) => setExpectedPrice(Number(e.target.value))}
              className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-1.5 text-sm font-semibold text-[#103D2C]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#292B26] mb-1">Inputs Cost (₹)</label>
            <input
              type="number"
              min="0"
              step="500"
              value={inputCost}
              onChange={(e) => setInputCost(Number(e.target.value))}
              className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-1.5 text-sm font-semibold text-[#103D2C]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#292B26] mb-1">Labour Cost (₹)</label>
            <input
              type="number"
              min="0"
              step="500"
              value={labourCost}
              onChange={(e) => setLabourCost(Number(e.target.value))}
              className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-1.5 text-sm font-semibold text-[#103D2C]"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-[#292B26] mb-1">Irrigation Cost (₹)</label>
            <input
              type="number"
              min="0"
              step="250"
              value={irrigationCost}
              onChange={(e) => setIrrigationCost(Number(e.target.value))}
              className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-1.5 text-sm font-semibold text-[#103D2C]"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-[#E5DDCF]">
          <p className="text-sm text-[#292B26]/60 mb-2">Total Cultivation Cost</p>
          <div className="text-3xl font-bold text-[#B6532A] mb-2">
            ₹{economics ? economics.total_cost.toLocaleString('en-IN') : '...'}
          </div>
          <p className="text-xs text-[#292B26]/50">
            Break-even price: ₹{economics ? Math.round(economics.break_even_price) : '0'}/Qtl
          </p>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-[#E5DDCF]">
          <p className="text-sm text-[#292B26]/60 mb-2">Expected Revenue</p>
          <div className="text-3xl font-bold text-[#17643E] mb-2">
            ₹{economics ? economics.expected_revenue.toLocaleString('en-IN') : '...'}
          </div>
          <p className="text-xs text-[#292B26]/50">Based on expected market pricing</p>
        </div>
        <div className="bg-[#103D2C] text-white p-6 rounded-2xl shadow-sm">
          <p className="text-sm text-[#A8C69A] mb-2">Expected Net Profit</p>
          <div className="text-3xl font-bold text-white mb-2">
            ₹{economics ? economics.expected_profit.toLocaleString('en-IN') : '...'}
          </div>
          <div className="text-xs text-[#A8C69A] flex items-center gap-1">
            <TrendingUp size={12} /> ROI: {economics ? economics.roi_percent : 0}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-[#103D2C] flex items-center gap-2"><PieChart size={18} /> Cost Breakdown</h3>
          </div>
          <div className="space-y-4">
            {[
              { name: 'Seeds & Seed Treatment', val: `₹${seedsCost.toLocaleString('en-IN')}`, pct: totalCost > 0 ? Math.round((seedsCost / totalCost) * 100) : 0, color: 'bg-[#17643E]' },
              { name: 'Fertilizers & Nutrients', val: `₹${fertCost.toLocaleString('en-IN')}`, pct: totalCost > 0 ? Math.round((fertCost / totalCost) * 100) : 0, color: 'bg-[#A8C69A]' },
              { name: 'Labor & Field Operations', val: `₹${labourCost.toLocaleString('en-IN')}`, pct: totalCost > 0 ? Math.round((labourCost / totalCost) * 100) : 0, color: 'bg-[#B6532A]' },
              { name: 'Machinery & Irrigation', val: `₹${irrigationCost.toLocaleString('en-IN')}`, pct: totalCost > 0 ? Math.round((irrigationCost / totalCost) * 100) : 0, color: 'bg-[#E5DDCF]' },
            ].map(item => (
              <div key={item.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-[#292B26]">{item.name}</span>
                  <span className="font-bold text-[#103D2C]">{item.val} ({item.pct}%)</span>
                </div>
                <div className="w-full bg-[#FBF7EF] h-2 rounded-full">
                  <div className={`${item.color} h-2 rounded-full`} style={{ width: `${item.pct}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-[#103D2C] flex items-center gap-2"><BarChart size={18} /> Profitability Overview</h3>
          </div>
          <div className="p-4 bg-[#FBF7EF] rounded-xl border border-[#E5DDCF] space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-[#292B26]/70">Yield Target</span>
              <span className="font-bold text-[#103D2C]">{expectedYield} Quintals</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#292B26]/70">Selling Price Point</span>
              <span className="font-bold text-[#103D2C]">₹{expectedPrice} / Qtl</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[#292B26]/70">Cost per Quintal</span>
              <span className="font-bold text-[#B6532A]">₹{expectedYield > 0 ? Math.round(totalCost / expectedYield) : 0} / Qtl</span>
            </div>
            <div className="flex justify-between text-sm pt-2 border-t border-[#E5DDCF]">
              <span className="font-bold text-[#103D2C]">Profit per Quintal</span>
              <span className="font-bold text-[#17643E]">₹{expectedYield > 0 ? Math.round((economics?.expected_profit ?? 0) / expectedYield) : 0} / Qtl</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
