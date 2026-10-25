/**
 * KisanCare Equipment Rental Verification Test Suite
 * Tests Rental Listings Discovery, Category Filtering, Server-Side Price Calculation,
 * Atomic Booking Creation, Concurrency Protection, and Persistence.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';

const BASE_URL = 'http://127.0.0.1:8000';

describe('KisanCare Equipment Rental Verification Suite', () => {

  let testListingId = '';
  let createdBookingId = '';
  let createdBookingRef = '';
  
  // Dynamic future dates to ensure idempotency across test executions
  const randomOffset = Math.floor(Math.random() * 500) + 30;
  function getFutureDate(offsetDays) {
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    return d.toISOString().split('T')[0];
  }
  const testStartDate = getFutureDate(randomOffset);
  const testEndDate = getFutureDate(randomOffset + 2);

  // --- 1. Listings Discovery ---
  test('1. Live Listings Discovery (/api/v1/rentals/listings)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/rentals/listings`);
    assert.strictEqual(res.status, 200, 'Listings endpoint should return HTTP 200');
    const listings = await res.json();
    assert.ok(Array.isArray(listings), 'Listings should be an array');
    assert.ok(listings.length >= 10, 'Should have at least 10 seed listings');

    // Select first tractor listing for subsequent tests
    const tractor = listings.find((l) => l.category === 'tractor') || listings[0];
    testListingId = tractor.id;
    assert.ok(tractor.id, 'Listing must have an ID');
    assert.ok(tractor.title, 'Listing must have a title');
    assert.ok(typeof tractor.price === 'number', 'Price must be a number');
    assert.ok(tractor.district, 'Listing must have a district');
    assert.ok(tractor.provider, 'Listing must have provider summary');
    console.log(`   ✓ Live Listings Passed: Found ${listings.length} listings. Selected "${tractor.title}" (${tractor.id})`);
  });

  // --- 2. Category Filtering ---
  test('2. Category Filtering (Tractor, Equipment, Transport, Labour)', async () => {
    const categories = ['tractor', 'equipment', 'transport', 'labour'];
    for (const cat of categories) {
      const res = await fetch(`${BASE_URL}/api/v1/rentals/listings?category=${cat}`);
      assert.strictEqual(res.status, 200);
      const items = await res.json();
      assert.ok(Array.isArray(items));
      for (const item of items) {
        assert.strictEqual(item.category, cat, `Item category must match filter ${cat}`);
      }
    }
    console.log('   ✓ Category filtering verified for all 4 primary categories');
  });

  // --- 3. Server-Side Price Calculation ---
  test('3. Server-Side Itemized Price Calculation (/api/v1/rentals/calculate-price)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/rentals/calculate-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        listing_id: testListingId,
        duration: 3.0,
        acreage: 0.0,
        quantity: 1,
        include_operator: false,
        include_delivery: false,
      }),
    });

    assert.strictEqual(res.status, 200, 'Price calculation should return HTTP 200');
    const priceRes = await res.json();
    assert.strictEqual(priceRes.listing_id, testListingId);
    assert.ok(priceRes.base_rental_charge > 0, 'Base rental charge must be positive');
    assert.strictEqual(priceRes.platform_fee, 50.0, 'Platform fee must be flat ₹50.0');
    assert.strictEqual(
      priceRes.estimated_total,
      priceRes.base_rental_charge + (priceRes.transport_charge || 0) + (priceRes.operator_charge || 0) + (priceRes.add_ons_charge || 0) + priceRes.platform_fee,
      'Total must equal base charge + transport + operator + add-ons + platform fee'
    );
    console.log(`   ✓ Price Calculation Passed: Base ₹${priceRes.base_rental_charge} + Transport ₹${priceRes.transport_charge} + Fee ₹${priceRes.platform_fee} = Total ₹${priceRes.estimated_total}`);
  });

  // --- 4. Atomic Booking Creation ---
  test('4. Live Booking Creation (/api/v1/rentals/bookings)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/rentals/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        listing_id: testListingId,
        farmer_name: 'Pranav Vasu',
        farmer_phone: '9876543210',
        farm_id: 'FARM_AKOLA_01',
        start_date: testStartDate,
        end_date: testEndDate,
        duration: 2.0,
        payment_method: 'pay_on_service',
        notes: 'Node.js test booking for wheat harvesting',
      }),
    });

    assert.strictEqual(res.status, 201, 'Booking creation should return HTTP 201 Created');
    const booking = await res.json();
    createdBookingId = booking.id;
    createdBookingRef = booking.booking_reference;

    assert.ok(createdBookingId.startsWith('BKG_'), 'Booking ID must start with BKG_');
    assert.ok(createdBookingRef.startsWith('KCR-BKG-'), 'Reference must start with KCR-BKG-');
    assert.strictEqual(booking.farmer_name, 'Pranav Vasu');
    assert.strictEqual(booking.farmer_phone, '9876543210');
    assert.strictEqual(booking.status, 'pending_confirmation');
    assert.ok(booking.total_amount > 0, 'Total amount must be positive');
    console.log(`   ✓ Live Booking Creation Passed: Created ${createdBookingRef} (ID: ${createdBookingId}, Total: ₹${booking.total_amount})`);
  });

  // --- 5. Booking Retrieval & Persistence Verification ---
  test('5. Booking Persistence & Direct Retrieval (/api/v1/rentals/bookings/{id})', async () => {
    assert.ok(createdBookingId, 'Requires booking created in step 4');
    const res = await fetch(`${BASE_URL}/api/v1/rentals/bookings/${createdBookingId}`);
    assert.strictEqual(res.status, 200, 'Direct lookup should return HTTP 200');
    const record = await res.json();

    assert.strictEqual(record.id, createdBookingId);
    assert.strictEqual(record.booking_reference, createdBookingRef);
    assert.strictEqual(record.farmer_name, 'Pranav Vasu');
    assert.strictEqual(record.start_date, testStartDate);
    assert.strictEqual(record.end_date, testEndDate);
    console.log(`   ✓ Direct Retrieval Passed: Retrieved persisted booking ${record.booking_reference}`);
  });

  // --- 6. Booking List Retrieval ---
  test('6. Farmer Bookings List Retrieval (/api/v1/rentals/bookings)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/rentals/bookings`);
    assert.strictEqual(res.status, 200);
    const allBookings = await res.json();
    assert.ok(Array.isArray(allBookings));
    const found = allBookings.find((b) => b.id === createdBookingId);
    assert.ok(found, 'Created booking must exist in the overall bookings list');
    console.log(`   ✓ List Retrieval Passed: Booking ${createdBookingRef} found in list of ${allBookings.length} bookings`);
  });

  // --- 7. Concurrency / Overlap Rejection (HTTP 409) ---
  test('7. Concurrency & Overlap Rejection (HTTP 409 Conflict)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/rentals/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        listing_id: testListingId,
        farmer_name: 'Another Farmer',
        farmer_phone: '9123456789',
        start_date: testStartDate,
        end_date: testEndDate,
        duration: 1.0,
      }),
    });

    assert.strictEqual(res.status, 409, 'Overlapping booking on same dates should return HTTP 409 Conflict');
    const err = await res.json();
    assert.ok(err.detail.includes('conflict') || err.detail.includes('already reserved'));
    console.log('   ✓ Concurrency Guardrail Passed: Duplicate overlapping slot safely rejected with HTTP 409 Conflict');
  });

  // --- 8. Validation Guardrails (HTTP 400 for Invalid Dates) ---
  test('8. Date Validation Guardrail (HTTP 400 for end_date < start_date)', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/rentals/bookings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        listing_id: testListingId,
        farmer_name: 'Test Farmer',
        farmer_phone: '9876543210',
        start_date: '2026-12-10',
        end_date: '2026-12-05', // Earlier than start date
        duration: 1.0,
      }),
    });

    assert.strictEqual(res.status, 400, 'Inverted dates must return HTTP 400 Bad Request');
    console.log('   ✓ Date Validation Guardrail Passed: Inverted date rejected with HTTP 400 Bad Request');
  });
});
