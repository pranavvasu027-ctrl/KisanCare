/**
 * KisanCare Market Intelligence Service
 * Connects to live /api/v1/market-price endpoint.
 * Backed by trained XGBoost models (models/*.json) and Agmarknet mandi historical datasets.
 */

import { apiClient } from './apiClient';
import { ENDPOINTS } from './endpoints';

export interface MarketPriceRequest {
  crop: string;
  market: string;
  date: string; // YYYY-MM-DD
}

export interface MarketPriceResponse {
  status: string;
  model_type: string;
  crop: string;
  market: string;
  target_date: string;
  current_price: number;
  forecast_7d: number | string;
  forecast_14d?: number | string;
  trend: string;
  is_mock?: boolean;
  data_provenance?: string;
  message?: string;
  nearby_markets?: Array<{
    name: string;
    distance: number;
    price: number;
    trend: string;
  }>;
}

export interface SupportedCommodity {
  id: string;
  name: string;
  cropKey: string;
  marketKey: string;
  marketName: string;
  defaultDate: string;
  image: any;
  category: string;
}

export const SUPPORTED_MARKET_COMMODITIES: SupportedCommodity[] = [
  {
    id: 'onion_pune',
    name: 'Onion (कांदा)',
    cropKey: 'onion',
    marketKey: 'pune_pimpri',
    marketName: 'Pune (Pimpri) APMC',
    defaultDate: '2025-11-04',
    image: require('../../assets/images/ui/crop_cotton.png'),
    category: 'Vegetables',
  },
  {
    id: 'tomato_pune',
    name: 'Tomato (टोमॅटो)',
    cropKey: 'tomato',
    marketKey: 'pune_pimpri',
    marketName: 'Pune (Pimpri) APMC',
    defaultDate: '2025-11-04',
    image: require('../../assets/images/ui/crop_soybean.png'),
    category: 'Vegetables',
  },
  {
    id: 'potato_pune',
    name: 'Potato (बटाटा)',
    cropKey: 'potato',
    marketKey: 'pune_manjriapmc',
    marketName: 'Pune (Manjri) APMC',
    defaultDate: '2025-11-20',
    image: require('../../assets/images/ui/crop_maize.png'),
    category: 'Vegetables',
  },
  {
    id: 'cabbage_pune',
    name: 'Cabbage (कोबी)',
    cropKey: 'cabbage',
    marketKey: 'pune_manjri',
    marketName: 'Pune (Manjri) APMC',
    defaultDate: '2025-11-03',
    image: require('../../assets/images/ui/crop_soybean.png'),
    category: 'Vegetables',
  },
  {
    id: 'cauliflower_pune',
    name: 'Cauliflower (फ्लॉवर)',
    cropKey: 'cauliflower',
    marketKey: 'pune_manjriapmc',
    marketName: 'Pune (Manjri) APMC',
    defaultDate: '2025-11-20',
    image: require('../../assets/images/ui/crop_cotton.png'),
    category: 'Vegetables',
  },
];

export async function fetchMarketPrice(
  request: MarketPriceRequest
): Promise<MarketPriceResponse> {
  return apiClient.post<MarketPriceResponse>(
    ENDPOINTS.MARKET_PRICE,
    {
      crop: request.crop.trim(),
      market: request.market.trim(),
      date: request.date.trim(),
    },
    { timeoutMs: 12_000 }
  );
}
