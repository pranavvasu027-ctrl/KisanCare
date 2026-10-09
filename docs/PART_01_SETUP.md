# KisanCare Part 01 - Database Setup Instructions

## 1. Environment Configuration
1. Create a `.env` file in the root directory (copy from `.env.example`).
2. Obtain your project credentials from the Supabase Dashboard -> Settings -> API.
3. Add the following variables to `.env`:
   ```env
   SUPABASE_URL=https://fqsqgggknbokrtiarrid.supabase.co
   SUPABASE_ANON_KEY=<your_anon_key>
   SUPABASE_SERVICE_ROLE_KEY=<your_service_role_key>
   ```
*(Do not commit this file to Git. It is already excluded in `.gitignore`)*

## 2. Running Migrations on Remote Supabase
To apply the database schema to your Supabase project (KisanCare - `fqsqgggknbokrtiarrid`):

1. Install Supabase CLI locally if you haven't (or use npx):
   ```bash
   npm i -g supabase
   ```
2. Login to Supabase CLI:
   ```bash
   npx supabase login
   ```
3. Link your project:
   ```bash
   npx supabase link --project-ref fqsqgggknbokrtiarrid
   ```
   *(Enter your database password when prompted)*
4. Push the migrations:
   ```bash
   npx supabase db push
   ```

## 3. Backend Integration Setup
1. Ensure your virtual environment is active.
2. Install updated dependencies:
   ```bash
   pip install -r ml/requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn ml.main:app --reload --port 8001
   ```

## 4. Running the Database Tests
Once your `.env` is configured and migrations are applied, run the comprehensive database tests:
```bash
pytest tests/test_database.py -v
```
