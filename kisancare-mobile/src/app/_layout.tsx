import React, { useEffect } from 'react';
import { Stack, DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useColorScheme } from 'react-native';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/services/queryClient';
import { Colors, Typography } from '@/constants/theme';

SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  const navTheme = {
    ...(colorScheme === 'dark' ? DarkTheme : DefaultTheme),
    colors: {
      ...(colorScheme === 'dark' ? DarkTheme.colors : DefaultTheme.colors),
      primary: theme.primary,
      background: theme.background,
      card: theme.surface,
      text: theme.text,
      border: theme.borderLight,
    },
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider value={navTheme}>
        <Stack
          screenOptions={{
            headerStyle: {
              backgroundColor: theme.surface,
            },
            headerTintColor: theme.primary,
            headerTitleStyle: {
              fontWeight: Typography.weights.bold,
              color: theme.text,
              fontSize: Typography.sizes.md,
            },
            headerShadowVisible: false,
            headerBackTitle: 'Back',
          }}
        >
          <Stack.Screen name="welcome" options={{ headerShown: false }} />
          <Stack.Screen name="otp" options={{ headerShown: false }} />
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="crop-planning"
            options={{
              headerShown: false,
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="crop-recommendations"
            options={{
              headerShown: false,
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="crop-details"
            options={{
              headerShown: false,
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="crop-health"
            options={{
              title: 'Crop Health AI',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="soil-report"
            options={{
              title: 'Soil Health Card',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="finances"
            options={{
              title: 'Financial Records',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="profile"
            options={{
              title: 'Farmer Profile',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="digital-twin"
            options={{
              title: 'Digital Twin Simulation',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="rentals"
            options={{
              title: 'Equipment Rentals',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="chatbot"
            options={{
              title: 'AI Copilot',
              headerShown: false,
              presentation: 'card',
            }}
          />
        </Stack>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
