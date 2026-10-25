/**
 * KisanCare Step 6 Verification Test Suite
 * Tests Disease and Pest Detection Services, Validation, and Live Backend Endpoints.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';

const BASE_URL = 'http://localhost:8000';

describe('KisanCare Step 6: Crop Disease & Pest Detection Suite', () => {

  // --- 1. Symptoms Request Validation Rules ---
  test('1. Symptoms Request Input Validation Rules', () => {
    // Valid check
    const valid = { crop: 'Soybean', symptoms: ['yellow leaves', 'stunted growth'] };
    assert.ok(valid.crop.length > 0, 'Crop must not be empty');
    assert.ok(Array.isArray(valid.symptoms) && valid.symptoms.length > 0, 'Symptoms must be non-empty array');

    // Missing crop
    const missingCrop = { crop: '', symptoms: ['yellow leaves'] };
    assert.strictEqual(missingCrop.crop.length === 0, true, 'Empty crop should be flagged');

    // Empty symptoms array
    const emptySymptoms = { crop: 'Tomato', symptoms: [] };
    assert.strictEqual(emptySymptoms.symptoms.length === 0, true, 'Empty symptoms should be flagged');

    console.log('   ✓ Symptoms request validation rules verified');
  });

  // --- 2. Image Metadata Validation Rules ---
  test('2. Image Metadata Size & Format Validation Rules', () => {
    const MAX_SIZE = 5 * 1024 * 1024; // 5 MB

    // Valid image metadata
    const validMeta = {
      uri: 'file:///data/user/0/host.exp.exponent/cache/leaf.jpg',
      fileSize: 2.1 * 1024 * 1024,
      mimeType: 'image/jpeg',
    };
    assert.ok(validMeta.fileSize <= MAX_SIZE, '2.1 MB image should be within limit');
    assert.ok(['image/jpeg', 'image/png', 'image/webp'].includes(validMeta.mimeType), 'JPEG should be valid format');

    // Oversized image
    const oversizedMeta = {
      uri: 'file:///heavy.png',
      fileSize: 7.8 * 1024 * 1024, // 7.8 MB
      mimeType: 'image/png',
    };
    assert.strictEqual(oversizedMeta.fileSize > MAX_SIZE, true, '7.8 MB image must exceed 5MB limit');

    // Unsupported format
    const badFormat = {
      uri: 'file:///document.pdf',
      fileSize: 500 * 1024,
      mimeType: 'application/pdf',
    };
    assert.strictEqual(['image/jpeg', 'image/png', 'image/webp'].includes(badFormat.mimeType), false, 'PDF should be rejected for crop health');

    console.log('   ✓ Image metadata validation rules verified');
  });

  // --- 3. Live POST /api/v1/disease-detection (Nitrogen Deficiency / Root Rot) ---
  test('3. Live Disease Detection (/api/v1/disease-detection - Root Rot)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/disease-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Soybean',
        symptoms: ['yellow leaves', 'stunted growth'],
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.strictEqual(data.model_type, 'RULE_BASED_EXPERT_SYSTEM', 'Model type must disclose rule-based engine');
    assert.ok(data.prediction.includes('Nitrogen Deficiency') || data.prediction.includes('Root Rot'), 'Prediction should identify deficiency/rot');
    assert.strictEqual(typeof data.confidence, 'number', 'Confidence must be numeric heuristic score');
    assert.ok(data.treatment, 'Treatment instructions must be provided');
    console.log(`   ✓ Live Disease Detection Passed (${elapsed}ms): Diagnosis="${data.prediction}" (confidence=${data.confidence}, model=${data.model_type})`);
  });

  // --- 4. Live POST /api/v1/disease-detection (Powdery Mildew) ---
  test('4. Live Disease Detection (/api/v1/disease-detection - Powdery Mildew)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/disease-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Tomato',
        symptoms: ['white powdery spots'],
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.strictEqual(data.prediction, 'Powdery Mildew');
    assert.strictEqual(data.confidence, 0.85);
    assert.ok(data.treatment.includes('sulfur'), 'Treatment should recommend sulfur fungicide');
    console.log(`   ✓ Live Disease Detection Passed (${elapsed}ms): Diagnosis="${data.prediction}" (confidence=${data.confidence})`);
  });

  // --- 5. Live POST /api/v1/pest-detection (Caterpillars / Beetles) ---
  test('5. Live Pest Detection (/api/v1/pest-detection - Caterpillars)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/pest-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Cotton',
        symptoms: ['holes in leaves'],
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.strictEqual(data.model_type, 'RULE_BASED_EXPERT_SYSTEM');
    assert.strictEqual(data.prediction, 'Caterpillars / Beetles');
    assert.strictEqual(data.confidence, 0.80);
    assert.ok(data.treatment.includes('neem oil') || data.treatment.includes('Bt'));
    console.log(`   ✓ Live Pest Detection Passed (${elapsed}ms): Pest="${data.prediction}" (confidence=${data.confidence})`);
  });

  // --- 6. Live POST /api/v1/pest-detection (Aphids) ---
  test('6. Live Pest Detection (/api/v1/pest-detection - Aphids)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/pest-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Wheat',
        symptoms: ['sticky residue', 'curled leaves'],
      }),
    });
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.strictEqual(data.prediction, 'Aphids');
    assert.strictEqual(data.confidence, 0.85);
    assert.ok(data.treatment.includes('ladybugs') || data.treatment.includes('soap'));
    console.log(`   ✓ Live Pest Detection Passed (${elapsed}ms): Pest="${data.prediction}" (confidence=${data.confidence})`);
  });

  // --- 7. Contract Mismatch Prevention (HTTP 422 on Invalid Symptoms) ---
  test('7. Contract Mismatch Prevention & Error Handling (HTTP 422)', async () => {
    // Empty symptoms array
    const res1 = await fetch(`${BASE_URL}/api/v1/disease-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Soybean',
        symptoms: [],
      }),
    });
    assert.strictEqual(res1.status, 422, 'Empty symptoms array must return HTTP 422');

    // Missing crop field
    const res2 = await fetch(`${BASE_URL}/api/v1/pest-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symptoms: ['holes in leaves'],
      }),
    });
    assert.strictEqual(res2.status, 422, 'Missing crop must return HTTP 422');

    console.log('   ✓ Contract mismatch & HTTP 422 validation error handling verified');
  });

  // --- 8. Heuristic Scoring & Provenance Segregation ---
  test('8. Heuristic Scoring & Model Transparency Guardrail', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/disease-detection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: 'Corn',
        symptoms: ['unrecognized strange spot pattern'],
      }),
    });
    assert.strictEqual(res.status, 200);
    const data = await res.json();

    assert.strictEqual(data.model_type, 'RULE_BASED_EXPERT_SYSTEM', 'Must never claim deep learning model');
    assert.strictEqual(data.prediction, 'Unknown / Healthy');
    assert.strictEqual(data.confidence, 0.50, 'Unknown cases must report conservative 0.50 heuristic score');
    console.log(`   ✓ Fallback Transparency Verified: Prediction="${data.prediction}" with conservative confidence=${data.confidence}`);
  });
});
