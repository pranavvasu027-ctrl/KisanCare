/**
 * KisanCare Mobile API Configuration
 * Manages base URLs and timeout settings across platforms without hardcoding.
 */

import { Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Device from 'expo-device';

/**
 * Extracts host machine LAN IP from any available Expo manifest / runtime property.
 * When Expo Go loads from Metro over Wi-Fi, the debugger host or linking URI
 * contains the exact IP of the development host.
 */
function resolveHostIp(): string | null {
  const candidates: (string | undefined | null)[] = [
    // Expo Go debugger host (e.g. "192.168.137.165:8081")
    (Constants as any).expoGoConfig?.debuggerHost,
    (Constants as any).manifest?.debuggerHost,
    (Constants as any).manifest2?.extra?.expoGo?.debuggerHost,
    (Constants as any).manifest2?.extra?.expoClient?.hostUri,
    Constants.expoConfig?.hostUri,
    Constants.linkingUri,
    (Constants as any).experienceUrl,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim().length > 0) {
      // Check for URL format: exp://192.168.1.100:8081 or http://192.168.1.100:8081
      const urlMatch = candidate.match(/:\/\/(.*?)(:\d+)?(\/|$)/);
      if (urlMatch && urlMatch[1]) {
        const ip = urlMatch[1].split(':')[0];
        if (ip && ip !== 'localhost' && ip !== '127.0.0.1' && !ip.includes('/')) {
          return ip;
        }
      }
      // Check for host:port format: 192.168.1.100:8081
      const ip = candidate.split(':')[0];
      if (ip && ip !== 'localhost' && ip !== '127.0.0.1' && !ip.includes('/')) {
        return ip;
      }
    }
  }
  return null;
}

export const getApiBaseUrl = (): string => {
  // 1. Explicit environment variable takes top precedence
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.replace(/\/+$/, ''); // Remove trailing slashes
  }

  // 2. Dynamic host IP detection across Expo Go physical devices
  const hostIp = resolveHostIp();

  // 3. Android platform routing
  if (Platform.OS === 'android') {
    // Android Emulator MUST use 10.0.2.2 to loop back to the host development PC
    if (!Device.isDevice) {
      return 'http://10.0.2.2:8000';
    }

    // Physical Android phone running Expo Go over local Wi-Fi / LAN
    if (hostIp) {
      return `http://${hostIp}:8000`;
    }

    // Fallback for physical Android device on current dev network
    return 'http://192.168.137.165:8000';
  }

  // 4. iOS device or simulator
  if (hostIp && Device.isDevice) {
    return `http://${hostIp}:8000`;
  }

  // 5. Desktop localhost
  return 'http://localhost:8000';
};

export const API_TIMEOUT_MS = 10_000; // 10 second default timeout
export const UPLOAD_TIMEOUT_MS = 30_000; // 30 second timeout for image uploads
