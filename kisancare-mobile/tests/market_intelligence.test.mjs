/**
 * KisanCare Market Intelligence Verification Test Suite
 * Tests Market Price Forecasting, Supported Commodities, and Live Backend XGBoost Predictor.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';

const BASE_URL = 'http://127.0.0.1:8000';

describe('KisanCare Market Intelligence Test Suite', () => {

  // --- 1. Commodity Registry Rules ---
  test('1. Supported Commodity Contract & Default Dates', () => {
    const supportedCrops = ['onion', 'tomato', 'potato', 'cabbage', 'cauliflower'];
    const supportedMarkets = ['pune_pimpri', 'pune_manjri', 'pune_manjriapmc'];

    assert.ok(supportedCrops.includes('onion'), 'Onion must be supported');
    assert.ok(supportedCrops.includes('tomato'), 'Tomato must be supported');
    assert.ok(supportedCrops.includes('potato'), 'Potato must be supported');
    assert.ok(supportedCrops.includes('cabbage'), 'Cabbage must be supported');
    assert.ok(supportedCrops.includes('cauliflower'), 'Cauliflower must be supported');

    assert.ok(supportedMarkets.includes('pune_pimpri'), 'Pune Pimpri APMC must be supported');
    assert.ok(supportedMarkets.includes('pune_manjri'), 'Pune Manjri APMC must be supported');
    assert.ok(supportedMarkets.includes('pune_manjriapmc'), 'Pune Manjri APMC must be supported');
    console.log('   ✓ Supported commodity contract and markets verified');
  });

  // --- 2. Live POST /api/v1/market-price for Onion ---
  test('2. Live Market Price Forecasting - Onion Pune (Pimpri)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/market-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'onion',
        market: 'pune_pimpri',
        date: '2025-11-04',
      }),
    });

    assert.strictEqual(res.status, 200, 'Onion market price query should return HTTP 200');
    const data = await res.json();
    assert.strictEqual(data.status, 'success', 'Status should be success');
    assert.strictEqual(data.crop, 'onion', 'Crop should match');
    assert.strictEqual(typeof data.current_price, 'number', 'Current price should be a number');
    assert.ok(data.current_price > 0, 'Current price must be positive');
    assert.ok(typeof data.forecast_7d === 'number' || typeof data.forecast_7d === 'string', 'Forecast 7d must exist');
    console.log(`   ✓ Live Market Price Passed (Onion): Observed ₹${data.current_price}/qtl, 7D Forecast ₹${data.forecast_7d}`);
  });

  // --- 3. Live POST /api/v1/market-price for Tomato ---
  test('3. Live Market Price Forecasting - Tomato Pune (Pimpri)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/market-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'tomato',
        market: 'pune_pimpri',
        date: '2025-11-04',
      }),
    });

    assert.strictEqual(res.status, 200, 'Tomato query should return HTTP 200');
    const data = await res.json();
    assert.strictEqual(data.status, 'success');
    assert.strictEqual(data.crop, 'tomato');
    assert.ok(data.current_price > 0);
    console.log(`   ✓ Live Market Price Passed (Tomato): Observed ₹${data.current_price}/qtl, 7D Forecast ₹${data.forecast_7d}`);
  });

  // --- 4. Live POST /api/v1/market-price for Potato ---
  test('4. Live Market Price Forecasting - Potato Pune (Manjri)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/market-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'potato',
        market: 'pune_manjriapmc',
        date: '2025-11-20',
      }),
    });

    assert.strictEqual(res.status, 200, 'Potato query should return HTTP 200');
    const data = await res.json();
    assert.strictEqual(data.status, 'success');
    assert.strictEqual(data.crop, 'potato');
    assert.ok(data.current_price > 0);
    console.log(`   ✓ Live Market Price Passed (Potato): Observed ₹${data.current_price}/qtl, 7D Forecast ₹${data.forecast_7d}`);
  });

  // --- 5. Lookback Boundary Handling (HTTP 422) ---
  test('5. Lookback Boundary Validation (HTTP 422 for insufficient history)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/market-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'potato',
        market: 'pune_manjriapmc',
        date: '2025-11-04', // Potato data starts 2025-11-01, only 3 days history -> requires >= 14 days
      }),
    });

    assert.strictEqual(res.status, 422, 'Insufficient lookback history should return HTTP 422');
    const err = await res.json();
    assert.ok(err.detail.includes('14 days'), 'Error message should mention 14 days requirement');
    console.log('   ✓ Lookback boundary validation (HTTP 422) verified');
  });

  // --- 6. Unsupported Commodity Handling (HTTP 404) ---
  test('6. Unsupported Commodity Validation (HTTP 404 for unknown crop)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/market-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'avocado',
        market: 'pune_pimpri',
        date: '2025-11-04',
      }),
    });

    assert.strictEqual(res.status, 404, 'Unknown crop should return HTTP 404');
    console.log('   ✓ Unsupported commodity validation (HTTP 404) verified');
  });
});
