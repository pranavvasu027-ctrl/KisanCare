# Development Workflow

## Getting Started

1. Clone the repository.
2. Initialize environment variables from `.env.example`.
3. Start the system: `docker-compose up --build`.

## Agent / Developer Boundaries

See `agent-ownership.md` for specific folder permissions.

### Cross-Agent Communication
If PERSON 3 (Frontend) needs a new API, they must propose it in `api-contract.md`.
PERSON 2 (Backend) will then implement the mock endpoint immediately, allowing PERSON 3 to continue working.
Once PERSON 2 finishes the real implementation, the system integrates seamlessly.

### Testing
- Run backend tests: `cd backend && pytest`
- Run ML tests: `cd ml && pytest`

## Mocking and MVP
Do NOT build deep functionality at the beginning.
1. Build vertical slices (API -> Logic -> Mock -> UI).
2. Wire it up.
3. Replace mocks with actual models/business logic iteratively.
