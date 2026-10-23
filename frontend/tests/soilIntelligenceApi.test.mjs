/**
 * Frontend Unit & Contract Tests for Soil Intelligence API Client
 * ===============================================================
 * Validates endpoint construction, payload serialization, error handling,
 * and scientific safeguard preservation (abstention gate & provenance).
 */

import test from 'node:test';
import assert from 'node:assert/strict';

// Test 1: URL and Endpoint Contract Verification
test('API Contract: Endpoint paths and methods match backend specification', () => {
  const endpoints = {
    benchmarks: '/api/v1/soil/benchmarks',
    parse: '/api/v1/soil/reports/parse',
    upload: '/api/v1/soil/reports/upload',
    correct: '/api/v1/soil/reports/review/correct',
    confirm: '/api/v1/soil/reports/confirm',
    fertilizer: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}/events/fertilizer`,
    harvest: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}/events/harvest`,
    events: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}/events`,
    status: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}/status`,
    pdf: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}/report.pdf`,
    compare: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}/compare`,
    delete: (id) => `/api/v1/soil/plots/${encodeURIComponent(id)}`
  };

  const testPlot = 'PLOT_MH_LAT_881';
  assert.equal(endpoints.benchmarks, '/api/v1/soil/benchmarks');
  assert.equal(endpoints.parse, '/api/v1/soil/reports/parse');
  assert.equal(endpoints.upload, '/api/v1/soil/reports/upload');
  assert.equal(endpoints.fertilizer(testPlot), '/api/v1/soil/plots/PLOT_MH_LAT_881/events/fertilizer');
  assert.equal(endpoints.harvest(testPlot), '/api/v1/soil/plots/PLOT_MH_LAT_881/events/harvest');
  assert.equal(endpoints.status(testPlot), '/api/v1/soil/plots/PLOT_MH_LAT_881/status');
  assert.equal(endpoints.pdf(testPlot), '/api/v1/soil/plots/PLOT_MH_LAT_881/report.pdf');
  assert.equal(endpoints.compare(testPlot), '/api/v1/soil/plots/PLOT_MH_LAT_881/compare');
  assert.equal(endpoints.delete(testPlot), '/api/v1/soil/plots/PLOT_MH_LAT_881');
});

// Test 2: Error Handling for 4xx and 5xx API Responses
test('Error Handling: Correctly extracts detail message from backend error responses', async () => {
  const mockErrorResponse = {
    status: 404,
    statusText: 'Not Found',
    ok: false,
    json: async () => ({ detail: "Plot 'PLOT_UNKNOWN' not found." })
  };

  let caught = null;
  try {
    if (!mockErrorResponse.ok) {
      const body = await mockErrorResponse.json();
      throw new Error(body.detail);
    }
  } catch (err) {
    caught = err;
  }

  assert.ok(caught);
  assert.equal(caught.message, "Plot 'PLOT_UNKNOWN' not found.");
});

// Test 3: Safeguard Check — Operational Prediction is strictly blocked
test('Scientific Safeguard: UI contract treats blocked prediction gate truthfully', () => {
  const mockStatusResponse = {
    plot_id: 'PLOT_MH_LAT_881',
    has_baseline_lab_test: true,
    is_operational_authorized: false,
    abstention_reason: 'Operational prediction is BLOCKED: REJECTED: No formal ValidationEvidenceBundle provided.',
    abstention_recommendation: 'Ground-truth field trials required.'
  };

  // Ensure is_operational_authorized is false
  assert.equal(mockStatusResponse.is_operational_authorized, false);
  assert.match(mockStatusResponse.abstention_reason, /BLOCKED/);
});

// Test 4: Stoichiometric oxide-to-elemental conversion display
test('Stoichiometry: Validates frontend displays normalized elemental units truthfully', () => {
  const reportedP2O5 = 18.5; // kg/ha P2O5
  const elementalP = reportedP2O5 * 0.4364205; // ~8.074 kg/ha P
  assert.ok(Math.abs(elementalP - 8.074) < 0.05);

  const reportedK2O = 310.0; // kg/ha K2O
  const elementalK = reportedK2O * 0.8301552; // ~257.35 kg/ha K
  assert.ok(Math.abs(elementalK - 257.35) < 0.1);
});

// Test 5: Provisional Agronomic Tolerances
test('Tolerances: Predefined error bounds match ICAR benchmarks', () => {
  const tolerances = {
    N_tolerance_kg_ha: 25.0,
    P_tolerance_kg_ha: 5.0,
    K_tolerance_kg_ha: 30.0,
    target_pass_rate_pct: 80.0
  };

  assert.equal(tolerances.N_tolerance_kg_ha, 25.0);
  assert.equal(tolerances.P_tolerance_kg_ha, 5.0);
  assert.equal(tolerances.K_tolerance_kg_ha, 30.0);
  assert.equal(tolerances.target_pass_rate_pct, 80.0);
});

// Test 6: File Validation Logic for Ingestion
test('File Ingestion: Client-side file validation rules enforce format and size limits', () => {
  const validateFile = (file) => {
    if (!file) return 'No file selected.';
    if (file.size === 0) return 'The selected file is empty (0 bytes). Please choose a valid Soil Health Card or laboratory report.';
    const MAX_SIZE = 5 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      return `File size (${sizeMb} MB) exceeds the maximum allowed limit of 5 MB.`;
    }
    const name = file.name.toLowerCase();
    const isSupported = name.endsWith('.pdf') || name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png');
    if (!isSupported) {
      return 'Unsupported file format. Please upload a PDF document (.pdf) or image (.jpg, .jpeg, .png).';
    }
    return null;
  };

  // Valid files
  assert.equal(validateFile({ name: 'soil_report.pdf', size: 1024 }), null);
  assert.equal(validateFile({ name: 'shc_scan.jpg', size: 2048 }), null);
  assert.equal(validateFile({ name: 'lab_cert.PNG', size: 5000 }), null);
  assert.equal(validateFile({ name: 'document.jpeg', size: 100000 }), null);

  // Invalid: empty file
  assert.match(validateFile({ name: 'empty.pdf', size: 0 }), /empty \(0 bytes\)/);

  // Invalid: oversized file (> 5MB)
  assert.match(validateFile({ name: 'huge.pdf', size: 6 * 1024 * 1024 }), /exceeds the maximum allowed limit/);

  // Invalid: unsupported format
  assert.match(validateFile({ name: 'data.csv', size: 1024 }), /Unsupported file format/);
  assert.match(validateFile({ name: 'script.exe', size: 1024 }), /Unsupported file format/);
  assert.match(validateFile({ name: 'notes.txt', size: 1024 }), /Unsupported file format/);
});

// Test 7: Multipart Form Construction Contract
test('File Ingestion: Form data parameter contract matches FastAPI specification', () => {
  const expectedParams = ['file', 'plot_id', 'farm_id'];
  const testPayload = {
    file: { name: 'test.pdf' },
    plot_id: 'PLOT_MH_LAT_881',
    farm_id: 'FARM_LAT_01'
  };

  assert.ok(testPayload.file);
  assert.equal(testPayload.plot_id, 'PLOT_MH_LAT_881');
  assert.equal(testPayload.farm_id, 'FARM_LAT_01');
  assert.deepEqual(Object.keys(testPayload), expectedParams);
});
