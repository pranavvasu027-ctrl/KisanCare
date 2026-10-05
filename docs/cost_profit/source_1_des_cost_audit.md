# SOURCE 1: DES Cost of Cultivation Audit
    
## DATA DISCOVERED
* **Number of datasets**: Dozens of Excel/PDF files split by year.
* **Largest dataset**: National consolidated tables (~3000 rows over 15 years).
* **Observation unit**: **Crop × State × Year** (State-level aggregates).

## DATA SIZE
* **Raw rows**: ~3,000
* **Quality-approved**: 3,000
* **Leakage-approved**: 3,000
* **Final Model 6 usable rows**: 0 (for Farm-level ML), 3,000 (for State-level benchmarking).
* **Maharashtra usable rows**: ~300.

## 10,000+ TARGET
**NOT ACHIEVED**. The public data is aggregated to state averages. Unit-level farm observations are strictly not publicly downloadable as CSVs.

## TARGETS & LEAKAGE
* **Targets**: Cost C2, Cost A2+FL, Cost A2.
* **Leakage**: Seed cost, fertilizer cost, labour cost, etc. are mathematically summed to create the targets. They cannot be used as independent predictive inputs if the goal is to predict Total Cost before inputs are applied.
