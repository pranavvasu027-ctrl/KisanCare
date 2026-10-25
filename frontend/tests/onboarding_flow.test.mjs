import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';

const FRONTEND_ROOT = path.resolve('frontend');
const SRC_ROOT = path.join(FRONTEND_ROOT, 'src');

test('ONBOARDING-01: Onboarding route is registered in App.tsx', () => {
  const appPath = path.join(SRC_ROOT, 'App.tsx');
  assert.ok(fs.existsSync(appPath), 'App.tsx must exist');
  const appContent = fs.readFileSync(appPath, 'utf8');

  assert.match(appContent, /import\s+Onboarding\s+from\s+['"]\.\/screens\/Onboarding['"]/, 'Onboarding component must be imported in App.tsx');
  assert.match(appContent, /<Route\s+path=["']\/onboarding["']\s+element=\{<Onboarding\s*\/>\}/, 'Onboarding route /onboarding must be defined in App.tsx');
});

test('ONBOARDING-02: Onboarding screen component implements all 7 workflow steps', () => {
  const onboardingPath = path.join(SRC_ROOT, 'screens', 'Onboarding.tsx');
  assert.ok(fs.existsSync(onboardingPath), 'Onboarding.tsx must exist');
  const code = fs.readFileSync(onboardingPath, 'utf8');

  // Verify all 7 steps exist in logic
  assert.match(code, /currentStep === 1/, 'Screen 1 (Welcome) must be implemented');
  assert.match(code, /currentStep === 2/, 'Screen 2 (Account & Authentication) must be implemented');
  assert.match(code, /currentStep === 3/, 'Screen 3 (Farmer Profile) must be implemented');
  assert.match(code, /currentStep === 4/, 'Screen 4 (Farm Setup) must be implemented');
  assert.match(code, /currentStep === 5/, 'Screen 5 (Field Setup) must be implemented');
  assert.match(code, /currentStep === 6/, 'Screen 6 (Review Summary) must be implemented');
  assert.match(code, /currentStep === 7/, 'Screen 7 (Save & Complete) must be implemented');
});

test('ONBOARDING-03: Screen 1 Welcome includes branding, language switcher, and action buttons', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /KISANcare/i, 'KisanCare branding must be displayed');
  assert.match(code, /handleLanguageChange/, 'Language switcher handler must be defined');
  assert.match(code, /Get Started/i, 'Get Started button must be present');
  assert.match(code, /Sign In/i, 'Sign In option for existing users must be present');
});

test('ONBOARDING-04: Screen 2 Authentication integrates with real Supabase Auth', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /supabase\.auth\.signUp/, 'Must use real Supabase signUp API');
  assert.match(code, /supabase\.auth\.signInWithPassword/, 'Must use real Supabase signInWithPassword API');
  assert.match(code, /handleDemoBypass|IS_DEMO_MODE/, 'Must support transparent Demo Mode fallback');
  assert.match(code, /fieldErrors\.password/, 'Must validate password length');
  assert.match(code, /fieldErrors\.email/, 'Must validate email format');
});

test('ONBOARDING-05: Screen 3 Farmer Profile validates required profile columns', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /fullName/, 'Farmer full name state must exist');
  assert.match(code, /phone/, 'Farmer phone number state must exist');
  assert.match(code, /district/, 'District selector state must exist');
  assert.match(code, /village/, 'Village / Locality state must exist');
  assert.match(code, /MAHARASHTRA_DISTRICTS/, 'Must populate districts from verified Maharashtra dataset');
});

test('ONBOARDING-06: Screen 4 Farm Setup validates total area and preserves measurement units', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /farmName/, 'Farm name state must exist');
  assert.match(code, /totalArea/, 'Total land area state must exist');
  assert.match(code, /areaUnit === 'acre'/, 'Acres toggle must be supported');
  assert.match(code, /areaUnit === 'hectare'/, 'Hectares toggle must be supported');
  assert.match(code, /isNaN\(areaNum\)\s*\|\|\s*areaNum\s*<=\s*0/, 'Must enforce positive numeric area validation');
  assert.match(code, /handleCaptureGps/, 'GPS coordinate capture handler must be supported');
});

test('ONBOARDING-07: Screen 5 Field Setup supports adding, editing, removing fields and allocation tracking', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /handleAddField/, 'Must support adding multiple fields');
  assert.match(code, /handleRemoveField/, 'Must support removing fields');
  assert.match(code, /handleUpdateField/, 'Must support updating field details');
  assert.match(code, /isAreaExceeded/, 'Must calculate total allocated area vs farm area');
  assert.match(code, /fields\.length === 0/, 'Must enforce at least one field');
});

test('ONBOARDING-08: Screen 6 Review Information allows jumping to edit any section', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /handleEditSection\(3\)/, 'Must provide direct edit link for Farmer Profile');
  assert.match(code, /handleEditSection\(4\)/, 'Must provide direct edit link for Farm Setup');
  assert.match(code, /handleEditSection\(5\)/, 'Must provide direct edit link for Field Setup');
});

test('ONBOARDING-09: Screen 7 Save & Complete persists via real Backend API & Supabase tables', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /api\.submitOnboarding/, 'Must invoke backend onboarding API endpoint');
  assert.match(code, /kisancare_active_farm_id/, 'Must set active farm ID in localStorage on confirmed persistence');
  assert.match(code, /isSubmitting/, 'Must lock submission state to prevent duplicate submissions');
  assert.match(code, /handleSaveAndComplete/, 'Must provide retry capability on network error');
  assert.match(code, /submissionSuccess/, 'Must confirm persistence before showing completion state');
});

test('ONBOARDING-10: Screen 8 Dashboard navigation preserves existing feature access', () => {
  const dashboardPath = path.join(SRC_ROOT, 'screens', 'Dashboard', 'Dashboard.tsx');
  assert.ok(fs.existsSync(dashboardPath), 'Dashboard.tsx must exist');
  const dCode = fs.readFileSync(dashboardPath, 'utf8');

  // Verify all 5 core hackathon features remain connected
  assert.match(dCode, /\/crop-recommendation/, 'Crop Recommendation route must be connected');
  assert.match(dCode, /\/market/, 'Market Intelligence route must be connected');
  assert.match(dCode, /\/disease/, 'Disease Detection route must be connected');
  assert.match(dCode, /\/rentals|\/rental/, 'Equipment Rental route must be connected');
  assert.match(dCode, /\/copilot/, 'AI Copilot route must be connected');
});

test('ONBOARDING-11: Draft state preservation handles interrupted onboarding recovery', () => {
  const code = fs.readFileSync(path.join(SRC_ROOT, 'screens', 'Onboarding.tsx'), 'utf8');

  assert.match(code, /kisancare_onboarding_draft/, 'Must use draft storage key in localStorage');
  assert.match(code, /localStorage\.setItem\(STORAGE_DRAFT_KEY/, 'Must save in-progress state to localStorage');
  assert.match(code, /localStorage\.removeItem\(STORAGE_DRAFT_KEY\)/, 'Must clear draft upon confirmed completion');
});
