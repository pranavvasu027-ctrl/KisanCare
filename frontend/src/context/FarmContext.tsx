import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export interface FarmSummary {
  id: string;
  farm_name: string;
  location: string;
  latitude?: number | null;
  longitude?: number | null;
  total_area: number;
  area_unit: string;
  status?: string;
  has_precise_coordinates?: boolean;
}

interface FarmContextType {
  farms: FarmSummary[];
  activeFarmId: string | null;
  activeFarm: FarmSummary | null;
  loading: boolean;
  error: string | null;
  setActiveFarmId: (farmId: string) => void;
  refreshFarms: (preferredFarmId?: string) => Promise<FarmSummary[]>;
}

const FarmContext = createContext<FarmContextType>({
  farms: [],
  activeFarmId: null,
  activeFarm: null,
  loading: true,
  error: null,
  setActiveFarmId: () => {},
  refreshFarms: async () => [],
});

const ACTIVE_FARM_STORAGE_KEY = 'kisancare_active_farm_id';

export const FarmProvider = ({ children }: { children: React.ReactNode }) => {
  const { user, isAuthenticated, isDemoMode, loading: authLoading } = useAuth();
  const [farms, setFarms] = useState<FarmSummary[]>([]);
  const [activeFarmId, setActiveFarmIdState] = useState<string | null>(() => {
    return localStorage.getItem(ACTIVE_FARM_STORAGE_KEY);
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const setActiveFarmId = useCallback((farmId: string) => {
    setActiveFarmIdState(farmId);
    if (farmId) {
      localStorage.setItem(ACTIVE_FARM_STORAGE_KEY, farmId);
    } else {
      localStorage.removeItem(ACTIVE_FARM_STORAGE_KEY);
    }
  }, []);

  const refreshFarms = useCallback(async (preferredFarmId?: string): Promise<FarmSummary[]> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getFarms();
      const list: FarmSummary[] = res?.farms || [];
      setFarms(list);

      if (list.length > 0) {
        // Selection priority:
        // 1. Explicitly preferred ID if valid
        // 2. Currently selected activeFarmId if valid
        // 3. Stored localStorage ID if valid
        // 4. First farm in list
        const storedId = localStorage.getItem(ACTIVE_FARM_STORAGE_KEY);
        const candidateId = preferredFarmId || activeFarmId || storedId;
        const matchingFarm = list.find(f => f.id === candidateId);

        if (matchingFarm) {
          setActiveFarmId(matchingFarm.id);
        } else {
          setActiveFarmId(list[0].id);
        }
      } else {
        setActiveFarmId('');
      }
      return list;
    } catch (err: any) {
      console.error('Failed to load user farms in FarmProvider:', err);
      setError(err.message || 'Failed to fetch farms');
      return [];
    } finally {
      setLoading(false);
    }
  }, [activeFarmId, setActiveFarmId]);

  // Reload farms whenever authentication state completes or user changes
  useEffect(() => {
    if (!authLoading) {
      refreshFarms();
    }
  }, [authLoading, user?.id, isAuthenticated, isDemoMode]);

  const activeFarm = farms.find(f => f.id === activeFarmId) || null;

  return (
    <FarmContext.Provider
      value={{
        farms,
        activeFarmId,
        activeFarm,
        loading,
        error,
        setActiveFarmId,
        refreshFarms,
      }}
    >
      {children}
    </FarmContext.Provider>
  );
};

export const useFarm = () => useContext(FarmContext);
