# Farm Digital Twin Foundation

## Concept
The Farm Digital Twin is a conceptual representation of a physical farm. It serves as the shared state used by KisanCare's prediction and simulation systems (the "What-If Simulator" and "Decision & Optimization Engine"). 

*Note: This is a foundational schema. A complex digital twin is not yet implemented.*

## Conceptual Farm Object Schema

Below are the fields for the conceptual farm object, detailing what is currently implemented, planned, or a future data source:

| Field | Description | Status |
|---|---|---|
| `farm_id` | Unique identifier for the farm | Planned |
| `farmer_id` | Identifier for the farm owner/user | Planned |
| `location` | Geospatial data (Lat/Lon, Region) | Future Data Source |
| `area` | Size of the farm (e.g., in hectares) | Planned |
| `current_crop` | The crop currently being grown | Planned |
| `soil` | Soil parameters (N, P, K, pH) | **Implemented (in Model 1)** |
| `weather` | Weather conditions (Temperature, Humidity, Rainfall) | **Implemented (in Model 1)** |
| `water` | Irrigation data and water availability | Future Data Source |
| `crop_health` | Disease/Pest presence, growth stage | Planned |
| `costs` | Input costs (seeds, fertilizer, labor, etc.) | Planned |
| `yield` | Expected or historical yield | Planned |
| `market` | Current and forecasted market prices | Future Data Source |
| `risk` | Calculated risks (weather, pest, financial) | Planned |
| `farm_history` | Historical logs of previous seasons | Future Data Source |

## Usage
Eventually, as the 8 core AI models are developed, they will read from and write to this shared Digital Twin state to provide comprehensive, integrated farm decision intelligence.
