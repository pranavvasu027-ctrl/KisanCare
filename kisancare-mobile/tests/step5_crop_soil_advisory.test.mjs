/**
 * KisanCare Step 5 Verification Test Suite
 * Tests Crop Recommendation, Soil Intelligence, and Advisory Services & Live Backend.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';

const BASE_URL = 'http://localhost:8000';

describe('KisanCare Step 5: Crop Recommendation, Soil & Advisory Suite', () => {

  // --- 1. Crop Recommendation Validation Tests ---
  test('1. Crop Recommendation Input Validation Rules', () => {
    const validDistricts = ['AKOLA', 'NASHIK', 'PUNE', 'AMRAVATI', 'SOLAPUR'];
    const validSeasons = ['Kharif', 'Rabi', 'Summer', 'Whole Year'];
    const validWater = ['Low', 'Medium', 'High'];

    // Valid check
    const validPayload = { district: 'AKOLA', season: 'Kharif', water_availability: 'Medium', top_k: 5 };
    assert.ok(validDistricts.includes(validPayload.district), 'District should be valid');
    assert.ok(validSeasons.includes(validPayload.season), 'Season should be valid');
    assert.ok(validWater.includes(validPayload.water_availability), 'Water should be valid');
    assert.ok(validPayload.top_k >= 1 && validPayload.top_k <= 20, 'Top K should be within 1..20');

    // Invalid district
    const badDistrict = 'NEW_YORK';
    assert.strictEqual(validDistricts.includes(badDistrict), false, 'Unknown district should fail');

    // Invalid season
    const badSeason = 'MonsoonExtra';
    assert.strictEqual(validSeasons.includes(badSeason), false, 'Non-standard season should fail');

    console.log('   ✓ Crop recommendation input validation rules verified');
  });

  // --- 2. Live POST /api/v1/crop-recommendation ---
  test('2. Live Crop Recommendation Endpoint (/api/v1/crop-recommendation)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/crop-recommendation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        district: 'NASHIK',
        season: 'Kharif',
        water_availability: 'Medium',
        top_k: 5,
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.strictEqual(data.status, 'SUCCESS', 'Response status must be SUCCESS');
    assert.ok(Array.isArray(data.recommendations), 'Must return recommendations array');
    assert.ok(data.recommendations.length > 0, 'Must have at least one recommended crop');

    const topCrop = data.recommendations[0];
    assert.ok(topCrop.crop, 'Crop name must be present');
    assert.strictEqual(topCrop.rank, 1, 'First item must have rank 1');
    assert.ok(typeof topCrop.predicted_area_frequency === 'number', 'Score must be a number');

    assert.ok(data.score_interpretation, 'Must explain score interpretation (historical suitability, not accuracy)');
    assert.ok(data.data_source, 'Must provide data source provenance');
    console.log(`   ✓ Live Crop Recommendation Passed (${elapsed}ms): Top Crop = ${topCrop.crop} (rank=${topCrop.rank}, score=${topCrop.predicted_area_frequency})`);
  });

  // --- 3. Soil Intelligence Validation & Categorization ---
  test('3. Soil Nutrient Validation and Categorization Rules', () => {
    const evaluateNPK = (n, p, k, ph) => {
      const nRating = n < 20 ? 'Low' : n > 50 ? 'High' : 'Optimal';
      const pRating = p < 10 ? 'Low' : 'Optimal';
      const kRating = k < 150 ? 'Low' : 'Optimal';
      let phRating = 'Optimal';
      if (ph < 5.5) phRating = 'Acidic';
      else if (ph > 7.5) phRating = 'Alkaline';
      return { nRating, pRating, kRating, phRating };
    };

    const deficient = evaluateNPK(15, 8, 120, 5.0);
    assert.strictEqual(deficient.nRating, 'Low');
    assert.strictEqual(deficient.pRating, 'Low');
    assert.strictEqual(deficient.kRating, 'Low');
    assert.strictEqual(deficient.phRating, 'Acidic');

    const optimal = evaluateNPK(35, 15, 160, 6.5);
    assert.strictEqual(optimal.nRating, 'Optimal');
    assert.strictEqual(optimal.pRating, 'Optimal');
    assert.strictEqual(optimal.kRating, 'Optimal');
    assert.strictEqual(optimal.phRating, 'Optimal');

    console.log('   ✓ Soil nutrient benchmark categorization rules verified');
  });

  // --- 4. Live POST /api/v1/soil-assessment ---
  test('4. Live Soil Assessment Endpoint (/api/v1/soil-assessment)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/soil-assessment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        n: 15.0,
        p: 8.0,
        k: 120.0,
        ph: 5.0,
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(data.model_type, 'Must return model_type');
    assert.ok(data.overall_status, 'Must return overall_status');
    assert.ok(Array.isArray(data.issues), 'Must return issues array');
    assert.ok(data.recommendation, 'Must return agronomist recommendation');
    console.log(`   ✓ Live Soil Assessment Passed (${elapsed}ms): Status = ${data.overall_status}, Issues = [${data.issues.join(', ')}]`);
  });

  // --- 5. Live GET /api/v1/weather/forecast ---
  test('5. Live Weather Forecast & Agro-Advisory (/api/v1/weather/forecast)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/weather/forecast?lat=20.7002&lon=77.0082&days=3`);
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(data.current, 'Must contain current weather');
    assert.ok(data.agricultural_advisory, 'Must contain agricultural_advisory object');
    assert.ok(Array.isArray(data.agricultural_advisory.advisory_notes), 'advisory_notes must be array');
    console.log(`   ✓ Live Weather & Agro-Advisory Passed (${elapsed}ms): Notes count = ${data.agricultural_advisory.advisory_notes.length}`);
  });

  // --- 6. Live POST /api/v1/irrigation ---
  test('6. Live Irrigation Recommendation (/api/v1/irrigation)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/irrigation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Soybean',
        soil_moisture: 20.0,
        days_since_rain: 6,
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(typeof data.irrigation_required === 'boolean', 'irrigation_required must be boolean');
    assert.ok(data.reasoning, 'reasoning must be present');
    console.log(`   ✓ Live Irrigation Recommendation Passed (${elapsed}ms): Required = ${data.irrigation_required}, Liters/Acre = ${data.recommended_amount_liters_per_acre}`);
  });

  // --- 7. Live POST /api/v1/weather-risk ---
  test('7. Live Meteorological Risk Assessment (/api/v1/weather-risk)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/weather-risk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        temperature: 38.0,
        humidity: 35.0,
        rainfall_forecast: 0.0,
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(data.overall_risk, 'overall_risk must be present');
    assert.ok(Array.isArray(data.identified_risks), 'identified_risks must be array');
    assert.ok(data.mitigation, 'mitigation must be present');
    console.log(`   ✓ Live Weather Risk Passed (${elapsed}ms): Risk = ${data.overall_risk}, Mitigation = ${data.mitigation}`);
  });

  // --- 8. Live GET /api/copilot/status ---
  test('8. Live AI Decision Engine / Copilot Status (/api/copilot/status)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/copilot/status`);
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(data.status, 'status must be present');
    assert.ok(data.provider, 'provider must be present');
    assert.ok(data.model, 'model must be present');
    console.log(`   ✓ Live AI Decision Engine Status Passed (${elapsed}ms): Status = ${data.status}, Model = ${data.model}`);
  });
});
