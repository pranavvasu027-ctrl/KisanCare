# Data Model

The KisanCare application models the Farm Digital Twin.

## Core Entities

### Farmer
- `farmer_id` (UUID)
- `name` (String)
- `contact` (String)

### Farm (The Digital Twin Root)
- `farm_id` (UUID)
- `farmer_id` (UUID)
- `location` (GeoJSON/Point)
- `area` (Float)
- `soil_type` (String)

### FarmHistory
Tracks historical data for learning.
- `history_id` (UUID)
- `farm_id` (UUID)
- `season` (String)
- `crop_grown` (String)
- `actual_yield` (Float)
- `actual_profit` (Float)

### Simulation
Tracks "What-If" scenarios.
- `sim_id` (UUID)
- `farm_id` (UUID)
- `scenario_parameters` (JSON)
- `baseline_results` (JSON)
- `scenario_results` (JSON)
