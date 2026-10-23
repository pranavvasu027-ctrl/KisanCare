-- =====================================================================
-- Migration: 20261023000000_rental_marketplace.sql
-- Description: Agricultural Equipment, Vehicle, and Labour Rental Marketplace
-- Focus Region: Akola and Vidarbha, Maharashtra
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Rental Providers
CREATE TABLE IF NOT EXISTS rental_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- References auth.users(id) when Supabase Auth is active
    business_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    alt_phone VARCHAR(20),
    email VARCHAR(255),
    state VARCHAR(100) DEFAULT 'Maharashtra',
    district VARCHAR(100) NOT NULL DEFAULT 'Akola',
    taluka VARCHAR(100) NOT NULL,
    village VARCHAR(100),
    address TEXT,
    verified BOOLEAN DEFAULT false,
    verification_badge VARCHAR(50) DEFAULT 'unverified', -- 'verified_fpo', 'chc_authorized', 'verified_owner', 'unverified'
    verification_date TIMESTAMPTZ,
    rating NUMERIC(3, 2) DEFAULT 0.0 CHECK (rating >= 0 AND rating <= 5),
    review_count INTEGER DEFAULT 0 CHECK (review_count >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Rental Listings
CREATE TABLE IF NOT EXISTS rental_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES rental_providers(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('equipment', 'tractor', 'transport', 'labour')),
    subcategory VARCHAR(100) NOT NULL, -- e.g., 'rotavator', 'seed_drill', 'sprayer', '45hp_tractor', 'bolero_pickup', 'sowing_crew'
    description TEXT NOT NULL,
    image_url TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    
    -- Pricing and billing unit
    billing_unit VARCHAR(50) NOT NULL CHECK (
        billing_unit IN (
            'per_hour',
            'per_operating_hour',
            'per_half_day',
            'per_day',
            'per_acre',
            'per_worker_day',
            'per_worker_hour',
            'per_job',
            'per_trip',
            'per_km'
        )
    ),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    currency VARCHAR(10) DEFAULT 'INR',
    min_duration INTEGER DEFAULT 1 CHECK (min_duration >= 1),
    min_charge NUMERIC(10, 2) DEFAULT 0 CHECK (min_charge >= 0),
    
    -- Geography
    state VARCHAR(100) DEFAULT 'Maharashtra',
    district VARCHAR(100) NOT NULL DEFAULT 'Akola',
    taluka VARCHAR(100) NOT NULL,
    village VARCHAR(100),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    service_radius_km NUMERIC(6, 2) DEFAULT 25.0 CHECK (service_radius_km > 0),
    
    -- Category-specific specifications (stored structured in JSONB)
    -- e.g. { horsepower: 50, fuel_policy: "renter_bears_fuel", operator_included: true, team_size: 4, payload_tonnes: 3.5 }
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Commercial terms
    -- e.g. { cancellation_policy: "free_before_24h", deposit: 0, extra_km_rate: 25, delivery_fee: 200 }
    terms JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Listing Availability Exceptions / Custom Schedule
CREATE TABLE IF NOT EXISTS rental_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES rental_listings(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    is_available BOOLEAN DEFAULT true,
    reason VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Rental Bookings
CREATE TABLE IF NOT EXISTS rental_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_reference VARCHAR(32) UNIQUE NOT NULL, -- e.g. 'KCR-BKG-20261023-XXXX'
    listing_id UUID NOT NULL REFERENCES rental_listings(id) ON DELETE RESTRICT,
    farmer_id UUID, -- References auth.users(id)
    farmer_name VARCHAR(255) NOT NULL,
    farmer_phone VARCHAR(20) NOT NULL,
    
    -- Farm Digital Twin connection
    farm_id VARCHAR(100),
    field_id VARCHAR(100),
    field_name VARCHAR(100),
    crop_name VARCHAR(100),
    farm_location TEXT,
    farm_latitude NUMERIC(10, 7),
    farm_longitude NUMERIC(10, 7),
    
    -- Timing
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME NOT NULL DEFAULT '08:00:00',
    duration NUMERIC(8, 2) NOT NULL CHECK (duration > 0),
    billing_unit VARCHAR(50) NOT NULL,
    acreage NUMERIC(8, 2) DEFAULT 0 CHECK (acreage >= 0),
    quantity INTEGER DEFAULT 1 CHECK (quantity >= 1),
    
    -- Transparent Pricing Breakdown
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    base_rental_charge NUMERIC(10, 2) NOT NULL CHECK (base_rental_charge >= 0),
    operator_charge NUMERIC(10, 2) DEFAULT 0.0 CHECK (operator_charge >= 0),
    transport_charge NUMERIC(10, 2) DEFAULT 0.0 CHECK (transport_charge >= 0),
    add_ons_charge NUMERIC(10, 2) DEFAULT 0.0 CHECK (add_ons_charge >= 0),
    platform_fee NUMERIC(10, 2) DEFAULT 0.0 CHECK (platform_fee >= 0),
    taxes NUMERIC(10, 2) DEFAULT 0.0 CHECK (taxes >= 0),
    discounts NUMERIC(10, 2) DEFAULT 0.0 CHECK (discounts >= 0),
    total_amount NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    
    -- Payment Terms
    payment_method VARCHAR(50) DEFAULT 'pay_on_service' CHECK (payment_method IN ('pay_on_service', 'online_upi', 'escrow_advance')),
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'pay_on_delivery', 'refunded', 'disputed')),
    
    -- Booking Lifecycle State Machine
    status VARCHAR(50) NOT NULL DEFAULT 'pending_confirmation' CHECK (
        status IN (
            'draft',
            'pending_confirmation',
            'confirmed',
            'rejected',
            'cancelled',
            'in_progress',
            'completed',
            'disputed'
        )
    ),
    rejection_reason TEXT,
    cancellation_reason TEXT,
    cancelled_by VARCHAR(50),
    
    -- Dispatch / Execution Status
    dispatch_status VARCHAR(50) DEFAULT 'ready' CHECK (
        dispatch_status IN ('ready', 'dispatched', 'arrived', 'working', 'completed')
    ),
    actual_hours_used NUMERIC(6, 2),
    actual_acreage_completed NUMERIC(6, 2),
    
    -- Farm Memory / Economics Integration
    recorded_in_economics BOOLEAN DEFAULT false,
    farm_expense_id VARCHAR(100),
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_dates CHECK (end_date >= start_date)
);

