import React, { useState } from 'react';
import {
  Package, AlertTriangle, TrendingDown, Clock, ShieldCheck,
  HelpCircle, ArrowRight, Loader2, Sparkles, CheckCircle2, Warehouse
} from 'lucide-react';

interface LossEstimate {
  lossPercentage: number;
  quantityLostQtl: number;
  financialLossRs: number;
  spoilageRisk: 'Low' | 'Moderate' | 'High';
  maxSafeDays: number;
  recommendations: string[];
  sellVsHoldAdvice: string;
}

export default function PostHarvestLoss() {
  const [crop, setCrop] = useState('Soybean');
  const [quantity, setQuantity] = useState<number>(100);
  const [storageType, setStorageType] = useState('Traditional Gunny Bags');
  const [storageDays, setStorageDays] = useState<number>(60);
  const [loading, setLoading] = useState(false);
  const [estimate, setEstimate] = useState<LossEstimate | null>({
    lossPercentage: 4.8,
    quantityLostQtl: 4.8,
    financialLossRs: 22320,
    spoilageRisk: 'Moderate',
    maxSafeDays: 75,
    recommendations: [
      'Maintain grain moisture below 10% before bagging.',
      'Place bags on wooden pallets at least 30cm away from exterior walls.',
      'Inspect weekly for pulse beetle / storage weevil activity.'
    ],
    sellVsHoldAdvice: 'Expected market price gain (+4.2%) is higher than storage loss costs (1.8% per month). Holding for 30-45 days is economically advantageous if hermetic storage is used.'
  });

  const handleCalculate = () => {
    setLoading(true);
    setTimeout(() => {
      let baseRate = 0.05; // 5% default
      let maxDays = 90;

      if (crop === 'Tomato' || crop === 'Onion') {
        baseRate = 0.15;
        maxDays = 30;
      } else if (crop === 'Wheat') {
        baseRate = 0.03;
        maxDays = 180;
      }

      if (storageType === 'Hermetic Bags / Silo' || storageType === 'Cold Storage') {
        baseRate *= 0.4;
        maxDays *= 1.8;
      } else if (storageType === 'Covered Farm Shed') {
        baseRate *= 1.3;
      }

      const daysFactor = storageDays / 60;
      const calcLossPct = Math.min(Math.round(baseRate * daysFactor * 100 * 10) / 10, 45);
      const lostQtl = Math.round((quantity * (calcLossPct / 100)) * 10) / 10;
      const avgPrice = crop === 'Soybean' ? 4650 : crop === 'Cotton' ? 6880 : crop === 'Wheat' ? 2340 : 2500;
      const finLoss = Math.round(lostQtl * avgPrice);

      setEstimate({
        lossPercentage: calcLossPct,
        quantityLostQtl: lostQtl,
        financialLossRs: finLoss,
        spoilageRisk: calcLossPct > 10 ? 'High' : calcLossPct > 4 ? 'Moderate' : 'Low',
        maxSafeDays: Math.round(maxDays),
        recommendations: [
          `Target moisture content for ${crop} should be monitored periodically.`,
          storageType.includes('Hermetic')
            ? 'Ensure airtight seal is maintained without punctures.'
            : 'Consider transitioning to hermetic inner liners to reduce pest respiration.',
          'Keep storage area dry and ventilated during peak afternoon humidity.'
        ],
        sellVsHoldAdvice: calcLossPct > 8
          ? 'Storage risk is high. Current market price indicates selling within 15 days will minimize net revenue loss.'
          : 'Storage conditions are stable. Holding for market upside is viable.'
      });
      setLoading(false);
    }, 600);
  };

  return (
    <div className="p-4 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Post-Harvest Loss Intelligence</h1>
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
              Sample Model
            </span>
          </div>
          <p className="text-[#292B26]/70 mt-1">
            Predict storage degradation, spoilage risk, and identify the optimal selling window for your harvest.
          </p>
        </div>
      </div>

      {/* Info Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 flex items-start gap-3">
        <Sparkles className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">UI Integration Prototype:</span> This interface models post-harvest shelf life using standard agricultural storage curves. Once backend ML service stabilization completes, it will connect to live predictive endpoints.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Parameters Form */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5DDCF] space-y-5 h-fit">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E5DDCF]">
            <Warehouse className="text-[#17643E] w-5 h-5" />
            <h3 className="font-bold text-[#103D2C]">Harvest & Storage Inputs</h3>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#292B26] mb-1">Harvested Crop</label>
            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm font-medium text-[#103D2C] focus:outline-none focus:border-[#17643E]"
            >
              <option value="Soybean">Soybean</option>
              <option value="Cotton">Cotton</option>
              <option value="Wheat">Wheat</option>
              <option value="Onion">Onion</option>
              <option value="Tomato">Tomato</option>
              <option value="Potato">Potato</option>
              <option value="Maize">Maize</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#292B26] mb-1">Total Harvest Quantity (Quintals)</label>
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
              className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm focus:outline-none focus:border-[#17643E]"
            />
            <span className="text-[11px] text-[#292B26]/50 mt-1 block">1 Quintal = 100 kg</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#292B26] mb-1">Storage Facility Type</label>
            <select
              value={storageType}
              onChange={(e) => setStorageType(e.target.value)}
              className="w-full border border-[#E5DDCF] rounded-lg px-3 py-2 bg-[#FBF7EF] text-sm font-medium text-[#103D2C] focus:outline-none focus:border-[#17643E]"
            >
              <option value="Traditional Gunny Bags">Traditional Gunny Bags (Jute)</option>
              <option value="Hermetic Bags / Silo">Hermetic Bags / Metal Silo (Airtight)</option>
              <option value="Covered Farm Shed">Covered On-Farm Shed</option>
              <option value="Ventilated Warehouse">Ventilated APMC Warehouse</option>
              <option value="Cold Storage">Commercial Cold Storage</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-xs font-semibold text-[#292B26]">Planned Storage Duration</label>
              <span className="text-xs font-bold text-[#17643E]">{storageDays} Days</span>
            </div>
            <input
              type="range"
              min={7}
              max={180}
              step={7}
              value={storageDays}
              onChange={(e) => setStorageDays(Number(e.target.value))}
              className="w-full accent-[#17643E] cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-[#292B26]/50">
              <span>1 Week</span>
              <span>1 Month</span>
              <span>3 Months</span>
              <span>6 Months</span>
            </div>
          </div>

          <button
            onClick={handleCalculate}
            disabled={loading}
            className="w-full bg-[#103D2C] hover:bg-[#17643E] text-white font-semibold py-2.5 px-4 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Package className="w-4 h-4" />}
            <span>Calculate Loss & Risk</span>
          </button>
        </div>

        {/* Prediction Results */}
        <div className="lg:col-span-2 space-y-6">
          {loading ? (
            <div className="bg-white rounded-2xl p-12 border border-[#E5DDCF] text-center flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 text-[#17643E] animate-spin mb-3" />
              <p className="text-sm font-medium text-[#103D2C]">Computing storage degradation curve...</p>
              <p className="text-xs text-[#292B26]/50 mt-1">Analyzing crop moisture loss and ambient temperature factor</p>
            </div>
          ) : estimate ? (
            <>
              {/* Top KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center text-red-600">
                      <TrendingDown className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-xs text-[#292B26]/60">Projected Loss</span>
                      <div className="text-2xl font-bold text-[#103D2C]">{estimate.lossPercentage}%</div>
                    </div>
                  </div>
                  <p className="text-xs text-[#292B26]/60">{estimate.quantityLostQtl} Quintals estimated lost</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-amber-600">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-xs text-[#292B26]/60">Financial Impact</span>
                      <div className="text-2xl font-bold text-[#B6532A]">₹{estimate.financialLossRs.toLocaleString()}</div>
                    </div>
                  </div>
                  <p className="text-xs text-[#292B26]/60">At current market baseline</p>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-[#E5DDCF] shadow-sm">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      estimate.spoilageRisk === 'High' ? 'bg-red-50 text-red-600' :
                      estimate.spoilageRisk === 'Moderate' ? 'bg-amber-50 text-amber-600' :
                      'bg-emerald-50 text-emerald-600'
                    }`}>
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-xs text-[#292B26]/60">Spoilage Risk</span>
                      <div className={`text-xl font-bold ${
                        estimate.spoilageRisk === 'High' ? 'text-red-700' :
                        estimate.spoilageRisk === 'Moderate' ? 'text-amber-700' :
                        'text-emerald-700'
                      }`}>
                        {estimate.spoilageRisk}
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-[#292B26]/60">Max safe shelf-life: ~{estimate.maxSafeDays} days</p>
                </div>
              </div>

              {/* Economic Recommendation: Hold vs Sell */}
              <div className="bg-[#FBF7EF] rounded-2xl p-6 border border-[#E5DDCF] space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-[#17643E]" />
                  <h3 className="font-bold text-[#103D2C]">Sell vs. Hold Window Strategy</h3>
                </div>
                <p className="text-sm text-[#292B26]/80 leading-relaxed bg-white p-4 rounded-xl border border-[#E5DDCF]">
                  {estimate.sellVsHoldAdvice}
                </p>
              </div>

              {/* Actionable Storage Guidelines */}
              <div className="bg-white rounded-2xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
                <h3 className="font-bold text-[#103D2C] flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-[#17643E]" />
                  Recommended Storage Precautions
                </h3>
                <ul className="space-y-2.5">
                  {estimate.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-[#292B26]/80 bg-[#FBF7EF] p-3 rounded-xl border border-[#E5DDCF]/70">
                      <span className="w-5 h-5 rounded-full bg-[#17643E]/10 text-[#17643E] font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
