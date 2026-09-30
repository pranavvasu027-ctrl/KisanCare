# Agent Ownership & Boundaries

The KISANCARE repository is designed for a 3-person (or 3-agent) development model. Strict ownership boundaries ensure minimal conflict.

## PERSON 1: AI/ML & Agricultural Intelligence
**Owns:** `/ml`
- Responsible for all predictive models (crop, yield, disease, pest, risk, price).
- Must expose consistent interfaces defined in `docs/ml-contract.md`.
- **Constraint:** Must not modify frontend code unless explicitly required. Must not redesign backend core schemas without agreement.

## PERSON 2: Backend, Digital Twin & Decision Engine
**Owns:** `/backend`
- Responsible for the core FastAPI backend, Digital Twin state, Economics Engine, and Simulation Engine.
- Integrates ML models and exposes the final unified API to the frontend.
- **Constraint:** Must not redesign the frontend.

## PERSON 3: Frontend, Farmer Experience & AI Copilot
**Owns:** `/frontend`
- Responsible for the React frontend, UI/UX, and AI Copilot interaction.
- Communicates with the backend exclusively through documented API contracts.
- **Constraint:** Must not implement ML logic or complex economic calculations inside the frontend.

## Shared Areas
- `/docs`
- `/tests/integration`
- Root configurations (`docker-compose.yml`, `.env.example`)
- API Contracts (`docs/api-contract.md`)

All cross-module communication must happen through documented contracts!
Never duplicate business logic between frontend and backend.
