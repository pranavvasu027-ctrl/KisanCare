import React, { useState, useEffect } from 'react';
import { Sparkles, ArrowRight, Zap, TrendingUp, CheckCircle, ShieldCheck } from 'lucide-react';
import { SmartRecommendationsResponse } from '../../types/rental';
import { rentalApi } from '../../services/rentalApi';

interface SmartRecommendationBannerProps {
  crop?: string;
  acreage?: number;
  onSelectListing?: (listingId: string) => void;
}

export default function SmartRecommendationBanner({
  crop = 'Cotton',
  acreage = 4.5,
  onSelectListing
}: SmartRecommendationBannerProps) {
  const [data, setData] = useState<SmartRecommendationsResponse | null>(null);

  useEffect(() => {
    let isMounted = true;
    rentalApi.getRecommendations(crop, acreage).then((res) => {
      if (isMounted) setData(res);
    }).catch((err) => {
      console.error('Failed to get recommendations:', err);
    });
    return () => { isMounted = false; };
  }, [crop, acreage]);

  if (!data || data.recommendations.length === 0) return null;

  const topRec = data.recommendations[0];

  return (
    <div className="bg-gradient-to-r from-[#103D2C] to-[#17643E] text-white rounded-3xl p-5 md:p-6 shadow-md border border-[#E5DDCF] relative overflow-hidden">
      <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-10 pointer-events-none flex items-center justify-end pr-8">
        <Sparkles size={160} />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-1.5 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-white/20 text-white px-2.5 py-0.5 rounded-full flex items-center gap-1 backdrop-blur-sm">
              <Zap size={11} className="text-amber-300" /> Agronomic Match for {crop} ({acreage} Acres)
            </span>
            <span className="text-xs text-emerald-200">Akola Agro-Climatic Zone</span>
          </div>

          <h3 className="font-serif font-bold text-lg text-white">
            Recommended: {topRec.recommended_equipment}
          </h3>
          <p className="text-xs text-emerald-100/90 leading-relaxed">
            {topRec.rationale}
          </p>

          <div className="flex flex-wrap items-center gap-4 text-xs pt-1">
            <div className="flex items-center gap-1.5 text-emerald-200">
              <TrendingUp size={13} className="text-emerald-300" />
              <span>Est. Machinery Cost: <strong>₹{topRec.estimated_machinery_cost}</strong></span>
            </div>
            <span className="text-emerald-400">•</span>
            <div className="text-emerald-200">
              Manual Equivalent: <span className="line-through text-emerald-300/70">₹{topRec.estimated_labour_cost}</span>
            </div>
            <span className="text-emerald-400">•</span>
            <span className="bg-amber-400 text-stone-900 font-bold px-2 py-0.5 rounded text-[11px]">
              Save ~{topRec.savings_percent}%
            </span>
          </div>
        </div>

        {onSelectListing && (
          <button
            type="button"
            onClick={() => onSelectListing(topRec.best_value_listing_id)}
            className="bg-white hover:bg-[#FBF7EF] text-[#103D2C] font-bold text-xs px-4 py-3 rounded-2xl flex items-center gap-2 transition-transform hover:scale-105 shadow-md shrink-0"
          >
            <span>View Suitable Machinery</span>
            <ArrowRight size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
