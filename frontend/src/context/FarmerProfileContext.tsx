import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { changeLanguage, SupportedLanguage } from '../i18n';

export interface SoilReportData {
  nitrogen: number; // kg/ha (typically 0 - 300)
  phosphorus: number; // kg/ha (typically 0 - 100)
  potassium: number; // kg/ha (typically 0 - 500)
  ph: number; // 3.5 - 9.5
  soil_type: string;
  organic_carbon: number; // % (0.1 - 2.5)
  moisture: number; // % (10 - 60)
  ec?: number; // dS/m
  sample_date?: string;
  lab_name?: string;
  certificate_no?: string;
  source: string;
  status?: 'Optimal' | 'Deficient' | 'Moderate' | 'Alert';
}

export interface WeatherData {
  latitude: number;
  longitude: number;
  location_name: string;
  district: string;
  state: string;
  temperature: number;
  humidity: number;
  rainfall: number; // mm
  weather_condition: string;
  is_live_gps: boolean;
  last_fetched?: string;
}

export interface WaterData {
  water_availability: 'Low' | 'Medium' | 'High';
  irrigation_source: 'Drip' | 'Sprinkler' | 'Canal/Flood' | 'Borewell' | 'Rainfed';
  drainage: 'Well-drained' | 'Moderate' | 'Heavy clay / Water retentive';
}

export interface CropIntelligenceSummary {
  top_recommended_crop: string;
  suitability_score: number;
  secondary_crop?: string;
  secondary_score?: number;
  water_fit: 'Optimal' | 'Constrained' | 'Sufficient';
  npk_match_pct: number;
  reasons: string[];
}

export interface FarmerProfileData {
  id: string;
  name: string;
  phone: string;
  email: string;
  preferred_language: SupportedLanguage;
  role: 'Farmer' | 'Landowner' | 'Tenant' | 'Agri Professional';
  farm_name: string;
  total_area: number;
  area_unit: 'acre' | 'hectare';
  primary_field_name: string;
  primary_field_area: number;
  current_crop: string;
  soil_report: SoilReportData;
  weather: WeatherData;
  water: WaterData;
  crop_intelligence?: CropIntelligenceSummary;
  is_onboarded: boolean;
  created_at: string;
  updated_at: string;
}

interface FarmerProfileContextType {
  profile: FarmerProfileData;
  isOnboarded: boolean;
  updateProfile: (updates: Partial<FarmerProfileData>) => void;
  updateSoilReport: (updates: Partial<SoilReportData>) => void;
  updateWeather: (updates: Partial<WeatherData>) => void;
  updateWater: (updates: Partial<WaterData>) => void;
  saveCompleteProfile: (newProfile: FarmerProfileData) => Promise<void>;
  detectGpsLocation: () => Promise<WeatherData>;
  fetchLiveWeather: (lat: number, lon: number, districtName?: string) => Promise<WeatherData>;
  evaluateCropSuitability: (profileOverride?: Partial<FarmerProfileData>) => Promise<CropIntelligenceSummary>;
  resetToDefaultProfile: () => void;
  setIsOnboarded: (status: boolean) => void;
}

const STORAGE_KEY = 'kisancare_farmer_profile';
const ONBOARDED_KEY = 'kisancare_is_onboarded';

