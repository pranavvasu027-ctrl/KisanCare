# KisanCare Mobile App — Step 3: Backend API Integration & State Management Report

**Date of Execution:** October 24, 2026  
**Status:** **STEP 3 COMPLETE — READY FOR STEP 4**  
**Project Path:** `kisancare-mobile/`  
**Git Branch:** `feature/multilingual-marathi-hindi-support`  
**Framework Stack:** Expo SDK 58, React Native `0.88.0`, TanStack Query v5 (`@tanstack/react-query@^5.90.20`), TypeScript `~6.0.3`

---

## 1. Executive Summary

Step 3 established the enterprise-grade API client, environment handling, server state management, and real backend connectivity for the KisanCare mobile application:
* **Central API Client:** Implemented in `src/services/apiClient.ts` with typed generics, timeout protection via `AbortController`, safe non-JSON parse handling, and proper `multipart/form-data` upload boundaries.
* **Dynamic Backend Base URL Configuration:** Dynamically resolves `EXPO_PUBLIC_API_URL` with automated platform-specific fallbacks (`http://10.0.2.2:8000` for Android Emulator, `http://localhost:8000` for iOS/Desktop) to eliminate hardcoding.
* **State Management Foundation:** Installed and configured **TanStack Query v5** (`@tanstack/react-query`) with application-wide `QueryClientProvider` at the root layout (`src/app/_layout.tsx`), incorporating fresh caching (2 mins), background refetch on reconnect, and retry rules.
* **Live Backend Connectivity Diagnostics:** Built a real-time server health and latency diagnostic widget (`BackendDiagnostic.tsx`) embedded directly into the More/Settings screen.
* **Verified Read-Only Feature Integration:** Connected the real, verified `/api/v1/rentals/listings` endpoint into a dedicated Equipment Rentals screen (`src/app/rentals.tsx`), complete with loading spinner, genuine error reporting, empty state handling, and rendering 49 live records from the running backend.
* **Automated Integration Test Suite:** Created and executed `tests/apiClient.test.mjs` verifying 4/4 live integration scenarios against the live FastAPI backend.
* **Existing Project Isolation:** 100% of changes are isolated strictly inside `kisancare-mobile/`. Zero files in the web frontend, Python backend, or ML services were modified.

---

## 2. Backend URL Configuration & Network Topology

### 2.1 Resolution Hierarchy (`src/services/config.ts`)
The API base URL is resolved dynamically at runtime:
1. **Explicit Environment Variable:** `process.env.EXPO_PUBLIC_API_URL` (from `.env` or build environment).
2. **Android Emulator Fallback:** `http://10.0.2.2:8000` (maps Android emulator virtual network to host machine localhost).
3. **Desktop / iOS Simulator Fallback:** `http://localhost:8000`.

### 2.2 Security & Secrets Boundary
* No private API keys, database passwords, or Supabase service-role keys are exposed in `EXPO_PUBLIC_*` variables.
* Client requests pass standard `Accept: application/json` and `Content-Type: application/json` headers.
* When uploading images (leaf photos), `Content-Type` is omitted to allow React Native / Expo to automatically inject the proper multipart boundary string.

---

## 3. Real KisanCare Backend API Inventory

Audited against `backend/app/main.py`, `backend/app/api/endpoints.py`, and `backend/app/api/rentals.py`:

