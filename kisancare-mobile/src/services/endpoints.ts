/**
 * KisanCare Central Backend API Endpoints Inventory
 * Corresponds to FastAPI routes in backend/app/main.py & backend/app/api/endpoints.py
 */

export const ENDPOINTS = {
  // Service Health & Status
  HEALTH: '/health',

  // Crop & Agronomic Intelligence
  CROP_RECOMMENDATION: '/api/v1/crop-recommendation',
  YIELD_PREDICTION: '/api/v1/yield-prediction',
  WEATHER_RISK: '/api/v1/weather-risk',
  IRRIGATION: '/api/v1/irrigation',
  DISEASE_DETECTION: '/api/v1/disease-detection',
  PEST_DETECTION: '/api/v1/pest-detection',

  // Soil & Fertilizer Advisory
  SOIL_ASSESSMENT: '/api/v1/soil-assessment',
  SOIL_BENCHMARKS: '/api/v1/soil/benchmarks',
  SOIL_REPORT_UPLOAD: '/api/v1/soil/reports/upload',
  FERTILIZER_ADVISORY: '/api/v1/fertilizer-advisory',

  // Weather Intelligence
  WEATHER_CURRENT: '/api/v1/weather/current',
  WEATHER_FORECAST: '/api/v1/weather/forecast',

  // Farm & Digital Twin
  FARMS: '/api/v1/farms',
  DIGITAL_TWIN: '/api/v1/digital-twin',
  DIGITAL_TWIN_SIMULATE: '/api/v1/digital-twin/simulate',
  DIGITAL_TWIN_WHAT_IF: '/api/v1/digital-twin/what-if',

  // Market Intelligence
  MARKET_PRICE: '/api/v1/market-price',

  // Equipment Rental Marketplace
  RENTALS_LISTINGS: '/api/v1/rentals/listings',
  RENTALS_GEOGRAPHY: '/api/v1/rentals/geography',
  RENTALS_CALCULATE_PRICE: '/api/v1/rentals/calculate-price',
  RENTALS_CHECK_AVAILABILITY: '/api/v1/rentals/check-availability',
  RENTALS_BOOKINGS: '/api/v1/rentals/bookings',

  // AI Decision Engine & Copilot
  COPILOT_STATUS: '/api/copilot/status',
  COPILOT_CHAT: '/api/v1/copilot/chat',
} as const;

export type EndpointKey = keyof typeof ENDPOINTS;