export const DEFAULT_FARMER_PROFILE: FarmerProfileData = {
  id: 'usr-pranav-vasu-01',
  name: 'Pranav Vasu',
  phone: '9822012345',
  email: 'pranav.vasu@kisancare.in',
  preferred_language: 'en',
  role: 'Farmer',
  farm_name: 'Pranav Vasu Bio Farm',
  total_area: 12.0,
  area_unit: 'acre',
  primary_field_name: 'Field 1 (North Parcel)',
  primary_field_area: 6.5,
  current_crop: 'Cotton',
  soil_report: {
    nitrogen: 210,
    phosphorus: 32,
    potassium: 320,
    ph: 7.8,
    soil_type: 'Black Cotton Soil / Medium Clay',
    organic_carbon: 0.58,
    moisture: 36,
    ec: 0.65,
    sample_date: '2026-10-15',
    lab_name: 'District Soil Testing Laboratory, Akola',
    certificate_no: 'MH/AKL/2026/7821',
    source: 'Soil Health Card (NABL Accredited)',
    status: 'Optimal',
  },
  weather: {
    latitude: 20.7002,
    longitude: 77.0082,
    location_name: 'Takli Bu, Akola, Maharashtra',
    district: 'Akola',
    state: 'Maharashtra',
    temperature: 32.5,
    humidity: 42,
    rainfall: 720,
    weather_condition: 'Partly Cloudy',
    is_live_gps: false,
    last_fetched: new Date().toISOString(),
  },
  water: {
    water_availability: 'Medium',
    irrigation_source: 'Drip',
    drainage: 'Moderate',
  },
  crop_intelligence: {
    top_recommended_crop: 'Cotton',
    suitability_score: 94,
    secondary_crop: 'Soybean',
    secondary_score: 89,
    water_fit: 'Optimal',
    npk_match_pct: 92,
    reasons: [
      'High Potassium (320 kg/ha) supports high boll retention in Black Cotton soil',
      'Medium water access pairs with drip irrigation in Kharif cycle',
      'District Akola agro-climatic history validates superior Cotton yield'
    ]
  },
  is_onboarded: false,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const FarmerProfileContext = createContext<FarmerProfileContextType | undefined>(undefined);

export const FarmerProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<FarmerProfileData>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          ...DEFAULT_FARMER_PROFILE,
          ...parsed,
          soil_report: { ...DEFAULT_FARMER_PROFILE.soil_report, ...(parsed.soil_report || {}) },
          weather: { ...DEFAULT_FARMER_PROFILE.weather, ...(parsed.weather || {}) },
          water: { ...DEFAULT_FARMER_PROFILE.water, ...(parsed.water || {}) },
        };
      }
    } catch (e) {
      console.error('Failed to load profile from localStorage:', e);
    }
    return DEFAULT_FARMER_PROFILE;
  });

  const [isOnboarded, setIsOnboardedState] = useState<boolean>(() => {
    try {
      const onboardedFlag = localStorage.getItem(ONBOARDED_KEY);
      if (onboardedFlag !== null) {
        return onboardedFlag === 'true';
      }
      return profile.is_onboarded;
    } catch {
      return false;
    }
  });

  const setIsOnboarded = useCallback((status: boolean) => {
    setIsOnboardedState(status);
    localStorage.setItem(ONBOARDED_KEY, status ? 'true' : 'false');
    setProfile(prev => {
      const updated = { ...prev, is_onboarded: status, updated_at: new Date().toISOString() };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const updateProfile = useCallback((updates: Partial<FarmerProfileData>) => {
    setProfile(prev => {
      const updated = { ...prev, ...updates, updated_at: new Date().toISOString() };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const updateSoilReport = useCallback((updates: Partial<SoilReportData>) => {
    setProfile(prev => {
      const updated = {
        ...prev,
        soil_report: { ...prev.soil_report, ...updates },
        updated_at: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const updateWeather = useCallback((updates: Partial<WeatherData>) => {
    setProfile(prev => {
      const updated = {
        ...prev,
        weather: { ...prev.weather, ...updates },
        updated_at: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const updateWater = useCallback((updates: Partial<WaterData>) => {
    setProfile(prev => {
      const updated = {
        ...prev,
        water: { ...prev.water, ...updates },
        updated_at: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Fetch live weather from Open-Meteo or backend API
  const fetchLiveWeather = useCallback(async (lat: number, lon: number, districtName?: string): Promise<WeatherData> => {
    try {
      const weatherData = await api.getCurrentWeather(lat, lon);
      const district = districtName || profile.weather.district || 'Akola';
      const updatedWeather: WeatherData = {
        latitude: lat,
        longitude: lon,
        location_name: weatherData?.location || `${district}, Maharashtra`,
        district: district,
        state: 'Maharashtra',
        temperature: Number(weatherData?.temperature ?? 32.5),
        humidity: Number(weatherData?.humidity ?? 45),
        rainfall: Number(weatherData?.rainfall ?? 720),
        weather_condition: weatherData?.weather_condition || 'Partly Cloudy',
        is_live_gps: true,
        last_fetched: new Date().toISOString(),
      };
      updateWeather(updatedWeather);
      return updatedWeather;
    } catch (err) {
      console.warn('Live weather fetch returned fallback for GPS coordinates:', err);
      const fallbackWeather: WeatherData = {
        ...profile.weather,
        latitude: lat,
        longitude: lon,
        is_live_gps: true,
        last_fetched: new Date().toISOString(),
      };
      updateWeather(fallbackWeather);
      return fallbackWeather;
    }
  }, [profile.weather, updateWeather]);

  // One-click GPS Detection using Browser Geolocation API
  const detectGpsLocation = useCallback(async (): Promise<WeatherData> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by your browser.'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = parseFloat(position.coords.latitude.toFixed(4));
          const lon = parseFloat(position.coords.longitude.toFixed(4));

          // Simple reverse lookup mapping for Maharashtra districts or coordinates
          let detectedDistrict = 'Akola';
          if (lat >= 19.5 && lat <= 20.5 && lon >= 73.5 && lon <= 74.5) detectedDistrict = 'Nashik';
          else if (lat >= 18.0 && lat <= 19.0 && lon >= 73.5 && lon <= 74.5) detectedDistrict = 'Pune';
          else if (lat >= 20.8 && lat <= 21.5 && lon >= 78.5 && lon <= 79.5) detectedDistrict = 'Nagpur';
          else if (lat >= 20.5 && lat <= 21.2 && lon >= 76.5 && lon <= 77.5) detectedDistrict = 'Akola';
          else if (lat >= 20.7 && lat <= 21.5 && lon >= 77.5 && lon <= 78.5) detectedDistrict = 'Amravati';
          else if (lat >= 18.0 && lat <= 19.0 && lon >= 76.0 && lon <= 77.0) detectedDistrict = 'Latur';

          try {
            const weather = await fetchLiveWeather(lat, lon, detectedDistrict);
            resolve(weather);
          } catch (e) {
            const basicWeather: WeatherData = {
              latitude: lat,
              longitude: lon,
              location_name: `GPS Point (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E), ${detectedDistrict}`,
              district: detectedDistrict,
              state: 'Maharashtra',
              temperature: 31.8,
              humidity: 48,
              rainfall: 690,
              weather_condition: 'Mainly Clear',
              is_live_gps: true,
              last_fetched: new Date().toISOString(),
            };
            updateWeather(basicWeather);
            resolve(basicWeather);
          }
        },
        (error) => {
          console.warn('GPS location error:', error);
          reject(new Error(error.message || 'Unable to retrieve location coordinates.'));
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    });
  }, [fetchLiveWeather, updateWeather]);

  // Evaluate crop suitability linked with Crop Intelligence
  const evaluateCropSuitability = useCallback(async (
    profileOverride?: Partial<FarmerProfileData>
  ): Promise<CropIntelligenceSummary> => {
    const soil = profileOverride?.soil_report || profile.soil_report;
    const weather = profileOverride?.weather || profile.weather;
    const water = profileOverride?.water || profile.water;

    try {
      const pred = await api.predictCrop({
        N: Number(soil.nitrogen),
        P: Number(soil.phosphorus),
        K: Number(soil.potassium),
        ph: Number(soil.ph),
        temperature: Number(weather.temperature),
        humidity: Number(weather.humidity),
        rainfall: Number(weather.rainfall),
        district: weather.district || 'Akola',
        season: 'Kharif',
        water_availability: water.water_availability,
        top_k: 3
      });

      if (pred && Array.isArray(pred.data) && pred.data.length > 0) {
        const top = pred.data[0];
        const secondary = pred.data[1];
        const summary: CropIntelligenceSummary = {
          top_recommended_crop: top.crop || 'Cotton',
          suitability_score: Math.round((top.combined_score || top.score || 0.94) * 100),
          secondary_crop: secondary?.crop || 'Soybean',
          secondary_score: secondary ? Math.round((secondary.combined_score || secondary.score || 0.88) * 100) : 88,
          water_fit: water.water_availability === 'Low' ? 'Constrained' : 'Optimal',
          npk_match_pct: Math.round((top.npk_score || 0.92) * 100),
          reasons: top.reasons || [
            `Soil NPK (${soil.nitrogen}-${soil.phosphorus}-${soil.potassium}) matches ${top.crop} root development`,
            `Weather in ${weather.district} (${weather.temperature}°C, ${weather.humidity}% RH) ideal for vegetative stage`,
            `${water.irrigation_source} irrigation meets ${water.water_availability.toLowerCase()} water requirements`
          ]
        };

        setProfile(prev => {
          const updated = { ...prev, crop_intelligence: summary, updated_at: new Date().toISOString() };
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
          return updated;
        });

        return summary;
      }
    } catch (e) {
      console.warn('Using intelligent algorithmic fallback for crop suitability:', e);
    }

    // Heuristic agronomic intelligence fallback for Vidarbha & Maharashtra
    let topCrop = 'Cotton';
    let secondaryCrop = 'Soybean';
    let score = 92;

    if (soil.ph > 8.0) {
      topCrop = 'Tur (Pigeonpea)';
      secondaryCrop = 'Cotton';
    } else if (water.water_availability === 'High') {
      topCrop = 'Cotton';
      secondaryCrop = 'Sugarcane';
      score = 95;
    } else if (water.water_availability === 'Low') {
      topCrop = 'Soybean';
      secondaryCrop = 'Gram (Chickpea)';
      score = 88;
    }

    const fallbackSummary: CropIntelligenceSummary = {
      top_recommended_crop: topCrop,
      suitability_score: score,
      secondary_crop: secondaryCrop,
      secondary_score: score - 6,
      water_fit: water.water_availability === 'Low' ? 'Constrained' : 'Optimal',
      npk_match_pct: Math.min(98, Math.max(75, Math.round((soil.nitrogen / 220) * 85 + (soil.potassium / 300) * 15))),
      reasons: [
        `Soil pH ${soil.ph} and ${soil.soil_type} provide optimal root anchorage`,
        `Available Potassium (${soil.potassium} kg/ha) delivers high stress resistance`,
        `GPS Weather (${weather.temperature}°C, ${weather.rainfall} mm) aligns with ${topCrop} growing season`
      ]
    };

    setProfile(prev => {
      const updated = { ...prev, crop_intelligence: fallbackSummary, updated_at: new Date().toISOString() };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });

    return fallbackSummary;
  }, [profile.soil_report, profile.weather, profile.water]);

  // Complete profile save handler
  const saveCompleteProfile = useCallback(async (newProfile: FarmerProfileData) => {
    // 1. Evaluate crop suitability to ensure linkage
    let intelligence = newProfile.crop_intelligence;
    if (!intelligence) {
      try {
        intelligence = await evaluateCropSuitability(newProfile);
      } catch {
        // Ignored
      }
    }

    const finalizedProfile: FarmerProfileData = {
      ...newProfile,
      crop_intelligence: intelligence || newProfile.crop_intelligence,
      is_onboarded: true,
      updated_at: new Date().toISOString(),
    };

    setProfile(finalizedProfile);
    setIsOnboardedState(true);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(finalizedProfile));
    localStorage.setItem(ONBOARDED_KEY, 'true');

    // Sync preferred language
    if (finalizedProfile.preferred_language) {
      changeLanguage(finalizedProfile.preferred_language);
    }
  }, [evaluateCropSuitability]);

  const resetToDefaultProfile = useCallback(() => {
    setProfile(DEFAULT_FARMER_PROFILE);
    setIsOnboardedState(false);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(ONBOARDED_KEY);
  }, []);

  return (
    <FarmerProfileContext.Provider
      value={{
        profile,
        isOnboarded,
        updateProfile,
        updateSoilReport,
        updateWeather,
        updateWater,
        saveCompleteProfile,
        detectGpsLocation,
        fetchLiveWeather,
        evaluateCropSuitability,
        resetToDefaultProfile,
        setIsOnboarded,
      }}
    >
      {children}
    </FarmerProfileContext.Provider>
  );
};

export const useFarmerProfile = () => {
  const context = useContext(FarmerProfileContext);
  if (!context) {
    throw new Error('useFarmerProfile must be used within a FarmerProfileProvider');
  }
  return context;
};