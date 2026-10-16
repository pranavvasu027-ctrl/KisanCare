import { IS_DEMO_MODE } from '../config/demo';

// In demo mode, no application API request is sent. Returned values are local,
// sample data and each response is marked with isDemo for the UI.
export const DEMO_MODE = IS_DEMO_MODE;

// Shared API fetcher with robust error handling
async function fetchAPI(endpoint: string, options?: RequestInit) {
  try {
    const response = await fetch(endpoint, options);
    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorJson = await response.json();
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (errorJson.detail?.message) {
          errorDetail = errorJson.detail.message;
        } else if (errorJson.message) {
          errorDetail = errorJson.message;
        }
      } catch {
        // Response wasn't JSON
      }
      throw new Error(`API Error (${response.status}): ${errorDetail}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Fetch failed for ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // 1. Digital Twin API
  getFarmDetails: async (farmId: string) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI(`/api/v1/digital-twin/${farmId}`);
      return { ...data, isDemo: false };
    }
    
    return {
      farm_id: farmId,
      name: "Patil Farm",
      area_acres: 12,
      healthScore: 78,
      climate: { temperature: 28, weather_condition: "Partly Cloudy", humidity: 62 },
      isDemo: true
    };
  },
  
  // 2. Crop Recommendation API (ML Model)
  predictCrop: async (district: string, season: string, waterAvailability: string, topK: number = 3) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/crop-recommendation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          district,
          season,
          water_availability: waterAvailability,
          top_k: topK
        })
      });
      return { data: data.recommendations, raw: data, isDemo: false };
    }
    
    // Simulating ML Model Inference delay in demo mode
    await new Promise(r => setTimeout(r, 600));
    return {
      isDemo: true,
      data: [
        { crop: 'Soybean', predicted_area_frequency: 0.4215, rank: 1, water_requirement: 'Medium' },
        { crop: 'Cotton', predicted_area_frequency: 0.2840, rank: 2, water_requirement: 'High' },
        { crop: 'Pigeon Pea', predicted_area_frequency: 0.1532, rank: 3, water_requirement: 'Low' }
      ],
      raw: {
        model_version: 'crop-recommendation-mvp-v2',
        district,
        season,
        water_availability: waterAvailability,
        status: 'SUCCESS',
        recommendations: [
          { crop: 'Soybean', predicted_area_frequency: 0.4215, rank: 1 },
          { crop: 'Cotton', predicted_area_frequency: 0.2840, rank: 2 },
          { crop: 'Pigeon Pea', predicted_area_frequency: 0.1532, rank: 3 }
        ],
        filtered_candidates: [
          { crop: 'Sugarcane', model_score: 0.082, eligible: false, filter_reason: `Requires High/Perennial water availability; field has ${waterAvailability}` },
          { crop: 'Wheat', model_score: 0.312, eligible: false, filter_reason: `Rabi crop; not suitable for ${season} season sowing` }
        ],
        data_source: 'APY_2005_2015',
        score_interpretation: 'Predicted historical area-allocation suitability score',
        latency_ms: 38.5
      }
    };
  },

  // 3. Market Price Forecasting API (XGBoost ML Model)
  getMarketPrice: async (crop: string, market: string, date: string) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/market-price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop,
          market,
          date
        })
      });
      return { data, isDemo: false };
    }

    return {
      isDemo: true,
      data: {
        crop,
        market,
        current_price: 4650,
        trend: '+4.2%',
        forecast_min: 4700,
        forecast_max: 4800,
        forecast_7d: 4750,
        nearby_markets: [
          { name: 'Nagpur APMC', distance: 24, price: 4680, arrivals: 450, trend: '+20' },
          { name: 'Amravati APMC', distance: 145, price: 4710, arrivals: 820, trend: '-10' }
        ]
      }
    };
  },

  // 4. Disease Detection API (Rule-based Expert System)
  detectDisease: async (crop: string, symptoms: string[]) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/disease-detection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ crop, symptoms })
      });
      return { data, isDemo: false };
    }

    await new Promise(r => setTimeout(r, 600));
    return {
      isDemo: true,
      data: {
        model_type: 'rule_based_sample',
        prediction: 'Soybean Rust',
        confidence: 0.94,
        treatment: 'Apply triazole or strobilurin-based fungicide (e.g., Tebuconazole 25.9% EC @ 1ml/L). Ensure adequate plant spacing.'
      }
    };
  },

  // 5. Pest Detection API (Rule-based Expert System)
  detectPest: async (crop: string, symptoms: string[]) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/pest-detection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ crop, symptoms })
      });
      return { data, isDemo: false };
    }

    await new Promise(r => setTimeout(r, 600));
    return {
      isDemo: true,
      data: {
        model_type: 'rule_based_sample',
        prediction: 'Aphids',
        confidence: 0.85,
        treatment: 'Introduce ladybugs or apply insecticidal soap / neem oil.'
      }
    };
  },

  // 6. Soil Assessment API
  assessSoil: async (n: number, p: number, k: number, ph: number) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/soil-assessment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n, p, k, ph })
      });
      return { data, isDemo: false };
    }

    return {
      isDemo: true,
      data: {
        model_type: 'rule_based_sample',
        overall_status: 'Deficient/Imbalanced',
        issues: ['Low Nitrogen'],
        recommendation: 'Add NPK fertilizer balancing the deficiencies.'
      }
    };
  },

  // 7. Yield Prediction API
  predictYield: async (crop: string, areaAcres: number, soilHealthScore: number, weatherScore: number) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/yield-prediction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop,
          area_acres: areaAcres,
          soil_health_score: soilHealthScore,
          weather_score: weatherScore
        })
      });
      return { data, isDemo: false };
    }

    return {
      isDemo: true,
      data: {
        model_type: 'rule_based_sample',
        status: 'success',
        crop,
        predicted_yield_tons: 2.8,
        factors: {
          soil_impact: 'Positive',
          weather_impact: 'Positive'
        }
      }
    };
  },

  // 8. Irrigation Advisory API
  recommendIrrigation: async (crop: string, soilMoisture: number, daysSinceRain: number) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/irrigation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop,
          soil_moisture: soilMoisture,
          days_since_rain: daysSinceRain
        })
      });
      return { data, isDemo: false };
    }

    return {
      isDemo: true,
      data: {
        model_type: 'rule_based_sample',
        irrigation_required: soilMoisture < 30 || (daysSinceRain > 7 && soilMoisture < 50),
        recommended_amount_liters_per_acre: 2000,
        reasoning: `Soil moisture is at ${soilMoisture}% and it hasn't rained for ${daysSinceRain} days.`
      }
    };
  },

  // 9. Weather Risk Assessment API
  assessWeatherRisk: async (temperature: number, humidity: number, rainfallForecast: number) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/weather-risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          temperature,
          humidity,
          rainfall_forecast: rainfallForecast
        })
      });
      return { data, isDemo: false };
    }

    return {
      isDemo: true,
      data: {
        model_type: 'rule_based_sample',
        overall_risk: 'Medium',
        identified_risks: ['High Temperature / Heat Stress Warning'],
        mitigation: 'Ensure adequate irrigation to prevent heat stress.'
      }
    };
  },

  // 10. Economics Engine API
  calculateEconomics: async (payload: {
    expected_yield?: number;
    expected_price?: number;
    input_cost?: number;
    labour_cost?: number;
    irrigation_cost?: number;
  }) => {
    if (!DEMO_MODE) {
      const data = await fetchAPI('/api/v1/economics/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return { data, isDemo: false };
    }

    const expected_yield = payload.expected_yield ?? 24;
    const expected_price = payload.expected_price ?? 2500;
    const input_cost = payload.input_cost ?? 10000;
    const labour_cost = payload.labour_cost ?? 15000;
    const irrigation_cost = payload.irrigation_cost ?? 5000;
    const total_cost = input_cost + labour_cost + irrigation_cost;
    const expected_revenue = expected_yield * expected_price;
    const expected_profit = expected_revenue - total_cost;
    const roi = total_cost > 0 ? (expected_profit / total_cost) * 100 : 0;

    return {
      isDemo: true,
      data: {
        total_cost,
        expected_revenue,
        expected_profit,
        roi_percent: Math.round(roi * 100) / 100,
        break_even_price: expected_yield > 0 ? total_cost / expected_yield : 0
      }
    };
  }
};
