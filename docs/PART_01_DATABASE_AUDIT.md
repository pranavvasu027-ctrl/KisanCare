# KisanCare Part 01 - Database Audit

## 1. Existing Architecture
- Monorepo containing a Python/FastAPI backend and a React/TypeScript frontend.
- ML models (Model 1 Crop Recommendation, Model 6 Cost Profit, etc.) are available as Python artifacts under the `models/` directory.

## 2. Existing Backend
- **Framework**: FastAPI (Python 3)
- **Entry point**: `ml/main.py`
- **Current APIs**: Exposes `/health`, `/api/v1/crop-recommendation/meta`, and `/api/v1/crop-recommendation`.
- Contains ETL, training, and inference scripts in `ml/` and `models/`.

## 3. Existing Frontend
- **Framework**: React 18, TypeScript, Vite, Tailwind CSS (`frontend/`).
- Currently no Supabase client installed in `package.json`.

## 4. Existing Model Structure
- Core prediction pipelines in `ml/crop_recommendation/predict.py`.
- Pickled models and metadata saved in `models/crop_recommendation/`.
- No database integration; prediction API loads artifacts directly.

## 5. Existing Database Situation
- **Current state**: Empty (0 public tables, 0 migrations).
- No database client (like SQLAlchemy, asyncpg, or supabase-py) actively in use for operations in `ml/main.py`.
- Only a dummy `DATABASE_URL` exists in `.env.example`.

## 6. Existing Authentication
- None implemented. The `ml/main.py` endpoints are currently unauthenticated. 

## 7. Existing Supabase Integration
- None. Needs complete setup from scratch including `SUPABASE_URL` environment variables and Supabase DB/Auth architecture.

## 8. Recommended Integration Approach
- Implement version-controlled SQL migrations for Supabase in `supabase/migrations`.
- Use the official Supabase Python client `supabase` in the FastAPI backend to interact with the database.
- Use Supabase Auth for authentication. The frontend should handle Auth directly (via `@supabase/supabase-js`), passing JWT tokens to FastAPI. FastAPI will verify the JWT or use Service Role where appropriate. (For this phase, focus on DB schema and backend endpoints, but prepare the architecture).
- Expose REST endpoints in FastAPI for Farms, Fields, Seasons, and Documents.

## 9. Potential Conflicts
- Ensuring existing unauthenticated ML endpoints (`/api/v1/crop-recommendation`) are preserved as is, without breaking current tests. We will add new endpoints for database operations.
- The `supabase` python client requires `supabase-py` package, which we need to add to `ml/requirements.txt`.
