/**
 * KisanCare Mobile API Configuration
 * Manages base URLs and timeout settings across platforms without hardcoding.
 */

import { Platform } from 'react-native';
import Constants from 'expo-constants';
import * as Device from 'expo-device';

export const getApiBaseUrl = (): string => {
  // 1. Explicit environment variable takes top precedence
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.replace(/\/+$/, ''); // Remove trailing slashes
  }

  // 2. Android platform routing
  if (Platform.OS === 'android') {
    // Android Emulator MUST use 10.0.2.2 to loop back to the host development PC
    if (!Device.isDevice) {
      return 'http://10.0.2.2:8000';
    }

    // Physical Android phone running Expo Go over local Wi-Fi / LAN
    const hostUri = Constants.expoConfig?.hostUri;
    if (hostUri) {
      const ip = hostUri.split(':')[0];
      if (ip && ip !== 'localhost' && ip !== '127.0.0.1') {
        return `http://${ip}:8000`;
      }
    }
    return 'http://10.0.2.2:8000';
  }

  // 3. iOS simulator, web browser, and desktop localhost
  return 'http://localhost:8000';
};

export const API_TIMEOUT_MS = 10_000; // 10 second default timeout
export const UPLOAD_TIMEOUT_MS = 30_000; // 30 second timeout for image uploads
