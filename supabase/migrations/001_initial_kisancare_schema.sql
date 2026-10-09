-- Enable necessary extensions
-- Built-in gen_random_uuid() used instead of uuid-ossp

-- PROVENANCE ENUM
CREATE TYPE provenance_type AS ENUM (
    'MEASURED',
    'ESTIMATED',
    'FARMER_ENTERED',
    'AUTOMATICALLY_COLLECTED',
    'EXTRACTED'
);

-- PROFILES
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    phone TEXT,
    preferred_language TEXT DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- FARMS
CREATE TABLE farms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    farm_name TEXT NOT NULL,
    description TEXT,
    location TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    total_area DOUBLE PRECISION,
    area_unit TEXT DEFAULT 'hectare',
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- FIELDS
CREATE TABLE fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    area DOUBLE PRECISION,
    area_unit TEXT DEFAULT 'hectare',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    boundary JSONB,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SEASONS
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_name TEXT NOT NULL,
    crop TEXT,
    crop_variety TEXT,
    sowing_date DATE,
    expected_harvest_date DATE,
    actual_harvest_date DATE,
    crop_stage TEXT,
    previous_crop TEXT,
    status TEXT DEFAULT 'PLANNED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CROP RECORDS
CREATE TABLE crop_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    crop TEXT,
    variety TEXT,
    sowing_date DATE,
    crop_stage TEXT,
    area DOUBLE PRECISION,
    planting_information JSONB,
    provenance provenance_type,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SOIL RECORDS
CREATE TABLE soil_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    ph DOUBLE PRECISION,
    nitrogen DOUBLE PRECISION,
    phosphorus DOUBLE PRECISION,
    potassium DOUBLE PRECISION,
    organic_matter DOUBLE PRECISION,
    soil_type TEXT,
    moisture DOUBLE PRECISION,
    source TEXT,
    provenance provenance_type,
    measured_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- IRRIGATION RECORDS
CREATE TABLE irrigation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    irrigation_method TEXT,
    water_availability TEXT,
    irrigation_amount DOUBLE PRECISION,
    irrigation_date DATE,
    source TEXT,
    provenance provenance_type,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WEATHER RECORDS
CREATE TABLE weather_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    location TEXT,
    temperature DOUBLE PRECISION,
    rainfall DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind DOUBLE PRECISION,
    forecast_information JSONB,
    source TEXT,
    provenance provenance_type,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- FARM DATA RECORDS
CREATE TABLE farm_data_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    record_type TEXT NOT NULL,
    record_data JSONB,
    source TEXT,
    source_reference TEXT,
    reliability DOUBLE PRECISION,
    provenance provenance_type,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- DOCUMENTS
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    farm_id UUID REFERENCES farms(id) ON DELETE SET NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    storage_path TEXT NOT NULL,
    category TEXT,
    provenance provenance_type,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extraction_status TEXT DEFAULT 'PENDING',
    metadata JSONB
);

-- MODEL VERSIONS
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    artifact_reference TEXT,
    status TEXT DEFAULT 'ACTIVE',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(model_name, model_version)
);

-- MODEL PREDICTIONS
CREATE TABLE model_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    status TEXT,
    prediction JSONB,
    unit TEXT,
    uncertainty JSONB,
    inputs_used JSONB,
    data_provenance provenance_type,
    warnings JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RECOMMENDATIONS
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    explanation TEXT,
    severity TEXT,
    status TEXT DEFAULT 'PENDING',
    supporting_prediction_ids JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    re_evaluate_at TIMESTAMP WITH TIME ZONE,
    decision_engine_version TEXT
);

-- FARMER ACTIONS
CREATE TABLE farmer_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    status TEXT,
    farmer_confirmation BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OUTCOMES
CREATE TABLE outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    related_action_id UUID REFERENCES farmer_actions(id) ON DELETE SET NULL,
    outcome_type TEXT NOT NULL,
    actual_value DOUBLE PRECISION,
    unit TEXT,
    notes TEXT,
    provenance provenance_type,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SCENARIOS
CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    scenario_name TEXT NOT NULL,
    modified_variables JSONB,
    results JSONB,
    status TEXT,
    saved_by_user BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- DATA CORRECTIONS