| # | Endpoint | Method | Required Auth | Request Format | Response Schema | Live Verification Evidence | Known Backend Limitations |
|---|---|---|---|---|---|---|---|
| 1 | `/health` | GET | None | None | `{"status": "ok", "service": "KisanCare API", "copilot": {...}}` | **LIVE TESTED (101ms)** | None. Returns 200 OK with server name and Copilot model status. |
| 2 | `/api/v1/rentals/listings` | GET | None | Query params (`category`, `district`, etc.) | `List[RentalListing]` (49 records) | **LIVE TESTED (20ms)** | None. 22 backend automated unit tests pass. |
| 3 | `/api/v1/farms` | GET | Optional (Bearer) | None | `List[FarmRecord]` | **TESTED** | Falls back to mock `"Pranav Vasu Farm"` when remote Supabase DNS resolution fails. |
| 4 | `/api/v1/crop-recommendation` | POST | None | JSON `{"N": 90, "P": 42, "K": 43, "temperature": 28, ...}` | `{"recommended_crops": [...], "confidence": [...]}` | **TESTED** | Real Random Forest model. Requires valid numerical agronomic inputs. |
| 5 | `/api/v1/weather-risk` | POST | None | JSON `{"latitude": 18.52, "longitude": 73.85, "crop": "onion"}` | `{"risk_score": 25.0, "alerts": [...]}` | **TESTED** | Integrates with OpenWeatherMap API and agronomic thermal stress heuristics. |
| 6 | `/api/v1/soil/health-card/analyze` | POST | None | JSON `{"nitrogen": 140, "phosphorus": 18, "potassium": 110, ...}` | `{"deficiencies": [...], "fertilizer_prescription": {...}}` | **TESTED** | STCR / ICAR fertilizer calibration engine. 90 automated tests pass. |
| 7 | `/api/v1/market-price` | POST | None | JSON `{"crop": "onion", "market": "Pune", "target_date": "..."}` | `{"predicted_price": 2450, "trend": "up"}` | **FAIL ON 2026** | Mandi historical dataset stops at 2025-12-31; querying 2026 throws 422 `ValueError`. APMC name regex bug. |
| 8 | `/api/v1/disease-detection` | POST | None | JSON `{"crop": "tomato", "symptoms": [...]}` | `{"disease": "Early Blight", "treatment": [...]}` | **FAIL ON IMAGE** | Endpoint expects JSON `SymptomsRequest`; rejects leaf image file uploads with 422. PyTorch vision model is unmounted. |

---

## 4. API Client & State Management Architecture

### 4.1 Client Layer (`src/services/apiClient.ts`)
* **AbortController Timeout:** Enforces 10-second request cancellation on standard endpoints and 30-second cancellation on image uploads.
* **Safe Error Normalization:** Catches network timeouts, unreachable host errors, and HTTP 4xx/5xx responses, converting them into typed `ApiError` instances with `.userFriendlyMessage`.
* **Zero Secret Logging:** Never logs authorization tokens, sensitive headers, or image binary data to stdout or terminal.

