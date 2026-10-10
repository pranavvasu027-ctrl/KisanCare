# KISANcare Supabase & Security Audit

## Environment Verification
* Frontend relies on `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
* Backend (seeds, etc.) relies on `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
* **Security Check**: Verified that no secrets are hardcoded in the frontend bundles. `frontend/src/services/supabase.ts` strictly uses `import.meta.env` with placeholders. The service-role key is NOT exposed to the frontend.

## Schema & Migration Consistency
* **Profiles Table**: Defined in `001_initial_kisancare_schema.sql` with a unique `user_id` mapped to `auth.users`.
* **Roles**: Correctly introduced via `002_add_roles.sql` (`ALTER TABLE profiles ADD COLUMN role TEXT DEFAULT 'farmer'`).

## Authorization & RLS
* **Registration/Login**: Implemented in frontend `useAuth.tsx`.
* **Row Level Security (RLS)**: Present in `001_initial_kisancare_schema.sql`. Policies enforce that farmers can only view their own records (`auth.uid() = user_id`).
* **Backend Authorization**: Currently, the FastAPI endpoints (like `/farms`) lack strict JWT validation in the middleware to enforce server-side authorization. **This is a gap.** The backend proxies requests without extracting and validating the Supabase JWT.

## Testing Status
* **BLOCKED**: End-to-end auth testing (registration, session persistence) cannot be executed because actual Supabase credentials are not provided in the environment.

## Required Setup for Live Testing
1. Spin up a Supabase project (local or cloud).
2. Apply migrations `001` and `002`.
3. Populate `.env` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
4. Run frontend tests.
