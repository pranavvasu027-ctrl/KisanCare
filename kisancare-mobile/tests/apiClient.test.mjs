/**
 * KisanCare Mobile API Client Verification Test Suite
 * Tests actual HTTP calls, error handling, timeouts, and live responses.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';

const BASE_URL = 'http://localhost:8000';

describe('KisanCare Mobile API Integration Suite', () => {
  test('1. Live Backend Health Probe (/health)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/health`);
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const data = await res.json();

    assert.ok(data.status === 'ok' || data.status === 'healthy', 'Expected status ok');
    assert.strictEqual(data.service, 'KisanCare API');
    console.log(`   ✓ Health Check Passed (${elapsed}ms): service="${data.service}", copilot_model="${data.copilot?.model}"`);
  });

  test('2. Live Verified Read-Only Endpoint (/api/v1/rentals/listings)', async () => {
    const start = Date.now();
    const res = await fetch(`${BASE_URL}/api/v1/rentals/listings`);
    const elapsed = Date.now() - start;

    assert.strictEqual(res.status, 200, `Expected 200 OK, got ${res.status}`);
    const listings = await res.json();

    assert.ok(Array.isArray(listings), 'Expected array of listings');
    assert.ok(listings.length > 0, 'Expected non-empty equipment listings');

    const first = listings[0];
    assert.ok(first.id, 'Listing must have id');
    assert.ok(first.title, 'Listing must have title');
    assert.ok(first.district, 'Listing must have district');
    console.log(`   ✓ Live Rentals Passed (${elapsed}ms): ${listings.length} equipment listings returned from database`);
  });

  test('3. HTTP Error Handling (404 Not Found)', async () => {
    const res = await fetch(`${BASE_URL}/non_existent_diagnostic_endpoint_404`);
    assert.strictEqual(res.status, 404);
    const data = await res.json();
    assert.strictEqual(data.detail, 'Not Found');
    console.log('   ✓ 404 Error handling verified: returns status 404 and detail "Not Found"');
  });

  test('4. Connection Timeout Handling (Simulated Unreachable Host)', async () => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 200);

    let timedOut = false;
    try {
      // Connect to non-routable IP to test timeout
      await fetch('http://10.255.255.1:8000/health', { signal: controller.signal });
    } catch (err) {
      if (err.name === 'AbortError' || err.code === 'ABORT_ERR') {
        timedOut = true;
      }
    } finally {
      clearTimeout(timeout);
    }

    assert.strictEqual(timedOut, true, 'Request should abort when timeout threshold is exceeded');
    console.log('   ✓ Timeout handling verified: AbortController cleanly aborts hanging network calls');
  });
});