CREATE TABLE data_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_name TEXT NOT NULL,
    entity_id UUID NOT NULL,
    field_name TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE farms ENABLE ROW LEVEL SECURITY;
ALTER TABLE fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE crop_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE soil_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE irrigation_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE farm_data_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE farmer_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_corrections ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = user_id);

-- Farms Policies
CREATE POLICY "Users can view own farms" ON farms FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own farms" ON farms FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own farms" ON farms FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own farms" ON farms FOR DELETE USING (auth.uid() = user_id);

-- Fields Policies
CREATE POLICY "Users can access own fields" ON fields FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Seasons Policies
CREATE POLICY "Users can access own seasons" ON seasons FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid()))
);

-- Crop Records Policies
CREATE POLICY "Users can access own crop records" ON crop_records FOR ALL USING (
    season_id IN (SELECT id FROM seasons WHERE field_id IN (SELECT id FROM fields WHERE farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())))
);

-- Soil Records Policies
CREATE POLICY "Users can access own soil records" ON soil_records FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid()))
);

-- Irrigation Records Policies
CREATE POLICY "Users can access own irrigation records" ON irrigation_records FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid()))
);

-- Weather Records Policies
CREATE POLICY "Users can access own weather records" ON weather_records FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid()))
);

-- Farm Data Records Policies
CREATE POLICY "Users can access own farm data records" ON farm_data_records FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Documents Policies
CREATE POLICY "Users can access own documents" ON documents FOR ALL USING (auth.uid() = user_id);

-- Model Versions Policies
CREATE POLICY "Anyone can view model versions" ON model_versions FOR SELECT USING (true);
CREATE POLICY "Only service role can modify model versions" ON model_versions FOR ALL USING (
    auth.jwt() ->> 'role' = 'service_role' OR current_user = 'postgres' OR current_user = 'supabase_admin'
);

-- Model Predictions Policies
CREATE POLICY "Users can access own predictions" ON model_predictions FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Recommendations Policies
CREATE POLICY "Users can access own recommendations" ON recommendations FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Farmer Actions Policies
CREATE POLICY "Users can access own actions" ON farmer_actions FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Outcomes Policies
CREATE POLICY "Users can access own outcomes" ON outcomes FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Scenarios Policies
CREATE POLICY "Users can access own scenarios" ON scenarios FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Data Corrections Policies
CREATE POLICY "Users can access own corrections" ON data_corrections FOR ALL USING (auth.uid() = changed_by);

-- Create storage bucket for farmer documents
INSERT INTO storage.buckets (id, name, public) VALUES ('farmer_documents', 'farmer_documents', false) ON CONFLICT (id) DO NOTHING;

-- Service Role Bypass RLS policies (optional, standard in supabase)
-- Usually service_role automatically bypasses RLS, so explicit policies are not strictly needed.


-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_farms_updated_at BEFORE UPDATE ON farms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_fields_updated_at BEFORE UPDATE ON fields FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_seasons_updated_at BEFORE UPDATE ON seasons FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_farmer_actions_updated_at BEFORE UPDATE ON farmer_actions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scenarios_updated_at BEFORE UPDATE ON scenarios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Storage RLS Policies for farmer_documents
CREATE POLICY "Users can upload their own documents" ON storage.objects FOR INSERT TO authenticated WITH CHECK (bucket_id = 'farmer_documents' AND owner_id = (select auth.uid()::text) AND (storage.foldername(name))[1] = (select auth.uid()::text));
CREATE POLICY "Users can view their own documents" ON storage.objects FOR SELECT TO authenticated USING (bucket_id = 'farmer_documents' AND owner_id = (select auth.uid()::text));
CREATE POLICY "Users can update their own documents" ON storage.objects FOR UPDATE TO authenticated USING (bucket_id = 'farmer_documents' AND owner_id = (select auth.uid()::text)) WITH CHECK (bucket_id = 'farmer_documents' AND owner_id = (select auth.uid()::text) AND (storage.foldername(name))[1] = (select auth.uid()::text));
CREATE POLICY "Users can delete their own documents" ON storage.objects FOR DELETE TO authenticated USING (bucket_id = 'farmer_documents' AND owner_id = (select auth.uid()::text));
