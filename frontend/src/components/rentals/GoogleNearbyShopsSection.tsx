import React from 'react';
import {
  MapPin, Phone, Star, Navigation, Store, ExternalLink,
  Compass, Award
} from 'lucide-react';
import { NearbyShopPlace } from '../../types/rental';

interface GoogleNearbyShopsSectionProps {
  shops: NearbyShopPlace[];
  radiusKm?: number;
  centerAddress?: string;
  loading?: boolean;
  onRefresh?: () => void;
  onSelectShop?: (shop: NearbyShopPlace) => void;
}

export const GoogleNearbyShopsSection: React.FC<GoogleNearbyShopsSectionProps> = ({
  shops,
  radiusKm = 50,
  centerAddress = 'Akola',
  loading = false,
  onRefresh,
  onSelectShop
}) => {
  // Guarantee strict nearest-first sorting by distance ascending
  const sortedShops = [...shops].sort((a, b) => (a.distance_km || 0) - (b.distance_km || 0));

  return (
    <div className="bg-white rounded-2xl p-4 lg:p-5 border border-[#E5DDCF] shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 border-b border-[#E5DDCF]/60 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-emerald-100 text-[#17643E] rounded-lg">
            <Store size={18} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[#103D2C] flex items-center gap-2">
              <span>Nearby Rental Shops (Google Maps)</span>
              <span className="text-xs font-semibold text-[#17643E] bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                {sortedShops.length} Found • {radiusKm}km
              </span>
            </h2>
          </div>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            className="text-xs font-bold text-[#103D2C] hover:text-[#17643E] bg-[#FBF7EF] hover:bg-[#F2E8D5] border border-[#E5DDCF] px-3 py-1.5 rounded-xl transition-all flex items-center gap-1.5 shrink-0"
          >
            <Compass size={13} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Scanning...' : 'Re-scan'}</span>
          </button>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="py-8 text-center text-xs text-gray-500 space-y-2">
          <div className="w-6 h-6 border-2 border-[#103D2C] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-semibold text-[#103D2C]">Scanning nearest rental shops...</p>
        </div>
      ) : sortedShops.length === 0 ? (
        <div className="py-6 text-center text-xs text-gray-500 bg-[#FBF7EF] rounded-xl border border-dashed border-[#E5DDCF]">
          No rental shops found within {radiusKm} km.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {sortedShops.map((shop, idx) => {
            const isClosest = idx === 0;
            return (
              <div
                key={shop.place_id}
                className={`bg-[#FBF7EF] hover:bg-white rounded-xl p-3.5 border transition-all shadow-sm hover:shadow flex flex-col justify-between space-y-2.5 group ${
                  isClosest
                    ? 'border-[#17643E] ring-1 ring-[#17643E]/20 bg-emerald-50/20'
                    : 'border-[#E5DDCF] hover:border-[#17643E]'
                }`}
              >
                <div className="space-y-1.5">
                  {/* Distance & Rating */}
                  <div className="flex items-center justify-between text-xs">
                    <span className={`font-bold text-[11px] px-2 py-0.5 rounded-md border flex items-center gap-1 ${
                      isClosest
                        ? 'bg-[#103D2C] text-white border-[#103D2C]'
                        : 'bg-white text-[#103D2C] border-[#E5DDCF]'
                    }`}>
                      {isClosest ? (
                        <>
                          <Award size={11} className="text-amber-300" />
                          <span>{shop.distance_km ? `${shop.distance_km.toFixed(1)} km • Closest` : 'Nearest'}</span>
                        </>
                      ) : (
                        <>
                          <Navigation size={10} className="text-[#17643E]" />
                          <span>{shop.distance_km ? `${shop.distance_km.toFixed(1)} km` : 'Nearby'}</span>
                        </>
                      )}
                    </span>

                    <div className="flex items-center gap-1 text-amber-700 font-bold text-xs">
                      <Star size={11} className="fill-amber-500 text-amber-500" />
                      <span>{shop.rating ? shop.rating.toFixed(1) : '4.5'}</span>
                      {shop.user_ratings_total && (
                        <span className="text-gray-400 font-normal text-[10px]">({shop.user_ratings_total})</span>
                      )}
                    </div>
                  </div>

                  {/* Name & Address */}
                  <div>
                    <h3 className="font-bold text-xs text-[#103D2C] group-hover:text-[#17643E] transition-colors line-clamp-1">
                      {shop.name}
                    </h3>
                    <p className="text-[11px] text-gray-500 line-clamp-1 mt-0.5 flex items-center gap-1">
                      <MapPin size={11} className="text-gray-400 shrink-0" />
                      <span>{shop.address}</span>
                    </p>
                  </div>

                  {/* Rental Accessories Badges */}
                  {shop.rental_accessories && shop.rental_accessories.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-0.5">
                      {shop.rental_accessories.slice(0, 3).map((equip: string, equipIdx: number) => (
                        <span
                          key={equipIdx}
                          className="text-[10px] bg-white text-gray-600 px-1.5 py-0.5 rounded border border-[#E5DDCF]"
                        >
                          {equip}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="pt-2 border-t border-[#E5DDCF]/50 flex items-center gap-2">
                  {shop.phone ? (
                    <a
                      href={`tel:${shop.phone}`}
                      className="flex-1 bg-white hover:bg-emerald-50 text-[#103D2C] hover:text-[#17643E] border border-[#E5DDCF] rounded-lg py-1.5 px-2 text-xs font-bold text-center flex items-center justify-center gap-1 transition-colors"
                    >
                      <Phone size={11} />
                      <span>Call</span>
                    </a>
                  ) : (
                    <span className="text-[10px] text-gray-400 italic flex-1 text-center py-1">
                      Walk-in
                    </span>
                  )}

                  {shop.maps_url && (
                    <a
                      href={shop.maps_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-[#103D2C] hover:bg-[#17643E] text-white rounded-lg py-1.5 px-2.5 text-xs font-bold flex items-center gap-1 transition-colors"
                      title="Open in Google Maps"
                    >
                      <span>Maps</span>
                      <ExternalLink size={11} />
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default GoogleNearbyShopsSection;
