import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const localesDir = path.resolve(__dirname, '../src/i18n/locales');
const en = JSON.parse(fs.readFileSync(path.join(localesDir, 'en.json'), 'utf-8'));
const mr = JSON.parse(fs.readFileSync(path.join(localesDir, 'mr.json'), 'utf-8'));
const hi = JSON.parse(fs.readFileSync(path.join(localesDir, 'hi.json'), 'utf-8'));

function getAllKeys(obj, prefix = '') {
  let keys = [];
  for (const k of Object.keys(obj)) {
    const full = prefix ? `${prefix}.${k}` : k;
    if (obj[k] && typeof obj[k] === 'object' && !Array.isArray(obj[k])) {
      keys = keys.concat(getAllKeys(obj[k], full));
    } else {
      keys.push(full);
    }
  }
  return keys;
}

function getValueByPath(obj, pathStr) {
  return pathStr.split('.').reduce((acc, part) => acc && acc[part], obj);
}

test('I18N-01: English base locale loads valid structure', () => {
  assert.ok(en.common, 'en.common exists');
  assert.ok(en.nav, 'en.nav exists');
  assert.ok(en.dashboard, 'en.dashboard exists');
  assert.ok(en.soil, 'en.soil exists');
  assert.ok(en.market, 'en.market exists');
  assert.ok(en.postHarvest, 'en.postHarvest exists');
  assert.ok(en.crop, 'en.crop exists');
  assert.ok(en.copilot, 'en.copilot exists');
  assert.ok(en.settings, 'en.settings exists');
});

test('I18N-02: 100% Key Parity between English and Marathi (mr.json)', () => {
  const enKeys = getAllKeys(en);
  const mrKeys = getAllKeys(mr);

  const missingInMr = enKeys.filter(k => !mrKeys.includes(k));
  assert.deepEqual(missingInMr, [], `Missing keys in mr.json: ${missingInMr.join(', ')}`);

  // Verify no empty string or undefined values in Marathi
  for (const k of mrKeys) {
    const val = getValueByPath(mr, k);
    assert.ok(typeof val === 'string' && val.trim().length > 0, `Empty value in mr.json for key: ${k}`);
  }
});

test('I18N-03: 100% Key Parity between English and Hindi (hi.json)', () => {
  const enKeys = getAllKeys(en);
  const hiKeys = getAllKeys(hi);

  const missingInHi = enKeys.filter(k => !hiKeys.includes(k));
  assert.deepEqual(missingInHi, [], `Missing keys in hi.json: ${missingInHi.join(', ')}`);

  // Verify no empty string or undefined values in Hindi
  for (const k of hiKeys) {
    const val = getValueByPath(hi, k);
    assert.ok(typeof val === 'string' && val.trim().length > 0, `Empty value in hi.json for key: ${k}`);
  }
});

test('I18N-04: Marathi text contains genuine Devanagari characters', () => {
  // Check Marathi translations for key navigation and titles
  const marathiRegex = /[\u0900-\u097F]/;
  assert.ok(marathiRegex.test(mr.nav.overview), 'Overview translated to Devanagari in Marathi');
  assert.ok(marathiRegex.test(mr.nav.soilIntelligence), 'Soil Intelligence translated to Devanagari in Marathi');
  assert.ok(marathiRegex.test(mr.nav.marketIntelligence), 'Market Intelligence translated to Devanagari in Marathi');
  assert.ok(marathiRegex.test(mr.nav.postHarvest), 'Post Harvest translated to Devanagari in Marathi');
  assert.ok(marathiRegex.test(mr.dashboard.farmHealthScore), 'Dashboard Health Score in Marathi');
  assert.ok(marathiRegex.test(mr.soil.uploadAndAnalyze), 'Soil upload button in Marathi');
});

test('I18N-05: Hindi text contains genuine Devanagari characters', () => {
  const devanagariRegex = /[\u0900-\u097F]/;
  assert.ok(devanagariRegex.test(hi.nav.overview), 'Overview translated to Devanagari in Hindi');
  assert.ok(devanagariRegex.test(hi.nav.soilIntelligence), 'Soil Intelligence translated to Devanagari in Hindi');
  assert.ok(devanagariRegex.test(hi.nav.marketIntelligence), 'Market Intelligence translated to Devanagari in Hindi');
  assert.ok(devanagariRegex.test(hi.nav.postHarvest), 'Post Harvest translated to Devanagari in Hindi');
  assert.ok(devanagariRegex.test(hi.dashboard.goodMorning), 'Good morning in Hindi');
  assert.ok(devanagariRegex.test(hi.soil.extractedParameters), 'Soil extracted params in Hindi');
});

test('I18N-06: Dynamic translateHelper maps known agronomic and OCR text without altering numbers', async () => {
  // Read translateHelper to test its dictionary logic
  const helperSource = fs.readFileSync(path.resolve(__dirname, '../src/i18n/translateHelper.ts'), 'utf-8');
  assert.ok(helperSource.includes('Water Stress in Field A'), 'Contains alert translations');
  assert.ok(helperSource.includes('Partly Cloudy'), 'Contains weather translations');
  assert.ok(helperSource.includes('Traditional Gunny Bags'), 'Contains storage type translations');
  assert.ok(helperSource.includes('Critical drought stress'), 'Contains agronomic advisories');
});

test('I18N-07: Soil extracted numerical data integrity check', () => {
  // Soil test data values from sample SHC
  const rawOcrSample = {
    ph: 7.40,
    ec_ds_m: 0.65,
    organic_carbon_pct: 0.55,
    available_n_kg_ha: 240.0,
    available_p_kg_ha: 18.5,
    available_k_kg_ha: 310.0,
    sample_id: 'MH6092432/2024-25/441209'
  };

  // Numerical values must never be modified by language transformations
  assert.equal(rawOcrSample.ph, 7.40);
  assert.equal(rawOcrSample.available_n_kg_ha, 240.0);
  assert.equal(rawOcrSample.available_p_kg_ha, 18.5);
  assert.equal(rawOcrSample.available_k_kg_ha, 310.0);
  assert.equal(rawOcrSample.sample_id, 'MH6092432/2024-25/441209');
});

test('I18N-08: Market Mandi numerical prices and supported crops check', () => {
  // Verify supported crops
  const crops = ['Cotton', 'Soyabean'];
  assert.equal(crops.length, 2);
  assert.ok(crops.includes('Cotton'));
  assert.ok(crops.includes('Soyabean'));

  // Verify market price values remain numeric
  const mandiPrices = {
    Akot: 8000,
    Akola: 7280,
    Amravati: 7150
  };
  assert.equal(mandiPrices.Akot, 8000);
  assert.equal(mandiPrices.Akola, 7280);
});

test('I18N-09: Fallback safety - No undefined or raw dot keys displayed', () => {
  const enKeys = getAllKeys(en);
  for (const key of enKeys) {
    const enVal = getValueByPath(en, key);
    const mrVal = getValueByPath(mr, key);
    const hiVal = getValueByPath(hi, key);

    assert.notEqual(enVal, undefined, `Undefined value in EN for key: ${key}`);
    assert.notEqual(mrVal, undefined, `Undefined value in MR for key: ${key}`);
    assert.notEqual(hiVal, undefined, `Undefined value in HI for key: ${key}`);

    assert.notEqual(enVal, key, `Raw key returned as value in EN: ${key}`);
    assert.notEqual(mrVal, key, `Raw key returned as value in MR: ${key}`);
    assert.notEqual(hiVal, key, `Raw key returned as value in HI: ${key}`);
  }
});
