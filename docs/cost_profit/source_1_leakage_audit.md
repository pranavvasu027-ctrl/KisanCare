# SOURCE 1: Leakage Audit
### SAFE INPUT
* State, Crop, Year, Yield (Expected).
### POST-OUTCOME VARIABLE / LEAKAGE
* Seed_Cost, Fertilizer_Cost, Labour_Cost, Rent, Machine_Cost.
* *Why?* Because `Total Cost (C2) = Sum of all component costs`. Using components to predict Total Cost reproduces an accounting equation, not an ML prediction.
### TARGET
* Cost_C2, Cost_A2_FL, Cost_A2.
