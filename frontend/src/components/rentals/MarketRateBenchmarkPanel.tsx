import React, { useState, useEffect } from 'react';
import { Landmark, ShieldCheck, ExternalLink, Info, CheckCircle2, Loader2 } from 'lucide-react';
import { MarketRateBenchmark } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';

export default function MarketRateBenchmarkPanel() {
  const [benchmarks, setBenchmarks] = useState<MarketRateBenchmark[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await rentalApi.getMarketBenchmarks(undefined, 'Akola');
        setBenchmarks(data);
      } catch (err) {
        console.error('Failed to load benchmarks:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="bg-white rounded-3xl p-6 border border-[#E5DDCF] shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-900 flex items-center justify-center shrink-0">
            <Landmark size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-serif font-bold text-base text-[#103D2C]">
                Official Custom Hiring Center (CHC) Benchmarks
              </h3>
              <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                <ShieldCheck size={11} /> Verified Government Rates
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Reference tariff guidelines for Akola & Vidarbha (Dr. PDKV Akola & Maharashtra Dept of Agriculture)
            </p>
          </div>
        </div>

        <span className="text-[11px] text-gray-400">
          Last Verified: October 2026
        </span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8 text-xs text-gray-500 gap-2">
          <Loader2 size={16} className="animate-spin text-[#103D2C]" />
          Loading regional benchmarks...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
          {benchmarks.map((b) => (
            <div
              key={b.id}
              className="bg-[#FBF7EF] rounded-2xl p-4 border border-[#E5DDCF] flex flex-col justify-between space-y-3 hover:border-[#17643E]/50 transition-colors"
            >
              <div>
                <div className="flex justify-between items-center text-[10px] uppercase font-bold text-[#103D2C]">
                  <span>{b.category}</span>
                  <span className="text-gray-400 font-normal">{b.region}</span>
                </div>
                <h4 className="font-bold text-xs text-gray-900 mt-1">{b.item_name}</h4>
                <div className="mt-2 text-sm font-bold text-[#17643E]">
                  ₹{b.indicative_rate_min} – ₹{b.indicative_rate_max}
                  <span className="text-[11px] font-normal text-gray-500 ml-1">/{b.billing_unit.replace('per_', '')}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-[#E5DDCF]/60 text-[10px] text-gray-500 space-y-1">
                <div className="flex items-center gap-1 text-gray-700 font-medium">
                  <CheckCircle2 size={11} className="text-emerald-600 shrink-0" />
                  <span className="line-clamp-1">{b.source_name}</span>
                </div>
                <p className="line-clamp-2 text-gray-500">{b.notes}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="text-[11px] text-gray-500 bg-amber-50/60 p-3 rounded-2xl border border-amber-200/60 flex items-start gap-2">
        <Info size={14} className="text-amber-700 shrink-0 mt-0.5" />
        <span>
          <strong>Agronomic Transparency:</strong> Published CHC tariffs represent baseline indicative custom hiring rates. Individual provider quotations may vary based on implement wear, field soil moisture, and fuel inclusion.
        </span>
      </div>
    </div>
  );
}
