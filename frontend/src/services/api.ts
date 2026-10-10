export const DEMO_MODE = false;

// Shared API fetcher with error handling
async function fetchAPI(endpoint: string, options?: RequestInit) {
  try {
    const response = await fetch(endpoint, options);
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Fetch failed:', error);
    throw error;
  }
}

export const api = {
  // Digital Twin API
  getFarmDetails: async (farmId: string) => {
    if (!DEMO_MODE) {
      try {
        const data = await fetchAPI(`/api/v1/digital-twin/${farmId}`);
        return { ...data, isDemo: false };
      } catch (e) {
        console.warn('Falling back to demo data for farm details');
      }
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
  
  // Crop Recommendation API
  predictCrop: async (district: string, season: string, waterAvailability: string) => {
    if (!DEMO_MODE) {
      try {
        const data = await fetchAPI('/api/v1/crop-recommendation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            district,
            season,
            water_availability: waterAvailability,
            top_k: 3
          })
        });
        return { data: data.recommendations, isDemo: false };
      } catch (e) {
        console.warn('Falling back to demo data for crop recommendation');
      }
    }
    
    // Simulating ML Model Inference delay
    await new Promise(r => setTimeout(r, 1000));
    return {
      isDemo: true,
      data: [
        { crop: 'Soybean', score: 92, expected_yield: 2.8, predicted_profit: 42000, water_requirement: 'Medium', tags: ['High Profit', 'Suitable Soil'] },
        { crop: 'Cotton', score: 85, expected_yield: 1.2, predicted_profit: 38000, water_requirement: 'High', tags: ['Drought Tolerant'] },
        { crop: 'Pigeon Pea', score: 78, expected_yield: 0.8, predicted_profit: 28000, water_requirement: 'Low', tags: ['Low Maintenance'] }
      ]
    };
  },

  // Market Price API
  getMarketPrice: async (crop: string, market: string, date: string) => {
    if (!DEMO_MODE) {
      try {
        const data = await fetchAPI('/api/v1/market-price/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            crop,
            market,
            date,
            horizon_days: 7
          })
        });
        return { data, isDemo: false };
      } catch (e) {
        console.warn('Falling back to demo data for market price');
      }
    }

    return {
      isDemo: true,
      data: {
        current_price: 4650,
        trend: '+4.2%',
        forecast_min: 4700,
        forecast_max: 4800,
        nearby_markets: [
          { name: 'Nagpur APMC', distance: 24, price: 4680, arrivals: 450, trend: '+20' },
          { name: 'Amravati APMC', distance: 145, price: 4710, arrivals: 820, trend: '-10' }
        ]
      }
    };
  }
};