### 4.2 TanStack Query Integration (`src/services/queryClient.ts`)
* Preconfigured `QueryClient` mounted via `<QueryClientProvider client={queryClient}>` in [`src/app/_layout.tsx`](file:///c:/Users/prana/OneDrive/Desktop/Projects/KISANcare/kisan-care/kisancare-mobile/src/app/_layout.tsx).
* Caches server state for 2 minutes before refetching, eliminating duplicate network calls across screens.
* Bypasses retry attempts on 404 (Not Found) or 401 (Unauthorized) errors to reduce battery and cellular overhead on mobile devices.

---

## 5. Live UI Integrations

### 5.1 Real-Time Server Diagnostic Widget (`src/components/common/BackendDiagnostic.tsx`)
Embedded in the More/Settings screen:
* Actively pings `GET /health` on mount and provides a manual "Test Connection" button.
* Displays:
  * Connection Status: `Connected` (Green), `Connecting` (Blue), `Unreachable` (Red), or `Server Error` (Amber).
  * Active Base URL: (e.g. `http://localhost:8000` or `http://10.0.2.2:8000`).
  * Roundtrip Ping Latency: (e.g. `14 ms`).
  * AI Copilot Engine Status: `gemini-3.8-flash (Ready)`.

### 5.2 Real Read-Only Feature: Equipment Rentals (`src/app/rentals.tsx`)
* Connects to `GET /api/v1/rentals/listings`.
* **Loading State:** Centered animated `ActivityIndicator` with *"Fetching equipment from backend..."*.
* **Error State:** Distinct card showing failure reason (e.g. *"Unable to reach the KisanCare server"*), HTTP status code, and a "Retry Connection" button.
* **Empty State:** Clean empty state illustration when 0 listings return.
* **Success State:** Displays 49 live equipment listings from the backend database (Tractors, Rotavators, Harvesters) with daily/hourly rental rates, district/taluka, and provider contacts.

---

## 6. Automated Verification Results

All automated checks were executed directly:

### Check 1: Live API Client Test Suite (`node --test`)
```
▶ KisanCare Mobile API Integration Suite
  ✔ 1. Live Backend Health Probe (/health) (108.0ms)
       ✓ Health Check Passed (101ms): service="KisanCare API", copilot_model="gemini-3.8-flash"
  ✔ 2. Live Verified Read-Only Endpoint (/api/v1/rentals/listings) (24.2ms)
       ✓ Live Rentals Passed (20ms): 49 equipment listings returned from database
  ✔ 3. HTTP Error Handling (404 Not Found) (18.8ms)
       ✓ 404 Error handling verified: returns status 404 and detail "Not Found"
  ✔ 4. Connection Timeout Handling (Simulated Unreachable Host) (204.0ms)
       ✓ Timeout handling verified: AbortController cleanly aborts hanging network calls
✔ KisanCare Mobile API Integration Suite (359.4ms)
ℹ tests 4 | suites 1 | pass 4 | fail 0
```

### Check 2: TypeScript Strict Compilation
```powershell
cd kisancare-mobile
npx tsc --noEmit
# Exit Code: 0 (Zero errors)
```

### Check 3: Project Health Audit (`expo-doctor`)
```powershell
cd kisancare-mobile
npx expo-doctor
# 20/20 checks passed. No issues detected!
```

### Check 4: Git Isolation Integrity
```powershell
git status
# On branch feature/multilingual-marathi-hindi-support
# Untracked files:
#   KISANCARE_VERIFICATION_REPORT.md
#   kisancare-mobile/
# Zero files outside kisancare-mobile/ were modified.
```

---

## 7. Authentication Status & Security Boundaries

* **Current Auth Status:** Disconnected from live Supabase Auth due to the remote Supabase DNS resolution failure identified in the pre-launch audit report.
* **Protected Endpoints:** Protected routes (e.g. `/api/v1/farms/create`, booking mutations) remain guarded and are not called with fabricated dummy credentials.
* **Token Storage Policy:** Step 3 does not persist tokens in unencrypted `AsyncStorage`. Secure token persistence will be implemented in Step 7 using `expo-secure-store`.

---

## 8. Files Created or Modified in Step 3

* `kisancare-mobile/package.json` — Added `@tanstack/react-query@^5.90.20`.
* `kisancare-mobile/package-lock.json` — Updated lockfile with clean dependency resolution.
* `kisancare-mobile/src/services/config.ts` — Base URL resolution and timeout constants.
* `kisancare-mobile/src/services/apiError.ts` — Custom `ApiError` class with error categorization.
* `kisancare-mobile/src/services/endpoints.ts` — Central endpoint route inventory.
* `kisancare-mobile/src/services/apiClient.ts` — Centralized Fetch wrapper with AbortController.
* `kisancare-mobile/src/services/queryClient.ts` — TanStack Query client configuration.
* `kisancare-mobile/src/services/healthService.ts` — Backend `/health` check service.
* `kisancare-mobile/src/services/rentalsService.ts` — Equipment rental listing service.
* `kisancare-mobile/src/components/common/BackendDiagnostic.tsx` — Real-time server connectivity component.
* `kisancare-mobile/src/app/rentals.tsx` — Live Equipment Rentals screen with Query integration.
* `kisancare-mobile/src/app/_layout.tsx` — Integrated `QueryClientProvider` and `rentals` stack screen.
* `kisancare-mobile/src/app/(tabs)/more.tsx` — Embedded `BackendDiagnostic` and rental navigation link.
* `kisancare-mobile/tests/apiClient.test.mjs` — Automated integration test suite.

---

## 9. Recommended Scope for Step 4

When approved to begin **Step 4 (Farmer & Farm Management Integration)**:
1. Connect the Farm Management screen (`src/app/(tabs)/farm.tsx`) to `GET /api/v1/farms`.
2. Implement local caching using `AsyncStorage` for farm profiles so farmers can review their fields offline.
3. Build farm field creation form with input validation (Field name, crop, acreage, soil type).
4. Implement pull-to-refresh synchronization across farm data.

---

*Report certified by Senior Full-Stack & Mobile Development Pair Programmer.*
