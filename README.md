# KISANCARE - AI-Powered Farm Digital Twin

KisanCare is an AI-powered Farm Digital Twin and Farm Decision Intelligence platform.

## Architecture

OBSERVE → PREDICT → SIMULATE → COMPARE → DECIDE → LEARN

- **Frontend**: React, Vite, Tailwind CSS (Farmer Experience)
- **Backend**: FastAPI, PostgreSQL, PostGIS (Decision Engine, Digital Twin)
- **ML Services**: Python, scikit-learn (Agricultural Intelligence)

## Repository Structure

- `/frontend` - Owned by PERSON 3. React UI.
- `/backend` - Owned by PERSON 2. FastAPI backend, Decision Engine, Economics, Simulation.
- `/ml` - Owned by PERSON 1. Python ML modules for crop, yield, risk, etc.
- `/docs` - Shared documentation.
- `/data` - Sample datasets.
- `/tests` - Integration tests.

## How to run locally

1. Copy `.env.example` to `.env`.
2. Run `docker-compose up --build`.
3. The frontend will be available at `http://localhost:5173`.
4. The backend API will be available at `http://localhost:8000`.
5. The ML API will be available at `http://localhost:8001`.

## Development Model
See `docs/agent-ownership.md` for details on how the 3 developers work independently.
See `docs/api-contract.md` for cross-module communication rules.
