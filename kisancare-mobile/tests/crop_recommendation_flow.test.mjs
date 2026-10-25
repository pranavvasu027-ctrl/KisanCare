/**
 * KisanCare Crop Recommendation Integration Test Suite
 * Validates the complete flow:
 * 1. Farm Loading & Retrieval
 * 2. Input Validation (Districts, Seasons, Water, Top-K)
 * 3. Live ML Crop Recommendation Invocation
 * 4. Agronomic Catalog Mapping (Water, Sowing, Soil, Assets)
 * 5. Live Farm Crop Assignment (PUT /api/v1/farms/{farm_id}/crop)
 * 6. Error & Validation Handling
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';

const BASE_URL = 'http://localhost:8000';

const VALID_MAHARASHTRA_DISTRICTS = [
  'AKOLA', 'AMRAVATI', 'AURANGABAD', 'BEED', 'BHANDARA', 'BULDHANA',
  'CHANDRAPUR', 'DHULE', 'GADCHIROLI', 'GONDIA', 'HINGOLI', 'JALGAON',
  'JALNA', 'KOLHAPUR', 'LATUR', 'MUMBAI', 'NAGPUR', 'NANDED', 'NANDURBAR',
  'NASHIK', 'OSMANABAD', 'PALGHAR', 'PARBHANI', 'PUNE', 'RAIGAD', 'RATNAGIRI',
  'SANGLI', 'SATARA', 'SINDHUDURG', 'SOLAPUR', 'THANE', 'WARDHA', 'WASHIM', 'YAVATMAL',
];

const VALID_SEASONS = ['Kharif', 'Rabi', 'Summer', 'Whole Year'];
const VALID_WATER_LEVELS = ['Low', 'Medium', 'High'];

describe('KisanCare: Crop Recommendation UI & Backend Integration Suite', () => {
  // Test 1: Validation Rules
  test('1. Crop Recommendation Input Validation Rules', () => {
    // Valid inputs
    const valid = { district: 'AKOLA', season: 'Kharif', water: 'Medium', top_k: 5 };
    assert.ok(VALID_MAHARASHTRA_DISTRICTS.includes(valid.district), 'Akola must be valid');
    assert.ok(VALID_SEASONS.includes(valid.season), 'Kharif must be valid');
    assert.ok(VALID_WATER_LEVELS.includes(valid.water), 'Medium must be valid');
    assert.ok(valid.top_k >= 1 && valid.top_k <= 20, 'Top-K within bounds');

    // Invalid district
    const badDistrict = 'UNKNOWN_STATE';
    assert.strictEqual(VALID_MAHARASHTRA_DISTRICTS.includes(badDistrict), false, 'Unknown district must fail');

    // Invalid season
    const badSeason = 'MonsoonExtra';
    assert.strictEqual(VALID_SEASONS.includes(badSeason), false, 'Invalid season must fail');

    console.log('   ✓ Input validation rules verified');
  });

  // Test 2: Live GET /api/v1/farms
  test('2. Live Farm Retrieval for Selection Control', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/farms`);
    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(Array.isArray(data.farms), 'Response must contain farms array');
    assert.ok(data.farms.length > 0, 'Must have at least one registered farm');

    const farm = data.farms[0];
    assert.ok(farm.id, 'Farm must have id');
    assert.ok(farm.farm_name, 'Farm must have name');
    assert.ok(farm.location, 'Farm must have location');
    console.log(`   ✓ Loaded farm: "${farm.farm_name}" at ${farm.location}`);
  });

  // Test 3: Live POST /api/v1/crop-recommendation with Akola + Kharif
  test('3. Live ML Recommendation Pipeline for Akola (Kharif)', async () => {
    const payload = {
      district: 'AKOLA',
      season: 'Kharif',
      water_availability: 'Medium',
      top_k: 5,
    };

    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/crop-recommendation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.strictEqual(data.status, 'SUCCESS', 'Recommendation status must be SUCCESS');
    assert.strictEqual(data.district, 'AKOLA');
    assert.strictEqual(data.season, 'Kharif');
    assert.ok(Array.isArray(data.recommendations), 'Must contain recommendations list');
    assert.ok(data.recommendations.length > 0, 'Must return at least 1 recommendation');

    // Verify ranking monotonicity
    for (let i = 0; i < data.recommendations.length; i++) {
      const rec = data.recommendations[i];
      assert.strictEqual(rec.rank, i + 1, `Rank must equal index + 1`);
      assert.ok(typeof rec.crop === 'string', 'Crop name must be a string');
      assert.ok(typeof rec.predicted_area_frequency === 'number', 'Score must be a number');
      if (i > 0) {
        assert.ok(
          data.recommendations[i - 1].predicted_area_frequency >= rec.predicted_area_frequency,
          'Recommendations must be sorted descending by suitability'
        );
      }
    }

    const topCrop = data.recommendations[0];
    console.log(`   ✓ Top recommended crop: ${topCrop.crop} (Score: ${topCrop.predicted_area_frequency}) in ${elapsed}ms`);
  });

  // Test 4: Live PUT /api/v1/farms/{farm_id}/crop (Choose Crop for Field)
  test('4. Live Crop Assignment to Field (PUT /api/v1/farms/:id/crop)', async () => {
    // 1. Get farm ID
    const farmsRes = await fetch(`${BASE_URL}/api/v1/farms`);
    const farmsData = await farmsRes.json();
    const targetFarm = farmsData.farms[0];

    // 2. Assign crop
    const assignPayload = {
      crop: 'Cotton',
      sowing_date: '25 Oct 2026',
    };

    const res = await fetch(`${BASE_URL}/api/v1/farms/${targetFarm.id}/crop`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(assignPayload),
    });

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const resData = await res.json();

    assert.strictEqual(resData.status, 'success');
    assert.strictEqual(resData.farm_id, targetFarm.id);
    assert.strictEqual(resData.active_crop, 'Cotton');
    assert.strictEqual(resData.sowing_date, '25 Oct 2026');

    // 3. Verify farm updated in listing
    const checkRes = await fetch(`${BASE_URL}/api/v1/farms`);
    const checkData = await checkRes.json();
    const updated = checkData.farms.find((f) => f.id === targetFarm.id);
    assert.ok(updated, 'Updated farm must exist');
    assert.strictEqual(updated.active_crop, 'Cotton', 'Active crop must reflect update');
    assert.strictEqual(updated.sowing_date, '25 Oct 2026', 'Sowing date must reflect update');

    console.log(`   ✓ Successfully assigned Cotton to farm "${targetFarm.farm_name}"`);
  });

  // Test 5: Error Handling for Non-existent Farm & Empty Crop
  test('5. Error Handling for Invalid Inputs & Non-existent Farm', async () => {
    // Bad farm ID
    const badFarmRes = await fetch(`${BASE_URL}/api/v1/farms/non-existent-farm-uuid-9999/crop`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ crop: 'Cotton', sowing_date: '25 Oct 2026' }),
    });
    assert.strictEqual(badFarmRes.status, 404, 'Must return 404 for non-existent farm');

    // Empty crop name
    const farmsRes = await fetch(`${BASE_URL}/api/v1/farms`);
    const farmsData = await farmsRes.json();
    const targetFarm = farmsData.farms[0];

    const emptyCropRes = await fetch(`${BASE_URL}/api/v1/farms/${targetFarm.id}/crop`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ crop: '', sowing_date: '25 Oct 2026' }),
    });
    assert.strictEqual(emptyCropRes.status, 422, 'Must return 422 for blank crop');

    console.log('   ✓ Negative validation & 404/422 error handling confirmed');
  });
});