-- 5. Booking Add-on Items
CREATE TABLE IF NOT EXISTS rental_booking_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES rental_bookings(id) ON DELETE CASCADE,
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('base', 'operator', 'fuel', 'implement', 'delivery', 'extra_worker', 'other')),
    item_name VARCHAR(255) NOT NULL,
    quantity NUMERIC(8, 2) DEFAULT 1.0 CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_price NUMERIC(10, 2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Verified Market Rate References (Akola & Vidarbha Benchmark Database)
CREATE TABLE IF NOT EXISTS rental_market_rate_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    region VARCHAR(100) DEFAULT 'Vidarbha',
    district VARCHAR(100) DEFAULT 'Akola',
    source_name VARCHAR(255) NOT NULL, -- e.g., 'Dr. PDKV Akola CHC Circular', 'Maharashtra Dept of Agri CHC Scheme'
    source_url TEXT,
    indicative_rate_min NUMERIC(10, 2) NOT NULL,
    indicative_rate_max NUMERIC(10, 2) NOT NULL,
    billing_unit VARCHAR(50) NOT NULL,
    fuel_included BOOLEAN DEFAULT false,
    operator_included BOOLEAN DEFAULT true,
    last_verified DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Rental Reviews
CREATE TABLE IF NOT EXISTS rental_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL UNIQUE REFERENCES rental_bookings(id) ON DELETE CASCADE,
    listing_id UUID NOT NULL REFERENCES rental_listings(id) ON DELETE CASCADE,
    farmer_id UUID,
    farmer_name VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Rental Notifications
CREATE TABLE IF NOT EXISTS rental_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    booking_id UUID REFERENCES rental_bookings(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'booking_requested', 'booking_confirmed', 'booking_rejected', 'dispatched', 'completed', 'cancelled'
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- Indexes for High Performance Queries
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_rental_listings_category ON rental_listings(category);
CREATE INDEX IF NOT EXISTS idx_rental_listings_district ON rental_listings(district);
CREATE INDEX IF NOT EXISTS idx_rental_listings_active ON rental_listings(is_active);
CREATE INDEX IF NOT EXISTS idx_rental_listings_provider ON rental_listings(provider_id);

CREATE INDEX IF NOT EXISTS idx_rental_bookings_farmer ON rental_bookings(farmer_id);
CREATE INDEX IF NOT EXISTS idx_rental_bookings_listing ON rental_bookings(listing_id);
CREATE INDEX IF NOT EXISTS idx_rental_bookings_status ON rental_bookings(status);
CREATE INDEX IF NOT EXISTS idx_rental_bookings_dates ON rental_bookings(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_rental_bookings_ref ON rental_bookings(booking_reference);

CREATE INDEX IF NOT EXISTS idx_rental_reviews_listing ON rental_reviews(listing_id);
CREATE INDEX IF NOT EXISTS idx_rental_notifications_user ON rental_notifications(user_id, is_read);

-- =====================================================================
-- Row Level Security (RLS) Policies
-- =====================================================================
ALTER TABLE rental_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_booking_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_market_rate_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE rental_notifications ENABLE ROW LEVEL SECURITY;

-- Providers: Public can view active providers; authenticated user can update their own
CREATE POLICY "Public providers read policy" ON rental_providers
    FOR SELECT USING (true);

CREATE POLICY "Owner update own provider profile" ON rental_providers
    FOR ALL USING (auth.uid() = user_id);

-- Listings: Anyone can view active listings; providers manage their own
CREATE POLICY "Public view active listings" ON rental_listings
    FOR SELECT USING (is_active = true);

CREATE POLICY "Providers manage own listings" ON rental_listings
    FOR ALL USING (
        provider_id IN (SELECT id FROM rental_providers WHERE user_id = auth.uid())
    );

-- Bookings: Farmer reads/manages own bookings; Provider reads/updates bookings on their listings
CREATE POLICY "Farmer view own bookings" ON rental_bookings
    FOR SELECT USING (
        auth.uid() = farmer_id OR
        listing_id IN (
            SELECT l.id FROM rental_listings l
            JOIN rental_providers p ON l.provider_id = p.id
            WHERE p.user_id = auth.uid()
        )
    );

CREATE POLICY "Farmer insert booking" ON rental_bookings
    FOR INSERT WITH CHECK (
        auth.uid() = farmer_id OR auth.uid() IS NULL -- Allow demo / guest booking fallback
    );

CREATE POLICY "Authorized update booking" ON rental_bookings
    FOR UPDATE USING (
        auth.uid() = farmer_id OR
        listing_id IN (
            SELECT l.id FROM rental_listings l
            JOIN rental_providers p ON l.provider_id = p.id
            WHERE p.user_id = auth.uid()
        )
    );

-- Market rates: Public read-only
CREATE POLICY "Public read market rates" ON rental_market_rate_references
    FOR SELECT USING (true);

-- Reviews: Public read
CREATE POLICY "Public read reviews" ON rental_reviews
    FOR SELECT USING (true);

CREATE POLICY "Farmer insert review" ON rental_reviews
    FOR INSERT WITH CHECK (auth.uid() = farmer_id OR auth.uid() IS NULL);

-- Notifications: User read/update own notifications
CREATE POLICY "User notifications policy" ON rental_notifications
    FOR ALL USING (auth.uid() = user_id OR auth.uid() IS NULL);
