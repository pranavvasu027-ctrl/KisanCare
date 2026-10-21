# GeoVerse AI — Data Provenance

This file exists so nobody (including you, a reviewer, or a future
contributor) mistakes synthetic data for real transaction records.

## ✅ REAL DATA

| Field | Source | Notes |
|---|---|---|
| `latitude`, `longitude` (locality centroids) | Publicly known locality center coordinates | `src/real_geo_data.py` |
| `distance_to_metro_km` | Haversine calc vs real Pune Metro station coordinates | Computed, not estimated |
| `distance_to_highway_km` | Haversine calc vs real highway reference points | Computed, not estimated |
| `distance_to_it_hub_km` | Haversine calc vs real IT park coordinates (Hinjawadi IT Park, EON Kharadi, Magarpatta) | Computed, not estimated |
| `schools_nearby`, `hospitals_nearby`, `commercial_density` | OpenStreetMap Overpass API (live query attempted first) | **Falls back to a static snapshot table (`FALLBACK_POI_COUNTS` in `data_processing.py`) if no network is available.** That fallback table was derived from a one-time manual Overpass query, not invented. Check `poi_data_source` column in `localities_real.csv` to see which was used for your run. |

## ⚠️ SYNTHETIC DATA (documented formulas, not random noise)

| Field | How it's generated | Why it's not "real" |
|---|---|---|
| `infrastructure_score` | Fixed weighted formula over the REAL fields above (see `compute_infrastructure_score()`) | No standardized public "infrastructure score" metric exists for Indian localities |
| `avg_price_per_sqft` / `price` | Seeded from **directional, publicly-reported broad price ranges** for Pune micro-markets (2019 baseline), then grown using a rate driven by each locality's real `infrastructure_score`, plus small bounded noise | No open, licensed, per-property historical transaction registry exists for Pune |
| `population_growth_pct` | Random within a plausible bounded range (1.0%–4.5%/yr) | No open ward-level annual growth series was integrated in this version |
| `new_projects_count` | Poisson-distributed, scaled by infrastructure score | No open real-time "new projects" registry integrated in this version |
| `property_age_years`, `bedrooms`, `area_sqft` (individual properties) | Randomly distributed within realistic ranges per property type | Individual-property-level open data does not exist publicly |

## Why this design is still meaningful for ML

The synthetic fields are **not random noise disconnected from reality** —
price growth is deliberately driven by real geospatial features
(distance to metro/IT hub, POI density). This means the XGBoost models
will learn genuine, explainable relationships between **real location
characteristics** and price/growth outcomes, which is exactly what
SHAP will surface in Step 8. It also means the pipeline is a drop-in
replacement target: swap `properties_synthetic.csv` /
`property_history_synthetic.csv` for a real licensed dataset later,
and everything downstream (features, training, Flask app) keeps working.

## To replace with real data later

Provide a CSV with these exact columns and drop it in `data/raw/`:
```
locality_name, year, property_type, area_sqft, bedrooms,
property_age_years, price, price_per_sqft
```
Then re-run `src/data_processing.py`'s merge stage (Stage C) instead of
Stage B's generator.

## Reproducibility

`RANDOM_SEED = 42` is fixed in `data_processing.py` — re-running the
script produces identical synthetic data every time.
