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

  // 3. Market Price Forecasting API (XGBoost ML Model & Demo Dataset)
  getMarketPrice: async (
    crop: string = 'Cotton',
    market: string = 'Akola',
    date?: string,
    timeRange: '7D' | '14D' | '30D' = '7D'
  ) => {
    // Standardize crop and market names to supported Vidarbha set
    const normalizedCrop = crop.toLowerCase() === 'soyabean' || crop.toLowerCase() === 'soybean'
      ? 'Soyabean'
      : crop.toLowerCase() === 'tur' || crop.toLowerCase() === 'pigeon pea'
      ? 'Tur'
      : 'Cotton';

    const normalizedMarket = market.toLowerCase().includes('amravati')
      ? 'Amravati'
      : market.toLowerCase().includes('akot')
      ? 'Akot'
      : 'Akola';

    if (!DEMO_MODE) {
      try {
        const data = await fetchAPI('/api/v1/market-price', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            crop: normalizedCrop,
            market: normalizedMarket,
            date: date || new Date().toISOString().split('T')[0]
          })
        });
        return { data, isDemo: false };
      } catch (err) {
        console.warn('Backend market price API failed or unavailable, falling back to demonstration dataset:', err);
      }
    }

    // High-fidelity Vidarbha Agricultural Demonstration Dataset (Cotton, Soyabean, Tur)
    const baseProfiles: Record<string, {
      msp: number;
      variety: Record<string, string>;
      markets: Record<string, {
        currentPrice: number;
        previousPrice: number;
        weeklyHigh: number;
        weeklyLow: number;
        distance: string;
        distanceKm: number;
        location: string;
        trend: 'Rising' | 'Falling' | 'Stable';
        changePct: number;
      }>;
      forecast7d: { expected: number; min: number; max: number; trend: 'Upward' | 'Downward' | 'Stable' };
      forecast14d: { expected: number; min: number; max: number; trend: 'Upward' | 'Downward' | 'Stable' };
    }> = {
      Cotton: {
        msp: 7121,
        variety: {
          Akola: 'Medium Staple',
          Amravati: 'Desi Medium',
          Akot: 'Shankar-6 Premium'
        },
        markets: {
          Akot: {
            currentPrice: 7350,
            previousPrice: 7180,
            weeklyHigh: 7410,
            weeklyLow: 7140,
            distance: '45 km',
            distanceKm: 45,
            location: 'Akot APMC, Akola District',
            trend: 'Rising',
            changePct: 2.37
          },
          Akola: {
            currentPrice: 7280,
            previousPrice: 7150,
            weeklyHigh: 7320,
            weeklyLow: 7110,
            distance: '0 km (Local)',
            distanceKm: 0,
            location: 'Akola APMC Yard',
            trend: 'Rising',
            changePct: 1.82
          },
          Amravati: {
            currentPrice: 7190,
            previousPrice: 7230,
            weeklyHigh: 7250,
            weeklyLow: 7120,
            distance: '95 km',
            distanceKm: 95,
            location: 'Amravati Main Mandi',
            trend: 'Stable',
            changePct: -0.55
          }
        },
        forecast7d: { expected: 7390, min: 7320, max: 7460, trend: 'Upward' },
        forecast14d: { expected: 7450, min: 7350, max: 7550, trend: 'Upward' }
      },
      Soyabean: {
        msp: 4892,
        variety: {
          Akola: 'Yellow JS-9305',
          Amravati: 'Yellow Standard',
          Akot: 'Yellow JS-335 Clean'
        },
        markets: {
          Akot: {
            currentPrice: 4670,
            previousPrice: 4590,
            weeklyHigh: 4710,
            weeklyLow: 4560,
            distance: '45 km',
            distanceKm: 45,
            location: 'Akot APMC, Akola District',
            trend: 'Rising',
            changePct: 1.74
          },
          Akola: {
            currentPrice: 4640,
            previousPrice: 4550,
            weeklyHigh: 4680,
            weeklyLow: 4520,
            distance: '0 km (Local)',
            distanceKm: 0,
            location: 'Akola APMC Yard',
            trend: 'Rising',
            changePct: 1.98
          },
          Amravati: {
            currentPrice: 4580,
            previousPrice: 4610,
            weeklyHigh: 4630,
            weeklyLow: 4540,
            distance: '95 km',
            distanceKm: 95,
            location: 'Amravati Main Mandi',
            trend: 'Stable',
            changePct: -0.65
          }
        },
        forecast7d: { expected: 4710, min: 4660, max: 4750, trend: 'Upward' },
        forecast14d: { expected: 4750, min: 4680, max: 4820, trend: 'Upward' }
      },
      Tur: {
        msp: 7550,
        variety: {
          Akola: 'Red (Maruti)',
          Amravati: 'White Local',
          Akot: 'White / Gajar Red'
        },
        markets: {
          Akot: {
            currentPrice: 9940,
            previousPrice: 9760,
            weeklyHigh: 10020,
            weeklyLow: 9720,
            distance: '45 km',
            distanceKm: 45,
            location: 'Akot APMC, Akola District',
            trend: 'Rising',
            changePct: 1.84
          },
          Akola: {
            currentPrice: 9850,
            previousPrice: 9700,
            weeklyHigh: 9920,
            weeklyLow: 9650,
            distance: '0 km (Local)',
            distanceKm: 0,
            location: 'Akola APMC Yard',
            trend: 'Rising',
            changePct: 1.55
          },
          Amravati: {
            currentPrice: 9720,
            previousPrice: 9750,
            weeklyHigh: 9800,
            weeklyLow: 9620,
            distance: '95 km',
            distanceKm: 95,
            location: 'Amravati Main Mandi',
            trend: 'Stable',
            changePct: -0.31
          }
        },
        forecast7d: { expected: 10010, min: 9900, max: 10120, trend: 'Upward' },
        forecast14d: { expected: 10110, min: 9950, max: 10280, trend: 'Upward' }
      }
    };

    const cropProfile = baseProfiles[normalizedCrop] || baseProfiles.Cotton;
    const marketInfo = cropProfile.markets[normalizedMarket] || cropProfile.markets.Akola;

    // Find regional best market
    let bestMktName = 'Akot';
    let highestPrice = 0;
    Object.entries(cropProfile.markets).forEach(([mName, mData]) => {
      if (mData.currentPrice > highestPrice) {
        highestPrice = mData.currentPrice;
        bestMktName = mName;
      }
    });

    const priceDiff = highestPrice - marketInfo.currentPrice;

    // Build 30-day realistic historical price trend + 14-day projection
    // Anchor date: 2026-10-23
    const anchorDate = new Date(2026, 9, 23); // Month is 0-indexed (9 = Oct)
    const chartPoints: Array<{
      date: string;
      label: string;
      historicalPrice?: number;
      forecastPrice?: number;
      forecastMin?: number;
      forecastMax?: number;
      isForecast: boolean;
    }> = [];

    // Historical 30 days
    const histDays = 30;
    const baseP = marketInfo.currentPrice;

    // Seed-like deterministic variation so curves look smooth and realistic
    for (let i = histDays - 1; i >= 0; i--) {
      const d = new Date(anchorDate);
      d.setDate(anchorDate.getDate() - i);
      const dayStr = d.toISOString().split('T')[0];
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const label = `${d.getDate()} ${monthNames[d.getMonth()]}`;

      // Gradual drift towards current price with authentic mandi variance (no extreme leaps)
      const dayFactor = (histDays - 1 - i) / (histDays - 1);
      const wave = Math.sin(i * 0.45) * (baseP * 0.012);
      const priceVal = Math.round((marketInfo.previousPrice * (1 - dayFactor) + baseP * dayFactor) + wave);

      chartPoints.push({
        date: dayStr,
        label,
        historicalPrice: i === 0 ? baseP : priceVal,
        isForecast: false
      });
    }

    // Connect transition point on anchor date
    const lastHist = chartPoints[chartPoints.length - 1];
    lastHist.forecastPrice = baseP;
    lastHist.forecastMin = baseP;
    lastHist.forecastMax = baseP;

    // Future 14 days forecast
    const forecastProfile = timeRange === '14D' || timeRange === '30D' ? cropProfile.forecast14d : cropProfile.forecast7d;
    const forecastDays = 14;
    const targetForecast = forecastProfile.expected;

    for (let f = 1; f <= forecastDays; f++) {
      const fd = new Date(anchorDate);
      fd.setDate(anchorDate.getDate() + f);
      const dayStr = fd.toISOString().split('T')[0];
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const label = `${fd.getDate()} ${monthNames[fd.getMonth()]}`;

      const fRatio = f / 7;
      const expectedAtDay = Math.round(baseP + (targetForecast - baseP) * Math.min(1.2, fRatio));
      const spread = Math.round(baseP * 0.008 * f);

      chartPoints.push({
        date: dayStr,
        label,
        forecastPrice: expectedAtDay,
        forecastMin: expectedAtDay - spread,
        forecastMax: expectedAtDay + spread,
        isForecast: true
      });
    }

    // Build nearby comparison list for Akola, Amravati, Akot
    const nearbyList = Object.entries(cropProfile.markets).map(([mName, mData]) => {
      return {
        id: mName.toLowerCase(),
        name: `${mName} APMC`,
        marketKey: mName,
        location: mData.location,
        distance: mData.distance,
        distanceKm: mData.distanceKm,
        currentPrice: mData.currentPrice,
        previousPrice: mData.previousPrice,
        priceChangePct: mData.changePct,
        trend: mData.trend,
        dataStatus: 'SAMPLE DATA',
        variety: cropProfile.variety[mName] || 'Standard Modal',
        weeklyHigh: mData.weeklyHigh,
        weeklyLow: mData.weeklyLow,
        tradingHours: '08:30 AM – 04:30 PM (Mon-Sat)'
      };
    });

    // Rule-based recommendation logic
    let actionRecommendation = '';
    if (normalizedMarket === bestMktName) {
      actionRecommendation = `${bestMktName} APMC currently offers the peak price of ₹${highestPrice.toLocaleString('en-IN')}/qtl for ${normalizedCrop}. With prices showing positive momentum, this represents a strong selling window over the next 3 to 7 days.`;
    } else {
      actionRecommendation = `${bestMktName} APMC offers a ₹${priceDiff}/qtl premium over ${normalizedMarket}. If your farm's transport differential to ${bestMktName} is under ₹${Math.round(priceDiff * 0.45)}/qtl, diverting harvest lots to ${bestMktName} can increase net returns.`;
    }

    return {
      isDemo: true,
      data: {
        crop: normalizedCrop,
        market: normalizedMarket,
        timeRange,
        current_price: marketInfo.currentPrice,
        previous_price: marketInfo.previousPrice,
        price_change_pct: marketInfo.changePct,
        trend: marketInfo.trend,
        msp_benchmark: cropProfile.msp,
        modal_variety: cropProfile.variety[normalizedMarket] || 'Commercial Grade',
        best_market: {
          name: `${bestMktName} APMC`,
          marketKey: bestMktName,
          price: highestPrice,
          difference: priceDiff,
          location: cropProfile.markets[bestMktName]?.location || `${bestMktName}, Maharashtra`
        },
        forecast: {
          expected_price: forecastProfile.expected,
          min_price: forecastProfile.min,
          max_price: forecastProfile.max,
          trend: forecastProfile.trend,
          horizon_days: timeRange === '14D' ? 14 : 7,
          confidence: 'Medium (Sample Model)'
        },
        chart_data: chartPoints,
        nearby_markets: nearbyList,
        rule_based_insight: {
          best_market_name: `${bestMktName} APMC`,
          best_price: highestPrice,
          price_signal: marketInfo.trend,
          recommended_action: actionRecommendation,
          reasoning: `Calculated from relative modal price spreads across ${Object.keys(cropProfile.markets).join(', ')} mandis.`,
          disclaimer: 'Based on available demonstration market prices & trend rules — not a black-box ML recommendation.'
        },
        last_updated: '23 Oct 2026, 05:30 PM IST',
        data_provenance: 'Demonstration dataset — not live mandi prices'
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
  },

  // 11. Post-Harvest Loss Intelligence API & Local Storage Engine
  // Strictly restricted to Cotton and Soyabean only
  getPostHarvestRecords: async (cropFilter?: 'Cotton' | 'Soyabean' | 'ALL'): Promise<{ data: LossRecord[]; isDemo: boolean }> => {
    try {
      const stored = localStorage.getItem('kisancare_post_harvest_records_v1');
      let records: LossRecord[];
      let isDemo = false;

      if (stored) {
        records = JSON.parse(stored);
        // Ensure non-Cotton/Soyabean crops are purged
        records = records.filter(r => r.crop === 'Cotton' || r.crop === 'Soyabean');
      } else {
        records = DEFAULT_POST_HARVEST_RECORDS;
        isDemo = true;
        localStorage.setItem('kisancare_post_harvest_records_v1', JSON.stringify(records));
      }

      if (cropFilter && cropFilter !== 'ALL') {
        records = records.filter(r => r.crop === cropFilter);
      }

      return { data: records, isDemo };
    } catch (e) {
      console.error('Failed to load post-harvest loss records from storage:', e);
      return { data: DEFAULT_POST_HARVEST_RECORDS, isDemo: true };
    }
  },

  savePostHarvestRecord: async (record: Omit<LossRecord, 'id' | 'lossPercentage' | 'financialLossRs' | 'recordedAt'>): Promise<{ data: LossRecord; isDemo: boolean }> => {
    const baselinePrice = record.crop === 'Cotton' ? 7280 : 4640;
    const lossPercentage = record.stageQuantityQtl > 0
      ? Math.round((record.observedLossQtl / record.stageQuantityQtl) * 10000) / 100
      : 0;
    const financialLossRs = Math.round(record.observedLossQtl * baselinePrice);

    const newRecord: LossRecord = {
      ...record,
      id: `phl-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      lossPercentage,
      financialLossRs,
      recordedAt: new Date().toISOString()
    };

    try {
      const stored = localStorage.getItem('kisancare_post_harvest_records_v1');
      const existing: LossRecord[] = stored ? JSON.parse(stored) : DEFAULT_POST_HARVEST_RECORDS;
      const updated = [newRecord, ...existing.filter(r => r.crop === 'Cotton' || r.crop === 'Soyabean')];
      localStorage.setItem('kisancare_post_harvest_records_v1', JSON.stringify(updated));
      return { data: newRecord, isDemo: false };
    } catch (e) {
      console.error('Failed to save post-harvest record:', e);
      return { data: newRecord, isDemo: false };
    }
  },

  deletePostHarvestRecord: async (id: string): Promise<boolean> => {
    try {
      const stored = localStorage.getItem('kisancare_post_harvest_records_v1');
      if (stored) {
        const existing: LossRecord[] = JSON.parse(stored);
        const filtered = existing.filter(r => r.id !== id && (r.crop === 'Cotton' || r.crop === 'Soyabean'));
        localStorage.setItem('kisancare_post_harvest_records_v1', JSON.stringify(filtered));
        return true;
      }
      return false;
    } catch (e) {
      console.error('Failed to delete post-harvest record:', e);
      return false;
    }
  },

  resetPostHarvestSampleData: async (): Promise<LossRecord[]> => {
    localStorage.setItem('kisancare_post_harvest_records_v1', JSON.stringify(DEFAULT_POST_HARVEST_RECORDS));
    return DEFAULT_POST_HARVEST_RECORDS;
  }
};

export type PostHarvestCrop = 'Cotton' | 'Soyabean';
export type PostHarvestStage = 'Harvest' | 'Handling' | 'Storage' | 'Transport' | 'Market';

export interface LossRecord {
  id: string;
  batchId: string;
  crop: PostHarvestCrop;
  harvestDate: string;
  stage: PostHarvestStage;
  stageQuantityQtl: number;
  observedLossQtl: number;
  lossPercentage: number;
  cause: string;
  facilityOrMethod: string;
  recoverableQuantityQtl: number;
  financialLossRs: number;
  notes?: string;
  recordedAt: string;
}

const DEFAULT_POST_HARVEST_RECORDS: LossRecord[] = [
  {
    id: 'phl-rec-001',
    batchId: 'BATCH-CT-2026-01',
    crop: 'Cotton',
    harvestDate: '2026-10-12',
    stage: 'Harvest',
    stageQuantityQtl: 120,
    observedLossQtl: 3.8,
    lossPercentage: 3.17,
    cause: 'Boll rot & trash contamination during manual picking',
    facilityOrMethod: 'Manual Picking / Cloth Bags',
    recoverableQuantityQtl: 1.2,
    financialLossRs: 27664,
    notes: 'Unseasonal morning dew increased boll moisture. Drying required before ginning.',
    recordedAt: '2026-10-12T10:30:00Z'
  },
  {
    id: 'phl-rec-002',
    batchId: 'BATCH-SB-2026-02',
    crop: 'Soyabean',
    harvestDate: '2026-10-14',
    stage: 'Handling',
    stageQuantityQtl: 140,
    observedLossQtl: 4.5,
    lossPercentage: 3.21,
    cause: 'Mechanical threshing & seed coat cracking',
    facilityOrMethod: 'Mechanical Thresher',
    recoverableQuantityQtl: 1.8,
    financialLossRs: 20880,
    notes: 'Drum speed slightly elevated; fine-tuned thresher rotor rpm to prevent further cracking.',
    recordedAt: '2026-10-14T15:20:00Z'
  },
  {
    id: 'phl-rec-003',
    batchId: 'BATCH-CT-2026-03',
    crop: 'Cotton',
    harvestDate: '2026-10-16',
    stage: 'Storage',
    stageQuantityQtl: 116.2,
    observedLossQtl: 4.2,
    lossPercentage: 3.61,
    cause: 'High ambient humidity & cottonseed heating',
    facilityOrMethod: 'Covered On-Farm Shed',
    recoverableQuantityQtl: 1.5,
    financialLossRs: 30576,
    notes: 'Stack aerated with floor pallets; relative humidity reached 78% after unseasonal drizzle.',
    recordedAt: '2026-10-17T11:00:00Z'
  },
  {
    id: 'phl-rec-004',
    batchId: 'BATCH-SB-2026-04',
    crop: 'Soyabean',
    harvestDate: '2026-10-18',
    stage: 'Storage',
    stageQuantityQtl: 135.5,
    observedLossQtl: 6.2,
    lossPercentage: 4.58,
    cause: 'Pulse beetle & moisture hotspot development',
    facilityOrMethod: 'Traditional Gunny Bags',
    recoverableQuantityQtl: 2.2,
    financialLossRs: 28768,
    notes: 'Discovered weevil larvae in two lower corner bags. Segregated and shifted to hermetic liner.',
    recordedAt: '2026-10-19T09:45:00Z'
  },
  {
    id: 'phl-rec-005',
    batchId: 'BATCH-CT-2026-05',
    crop: 'Cotton',
    harvestDate: '2026-10-20',
    stage: 'Transport',
    stageQuantityQtl: 112,
    observedLossQtl: 1.4,
    lossPercentage: 1.25,
    cause: 'Tractor trolley side spillage on transit to Akot Mandi',
    facilityOrMethod: 'Open Tractor Trolley with Tarpaulin',
    recoverableQuantityQtl: 0.6,
    financialLossRs: 10192,
    notes: 'Tarpaulin corner loosened during transit; retrieved and re-baled along roadside checkpoint.',
    recordedAt: '2026-10-20T17:15:00Z'
  },
  {
    id: 'phl-rec-006',
    batchId: 'BATCH-SB-2026-06',
    crop: 'Soyabean',
    harvestDate: '2026-10-21',
    stage: 'Transport',
    stageQuantityQtl: 129.3,
    observedLossQtl: 2.1,
    lossPercentage: 1.62,
    cause: 'Bag puncture and moisture seepage during transit',
    facilityOrMethod: 'Light Commercial Vehicle (Pickup)',
    recoverableQuantityQtl: 0.9,
    financialLossRs: 9744,
    notes: 'Bed was wet from morning wash; recommended plastic floor lining for future hauls.',
    recordedAt: '2026-10-21T18:00:00Z'
  }
];
