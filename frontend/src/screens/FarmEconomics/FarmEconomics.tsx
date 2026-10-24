import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { translateDynamic } from '../../i18n/translateHelper';
import { IndianRupee, TrendingUp, TrendingDown, PieChart, BarChart, Loader2, AlertCircle, ChevronDown, ChevronUp, DollarSign, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { WorkflowStepper } from '../../components/workflow/WorkflowStepper';
import { WorkflowFooter } from '../../components/workflow/WorkflowFooter';

export default function FarmEconomics() {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || 'en';
  const [expectedYield, setExpectedYield] = useState<number>(50);
  const [expectedPrice, setExpectedPrice] = useState<number>(8000);
  const [inputCost, setInputCost] = useState<number>(41000);
  const [labourCost, setLabourCost] = useState<number>(50000);
  const [irrigationCost, setIrrigationCost] = useState<number>(65000);
  const [showDisclosures, setShowDisclosures] = useState<boolean>(false);

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

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      <WorkflowStepper currentStageId={4} />

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-heading font-extrabold text-slate-900">{t('economics.title', 'Farm Economics & Budgeting')}</h1>
            {isDemo ? (
              <span className="bg-amber-100 text-amber-900 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                {t('economics.sampleBadge', 'Sample Economics Data')}
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-900 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300">
                {t('economics.liveBadge', 'Live Economics Engine')}
              </span>
            )}
          </div>
          <p className="text-slate-600 mt-1">{t('economics.subtitle', 'Track operational costs, expected APMC market revenue, and overall harvest ROI.')}</p>
        </div>
      </div>

      {/* COLLAPSIBLE COST LEDGER ACCORDION */}
      <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-2xl p-4 text-emerald-950 shadow-2xs">
        <button
          type="button"
          onClick={() => setShowDisclosures(!showDisclosures)}
          className="w-full flex items-center justify-between text-left cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <span className="bg-emerald-200 text-emerald-900 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded">
              Cost Ledger Reference
            </span>
            <span className="text-xs font-semibold text-emerald-900">
              Farmer: Pranav Vasu • Cotton (Godavari) 2026–27
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-emerald-800 font-semibold">
            <span>{showDisclosures ? 'Hide Ledger Details' : 'View Cost Breakdown'}</span>
            {showDisclosures ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>
        </button>

        {showDisclosures && (
          <div className="mt-3 pt-3 border-t border-emerald-200 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-emerald-950 animate-fadeIn">
            <div>
              &bull; <strong>Certified Hybrid Seed (₹11,000):</strong> High-germination Godavari variety seed bags.<br/>
              &bull; <strong>Fertilizer Application (₹20,000):</strong> Balanced NPK basal dose and top-dressing Urea splits.<br/>
              &bull; <strong>Crop Protection (₹10,000):</strong> Integrated pest management (IPM) and registered foliar spray.
            </div>
            <div>
              &bull; <strong>Intercultural Operations &amp; Picking (₹40,000):</strong> Seasonal manual weeding and cotton picking rounds.<br/>
              &bull; <strong>Market Realization (₹8,000/qtl):</strong> Grounded in Akot APMC benchmark prices.<br/>
              &bull; <strong>Labour (₹50,000) &amp; Machinery (₹20,000):</strong> Primary field preparation and mechanized intercultural operations.
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Interactive Economic Parameter Inputs */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <h3 className="font-bold text-xs text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
          <DollarSign size={16} className="text-emerald-700" /> Economic Model Parameters
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">{t('economics.expectedYieldLabel', 'Expected Yield (Quintals)')}</label>
            <input
              type="number"
              min="1"
              value={expectedYield}
              onChange={(e) => setExpectedYield(Number(e.target.value))}
              className="w-full border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 outline-none transition-colors"
            />
          </div>
          <div>
<label className="block text-xs font-semibold text-slate-700 mb-1">{t('economics.expectedPriceLabel', 'Expected Price (₹/Qtl)')}</label>
            <input
              type="number"
              min="100"
              step="50"
              value={expectedPrice}
              onChange={(e) => setExpectedPrice(Number(e.target.value))}
              className="w-full border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 outline-none transition-colors"
            />
          </div>
          <div>
<label className="block text-xs font-semibold text-slate-700 mb-1">{t('economics.inputCostLabel', 'Inputs Cost (₹)')}</label>
            <input
              type="number"
              min="0"
              step="500"
              value={inputCost}
              onChange={(e) => setInputCost(Number(e.target.value))}
              className="w-full border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 outline-none transition-colors"
            />
          </div>
          <div>
<label className="block text-xs font-semibold text-slate-700 mb-1">{t('economics.labourCostLabel', 'Labour Cost (₹)')}</label>
            <input
              type="number"
              min="0"
              step="500"
              value={labourCost}
              onChange={(e) => setLabourCost(Number(e.target.value))}
              className="w-full border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 outline-none transition-colors"
            />
          </div>
          <div>
<label className="block text-xs font-semibold text-slate-700 mb-1">{t('economics.irrigationCostLabel', 'Irrigation Cost (₹)')}</label>
            <input
              type="number"
              min="0"
              step="250"
              value={irrigationCost}
              onChange={(e) => setIrrigationCost(Number(e.target.value))}
              className="w-full border border-slate-200 bg-slate-50 focus:bg-white focus:border-emerald-500 rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900 outline-none transition-colors"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-1">
<p className="text-xs font-bold text-slate-600 uppercase tracking-wider">{t('economics.totalCost', 'Estimated Total Expenses')}</p>
            <span className="text-[10px] bg-slate-100 text-slate-800 font-semibold px-2 py-0.5 rounded">Seasonal Budget</span>
          </div>
          <div className="text-3xl font-heading font-extrabold text-slate-900 mb-1">
            ₹{totalCost.toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            *Includes seed, fertilizer, plant protection, intercultural operations, labour, and irrigation outlays.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-1">
<p className="text-xs font-bold text-emerald-700 uppercase tracking-wider">{t('economics.grossRevenue', 'Projected Revenue')}</p>
            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded">APMC Benchmark</span>
          </div>
          <div className="text-3xl font-heading font-extrabold text-emerald-700 mb-1">
            ₹{(expectedYield * expectedPrice).toLocaleString('en-IN')}
          </div>
          <p className="text-[11px] text-slate-500 leading-tight">
            {expectedYield} Qtl benchmark @ ₹{expectedPrice.toLocaleString('en-IN')}/Qtl based on Akot APMC market rates.
          </p>
        </div>

        <div className="bg-gradient-to-br from-emerald-800 to-emerald-950 text-white p-6 rounded-2xl shadow-md flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-bold text-emerald-300 uppercase tracking-wider">Estimated Net Margin</p>
              <span className="text-[10px] bg-emerald-500 text-slate-950 font-bold px-2 py-0.5 rounded">Expected ROI</span>
            </div>
            <div className="text-3xl font-heading font-extrabold text-white mb-1">
              ₹{((expectedYield * expectedPrice) - totalCost).toLocaleString('en-IN')}
            </div>
          </div>
          <p className="text-[10px] text-emerald-200 leading-tight pt-2 border-t border-emerald-700/60">
            Projected net earnings based on current input cost allocation and targeted harvest yield.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-slate-900 flex items-center gap-2"><PieChart size={18} className="text-emerald-700" /> Cost Breakdown</h3>
          </div>
          <div className="space-y-4">
            {[
              { name: 'Labour & Weeding', val: '₹50,000', pct: 32, note: 'Field labour & thinning', color: 'bg-emerald-700' },
              { name: 'Harvesting & Picking Rounds', val: '₹40,000', pct: 26, note: 'Cotton picking operations', color: 'bg-emerald-600' },
              { name: 'Fertilizers & Nutrients', val: '₹20,000', pct: 13, note: 'DAP, SSP & split Urea', color: 'bg-teal-600' },
              { name: 'Machinery & Tractor Operations', val: '₹20,000', pct: 13, note: 'Mechanized tillage & sowing', color: 'bg-blue-600' },
              { name: 'Certified Hybrid Seed (Godavari)', val: '₹11,000', pct: 7, note: 'Certified seed bags', color: 'bg-amber-600' },
              { name: 'Pre-Monsoon Land Preparation', val: '₹10,000', pct: 6, note: 'Deep ploughing & rotavator', color: 'bg-slate-500' },
              { name: 'Plant Protection & Spray', val: '₹10,000', pct: 6, note: 'IPM & registered fungicides', color: 'bg-rose-500' },
              { name: 'Mandi Transport (Akot APMC)', val: '₹5,000', pct: 3, note: 'Market transit & handling', color: 'bg-amber-500' },
            ].map(item => (
              <div key={item.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-slate-700">{item.name}</span>
                  <div className="text-right">
                    <span className="font-bold text-slate-900">{item.val}</span>
                    <span className="block text-[10px] text-slate-500 font-normal">{item.note}</span>
                  </div>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className={`${item.color} h-2 rounded-full`} style={{ width: `${item.pct}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-bold text-slate-900 flex items-center gap-2"><BarChart size={18} className="text-emerald-700" /> Profitability &amp; Unit Economics</h3>
            </div>
            <div className="p-5 bg-slate-50 rounded-xl border border-slate-200 space-y-3.5">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Yield Target</span>
                <span className="font-bold text-slate-900">{expectedYield} Quintals</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Selling Price Point</span>
                <span className="font-bold text-slate-900">₹{expectedPrice.toLocaleString('en-IN')} / Qtl</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Production Cost per Quintal</span>
                <span className="font-bold text-slate-900">₹{expectedYield > 0 ? Math.round(totalCost / expectedYield).toLocaleString('en-IN') : 0} / Qtl</span>
              </div>
              <div className="flex justify-between text-sm pt-2.5 border-t border-slate-200">
                <span className="font-bold text-slate-900">Net Profit per Quintal</span>
                <span className="font-bold text-emerald-700">₹{expectedYield > 0 ? Math.round(((expectedYield * expectedPrice) - totalCost) / expectedYield).toLocaleString('en-IN') : 0} / Qtl</span>
              </div>
            </div>
          </div>

          <div className="mt-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 flex items-start gap-2.5">
            <CheckCircle2 size={16} className="text-emerald-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-emerald-900">Break-Even Analysis:</span>
              <p className="text-[11px] leading-relaxed text-emerald-900/90 mt-0.5">
                At an average cultivation cost of ₹{expectedYield > 0 ? Math.round(totalCost / expectedYield).toLocaleString('en-IN') : 0}/Qtl, minimum MSP or APMC price required to break even is ₹{expectedYield > 0 ? Math.round(totalCost / expectedYield).toLocaleString('en-IN') : 0}/Qtl. Current market price of ₹{expectedPrice.toLocaleString('en-IN')}/Qtl provides a healthy margin safety buffer.
              </p>
            </div>
          </div>
        </div>
      </div>

      <WorkflowFooter
        currentStageNumber={4}
        currentStageName="Simulation & ROI"
        completedActionMessage={`Economics evaluated! Total Cost: ₹${totalCost.toLocaleString()}, Net Profit: ₹${((expectedYield * expectedPrice) - totalCost).toLocaleString()}. Proceed to APMC Mandi market forecasts.`}
        prevStep={{ label: "What-If Simulator", path: "/simulator" }}
        nextStep={{
          label: "Mandi Market Intelligence",
          labelMr: "बाजारभाव अंदाज",
          path: "/market",
          description: "Discover high-yield APMC markets and price trends"
        }}
        alternativeNextStep={{
          label: "Post-Harvest Storage",
          path: "/post-harvest"
        }}
      />
    </div>
  );
}
