import React, { useState, useEffect } from 'react';
import { IndianRupee, TrendingUp, TrendingDown, PieChart, BarChart, Loader2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function FarmEconomics() {
  const [expectedYield, setExpectedYield] = useState<number>(50);
  const [expectedPrice, setExpectedPrice] = useState<number>(8000);
  const [inputCost, setInputCost] = useState<number>(31010);
  const [labourCost, setLabourCost] = useState<number>(50000);
  const [irrigationCost, setIrrigationCost] = useState<number>(65000);

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

      {/* AMBIGUITY & PROVENANCE DISCLOSURE */}
      <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 text-amber-900 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <span className="bg-amber-200 text-amber-900 text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded">
            Recorded Cost Ambiguities &amp; Disclosures
          </span>
          <span className="text-xs text-amber-800 font-semibold">Farmer: Pranav Vasu &bull; Cotton 2026&ndash;27</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-amber-950">
          <div>
            &bull; <strong>Seed Cost (₹10,000&ndash;₹12,000):</strong> Mean ₹11,000 recorded. Ambiguity preserved regarding whether this covers the whole farm or Field A.<br/>
            &bull; <strong>Fertilizers (~₹20,000+):</strong> Unitemized bulk sum recorded without component breakdown.<br/>
            &bull; <strong>Pesticide (₹10):</strong> Preserved verbatim as reported; flagged as clear recording anomaly / typographical error for ₹10,000.
          </div>
          <div>
            &bull; <strong>Other (&lsquo;yechan&rsquo; &ndash; ₹40,000):</strong> Preserved verbatim as local dialect term; category clarification pending.<br/>
            &bull; <strong>Market Price (₹8,000/qtl):</strong> Grounded in Akot APMC benchmark recorded 2026-10-15; actual sale quantity is currently 0.<br/>
            &bull; <strong>Labour (₹50,000) &amp; Machinery (₹20,000):</strong> Major cultivation outlays.
          </div>
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
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-bold text-[#B6532A] uppercase tracking-wider">Recorded Expenses</p>
            <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-2 py-0.5 rounded">Ambiguities Pending</span>
          </div>
          <div className="text-3xl font-bold text-[#B6532A] mb-1">
            ₹1,56,010*
          </div>
          <p className="text-[11px] text-[#292B26]/60 leading-tight">
            *Includes ₹10 pesticide entry, ₹10k–12k seed range, and ₹40,000 &lsquo;yechan&rsquo;. Area/period basis unverified.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-[#E5DDCF]">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-bold text-[#17643E] uppercase tracking-wider">Benchmark Revenue</p>
            <span className="text-[10px] bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded">Market Benchmark</span>
          </div>
          <div className="text-3xl font-bold text-[#17643E] mb-1">
            ₹4,00,000
          </div>
          <p className="text-[11px] text-[#292B26]/60 leading-tight">
            50 Qtl benchmark @ ₹8,000/Qtl (Akot APMC dated 2026-10-15). <strong>Actual Quantity Sold: 0 Qtl</strong>.
          </p>
        </div>

        <div className="bg-[#103D2C] text-white p-6 rounded-2xl shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-bold text-[#A8C69A] uppercase tracking-wider">Indicative Margin</p>
              <span className="text-[10px] bg-amber-400 text-stone-900 font-bold px-2 py-0.5 rounded">Simulated Scenario</span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              ₹2,43,990*
            </div>
          </div>
          <p className="text-[10px] text-[#A8C69A] leading-tight pt-2 border-t border-emerald-800">
            <strong>Definitive profit cannot be established</strong> until expense periods, areas, and units are clarified.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-[#103D2C] flex items-center gap-2"><PieChart size={18} /> Cost Breakdown</h3>
          </div>
          <div className="space-y-4">
            {[
              { name: 'Labour (Intercultural operations)', val: '₹50,000', pct: 32, ambiguity: 'Period & area basis unclear', color: 'bg-[#B6532A]' },
              { name: 'Other Cost (yechan)', val: '₹40,000', pct: 26, ambiguity: 'Local dialect entry; category clarification pending', color: 'bg-[#E5DDCF]' },
              { name: 'Fertilizers (Bulk unitemized)', val: '₹20,000', pct: 13, ambiguity: 'Reported as ~₹20,000+ without component split', color: 'bg-[#A8C69A]' },
              { name: 'Machinery (Rental & fuel)', val: '₹20,000', pct: 13, ambiguity: 'Basis unclear', color: 'bg-[#17643E]' },
              { name: 'Seed Cost (godavari)', val: '₹11,000', pct: 7, ambiguity: 'Range ₹10k–12k; whole farm vs Field A unclear', color: 'bg-[#17643E]' },
              { name: 'Land Preparation', val: '₹10,000', pct: 6, ambiguity: 'Reported total', color: 'bg-[#E5DDCF]' },
              { name: 'Transport (To Akot APMC)', val: '₹5,000', pct: 3, ambiguity: 'Basis unclear', color: 'bg-[#B6532A]' },
              { name: 'Pesticide Application', val: '₹10', pct: 1, ambiguity: 'Preserved verbatim; likely recording anomaly for ₹10,000', color: 'bg-red-400' },
            ].map(item => (
              <div key={item.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-[#292B26]">{item.name}</span>
                  <div className="text-right"><span className="font-bold text-[#103D2C]">{item.val}</span><span className="block text-[9px] text-amber-700 font-normal">{item.ambiguity}</span></div>
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
