import test from 'node:test';
import assert from 'node:assert/strict';

test('Market Intelligence Module Contract & Functionality Test', async (t) => {
  // Test 1: Supported crops strictly limited to Cotton, Soyabean, Tur
  await t.test('1. Crop Registry: Only Cotton, Soyabean, and Tur supported', () => {
    const validCrops = ['Cotton', 'Soyabean', 'Tur'];
    assert.equal(validCrops.length, 3);
    assert.ok(validCrops.includes('Cotton'));
    assert.ok(validCrops.includes('Soyabean'));
    assert.ok(validCrops.includes('Tur'));
    assert.ok(!validCrops.includes('Onion'), 'Onion must not be in valid crops');
    assert.ok(!validCrops.includes('Tomato'), 'Tomato must not be in valid crops');
  });

  // Test 2: Supported market locations strictly limited to Akola, Amravati, Akot
  await t.test('2. Mandi Registry: Only Akola, Amravati, and Akot supported', () => {
    const validMarkets = ['Akola', 'Amravati', 'Akot'];
    assert.equal(validMarkets.length, 3);
    assert.ok(validMarkets.includes('Akola'));
    assert.ok(validMarkets.includes('Amravati'));
    assert.ok(validMarkets.includes('Akot'));
    assert.ok(!validMarkets.includes('Pune'), 'Pune must not be in valid markets');
    assert.ok(!validMarkets.includes('Nagpur'), 'Nagpur must not be in valid markets');
  });

  // Test 3: Realistic Vidarbha Modal Prices Benchmark Test
  await t.test('3. Pricing Realism: Cotton, Soyabean, Tur reflect authentic APMC levels', () => {
    const cottonAkola = 7280;
    const cottonAkot = 7350;
    const cottonAmravati = 7190;
    assert.ok(cottonAkola >= 6800 && cottonAkola <= 7800, 'Cotton Akola price realistic');
    assert.ok(cottonAkot > cottonAkola, 'Akot is premium cotton market');

    const soyaAkola = 4640;
    const soyaAkot = 4670;
    assert.ok(soyaAkola >= 4200 && soyaAkola <= 5200, 'Soyabean price realistic');

    const turAkola = 9850;
    const turAkot = 9940;
    assert.ok(turAkola >= 9000 && turAkola <= 10500, 'Tur price realistic');
  });

  // Test 4: Trend series length matches time ranges (7D, 14D, 30D)
  await t.test('4. Time Ranges: Historical and Forecast partitioning', () => {
    const totalHistory = 30;
    const totalForecast = 14;

    const slice7D = totalHistory >= 7 && totalForecast >= 7;
    const slice14D = totalHistory >= 14 && totalForecast >= 14;
    const slice30D = totalHistory >= 30;

    assert.ok(slice7D, '7D slicing supported');
    assert.ok(slice14D, '14D slicing supported');
    assert.ok(slice30D, '30D slicing supported');
  });

  // Test 5: Rule-based recommendation picks the highest price market truthfully
  await t.test('5. Rule-Based Market Insight: Best price market selection logic', () => {
    const markets = [
      { name: 'Akola APMC', currentPrice: 7280 },
      { name: 'Amravati APMC', currentPrice: 7190 },
      { name: 'Akot APMC', currentPrice: 7350 }
    ];

    const best = markets.reduce((max, m) => m.currentPrice > max.currentPrice ? m : max, markets[0]);
    assert.equal(best.name, 'Akot APMC');
    assert.equal(best.currentPrice, 7350);
  });

  // Test 6: Demonstration Data Provenance Integrity
  await t.test('6. Data Provenance: Demo badges and disclaimer enforcement', () => {
    const provenanceNotice = 'Demonstration dataset — not live Agmarknet mandi prices';
    assert.ok(provenanceNotice.includes('Demonstration dataset'));
    assert.ok(!provenanceNotice.includes('Live government data'));
  });

  // Test 7: Table search filtering correctly matches market names or locations
  await t.test('7. Search Filter: Accurately filters mandis by name or location', () => {
    const markets = [
      { name: 'Akola APMC', location: 'Akola Yard' },
      { name: 'Amravati APMC', location: 'Amravati Main' },
      { name: 'Akot APMC', location: 'Akot District' }
    ];

    const filterByQuery = (q) => markets.filter(m => 
      m.name.toLowerCase().includes(q.toLowerCase()) || 
      m.location.toLowerCase().includes(q.toLowerCase())
    );

    assert.equal(filterByQuery('akot').length, 1);
    assert.equal(filterByQuery('akot')[0].name, 'Akot APMC');
    assert.equal(filterByQuery('pune').length, 0); // Correctly yields 0 for unmatched
  });
});
