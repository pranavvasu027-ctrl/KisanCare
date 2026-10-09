# KisanCare Part 01 - Database Schema

## Overview
This schema uses Supabase PostgreSQL. It acts as the central source of truth for the KisanCare ecosystem, isolating data per farmer via Row Level Security (RLS) and supporting provenance tracking and historical preservation.

## Tables and Architecture

### 1. `profiles`
Stores farmer profiles connected to Supabase Auth.
- **Columns**: `id` (UUID, PK), `user_id` (UUID, FK auth.users), `name` (TEXT), `phone` (TEXT), `preferred_language` (TEXT), `created_at`, `updated_at`.
- **Relationships**: One-to-One with `auth.users`.
- **RLS**: Users can only select/insert/update their own profile.

### 2. `farms`
A farmer can own multiple farms.
- **Columns**: `id` (UUID, PK), `user_id` (UUID, FK auth.users), `farm_name` (TEXT), `description` (TEXT), `location` (TEXT), `latitude`, `longitude`, `total_area`, `area_unit`, `status`, `created_at`, `updated_at`.
- **Relationships**: Belongs to `auth.users`.
- **RLS**: Users can access only their own farms.

### 3. `fields`
Each field belongs to one farm.
- **Columns**: `id` (UUID, PK), `farm_id` (UUID, FK farms.id), `field_name` (TEXT), `area`, `area_unit`, `latitude`, `longitude`, `boundary` (JSONB), `status`, `created_at`, `updated_at`.
- **Relationships**: Belongs to `farms`.
- **RLS**: Access propagates from `farms`.

### 4. `seasons`
Each season belongs to a field. Historical seasons are preserved.
- **Columns**: `id` (UUID, PK), `field_id` (UUID, FK fields.id), `season_name`, `crop`, `crop_variety`, `sowing_date`, `expected_harvest_date`, `actual_harvest_date`, `crop_stage`, `previous_crop`, `status`, `created_at`, `updated_at`.
- **Relationships**: Belongs to `fields`.
- **RLS**: Access propagates from `fields`.

### 5. Data Records
- **`crop_records`**: Observations for a specific season.
- **`soil_records`**: NPK/pH readings linked to a field (and optionally season).
- **`irrigation_records`**: Watering records.
- **`weather_records`**: Climatological data for the field.
- **`farm_data_records`**: Flexible JSONB table for generic observations.
- *All data records support `provenance` (MEASURED, ESTIMATED, FARMER_ENTERED, AUTOMATICALLY_COLLECTED, EXTRACTED).*

### 6. `documents`
Metadata for files stored in Supabase Storage bucket `farmer_documents`.
- **Columns**: `id` (UUID, PK), `user_id`, `farm_id`, `field_id`, `season_id`, `file_name`, `file_type`, `storage_path`, `category`, `provenance`, `upload_timestamp`, `extraction_status`, `metadata`.
- **RLS**: Users can access only their own documents.

### 7. Intelligence & Digital Twin
- **`model_versions`**: Registry of ML artifacts.
- **`model_predictions`**: Historical log of all predictions made for fields/seasons.
- **`recommendations`**: Stored outputs from the Decision Engine.
- **`farmer_actions`**: Tracking what the farmer actually did based on a recommendation.
- **`outcomes`**: Results (e.g., Yield) mapped to actions (Farm Memory).
- **`scenarios`**: "What-If" isolated states containing JSONB variables.
- **`data_corrections`**: Audit log of farmer corrections to existing data without deleting history.

## RLS Policies
Strict Row Level Security is enforced on all tables. 
Users authenticate via Supabase Auth (JWT). 
Data access queries automatically filter based on the `auth.uid()` of the requester or propagate through ownership chains (`farm_id` -> `user_id`).

## Storage
- **Bucket**: `farmer_documents` (Private)
- **Structure**: `farmer_documents/[user_id]/[file_name]`
- **Access**: Validated via RLS on `storage.objects`.
