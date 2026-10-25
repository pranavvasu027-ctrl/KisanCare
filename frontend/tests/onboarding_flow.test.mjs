import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';

const FRONTEND_ROOT = fs.existsSync(path.resolve('src')) ? path.resolve('.') : path.resolve('frontend');
const SRC_ROOT = path.join(FRONTEND_ROOT, 'src');

test('ONBOARDING-01: Onboarding route is registered in App.tsx', () => {
  const appPath = path.join(SRC_ROOT, 'App.tsx');
  assert.ok(fs.existsSync(appPath), 'App.tsx must exist');
  const appContent = fs.readFileSync(appPath, 'utf8');

  assert.match(appContent, /import\s+Onboarding\s+from\s+['"]\.\/screens\/Onboarding['"]/, 'Onboarding component must be imported in App.tsx');
  assert.match(appContent, /<Route\s+path=["']\/onboarding["']\s+element=\{<Onboarding\s*\/>\}/, 'Onboarding route /onboarding must be defined in App.tsx');
});

test('ONBOARDING-02: Onboarding screen renders OnboardingLoginPortal single-page layout', () => {
  const onboardingPath = path.join(SRC_ROOT, 'screens', 'Onboarding.tsx');
  assert.ok(fs.existsSync(onboardingPath), 'Onboarding.tsx must exist');
  const code = fs.readFileSync(onboardingPath, 'utf8');

  assert.match(code, /OnboardingLoginPortal/, 'Onboarding screen must render OnboardingLoginPortal');
  assert.match(code, /initialMode="onboarding"/, 'Must default to onboarding mode');
});

test('ONBOARDING-03: Single-page portal captures Farmer Profile & language switcher', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  assert.ok(fs.existsSync(portalPath), 'OnboardingLoginPortal.tsx must exist');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /setName/, 'Farmer name state must exist');
  assert.match(code, /setPhone/, 'Farmer phone number state must exist');
  assert.match(code, /handleLanguageChange/, 'Language switcher handler must be defined');
  assert.match(code, /KISAN/i, 'Branding must be present');
});

test('ONBOARDING-04: Single-page portal captures Farm Details (farmName, totalArea)', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /setFarmName/, 'Farm name state must exist');
  assert.match(code, /setTotalArea/, 'Total land area state must exist');
  assert.match(code, /fieldName/, 'Primary field name state must exist');
  assert.match(code, /currentCrop/, 'Current crop state must exist');
});

test('ONBOARDING-05: 1-Click GPS detection captures coordinates & runs agromet weather silently', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /handleDetectGps/, 'GPS detection handler must be implemented');
  assert.match(code, /detectGpsLocation/, 'Must call browser geolocation detection');
  assert.match(code, /triggerSilentPrediction/, 'Must run crop suitability silently with GPS weather');
});

test('ONBOARDING-06: Soil report dropzone supports PDF, JPEG, PNG upload without manual NPK typing', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /handleFileUpload/, 'File upload handler must be implemented');
  assert.match(code, /\.pdf,\s*\.jpg,\s*\.jpeg,\s*\.png/, 'Must accept PDF, JPG, JPEG, and PNG formats');
  assert.match(code, /handleDrop/, 'Must support drag-and-drop file upload');
});

test('ONBOARDING-07: Automatic NPK extraction & Soil Health Card format verification', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /soilIntelligenceApi\.uploadSoilReport/, 'Must integrate with soilIntelligenceApi for report ingestion');
  assert.match(code, /extractedStatus/, 'Must display verified NPK status summary');
});

test('ONBOARDING-08: Crop Intelligence link evaluates sustainable crop based on soil NPK & GPS weather', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /cropResult/, 'Must display Crop Intelligence recommendation result');
  assert.match(code, /evaluateCropSuitability/, 'Must call evaluateCropSuitability engine');
  assert.match(code, /handleSaveAndLaunchDashboard/, 'Must save profile and launch dashboard');
});

test('ONBOARDING-09: FarmerProfileContext manages state persistence & localStorage sync', () => {
  const contextPath = path.join(SRC_ROOT, 'context', 'FarmerProfileContext.tsx');
  assert.ok(fs.existsSync(contextPath), 'FarmerProfileContext.tsx must exist');
  const code = fs.readFileSync(contextPath, 'utf8');

  assert.match(code, /kisancare_farmer_profile/, 'Must use profile storage key in localStorage');
  assert.match(code, /saveCompleteProfile/, 'Must implement complete profile save method');
  assert.match(code, /evaluateCropSuitability/, 'Must evaluate dual-model crop suitability');
});

test('ONBOARDING-10: Dashboard navigation preserves existing feature access', () => {
  const dashboardPath = path.join(SRC_ROOT, 'screens', 'Dashboard', 'Dashboard.tsx');
  assert.ok(fs.existsSync(dashboardPath), 'Dashboard.tsx must exist');
  const dCode = fs.readFileSync(dashboardPath, 'utf8');

  assert.match(dCode, /\/crop-recommendation/, 'Crop Recommendation route must be connected');
  assert.match(dCode, /\/market/, 'Market Intelligence route must be connected');
  assert.match(dCode, /\/disease/, 'Disease Detection route must be connected');
  assert.match(dCode, /\/rentals|\/rental/, 'Equipment Rental route must be connected');
  assert.match(dCode, /\/copilot/, 'AI Copilot route must be connected');
});

test('ONBOARDING-11: Returning farmer sign in & Instant Demo Mode support', () => {
  const portalPath = path.join(SRC_ROOT, 'screens', 'Onboarding', 'OnboardingLoginPortal.tsx');
  const code = fs.readFileSync(portalPath, 'utf8');

  assert.match(code, /handleLoginSubmit/, 'Must handle returning farmer login');
  assert.match(code, /handleQuickDemoAccess/, 'Must provide Instant Demo Mode shortcut');
  assert.match(code, /supabase\.auth\.signInWithPassword/, 'Must support Supabase credentials authentication');
});
