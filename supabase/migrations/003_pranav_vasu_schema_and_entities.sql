-- KisanCare Relational Database Schema Migration: 003_pranav_vasu_schema_and_entities.sql
-- Safely expands existing entities and adds specialized tables with foreign keys and RLS policies.

-- 1. PROFILES ENHANCEMENTS
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS age INTEGER;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS gender TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS village TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS district TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS state TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'India';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS farming_experience TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS farmer_category TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'farmer';

-- 2. FARMS ENHANCEMENTS
ALTER TABLE farms ADD COLUMN IF NOT EXISTS land_ownership TEXT DEFAULT 'Owned';
ALTER TABLE farms ADD COLUMN IF NOT EXISTS terrain TEXT;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS drainage TEXT;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS boundaries_mapped BOOLEAN DEFAULT FALSE;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS nearby_features TEXT;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS local_soil_description TEXT;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS reported_locations_count INTEGER DEFAULT 1;
ALTER TABLE farms ADD COLUMN IF NOT EXISTS unallocated_area NUMERIC(10, 2) DEFAULT 0.0;

-- 3. FIELDS ENHANCEMENTS
ALTER TABLE fields ADD COLUMN IF NOT EXISTS terrain TEXT;
ALTER TABLE fields ADD COLUMN IF NOT EXISTS soil_description TEXT;
ALTER TABLE fields ADD COLUMN IF NOT EXISTS soil_depth TEXT;
ALTER TABLE fields ADD COLUMN IF NOT EXISTS location_precision TEXT;

-- 4. FARM ACTIVITIES
CREATE TABLE IF NOT EXISTS farm_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    activity_type TEXT NOT NULL, -- 'planting', 'spraying', 'fertilizer', 'irrigation', 'labour', 'machinery'
    description TEXT,
    cost NUMERIC(12, 2),
    currency TEXT DEFAULT 'INR',
    activity_date DATE DEFAULT CURRENT_DATE,
    provenance provenance_type DEFAULT 'FARMER_ENTERED',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. FARM COSTS
CREATE TABLE IF NOT EXISTS farm_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    category TEXT NOT NULL, -- 'Land preparation', 'Seed cost', 'Fertilizer', 'Pesticide', 'Labour', 'Machinery', 'Irrigation', 'Transport', 'Other'
    amount NUMERIC(12, 2),
    amount_min NUMERIC(12, 2),
    amount_max NUMERIC(12, 2),
    currency TEXT DEFAULT 'INR',
    raw_entry TEXT,
    cost_basis TEXT,
    basis_ambiguity TEXT,
    status TEXT DEFAULT 'CONFIRMED', -- 'CONFIRMED', 'NEEDS_CLARIFICATION'
    cost_date DATE,
    provenance provenance_type DEFAULT 'FARMER_ENTERED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. YIELD RECORDS
CREATE TABLE IF NOT EXISTS yield_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE NOT NULL,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    crop TEXT NOT NULL,
    yield_type TEXT NOT NULL DEFAULT 'CURRENT', -- 'HISTORICAL_BENCHMARK', 'CURRENT_ACTUAL', 'TARGET'
    quantity NUMERIC(10, 2) NOT NULL,
    unit TEXT NOT NULL DEFAULT 'quintal/acre',
    harvest_date DATE,
    notes TEXT,
    provenance provenance_type DEFAULT 'FARMER_ENTERED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. SALES RECORDS
CREATE TABLE IF NOT EXISTS sales_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    crop TEXT NOT NULL,
    quantity_sold NUMERIC(10, 2) DEFAULT 0.0,
    unit TEXT DEFAULT 'quintal',
    price_per_unit NUMERIC(12, 2),
    currency TEXT DEFAULT 'INR',
    market_name TEXT, -- e.g. 'Akot APMC'
    selling_channel TEXT, -- e.g. 'APMC / local trader'
    transport_cost NUMERIC(10, 2),
    sale_date DATE,
    is_external_observation BOOLEAN DEFAULT FALSE,
    observation_source TEXT,
    observation_date DATE,
    notes TEXT,
    provenance provenance_type DEFAULT 'FARMER_ENTERED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. FARM RISK ASSESSMENTS
CREATE TABLE IF NOT EXISTS farm_risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    season_id UUID REFERENCES seasons(id) ON DELETE SET NULL,
    risk_level TEXT NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH', 'SEVERE'
    risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    drought_stress_status TEXT,
    mitigation_recommendations JSONB DEFAULT '[]'::jsonb,
    model_version TEXT,
    provenance provenance_type DEFAULT 'AUTOMATICALLY_COLLECTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. SIMULATION RUNS (What-If Scenarios)
CREATE TABLE IF NOT EXISTS simulation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    scenario_name TEXT NOT NULL,
    assumptions JSONB NOT NULL,
    baseline_output JSONB NOT NULL,
    simulated_output JSONB NOT NULL,
    differences JSONB NOT NULL,
    uncertainty_level TEXT,
    is_saved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. COPILOT CONVERSATIONS AND MESSAGES
CREATE TABLE IF NOT EXISTS copilot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    farm_id UUID REFERENCES farms(id) ON DELETE SET NULL,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS copilot_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES copilot_conversations(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    grounded_context JSONB,
    model_version TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. FARM MEMORY
CREATE TABLE IF NOT EXISTS farm_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID REFERENCES farms(id) ON DELETE CASCADE NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    topic TEXT NOT NULL,
    fact_description TEXT NOT NULL,
    verified BOOLEAN DEFAULT TRUE,
    source TEXT,
    provenance provenance_type DEFAULT 'FARMER_ENTERED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on all newly created tables
ALTER TABLE farm_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE farm_costs ENABLE ROW LEVEL SECURITY;
ALTER TABLE yield_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE farm_risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE copilot_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE farm_memory ENABLE ROW LEVEL SECURITY;

-- Farm Activities Policies
CREATE POLICY "Users can access own farm activities" ON farm_activities FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Farm Costs Policies
CREATE POLICY "Users can access own farm costs" ON farm_costs FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Yield Records Policies
CREATE POLICY "Users can access own yield records" ON yield_records FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Sales Records Policies
CREATE POLICY "Users can access own sales records" ON sales_records FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Farm Risk Policies
CREATE POLICY "Users can access own risk assessments" ON farm_risk_assessments FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Simulation Runs Policies
CREATE POLICY "Users can access own simulation runs" ON simulation_runs FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Copilot Conversations Policies
CREATE POLICY "Users can access own copilot conversations" ON copilot_conversations FOR ALL USING (
    user_id = auth.uid()
);

-- Copilot Messages Policies
CREATE POLICY "Users can access own copilot messages" ON copilot_messages FOR ALL USING (
    user_id = auth.uid()
);

-- Farm Memory Policies
CREATE POLICY "Users can access own farm memory" ON farm_memory FOR ALL USING (
    farm_id IN (SELECT id FROM farms WHERE user_id = auth.uid())
);

-- Triggers for updated_at
CREATE TRIGGER update_farm_costs_updated_at BEFORE UPDATE ON farm_costs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_copilot_conversations_updated_at BEFORE UPDATE ON copilot_conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
