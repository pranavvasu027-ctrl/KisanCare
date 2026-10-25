/**
 * KisanCare TanStack Query Client Configuration
 * Provides intelligent caching, background refetching, and offline persistence boundaries.
 */

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes fresh cache
      gcTime: 1000 * 60 * 15, // 15 minutes garbage collection (formerly cacheTime)
      retry: (failureCount, error) => {
        // Don't retry 404 or 401 errors
        if (typeof error === 'object' && error !== null && 'status' in error) {
          const status = (error as { status?: number }).status;
          if (status === 404 || status === 401) return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false, // Prevent jarring layout refetches on mobile
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 0,
    },
  },
});
